"""
Domain models for the final recruitment report.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.candidate import CandidateProfile, RecruitmentDecision


class ReportTimelineEvent(BaseModel):
	"""Timeline entry for the recruitment process."""

	step: str = Field(..., description="Pipeline step identifier.")
	timestamp: str = Field(..., description="ISO 8601 timestamp.")
	details: Optional[str] = Field(default=None, description="Optional notes.")


class RankingEntry(BaseModel):
	"""Ranking row for the final report."""

	candidate_id: str
	full_name: str = ""
	global_score: float = Field(ge=0.0, le=100.0)
	recommendation: RecruitmentDecision = RecruitmentDecision.PENDING


class FinalReport(BaseModel):
	"""Consolidated final report produced by the system."""

	executive_summary: str
	selected_candidate_id: Optional[str] = None
	selected_candidate: Optional[CandidateProfile] = None
	ranking_table: List[RankingEntry] = Field(default_factory=list)
	process_timeline: List[ReportTimelineEvent] = Field(default_factory=list)
	recommendations: str = ""
	generated_at: str
