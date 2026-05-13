"""
Modèles Pydantic — Décisions Human-In-The-Loop (HITL).

Ce module définit les structures pour les deux points de contrôle
humain intégrés dans le graphe LangGraph :
- HITL 1 : Validation RH de la shortlist
- HITL 2 : Validation managériale de la décision finale
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────


class HITLType(str, Enum):
    """Type de validation humaine."""

    HR_SHORTLIST_VALIDATION = "validation_rh_shortlist"
    MANAGER_FINAL_DECISION = "validation_manager_finale"


class HITLStatus(str, Enum):
    """Statut de la validation humaine."""

    PENDING = "en_attente"
    APPROVED = "approuvé"
    MODIFIED = "modifié"
    REJECTED = "rejeté"
    REANALYSIS_REQUESTED = "réanalyse_demandée"


class ManagerDecision(str, Enum):
    """Décisions disponibles pour le manager (HITL 2)."""

    HIRE = "recruter"
    ADDITIONAL_INTERVIEW = "entretien_supplémentaire"
    CANCEL = "annuler"


# ─────────────────────────────────────────────
# Modèle — Validation HITL 1 (RH → Shortlist)
# ─────────────────────────────────────────────


class HRShortlistValidation(BaseModel):
    """
    Décision du responsable RH sur la shortlist générée par l'Agent 2.
    Le RH peut approuver, modifier ou demander une réanalyse.
    """

    hitl_type: HITLType = Field(
        default=HITLType.HR_SHORTLIST_VALIDATION,
        description="Type de checkpoint HITL.",
    )
    status: HITLStatus = Field(
        default=HITLStatus.PENDING,
        description="Statut actuel de la validation.",
    )

    # Décision sur les candidats
    approved_candidate_ids: List[str] = Field(
        default_factory=list,
        description="IDs des candidats validés par le RH pour passer aux entretiens.",
    )
    removed_candidate_ids: List[str] = Field(
        default_factory=list,
        description="IDs des candidats retirés de la shortlist par le RH.",
    )
    added_candidate_ids: List[str] = Field(
        default_factory=list,
        description="IDs de candidats ajoutés manuellement par le RH.",
    )

    # Commentaires
    hr_comments: Optional[str] = Field(
        default=None,
        description="Commentaires libres du RH sur la shortlist.",
    )
    reanalysis_instructions: Optional[str] = Field(
        default=None,
        description="Instructions spécifiques si une réanalyse est demandée.",
    )

    # Horodatage
    validated_at: Optional[datetime] = Field(
        default=None,
        description="Date et heure de la validation.",
    )
    validated_by: Optional[str] = Field(
        default=None,
        description="Identifiant ou nom du responsable RH ayant validé.",
    )


# ─────────────────────────────────────────────
# Modèle — Validation HITL 2 (Manager → Décision finale)
# ─────────────────────────────────────────────


class ManagerFinalValidation(BaseModel):
    """
    Décision du manager sur la recommandation finale de l'Agent 4.
    Le manager peut recruter, demander un entretien supplémentaire
    ou annuler le processus.
    """

    hitl_type: HITLType = Field(
        default=HITLType.MANAGER_FINAL_DECISION,
        description="Type de checkpoint HITL.",
    )
    status: HITLStatus = Field(
        default=HITLStatus.PENDING,
        description="Statut actuel de la validation managériale.",
    )

    # Décision
    decision: Optional[ManagerDecision] = Field(
        default=None,
        description="Décision du manager : recruter / entretien_supplémentaire / annuler.",
    )
    selected_candidate_id: Optional[str] = Field(
        default=None,
        description="ID du candidat sélectionné par le manager (si décision = recruter).",
    )

    # Commentaires
    manager_comments: Optional[str] = Field(
        default=None,
        description="Commentaires libres du manager.",
    )
    override_reason: Optional[str] = Field(
        default=None,
        description=(
            "Justification si le manager contredit la recommandation IA "
            "(ex: raison pour laquelle un candidat mieux scoré est écarté)."
        ),
    )

    # Horodatage
    validated_at: Optional[datetime] = Field(
        default=None,
        description="Date et heure de la validation.",
    )
    validated_by: Optional[str] = Field(
        default=None,
        description="Identifiant ou nom du manager ayant validé.",
    )
