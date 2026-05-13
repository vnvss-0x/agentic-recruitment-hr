"""
Modèles Pydantic — Offre d'emploi & Profil de poste.

Ce module définit les structures de données utilisées par l'Agent 1
(Job Analyzer) pour représenter une offre d'emploi brute et le profil
structuré produit après analyse.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────


class ExperienceLevel(str, Enum):
    """Niveau d'expérience requis pour le poste."""

    JUNIOR = "junior"  # 0–2 ans
    MID = "mid"  # 2–5 ans
    SENIOR = "senior"  # 5–10 ans
    LEAD = "lead"  # 10+ ans / rôle de leadership
    EXECUTIVE = "executive"  # Direction / C-level


class ContractType(str, Enum):
    """Type de contrat proposé."""

    CDI = "CDI"
    CDD = "CDD"
    FREELANCE = "freelance"
    INTERNSHIP = "stage"
    APPRENTICESHIP = "alternance"
    OTHER = "autre"


class WorkMode(str, Enum):
    """Modalité de travail."""

    ON_SITE = "présentiel"
    REMOTE = "télétravail"
    HYBRID = "hybride"


# ─────────────────────────────────────────────
# Modèle — Offre brute (entrée Agent 1)
# ─────────────────────────────────────────────


class RawJobOffer(BaseModel):
    """
    Représente l'offre d'emploi telle qu'elle est fournie
    avant tout traitement (texte brut ou extrait de PDF).
    """

    title: str = Field(
        ...,
        description="Intitulé du poste tel qu'il apparaît dans l'offre.",
        examples=["Développeur Backend Python Senior"],
    )
    raw_text: str = Field(
        ...,
        description="Contenu complet de l'offre d'emploi, non traité.",
    )
    source_filename: Optional[str] = Field(
        default=None,
        description="Nom du fichier source si l'offre provient d'un PDF.",
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Nom de l'entreprise publiant l'offre.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Localisation géographique du poste.",
    )


# ─────────────────────────────────────────────
# Modèles — Compétences extraites
# ─────────────────────────────────────────────


class TechnicalSkill(BaseModel):
    """Compétence technique identifiée dans l'offre."""

    name: str = Field(..., description="Nom de la compétence (ex: Python, Docker).")
    level: Optional[str] = Field(
        default=None,
        description="Niveau attendu : débutant / intermédiaire / expert.",
    )
    is_mandatory: bool = Field(
        default=True,
        description="True si la compétence est obligatoire, False si souhaitable.",
    )


class SoftSkill(BaseModel):
    """Soft skill (compétence comportementale) identifiée dans l'offre."""

    name: str = Field(
        ..., description="Nom du soft skill (ex: Leadership, Communication)."
    )
    description: Optional[str] = Field(
        default=None,
        description="Contexte ou explication associée à ce soft skill.",
    )


class SalaryRange(BaseModel):
    """Fourchette salariale extraite ou estimée."""

    min_value: Optional[float] = Field(
        default=None, description="Salaire minimum (€/an)."
    )
    max_value: Optional[float] = Field(
        default=None, description="Salaire maximum (€/an)."
    )
    currency: str = Field(default="EUR", description="Devise.")
    is_estimated: bool = Field(
        default=False,
        description="True si la fourchette est estimée par l'IA (non explicite dans l'offre).",
    )


# ─────────────────────────────────────────────
# Modèle — Profil structuré du poste (sortie Agent 1)
# ─────────────────────────────────────────────


class JobProfile(BaseModel):
    """
    Profil structuré du poste produit par l'Agent 1 après analyse.
    C'est la sortie principale qui alimente les agents suivants.
    """

    # Informations générales
    job_title: str = Field(..., description="Intitulé normalisé du poste.")
    company_name: Optional[str] = Field(
        default=None, description="Nom de l'entreprise."
    )
    location: Optional[str] = Field(default=None, description="Localisation.")
    contract_type: ContractType = Field(
        default=ContractType.CDI,
        description="Type de contrat détecté.",
    )
    work_mode: WorkMode = Field(
        default=WorkMode.HYBRID,
        description="Modalité de travail détectée.",
    )

    # Niveau & expérience
    experience_level: ExperienceLevel = Field(
        ...,
        description="Niveau d'expérience requis (junior / mid / senior / lead / executive).",
    )
    years_of_experience_min: Optional[int] = Field(
        default=None,
        description="Nombre minimal d'années d'expérience requises.",
    )
    years_of_experience_max: Optional[int] = Field(
        default=None,
        description="Nombre maximal d'années d'expérience mentionnées.",
    )

    # Compétences
    technical_skills: List[TechnicalSkill] = Field(
        default_factory=list,
        description="Liste des compétences techniques extraites de l'offre.",
    )
    soft_skills: List[SoftSkill] = Field(
        default_factory=list,
        description="Liste des soft skills extraites de l'offre.",
    )

    # Formation
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Diplômes ou formations requis (ex: Bac+5 Informatique).",
    )

    # Missions
    key_responsibilities: List[str] = Field(
        default_factory=list,
        description="Principales responsabilités et missions du poste.",
    )

    # Rémunération
    salary_range: Optional[SalaryRange] = Field(
        default=None,
        description="Fourchette salariale extraite ou estimée.",
    )

    # Profil idéal synthétisé (texte libre généré par l'IA)
    ideal_candidate_summary: str = Field(
        ...,
        description=(
            "Résumé en langage naturel du profil candidat idéal, "
            "généré par l'Agent 1 pour guider le screening."
        ),
    )

    # Mots-clés pour le RAG
    rag_keywords: List[str] = Field(
        default_factory=list,
        description="Mots-clés extraits pour les requêtes RAG dans ChromaDB.",
    )

    # Métadonnées de traitement
    analysis_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score de confiance de l'analyse (0.0 à 1.0).",
    )
    analysis_notes: Optional[str] = Field(
        default=None,
        description="Notes internes de l'agent sur l'analyse (ambiguïtés, hypothèses).",
    )
