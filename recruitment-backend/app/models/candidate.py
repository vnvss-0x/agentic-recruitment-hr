"""
Modèles Pydantic — Candidats, CVs et résultats de scoring.

Ce module définit les structures partagées entre l'Agent 2 (CV Screener),
l'Agent 3 (Interview Generator) et les validations HITL.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────


class RecruitmentDecision(str, Enum):
    """Décision finale de recrutement."""

    HIRE = "recruter"
    WAITLIST = "liste_attente"
    REJECT = "rejeter"
    PENDING = "en_attente"


class CandidateStatus(str, Enum):
    """Statut du candidat dans le pipeline."""

    UPLOADED = "cv_uploadé"
    ANALYZED = "cv_analysé"
    SHORTLISTED = "shortlisté"
    INTERVIEW_PENDING = "entretien_en_attente"
    INTERVIEW_DONE = "entretien_effectué"
    EVALUATED = "évalué"
    DECIDED = "décision_prise"


# ─────────────────────────────────────────────
# Modèle — CV brut (entrée)
# ─────────────────────────────────────────────


class RawCV(BaseModel):
    """CV tel qu'il est reçu après extraction PDF."""

    candidate_id: str = Field(..., description="Identifiant unique du candidat.")
    full_name: Optional[str] = Field(
        default=None, description="Nom complet extrait du CV."
    )
    raw_text: str = Field(..., description="Texte brut extrait du PDF du CV.")
    source_filename: str = Field(..., description="Nom du fichier PDF source.")
    email: Optional[str] = Field(default=None, description="Email extrait du CV.")
    phone: Optional[str] = Field(default=None, description="Téléphone extrait du CV.")


# ─────────────────────────────────────────────
# Modèles — Détails du profil candidat analysé
# ─────────────────────────────────────────────


class WorkExperience(BaseModel):
    """Expérience professionnelle extraite du CV."""

    company: str = Field(..., description="Nom de l'entreprise.")
    role: str = Field(..., description="Intitulé du poste occupé.")
    duration_months: Optional[int] = Field(
        default=None,
        description="Durée en mois (calculée ou estimée).",
    )
    description: Optional[str] = Field(
        default=None,
        description="Description des missions accomplies.",
    )
    technologies_used: List[str] = Field(
        default_factory=list,
        description="Technologies et outils utilisés dans ce poste.",
    )


class Education(BaseModel):
    """Formation académique extraite du CV."""

    institution: str = Field(..., description="Nom de l'établissement.")
    degree: str = Field(..., description="Diplôme obtenu.")
    field: Optional[str] = Field(default=None, description="Domaine d'études.")
    year: Optional[int] = Field(default=None, description="Année d'obtention.")


class SkillMatch(BaseModel):
    """Résultat du matching d'une compétence entre le CV et le poste."""

    skill_name: str = Field(..., description="Nom de la compétence évaluée.")
    found_in_cv: bool = Field(
        ..., description="True si la compétence est présente dans le CV."
    )
    proficiency_level: Optional[str] = Field(
        default=None,
        description="Niveau détecté dans le CV : débutant / intermédiaire / expert.",
    )
    is_mandatory: bool = Field(
        default=True,
        description="True si la compétence est obligatoire pour le poste.",
    )


# ─────────────────────────────────────────────
# Modèle — Profil candidat analysé (sortie Agent 2)
# ─────────────────────────────────────────────


class CandidateProfile(BaseModel):
    """
    Profil structuré d'un candidat produit par l'Agent 2.
    Contient l'analyse du CV, le score de compatibilité
    et la justification du classement.
    """

    # Identité
    candidate_id: str = Field(..., description="Identifiant unique du candidat.")
    full_name: str = Field(
        default="Nom inconnu", description="Nom complet du candidat."
    )
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)

    # Expérience & Formation
    work_experiences: List[WorkExperience] = Field(
        default_factory=list,
        description="Liste des expériences professionnelles extraites.",
    )
    education: List[Education] = Field(
        default_factory=list,
        description="Parcours académique extrait du CV.",
    )
    total_years_experience: float = Field(
        default=0.0,
        description="Total des années d'expérience calculé depuis les expériences.",
    )

    # Compétences
    technical_skills_found: List[str] = Field(
        default_factory=list,
        description="Compétences techniques identifiées dans le CV.",
    )
    soft_skills_found: List[str] = Field(
        default_factory=list,
        description="Soft skills identifiés dans le CV.",
    )
    languages: List[str] = Field(
        default_factory=list,
        description="Langues parlées (ex: Français C2, Anglais B2).",
    )

    # Scoring & Matching (rempli par Agent 2)
    skill_matches: List[SkillMatch] = Field(
        default_factory=list,
        description="Détail du matching compétence par compétence.",
    )
    compatibility_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Score global de compatibilité avec le poste (0–100).",
    )
    technical_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Score sur les compétences techniques uniquement.",
    )
    experience_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Score sur l'expérience et la séniorité.",
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Compétences obligatoires absentes du CV.",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Points forts du candidat par rapport au poste.",
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Points faibles ou manques identifiés.",
    )
    score_justification: str = Field(
        default="",
        description="Explication textuelle du score attribué par l'Agent 2.",
    )

    # Statut dans le pipeline
    status: CandidateStatus = Field(
        default=CandidateStatus.UPLOADED,
        description="Étape actuelle du candidat dans le pipeline.",
    )
    is_shortlisted: bool = Field(
        default=False,
        description="True si le candidat est retenu dans la shortlist.",
    )
    final_decision: RecruitmentDecision = Field(
        default=RecruitmentDecision.PENDING,
        description="Décision finale de recrutement.",
    )
