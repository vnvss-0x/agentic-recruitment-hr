"""HITL endpoints for HR and manager validations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.events import dispatch_state_events
from app.api.pipeline import run_pipeline
from app.core.config import settings
from app.graph.state import PipelineStep, RecruitmentState
from app.models.hitl import HRShortlistValidation, ManagerFinalValidation
from app.services.session_manager import session_manager

router = APIRouter(prefix=f"{settings.api_prefix}/recruitment", tags=["HITL"])


class HITLResponse(BaseModel):
	session_id: str
	current_step: str
	status: str


@router.post(
	"/{session_id}/hitl/hr",
	response_model=HITLResponse,
	status_code=status.HTTP_200_OK,
)
async def submit_hr_validation(
	session_id: str,
	payload: HRShortlistValidation,
) -> HITLResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	prev_state: RecruitmentState = record.state
	known_ids = [p.candidate_id for p in (prev_state.get("candidate_profiles") or [])]
	invalid_ids = [
		cid
		for cid in (
			(payload.approved_candidate_ids or [])
			+ (payload.removed_candidate_ids or [])
			+ (payload.added_candidate_ids or [])
		)
		if cid not in known_ids
	]
	if invalid_ids:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail=f"Unknown candidate ids: {', '.join(invalid_ids)}",
		)
	update = {
		"hr_validation": payload,
		"current_step": PipelineStep.HITL_1_DONE,
	}

	try:
		new_state = run_pipeline(session_id, prev_state, update)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

	session_manager.update_state(session_id, new_state)
	await dispatch_state_events(session_id, prev_state, new_state)

	return HITLResponse(
		session_id=session_id,
		current_step=new_state.get("current_step").value,
		status=payload.status.value,
	)


@router.post(
	"/{session_id}/hitl/manager",
	response_model=HITLResponse,
	status_code=status.HTTP_200_OK,
)
async def submit_manager_validation(
	session_id: str,
	payload: ManagerFinalValidation,
) -> HITLResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	prev_state: RecruitmentState = record.state
	shortlist_ids = prev_state.get("validated_shortlist_ids") or prev_state.get(
		"shortlisted_candidate_ids"
	) or []
	selected_id = payload.selected_candidate_id
	if selected_id and selected_id not in shortlist_ids:
		raise HTTPException(
			status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
			detail="selected_candidate_id is not in shortlist",
		)
	update = {
		"manager_validation": payload,
		"current_step": PipelineStep.HITL_2_DONE,
	}

	try:
		new_state = run_pipeline(session_id, prev_state, update)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

	session_manager.update_state(session_id, new_state)
	await dispatch_state_events(session_id, prev_state, new_state)

	return HITLResponse(
		session_id=session_id,
		current_step=new_state.get("current_step").value,
		status=payload.status.value,
	)
