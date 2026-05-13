"""
Agent 1 — Analyse du Poste (Job Analyzer).

Responsabilités :
    - Extraire les compétences techniques et soft skills de l'offre brute.
    - Déterminer le niveau d'expérience requis.
    - Produire un JobProfile structuré (modèle Pydantic validé).
    - Enrichir l'analyse via le contexte RAG (postes similaires).
    - Mettre à jour le RecruitmentState avec job_profile et current_step.

Position dans le graphe :
    START ──► [job_analyzer_node] ──► cv_screener_node (Agent 2)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.state import PipelineError, PipelineStep, RecruitmentState
from app.models.job import (
    ContractType,
    ExperienceLevel,
    JobProfile,
    SalaryRange,
    SoftSkill,
    TechnicalSkill,
    WorkMode,
)
from app.prompts.job_analyzer_prompts import (
    JOB_ANALYZER_SYSTEM_PROMPT,
    build_main_prompt,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────

AGENT_NAME = "JobAnalyzer"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 4096


# ─────────────────────────────────────────────
# Helpers internes
# ─────────────────────────────────────────────


def _build_llm() -> ChatGoogleGenerativeAI:
    """
    Instancie le modèle Gemini Flash avec les paramètres de l'Agent 1.

    La clé API est lue automatiquement depuis la variable d'environnement
    GOOGLE_API_KEY (chargée via python-dotenv dans core/config.py).
    """
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        # Désactive le safety filtering agressif pour le contexte RH
        convert_system_message_to_human=False,
    )


def _log_activity(state: RecruitmentState, message: str) -> list[str]:
    """
    Ajoute une entrée horodatée au journal d'activité.

    Returns:
        Nouvelle liste activity_log à fusionner dans le state.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] [{AGENT_NAME}] {message}"
    logger.info(entry)

    existing: list[str] = state.get("activity_log") or []
    return existing + [entry]


def _parse_llm_response(raw_content: str) -> dict[str, Any]:
    """
    Parse la réponse JSON du LLM de manière sécurisée.

    Stratégie :
        1. Essai de parsing direct.
        2. Extraction entre balises ```json ... ``` si présentes.
        3. Recherche du premier '{' au cas où il y a du texte parasite.

    Raises:
        ValueError: Si aucune stratégie ne produit un JSON valide.
    """
    content = raw_content.strip()

    # Stratégie 1 — parsing direct
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Stratégie 2 — extraction depuis bloc markdown
    if "```json" in content:
        try:
            start = content.index("```json") + 7
            end = content.index("```", start)
            return json.loads(content[start:end].strip())
        except (ValueError, json.JSONDecodeError):
            pass

    # Stratégie 3 — extraction depuis le premier '{'
    try:
        start = content.index("{")
        end = content.rindex("}") + 1
        return json.loads(content[start:end])
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Impossible de parser la réponse JSON du LLM.\n"
            f"Contenu reçu (100 premiers chars) : {content[:100]}"
        ) from exc


def _build_job_profile(data: dict[str, Any], raw_filename: str | None) -> JobProfile:
    """
    Construit et valide un JobProfile Pydantic depuis le dict JSON du LLM.

    Applique des valeurs par défaut sécurisées pour les champs manquants
    et mappe les strings vers les Enums correspondants.

    Args:
        data:         Dictionnaire JSON parsé depuis la réponse du LLM.
        raw_filename: Nom du fichier source (pour les notes de débogage).

    Returns:
        JobProfile validé par Pydantic.
    """
    # ── Compétences techniques ─────────────────────────────────────
    technical_skills = [
        TechnicalSkill(
            name=skill.get("name", ""),
            level=skill.get("level"),
            is_mandatory=skill.get("is_mandatory", True),
        )
        for skill in data.get("technical_skills", [])
        if skill.get("name")  # filtre les entrées vides
    ]

    # ── Soft skills ────────────────────────────────────────────────
    soft_skills = [
        SoftSkill(
            name=skill.get("name", ""),
            description=skill.get("description"),
        )
        for skill in data.get("soft_skills", [])
        if skill.get("name")
    ]

    # ── Fourchette salariale ───────────────────────────────────────
    salary_range: SalaryRange | None = None
    if salary_data := data.get("salary_range"):
        if salary_data.get("min_value") or salary_data.get("max_value"):
            salary_range = SalaryRange(
                min_value=salary_data.get("min_value"),
                max_value=salary_data.get("max_value"),
                currency=salary_data.get("currency", "EUR"),
                is_estimated=salary_data.get("is_estimated", False),
            )

    # ── Mapping Enums avec fallback sécurisé ──────────────────────
    try:
        experience_level = ExperienceLevel(data.get("experience_level", "mid"))
    except ValueError:
        logger.warning("Niveau d'expérience inconnu, fallback sur 'mid'.")
        experience_level = ExperienceLevel.MID

    try:
        contract_type = ContractType(data.get("contract_type", "CDI"))
    except ValueError:
        contract_type = ContractType.OTHER

    try:
        work_mode = WorkMode(data.get("work_mode", "hybride"))
    except ValueError:
        work_mode = WorkMode.HYBRID

    # ── Construction du modèle Pydantic ───────────────────────────
    return JobProfile(
        job_title=data.get("job_title", "Poste non spécifié"),
        company_name=data.get("company_name"),
        location=data.get("location"),
        contract_type=contract_type,
        work_mode=work_mode,
        experience_level=experience_level,
        years_of_experience_min=data.get("years_of_experience_min"),
        years_of_experience_max=data.get("years_of_experience_max"),
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        education_requirements=data.get("education_requirements", []),
        key_responsibilities=data.get("key_responsibilities", []),
        salary_range=salary_range,
        ideal_candidate_summary=data.get("ideal_candidate_summary", ""),
        rag_keywords=data.get("rag_keywords", []),
        analysis_confidence=float(data.get("analysis_confidence", 0.75)),
        analysis_notes=data.get("analysis_notes"),
    )


def _build_error(message: str, recoverable: bool = False) -> PipelineError:
    """Construit une entrée d'erreur structurée pour le state."""
    return PipelineError(
        step=PipelineStep.JOB_ANALYSIS,
        agent=AGENT_NAME,
        message=message,
        recoverable=recoverable,
    )


# ─────────────────────────────────────────────
# Nœud LangGraph — Fonction principale
# ─────────────────────────────────────────────


def job_analyzer_node(state: RecruitmentState) -> dict:
    """
    Nœud LangGraph de l'Agent 1 — Analyse du Poste.

    Lit le RecruitmentState, appelle Gemini Flash avec le prompt
    structuré, parse la réponse JSON, valide le JobProfile Pydantic,
    et retourne un dictionnaire de mise à jour du state.

    Args:
        state: État global courant du pipeline de recrutement.

    Returns:
        Dictionnaire partiel du RecruitmentState avec les champs
        mis à jour par cet agent. LangGraph fusionne automatiquement
        ce dict dans l'état global.

    Raises:
        Ne lève pas d'exception — les erreurs sont capturées et
        stockées dans state["errors"] pour ne pas bloquer le pipeline.
    """
    log = _log_activity(state, "Démarrage de l'analyse du poste...")

    # ── 1. Récupération de l'offre brute depuis le state ──────────
    raw_offer = state.get("raw_job_offer")
    if not raw_offer:
        error_msg = "Aucune offre d'emploi (raw_job_offer) trouvée dans le state."
        logger.error(f"[{AGENT_NAME}] {error_msg}")
        log = _log_activity(state, f"ERREUR CRITIQUE : {error_msg}")
        existing_errors = state.get("errors") or []
        return {
            "current_step": PipelineStep.ERROR,
            "has_critical_error": True,
            "errors": existing_errors + [_build_error(error_msg, recoverable=False)],
            "activity_log": log,
        }

    raw_text = raw_offer.raw_text
    source_file = raw_offer.source_filename

    log = _log_activity(
        {**state, "activity_log": log},
        f"Offre chargée : '{raw_offer.title}' "
        f"({'fichier: ' + source_file if source_file else 'texte direct'}). "
        f"Longueur : {len(raw_text)} caractères.",
    )

    # ── 2. Récupération du contexte RAG (si disponible) ───────────
    rag_context = state.get("rag_job_context")
    rag_documents: list[str] | None = None

    if rag_context:
        rag_documents = [
            doc.get("content", "") for doc in rag_context if doc.get("content")
        ]
        log = _log_activity(
            {**state, "activity_log": log},
            f"Contexte RAG injecté : {len(rag_documents)} document(s) similaire(s).",
        )
    else:
        log = _log_activity(
            {**state, "activity_log": log},
            "Aucun contexte RAG disponible — analyse sans enrichissement.",
        )

    # ── 3. Construction du prompt ──────────────────────────────────
    user_prompt = build_main_prompt(
        raw_job_text=raw_text,
        rag_documents=rag_documents,
    )

    # ── 4. Appel au LLM (Gemini Flash) ────────────────────────────
    log = _log_activity(
        {**state, "activity_log": log},
        f"Envoi de la requête à {MODEL_NAME}...",
    )

    try:
        llm = _build_llm()

        messages = [
            ("system", JOB_ANALYZER_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]

        response = llm.invoke(messages)
        raw_content: str = response.content

        log = _log_activity(
            {**state, "activity_log": log},
            f"Réponse reçue de {MODEL_NAME} " f"({len(raw_content)} caractères).",
        )

    except Exception as exc:
        error_msg = f"Échec de l'appel à {MODEL_NAME} : {exc}"
        logger.exception(f"[{AGENT_NAME}] {error_msg}")
        log = _log_activity({**state, "activity_log": log}, f"ERREUR LLM : {error_msg}")
        existing_errors = state.get("errors") or []
        return {
            "current_step": PipelineStep.ERROR,
            "has_critical_error": True,
            "errors": existing_errors + [_build_error(error_msg, recoverable=False)],
            "activity_log": log,
        }

    # ── 5. Parsing de la réponse JSON ─────────────────────────────
    try:
        parsed_data = _parse_llm_response(raw_content)

    except ValueError as exc:
        error_msg = f"Échec du parsing JSON : {exc}"
        logger.error(f"[{AGENT_NAME}] {error_msg}")
        log = _log_activity(
            {**state, "activity_log": log}, f"ERREUR PARSING : {error_msg}"
        )
        existing_errors = state.get("errors") or []
        return {
            "current_step": PipelineStep.ERROR,
            "has_critical_error": True,
            "errors": existing_errors + [_build_error(error_msg, recoverable=False)],
            "activity_log": log,
        }

    # ── 6. Validation Pydantic & construction du JobProfile ───────
    try:
        job_profile = _build_job_profile(parsed_data, source_file)

    except Exception as exc:
        error_msg = f"Échec de la validation Pydantic (JobProfile) : {exc}"
        logger.exception(f"[{AGENT_NAME}] {error_msg}")
        log = _log_activity(
            {**state, "activity_log": log}, f"ERREUR VALIDATION : {error_msg}"
        )
        existing_errors = state.get("errors") or []
        return {
            "current_step": PipelineStep.ERROR,
            "has_critical_error": True,
            "errors": existing_errors + [_build_error(error_msg, recoverable=False)],
            "activity_log": log,
        }

    # ── 7. Logging du résultat ────────────────────────────────────
    tech_count = len(job_profile.technical_skills)
    soft_count = len(job_profile.soft_skills)
    mandatory_count = sum(1 for s in job_profile.technical_skills if s.is_mandatory)
    confidence_pct = int(job_profile.analysis_confidence * 100)

    log = _log_activity(
        {**state, "activity_log": log},
        f"Analyse terminée avec succès. "
        f"Poste : '{job_profile.job_title}' | "
        f"Niveau : {job_profile.experience_level.value} | "
        f"Compétences : {tech_count} techniques ({mandatory_count} obligatoires), "
        f"{soft_count} soft skills | "
        f"Confiance : {confidence_pct}%.",
    )

    # ── 8. Retour des mises à jour du state ───────────────────────
    # LangGraph fusionne ce dictionnaire dans le RecruitmentState global.
    # On ne retourne QUE les champs modifiés par cet agent.
    return {
        "current_step": PipelineStep.JOB_ANALYSIS_DONE,
        "job_profile": job_profile,
        "activity_log": log,
    }
