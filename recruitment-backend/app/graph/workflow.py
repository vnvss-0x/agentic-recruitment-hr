"""
Workflow LangGraph — Orchestration du Pipeline de Recrutement.

Ce module définit le graphe d'exécution complet du système multi-agents.
Il est le point central qui relie tous les agents, les transitions,
les conditions et les interruptions HITL.

Architecture du graphe :
    START
      │
      ▼
  [job_analyzer_node]          ← Agent 1 : Analyse du poste
      │
      ▼
  [cv_screener_node]           ← Agent 2 : Screening des CVs       [TODO]
      │
      ▼
  [hitl_hr_validation]         ← HITL 1  : Validation RH shortlist [TODO]
      │
      ├─► (réanalyse) ─────────────────────────────────► [cv_screener_node]
      │
      ▼
  [interview_generator_node]   ← Agent 3 : Génération entretiens   [TODO]
      │
      ▼
  [interview_analyzer_node]    ← Agent 4 : Analyse entretiens      [TODO]
      │
      ▼
  [hitl_manager_validation]    ← HITL 2  : Décision managériale    [TODO]
      │
      ├─► (entretien suppl.) ──────────────────────────► [interview_generator_node]
      │
      ▼
  [report_generator_node]      ← Agent 5 : Rapport final RH        [TODO]
      │
      ▼
    END

Gestion des erreurs :
    Chaque nœud peut positionner has_critical_error=True dans le state.
    L'edge conditionnel `route_on_error` détecte cette condition et
    redirige vers le nœud END pour arrêter proprement le pipeline.
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.cv_screener import cv_screener_node
from app.agents.interview_analyzer import interview_analyzer_node
from app.agents.interview_generator import interview_generator_node
from app.agents.job_analyzer import job_analyzer_node
from app.agents.report_generator import report_generator_node
from app.graph.hitl_manager import hitl_hr_node, hitl_manager_node
from app.graph.state import PipelineStep, RecruitmentState

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Constantes — Noms des nœuds
# ─────────────────────────────────────────────
# Centraliser les noms évite les fautes de frappe dans add_edge / add_node.

NODE_JOB_ANALYZER = "job_analyzer"
NODE_CV_SCREENER = "cv_screener"  # Agent 2  [TODO]
NODE_HITL_HR = "hitl_hr_validation"  # HITL 1   [TODO]
NODE_INTERVIEW_GENERATOR = "interview_generator"  # Agent 3  [TODO]
NODE_INTERVIEW_ANALYZER = "interview_analyzer"  # Agent 4  [TODO]
NODE_HITL_MANAGER = "hitl_manager_validation"  # HITL 2   [TODO]
NODE_REPORT_GENERATOR = "report_generator"  # Agent 5  [TODO]


# ─────────────────────────────────────────────
# Conditions de routage (edges conditionnels)
# ─────────────────────────────────────────────


def route_on_error(state: RecruitmentState) -> str:
    """
    Condition universelle de détection d'erreur critique.

    Si un agent a positionné has_critical_error=True dans le state,
    on court-circuite le reste du pipeline et on va directement à END.

    Returns:
        "end"       si une erreur critique est détectée.
        "continue"  sinon (le nœud suivant normal sera exécuté).
    """
    if state.get("has_critical_error"):
        logger.error(
            "[Workflow] Erreur critique détectée — " "interruption du pipeline."
        )
        return "end"
    return "continue"


def route_after_hitl_hr(state: RecruitmentState) -> str:
    """
    Condition de routage après la validation HITL 1 (RH).

    Si le RH demande une réanalyse, on retourne vers cv_screener.
    Sinon on continue vers la génération d'entretiens.

    Returns:
        "reanalyze"  si une réanalyse des CVs est demandée.
        "continue"   pour passer à la génération d'entretiens.
    """
    hr_validation = state.get("hr_validation")
    if hr_validation:
        from app.models.hitl import HITLStatus

        if hr_validation.status in (
            HITLStatus.REANALYSIS_REQUESTED,
            HITLStatus.REJECTED,
        ):
            logger.info("[Workflow] RH demande une réanalyse des CVs.")
            return "reanalyze"
    return "continue"


def route_after_hitl_manager(state: RecruitmentState) -> str:
    """
    Condition de routage après la validation HITL 2 (Manager).

    Trois cas possibles :
        - "hire"                → rapport final (Agent 5)
        - "additional_interview"→ retour à la génération d'entretiens
        - "cancel"              → fin du pipeline

    Returns:
        "hire" | "additional_interview" | "cancel"
    """
    manager_validation = state.get("manager_validation")
    if manager_validation:
        from app.models.hitl import ManagerDecision
        from app.models.hitl import HITLStatus

        if manager_validation.status == HITLStatus.REJECTED:
            logger.info("[Workflow] Manager rejette le processus.")
            return "cancel"

        decision = manager_validation.decision
        if decision == ManagerDecision.ADDITIONAL_INTERVIEW:
            logger.info("[Workflow] Manager demande un entretien supplémentaire.")
            return "additional_interview"
        if decision == ManagerDecision.CANCEL:
            logger.info("[Workflow] Manager annule le processus.")
            return "cancel"
    return "hire"


# ─────────────────────────────────────────────
# Constructeur du graphe
# ─────────────────────────────────────────────


def build_recruitment_graph() -> StateGraph:
    """
    Construit et compile le graphe LangGraph du pipeline de recrutement.

    Le graphe utilise un MemorySaver comme checkpointer, ce qui permet :
    - la persistance de l'état entre les nœuds,
    - les interruptions HITL (le graphe se suspend et reprend),
    - le rejoue partiel depuis un checkpoint.

    Returns:
        Graphe LangGraph compilé, prêt à être invoqué via
        `graph.invoke(state, config)` ou `graph.stream(state, config)`.
    """

    # ── Instanciation du graphe avec le state typé ────────────────
    graph = StateGraph(RecruitmentState)

    # ─────────────────────────────────────────────────────────────
    # NŒUDS
    # Chaque add_node associe un nom de nœud à sa fonction handler.
    # ─────────────────────────────────────────────────────────────

    # ✅ Agent 1 — Implémenté
    graph.add_node(NODE_JOB_ANALYZER, job_analyzer_node)

    # ✅ Agent 2
    graph.add_node(NODE_CV_SCREENER, cv_screener_node)

    # ✅ HITL 1
    graph.add_node(NODE_HITL_HR, hitl_hr_node)

    # ✅ Agent 3
    graph.add_node(NODE_INTERVIEW_GENERATOR, interview_generator_node)

    # ✅ Agent 4
    graph.add_node(NODE_INTERVIEW_ANALYZER, interview_analyzer_node)

    # ✅ HITL 2
    graph.add_node(NODE_HITL_MANAGER, hitl_manager_node)

    # ✅ Agent 5
    graph.add_node(NODE_REPORT_GENERATOR, report_generator_node)

    # ─────────────────────────────────────────────────────────────
    # EDGES SÉQUENTIELS
    # Flux principal du pipeline de recrutement.
    # ─────────────────────────────────────────────────────────────

    # START ──► Agent 1
    graph.add_edge(START, NODE_JOB_ANALYZER)

    # Agent 1 ──► [vérification erreur] ──► Agent 2 | END
    graph.add_conditional_edges(
        NODE_JOB_ANALYZER,
        route_on_error,
        {
            "continue": NODE_CV_SCREENER,
            "end": END,
        },
    )

    # Agent 2 ──► [vérification erreur] ──► HITL 1 | END
    graph.add_conditional_edges(
        NODE_CV_SCREENER,
        route_on_error,
        {
            "continue": NODE_HITL_HR,
            "end": END,
        },
    )

    # HITL 1 ──► [décision RH] ──► Agent 3 | Agent 2 (réanalyse)
    graph.add_conditional_edges(
        NODE_HITL_HR,
        route_after_hitl_hr,
        {
            "continue": NODE_INTERVIEW_GENERATOR,
            "reanalyze": NODE_CV_SCREENER,
        },
    )

    # Agent 3 ──► [vérification erreur] ──► Agent 4 | END
    graph.add_conditional_edges(
        NODE_INTERVIEW_GENERATOR,
        route_on_error,
        {
            "continue": NODE_INTERVIEW_ANALYZER,
            "end": END,
        },
    )

    # Agent 4 ──► [vérification erreur] ──► HITL 2 | END
    graph.add_conditional_edges(
        NODE_INTERVIEW_ANALYZER,
        route_on_error,
        {
            "continue": NODE_HITL_MANAGER,
            "end": END,
        },
    )

    # HITL 2 ──► [décision Manager] ──► Agent 5 | Agent 3 | END
    graph.add_conditional_edges(
        NODE_HITL_MANAGER,
        route_after_hitl_manager,
        {
            "hire": NODE_REPORT_GENERATOR,
            "additional_interview": NODE_INTERVIEW_GENERATOR,
            "cancel": END,
        },
    )

    # Agent 5 ──► END
    graph.add_edge(NODE_REPORT_GENERATOR, END)

    # ─────────────────────────────────────────────────────────────
    # COMPILATION
    # Le checkpointer MemorySaver maintient l'état en mémoire.
    # En production, remplacer par SqliteSaver ou PostgresSaver.
    # ─────────────────────────────────────────────────────────────
    checkpointer = MemorySaver()

    compiled_graph = graph.compile(
        checkpointer=checkpointer,
        # Points d'interruption HITL — le graphe se suspend ici
        # et attend une reprise explicite via graph.invoke(None, config).
        interrupt_before=[NODE_HITL_HR, NODE_HITL_MANAGER],
    )

    logger.info(
        "[Workflow] Graphe de recrutement compilé avec succès. "
        f"Nœuds : {list(compiled_graph.get_graph().nodes.keys())}"
    )

    return compiled_graph


# ─────────────────────────────────────────────
# Instance singleton du graphe
# ─────────────────────────────────────────────
# Importée par les routes FastAPI et le service WebSocket.
# Initialisée une seule fois au démarrage de l'application.

recruitment_graph = build_recruitment_graph()
