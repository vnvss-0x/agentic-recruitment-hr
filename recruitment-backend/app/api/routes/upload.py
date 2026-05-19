"""Upload endpoints for recruitment pipeline."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.events import dispatch_state_events
from app.api.pipeline import run_pipeline
from app.core.config import settings
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RawCV
from app.services.pdf_service import PDFExtractionError, pdf_service
from app.services.session_manager import session_manager

router = APIRouter(prefix=f"{settings.api_prefix}/recruitment", tags=["Upload"])


class UploadCVResponse(BaseModel):
	session_id: str
	added_count: int
	total_count: int
	current_step: str
	shortlisted_candidate_ids: list[str]


@router.post(
	"/{session_id}/upload-cvs",
	response_model=UploadCVResponse,
	status_code=status.HTTP_200_OK,
)
async def upload_cvs(
	session_id: str,
	files: list[UploadFile] = File(..., description="CVs PDF/TXT"),
) -> UploadCVResponse:
	record = session_manager.get(session_id)
	if not record:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

	if not files:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No files provided")

	raw_cvs: list[RawCV] = []
	for file in files:
		filename = file.filename or "cv.pdf"
		file_bytes = await file.read()

		try:
			pdf_service.validate_file(
				file_bytes=file_bytes,
				filename=filename,
				max_bytes=settings.max_upload_bytes,
			)
		except ValueError as exc:
			raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

		try:
			extraction = await pdf_service.extract(file_bytes=file_bytes, filename=filename)
		except PDFExtractionError as exc:
			raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

		candidate_id = str(uuid.uuid4())
		full_name = filename.replace(".pdf", "").replace(".txt", "")

		raw_cvs.append(
			RawCV(
				candidate_id=candidate_id,
				full_name=full_name,
				raw_text=extraction.text,
				source_filename=filename,
				email=None,
				phone=None,
			)
		)

	prev_state: RecruitmentState = record.state
	existing = prev_state.get("raw_cvs") or []
	update = {
		"raw_cvs": existing + raw_cvs,
		"current_step": PipelineStep.CV_SCREENING,
	}

	try:
		new_state = run_pipeline(session_id, prev_state, update)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

	session_manager.update_state(session_id, new_state)
	await dispatch_state_events(session_id, prev_state, new_state)

	shortlisted_ids = new_state.get("shortlisted_candidate_ids") or []
	return UploadCVResponse(
		session_id=session_id,
		added_count=len(raw_cvs),
		total_count=len(new_state.get("raw_cvs") or []),
		current_step=(
			new_state.get("current_step").value
			if new_state.get("current_step")
			else PipelineStep.INITIALIZED.value
		),
		shortlisted_candidate_ids=shortlisted_ids,
	)
