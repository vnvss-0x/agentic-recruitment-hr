"""API tests for upload and recruitment routes (mocking heavy dependencies)."""
from __future__ import annotations

import io
import pytest

# Skip this module if FastAPI isn't available in the environment
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_service import pdf_service
from app.api import pipeline
from app.services.session_manager import session_manager
from app.graph.state import PipelineStep
from app.models.interview import InterviewQuestion, InterviewQuestionSet, InterviewQuestionType
from tests.fixtures.data_fixtures import initial_state_for_tests


@pytest.fixture(autouse=True)
def clear_sessions():
    # Simple fixture to ensure isolated session store for each test
    session_manager._sessions.clear()
    yield
    session_manager._sessions.clear()


def test_get_session():
	client = TestClient(app)
	state = initial_state_for_tests("sess-0")
	state["current_step"] = PipelineStep.JOB_ANALYSIS_DONE
	session_manager.create("sess-0", state)

	r = client.get("/v1/recruitment/sess-0")
	assert r.status_code == 200
	data = r.json()
	assert data["session_id"] == "sess-0"
	assert data["current_step"] == PipelineStep.JOB_ANALYSIS_DONE.value
	assert data["has_critical_error"] is False


def test_get_interview_questions():
	client = TestClient(app)
	state = initial_state_for_tests("sess-q")
	state["shortlisted_candidate_ids"] = ["cand-1"]
	state["interview_questions"] = {
		"cand-1": InterviewQuestionSet(
			technical=[
				InterviewQuestion(
					question_id="cand-1-tech-1",
					text="Explain asyncio.",
					question_type=InterviewQuestionType.TECHNICAL,
				)
			],
		),
	}
	session_manager.create("sess-q", state)

	r = client.get("/v1/recruitment/sess-q/interviews/questions")
	assert r.status_code == 200
	data = r.json()
	assert "cand-1" in data["candidates"]
	assert data["candidates"]["cand-1"]["questions"]["technical"][0]["question_id"] == "cand-1-tech-1"


def test_get_shortlist_empty():
    client = TestClient(app)
    # create a session with no candidates
    state = initial_state_for_tests("sess-1")
    session_manager.create("sess-1", state)

    r = client.get(f"/v1/recruitment/sess-1/shortlist")
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == "sess-1"


def test_upload_cvs_endpoint(monkeypatch):
    client = TestClient(app)
    state = initial_state_for_tests("sess-2")
    session_manager.create("sess-2", state)

    # Mock pdf_service.extract to avoid PDF libs
    async def fake_extract(file_bytes: bytes, filename: str = "doc.txt"):
        from app.services.pdf_service import ExtractionResult, ExtractionMethod

        return ExtractionResult(text=("A" * 200), method_used=ExtractionMethod.PLAIN_TEXT, page_count=1)

    monkeypatch.setattr(pdf_service, "extract", fake_extract, raising=False)

    # Mock run_pipeline to avoid running full LangGraph
    def fake_run_pipeline(session_id, prev_state, update):
        new_state = {**prev_state, **update}
        new_state["current_step"] = PipelineStep.CV_SCREENING_DONE
        new_state["shortlisted_candidate_ids"] = ["cand-1"]
        return new_state

    monkeypatch.setattr(pipeline, "run_pipeline", fake_run_pipeline)

    files = {"files": ("cand-1.txt", io.BytesIO(b"hello world"), "text/plain")}
    r = client.post(f"/v1/recruitment/sess-2/upload-cvs", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["added_count"] == 1
    assert data["shortlisted_candidate_ids"] == ["cand-1"]
