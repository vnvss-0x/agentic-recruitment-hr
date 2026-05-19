"""Endpoints for reports and evaluations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.models.report import FinalReport
from app.services.session_manager import session_manager

router = APIRouter(prefix=f"{settings.api_prefix}/recruitment", tags=["Reports"])


class ReportResponse(BaseModel):
	session_id: str
	report: dict


class EvaluationsResponse(BaseModel):
	session_id: str
	evaluations: dict


@router.get(
	"/{session_id}/report",
	response_model=ReportResponse,
	status_code=status.HTTP_200_OK,
)
async def get_report(session_id: str) -> ReportResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	report = record.state.get("final_report")
	if not report:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not available")

	if hasattr(report, "model_dump"):
		report_payload = report.model_dump(mode="json")
	else:
		report_payload = report

	return ReportResponse(session_id=session_id, report=report_payload)


@router.get(
	"/{session_id}/evaluations",
	response_model=EvaluationsResponse,
	status_code=status.HTTP_200_OK,
)
async def get_evaluations(session_id: str) -> EvaluationsResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	evaluations = record.state.get("interview_evaluations")
	if not evaluations:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Evaluations not available",
		)

	payload: dict = {}
	for cid, evaluation in evaluations.items():
		if hasattr(evaluation, "model_dump"):
			payload[cid] = evaluation.model_dump(mode="json")
		else:
			payload[cid] = evaluation

	return EvaluationsResponse(session_id=session_id, evaluations=payload)
