"""
Modèles Pydantic — Évaluations et classements candidats.

Partagés entre :
    Agent 2 (CV Screener)       → CandidateRanking, ShortlistResult
    Agent 4 (Interview Analyzer)→ InterviewEvaluation
    Agent 5 (Report Generator)  → FinalRanking
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.candidate import RecruitmentDecision


class CandidateRanking(BaseModel):
    """Résultat du scoring d'un CV par l'Agent 2."""

    candidate_id: str
    full_name: str = ""
    compatibility_score: float = Field(ge=0.0, le=100.0)
    technical_score: float = Field(ge=0.0, le=100.0)
    experience_score: float = Field(ge=0.0, le=100.0)
    missing_skills: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    score_justification: str = ""
    is_shortlisted: bool = False
    rag_context_used: bool = False


class ShortlistResult(BaseModel):
    """Sortie consolidée de l'Agent 2."""

    rankings: List[CandidateRanking] = Field(default_factory=list)
    shortlisted_ids: List[str] = Field(default_factory=list)
    screening_summary: str = ""
    total_candidates: int = 0
    shortlist_size: int = 0


class InterviewEvaluation(BaseModel):
    """Evaluation detaillee d'un candidat apres entretien."""

    candidate_id: str
    technical_score: float = Field(ge=0.0, le=100.0)
    behavioral_score: float = Field(ge=0.0, le=100.0)
    global_score: float = Field(ge=0.0, le=100.0)
    recommendation: RecruitmentDecision = RecruitmentDecision.PENDING
    justification: str = ""
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
