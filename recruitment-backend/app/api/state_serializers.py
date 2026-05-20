"""Serialize RecruitmentState fragments for REST responses."""

from __future__ import annotations

from typing import Any

from app.graph.state import PipelineStep, RecruitmentState
from app.models.interview import InterviewQuestionSet


def step_value(step: PipelineStep | str | None) -> str:
	if step is None:
		return PipelineStep.INITIALIZED.value
	if isinstance(step, PipelineStep):
		return step.value
	return str(step)


def model_to_json(value: Any) -> Any:
	if hasattr(value, "model_dump"):
		return value.model_dump(mode="json")
	if isinstance(value, dict):
		return {k: model_to_json(v) for k, v in value.items()}
	if isinstance(value, list):
		return [model_to_json(v) for v in value]
	return value


def serialize_session_summary(state: RecruitmentState) -> dict[str, Any]:
	current = state.get("current_step")
	step_str = step_value(current)

	awaiting_hitl_hr = current in (
		PipelineStep.HITL_1_PENDING,
		PipelineStep.CV_SCREENING_DONE,
	) or step_str == PipelineStep.HITL_1_PENDING.value

	awaiting_hitl_manager = current in (
		PipelineStep.HITL_2_PENDING,
		PipelineStep.INTERVIEW_ANALYSIS_DONE,
	) or step_str == PipelineStep.HITL_2_PENDING.value

	job_profile = state.get("job_profile")
	interview_questions = state.get("interview_questions") or {}

	return {
		"session_id": state.get("session_id"),
		"current_step": step_str,
		"created_at": state.get("created_at"),
		"has_critical_error": bool(state.get("has_critical_error")),
		"job_profile": model_to_json(job_profile) if job_profile else None,
		"shortlisted_candidate_ids": state.get("shortlisted_candidate_ids") or [],
		"validated_shortlist_ids": state.get("validated_shortlist_ids") or [],
		"recommended_candidate_id": state.get("recommended_candidate_id"),
		"has_interview_questions": bool(interview_questions),
		"has_interview_responses": bool(state.get("interview_responses")),
		"has_final_report": state.get("final_report") is not None,
		"awaiting_hitl_hr": awaiting_hitl_hr,
		"awaiting_hitl_manager": awaiting_hitl_manager,
		"activity_log": state.get("activity_log") or [],
		"errors": model_to_json(state.get("errors") or []),
	}


def serialize_interview_questions(
	state: RecruitmentState,
) -> dict[str, Any]:
	"""Build API payload for interview question sets per candidate."""
	job_profile = state.get("job_profile")
	job_title = job_profile.job_title if job_profile else None
	questions_map = state.get("interview_questions") or {}
	shortlist_ids = state.get("validated_shortlist_ids") or state.get(
		"shortlisted_candidate_ids"
	) or []

	candidates: dict[str, Any] = {}
	for candidate_id in shortlist_ids:
		qset = questions_map.get(candidate_id)
		if qset is None:
			continue
		if isinstance(qset, InterviewQuestionSet):
			payload = qset.model_dump(mode="json")
		elif isinstance(qset, dict):
			payload = qset
		else:
			payload = model_to_json(qset)
		candidates[candidate_id] = {
			"candidate_id": candidate_id,
			"job_title": job_title,
			"questions": payload,
		}

	return {
		"session_id": state.get("session_id"),
		"candidates": candidates,
	}
