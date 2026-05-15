"""
Domain models for interview generation and responses.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class InterviewQuestionType(str, Enum):
	"""Category of an interview question."""

	TECHNICAL = "technical"
	BEHAVIORAL = "behavioral"
	SITUATIONAL = "situational"


class InterviewQuestion(BaseModel):
	"""Single interview question."""

	question_id: str = Field(..., description="Unique question identifier.")
	text: str = Field(..., description="Question text.")
	question_type: InterviewQuestionType = Field(
		default=InterviewQuestionType.TECHNICAL,
		description="Question category.",
	)
	difficulty: Optional[str] = Field(
		default=None,
		description="Optional difficulty tag (easy, medium, hard).",
	)
	skill_tags: List[str] = Field(
		default_factory=list,
		description="Skills targeted by the question.",
	)


class InterviewQuestionSet(BaseModel):
	"""Questions grouped by category for a candidate."""

	technical: List[InterviewQuestion] = Field(default_factory=list)
	behavioral: List[InterviewQuestion] = Field(default_factory=list)
	situational: List[InterviewQuestion] = Field(default_factory=list)


class InterviewQuestionnaire(BaseModel):
	"""Full questionnaire generated for a candidate."""

	candidate_id: str
	job_title: Optional[str] = None
	questions: InterviewQuestionSet = Field(default_factory=InterviewQuestionSet)
	generated_at: Optional[str] = Field(
		default=None,
		description="ISO 8601 timestamp when the questions were generated.",
	)


class InterviewResponseSet(BaseModel):
	"""Responses provided by a candidate."""

	candidate_id: str
	answers: Dict[str, str] = Field(
		default_factory=dict,
		description="Map question_id -> answer text.",
	)
	submitted_at: Optional[str] = Field(
		default=None,
		description="ISO 8601 timestamp when responses were submitted.",
	)
