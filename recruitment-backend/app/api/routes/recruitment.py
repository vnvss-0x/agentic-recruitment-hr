"""Recruitment endpoints for shortlist and interview responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.events import dispatch_state_events
from app.api.pipeline import run_pipeline
from app.api.state_serializers import (
	serialize_interview_questions,
	serialize_session_summary,
)
from app.core.config import settings
from app.graph.state import PipelineStep, RecruitmentState
from app.models.interview import InterviewResponseSet
from app.services.session_manager import session_manager

router = APIRouter(prefix=f"{settings.api_prefix}/recruitment", tags=["Recrutement"])


class ShortlistCandidate(BaseModel):
	candidate_id: str
	full_name: str
	compatibility_score: float
	strengths: list[str]
	weaknesses: list[str]


class ShortlistResponse(BaseModel):
	session_id: str
	shortlisted_candidate_ids: list[str]
	screening_summary: str
	candidates: list[ShortlistCandidate]


class InterviewResponsesPayload(BaseModel):
	responses: Dict[str, Dict[str, str]] = Field(
		default_factory=dict,
		description="Map candidate_id -> {question_id: answer}.",
	)


class InterviewResponsesResult(BaseModel):
	session_id: str
	current_step: str
	recommended_candidate_id: str | None = None


class SessionResponse(BaseModel):
	session_id: str
	current_step: str
	created_at: str | None = None
	has_critical_error: bool = False
	job_profile: dict | None = None
	shortlisted_candidate_ids: list[str] = Field(default_factory=list)
	validated_shortlist_ids: list[str] = Field(default_factory=list)
	recommended_candidate_id: str | None = None
	has_interview_questions: bool = False
	has_interview_responses: bool = False
	has_final_report: bool = False
	awaiting_hitl_hr: bool = False
	awaiting_hitl_manager: bool = False
	activity_log: list[str] = Field(default_factory=list)
	errors: list[dict] = Field(default_factory=list)


class InterviewQuestionsResponse(BaseModel):
	session_id: str
	candidates: Dict[str, dict] = Field(default_factory=dict)


@router.get(
	"/{session_id}",
	response_model=SessionResponse,
	status_code=status.HTTP_200_OK,
	summary="État courant de la session de recrutement",
)
async def get_session(session_id: str) -> SessionResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	summary = serialize_session_summary(record.state)
	return SessionResponse(**summary)


@router.get(
	"/{session_id}/interviews/questions",
	response_model=InterviewQuestionsResponse,
	status_code=status.HTTP_200_OK,
	summary="Questionnaires d'entretien par candidat shortlisté",
)
async def get_interview_questions(session_id: str) -> InterviewQuestionsResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	state: RecruitmentState = record.state
	questions = state.get("interview_questions")
	if not questions:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Interview questions not available yet. Complete HITL HR validation first.",
		)

	payload = serialize_interview_questions(state)
	return InterviewQuestionsResponse(**payload)


@router.get(
	"/{session_id}/shortlist",
	response_model=ShortlistResponse,
	status_code=status.HTTP_200_OK,
)
async def get_shortlist(session_id: str) -> ShortlistResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	state: RecruitmentState = record.state
	shortlist_ids = state.get("validated_shortlist_ids") or state.get(
		"shortlisted_candidate_ids"
	) or []
	profiles = state.get("candidate_profiles") or []

	candidates: list[ShortlistCandidate] = []
	for profile in profiles:
		if profile.candidate_id in shortlist_ids:
			candidates.append(
				ShortlistCandidate(
					candidate_id=profile.candidate_id,
					full_name=profile.full_name,
					compatibility_score=profile.compatibility_score,
					strengths=profile.strengths,
					weaknesses=profile.weaknesses,
				)
			)

	return ShortlistResponse(
		session_id=session_id,
		shortlisted_candidate_ids=shortlist_ids,
		screening_summary=state.get("screening_summary") or "",
		candidates=candidates,
	)


@router.post(
	"/{session_id}/interviews/submit",
	response_model=InterviewResponsesResult,
	status_code=status.HTTP_200_OK,
)
async def submit_interview_responses(
	session_id: str,
	payload: InterviewResponsesPayload,
) -> InterviewResponsesResult:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	state: RecruitmentState = record.state
	shortlist_ids = state.get("validated_shortlist_ids") or state.get(
		"shortlisted_candidate_ids"
	) or []

	if not payload.responses:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No responses provided")

	for candidate_id in payload.responses.keys():
		if candidate_id not in shortlist_ids:
			raise HTTPException(
				status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				detail=f"Candidate {candidate_id} is not in shortlist",
			)

	response_sets: dict[str, InterviewResponseSet] = {}
	submitted_at = datetime.now(timezone.utc).isoformat()
	for candidate_id, answers in payload.responses.items():
		if not answers:
			raise HTTPException(
				status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				detail=f"No answers for candidate {candidate_id}",
			)
		response_sets[candidate_id] = InterviewResponseSet(
			candidate_id=candidate_id,
			answers=answers,
			submitted_at=submitted_at,
		)

	prev_state = state
	update = {
		"interview_responses": response_sets,
		"current_step": PipelineStep.INTERVIEW_RESPONSES_DONE,
	}

	try:
		new_state = run_pipeline(session_id, prev_state, update)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

	session_manager.update_state(session_id, new_state)
	await dispatch_state_events(session_id, prev_state, new_state)

	return InterviewResponsesResult(
		session_id=session_id,
		current_step=new_state.get("current_step").value,
		recommended_candidate_id=new_state.get("recommended_candidate_id"),
	)
