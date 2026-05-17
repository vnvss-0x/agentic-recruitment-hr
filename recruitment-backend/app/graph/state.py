"""
RecruitmentState — État global partagé du graphe LangGraph.

Ce module définit la structure TypedDict qui constitue le contrat
de données entre tous les agents du pipeline de recrutement.

Principe :
    Chaque agent reçoit une copie de cet état, l'enrichit avec
    ses sorties, et retourne les champs mis à jour. LangGraph
    fusionne automatiquement les modifications dans l'état global.

Flux de données :
    RawJobOffer ──► Agent1 ──► JobProfile
                                  │
                              RawCV list ──► Agent2 ──► CandidateProfile list
                                                              │
                                                        HITL 1 (RH)
                                                              │
                                                        Agent3 ──► Interview questions
                                                              │
                                                        Agent4 ──► Evaluations
                                                              │
                                                        HITL 2 (Manager)
                                                              │
                                                        Agent5 ──► Final Report
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.models.candidate import CandidateProfile, RawCV
from app.models.evaluation import InterviewEvaluation
from app.models.hitl import HRShortlistValidation, ManagerFinalValidation
from app.models.interview import InterviewQuestionSet, InterviewResponseSet
from app.models.job import JobProfile, RawJobOffer
from app.models.report import FinalReport

# ─────────────────────────────────────────────
# Enum — Étapes du pipeline
# ─────────────────────────────────────────────


class PipelineStep(str, Enum):
    """
    Étapes séquentielles du workflow de recrutement.
    Permet de tracer la progression dans l'UI et les logs.
    """

    INITIALIZED = "initialized"
    JOB_ANALYSIS = "job_analysis"  # Agent 1 en cours
    JOB_ANALYSIS_DONE = "job_analysis_done"
    CV_SCREENING = "cv_screening"  # Agent 2 en cours
    CV_SCREENING_DONE = "cv_screening_done"
    HITL_1_PENDING = "hitl_1_pending"  # Attente validation RH
    HITL_1_DONE = "hitl_1_done"
    INTERVIEW_GENERATION = "interview_generation"  # Agent 3
    INTERVIEW_GENERATION_DONE = "interview_generation_done"
    INTERVIEW_RESPONSES_PENDING = "interview_responses_pending"
    INTERVIEW_RESPONSES_DONE = "interview_responses_done"
    INTERVIEW_ANALYSIS = "interview_analysis"  # Agent 4
    INTERVIEW_ANALYSIS_DONE = "interview_analysis_done"
    HITL_2_PENDING = "hitl_2_pending"  # Attente validation Manager
    HITL_2_DONE = "hitl_2_done"
    REPORT_GENERATION = "report_generation"  # Agent 5
    REPORT_GENERATION_DONE = "report_generation_done"
    COMPLETED = "completed"
    ERROR = "error"


class PipelineError(TypedDict, total=False):
    """Structure d'une erreur survenue dans le pipeline."""

    step: str  # Étape où l'erreur s'est produite
    agent: str  # Nom de l'agent fautif
    message: str  # Message d'erreur
    recoverable: bool  # True si le pipeline peut continuer


# ─────────────────────────────────────────────
# RecruitmentState — Définition principale
# ─────────────────────────────────────────────


class RecruitmentState(TypedDict, total=False):
    """
    État global partagé entre tous les nœuds du graphe LangGraph.

    Convention de nommage des champs :
        - Champs d'entrée      : raw_*
        - Sorties Agent 1      : job_profile
        - Sorties Agent 2      : candidate_profiles, shortlisted_ids
        - Sorties HITL 1       : hr_validation
        - Sorties Agent 3      : interview_questions
        - Sorties Agent 4      : interview_evaluations
        - Sorties HITL 2       : manager_validation
        - Sorties Agent 5      : final_report
        - Métadonnées système  : session_id, current_step, errors, logs

    Note sur `total=False` :
        Tous les champs sont optionnels au niveau TypedDict car le state
        est construit progressivement. Les agents valident eux-mêmes
        la présence des champs requis.
    """

    # ── Métadonnées de session ─────────────────────────────────────
    session_id: str
    """Identifiant unique de la session de recrutement (UUID)."""

    current_step: PipelineStep
    """Étape courante du pipeline, mise à jour par chaque agent."""

    created_at: str
    """Timestamp ISO 8601 de création de la session."""

    # ── Messages LangGraph (pour le débogage et la traçabilité) ───
    messages: Annotated[List[Any], add_messages]
    """
    Historique des messages LangGraph.
    Le reducer `add_messages` fusionne automatiquement les nouveaux
    messages avec ceux existants (pas d'écrasement).
    """

    # ── Entrées brutes ─────────────────────────────────────────────
    raw_job_offer: RawJobOffer
    """Offre d'emploi brute fournie par l'utilisateur (texte ou PDF)."""

    raw_cvs: List[RawCV]
    """Liste des CVs bruts uploadés par l'utilisateur."""

    # ── Sorties Agent 1 — Analyse du Poste ────────────────────────
    job_profile: Optional[JobProfile]
    """
    Profil structuré du poste produit par l'Agent 1.
    Contient : compétences, niveau, responsabilités, profil idéal.
    """

    rag_job_context: Optional[List[Dict[str, Any]]]
    """
    Documents similaires récupérés depuis ChromaDB par le RAG.
    Utilisés par l'Agent 1 pour enrichir son analyse du poste.
    Format : [{"content": str, "metadata": dict, "score": float}]
    """

    # ── Sorties Agent 2 — Screening CVs ───────────────────────────
    candidate_profiles: Optional[List[CandidateProfile]]
    """
    Profils analysés de tous les candidats, triés par score décroissant.
    Chaque profil contient : score, matching, forces/faiblesses.
    """

    shortlisted_candidate_ids: Optional[List[str]]
    """
    IDs des candidats retenus pour la shortlist initiale.
    Générés par l'Agent 2, potentiellement modifiés par HITL 1.
    """

    screening_summary: Optional[str]
    """Résumé textuel du screening produit par l'Agent 2."""

    # ── HITL 1 — Validation RH ────────────────────────────────────
    hr_validation: Optional[HRShortlistValidation]
    """
    Décision du responsable RH sur la shortlist.
    Renseigné lors de l'interruption HITL 1.
    """

    validated_shortlist_ids: Optional[List[str]]
    """
    IDs définitifs des candidats validés par le RH.
    Fusion de shortlisted_candidate_ids + modifications HITL 1.
    """

    # ── Sorties Agent 3 — Génération des Entretiens ───────────────
    interview_questions: Optional[Dict[str, InterviewQuestionSet]]
    """
    Questions d'entretien générées par l'Agent 3.
    Structure : {candidate_id: {"technical": [...], "behavioral": [...], "situational": [...]}}
    """

    interview_responses: Optional[Dict[str, InterviewResponseSet]]
    """
    Reponses des candidats aux questions d'entretien.
    Fournies par l'utilisateur via l'interface web.
    Structure : {candidate_id: InterviewResponseSet}
    """

    # ── Sorties Agent 4 — Analyse des Entretiens ──────────────────
    interview_evaluations: Optional[Dict[str, InterviewEvaluation]]
    """
    Évaluations détaillées par candidat produites par l'Agent 4.
    Structure : {
        candidate_id: {
            "technical_score": float,
            "behavioral_score": float,
            "global_score": float,
            "recommendation": RecruitmentDecision,
            "justification": str,
            "strengths": [...],
            "concerns": [...]
        }
    }
    """

    recommended_candidate_id: Optional[str]
    """ID du candidat le mieux évalué, recommandé par l'Agent 4."""

    # ── HITL 2 — Validation Managériale ───────────────────────────
    manager_validation: Optional[ManagerFinalValidation]
    """
    Décision finale du manager.
    Renseigné lors de l'interruption HITL 2.
    """

    # ── Sorties Agent 5 — Rapport Final ───────────────────────────
    final_report: Optional[FinalReport]
    """
    Rapport RH complet consolide par l'Agent 5.
    Structure basee sur le modele FinalReport.
    """

    # ── Évaluation des Prompts ────────────────────────────────────
    prompt_metrics: Optional[Dict[str, Any]]
    """
    Métriques de qualité des prompts collectées pendant l'exécution.
    Utilisées par le module d'évaluation A/B.
    Structure : {agent_name: {"latency_ms": float, "tokens": int, ...}}
    """

    # ── Gestion des erreurs ───────────────────────────────────────
    errors: Optional[List[PipelineError]]
    """Liste des erreurs survenues dans le pipeline (non bloquantes)."""

    has_critical_error: Optional[bool]
    """True si une erreur critique a interrompu le pipeline."""

    # ── Logs temps réel (diffusés via WebSocket) ──────────────────
    activity_log: Optional[List[str]]
    """
    Journal d'activité horodaté envoyé au frontend via WebSocket.
    Chaque entrée : "[HH:MM:SS] [AGENT_NAME] Message d'activité"
    """


# ─────────────────────────────────────────────
# Helpers — Initialiseur d'état
# ─────────────────────────────────────────────


def create_initial_state(
    session_id: str,
    raw_job_offer: RawJobOffer,
    raw_cvs: List[RawCV],
    created_at: str,
) -> RecruitmentState:
    """
    Crée un RecruitmentState initialisé avec les valeurs par défaut.

    Args:
        session_id:     UUID de la session de recrutement.
        raw_job_offer:  Offre d'emploi brute fournie par l'utilisateur.
        raw_cvs:        Liste des CVs bruts uploadés.
        created_at:     Timestamp ISO 8601.

    Returns:
        RecruitmentState prêt à être injecté dans le graphe LangGraph.
    """
    return RecruitmentState(
        session_id=session_id,
        current_step=PipelineStep.INITIALIZED,
        created_at=created_at,
        messages=[],
        # Entrées
        raw_job_offer=raw_job_offer,
        raw_cvs=raw_cvs,
        # Tous les champs agents initialisés à None
        job_profile=None,
        rag_job_context=None,
        candidate_profiles=None,
        shortlisted_candidate_ids=None,
        screening_summary=None,
        hr_validation=None,
        validated_shortlist_ids=None,
        interview_questions=None,
        interview_responses=None,
        interview_evaluations=None,
        recommended_candidate_id=None,
        manager_validation=None,
        final_report=None,
        prompt_metrics=None,
        # Gestion des erreurs
        errors=[],
        has_critical_error=False,
        # Logs
        activity_log=[],
    )
