"""Simple integration-style test that simulates a pipeline by merging state updates.

This test does not invoke LLMs or Chroma; it simulates the state transitions
that a real pipeline would perform and validates end-to-end data flow.
"""
from __future__ import annotations

import pytest

# Skip integration test if langgraph isn't available in the environment
pytest.importorskip("langgraph")

from app.services.session_manager import session_manager
from tests.fixtures.data_fixtures import initial_state_for_tests
from app.graph.state import PipelineStep


def test_pipeline_simulation_flow():
    sid = "integration-1"
    initial = initial_state_for_tests(sid)
    session_manager.create(sid, initial)

    # Step: CV screening produced shortlisted ids
    session_manager.merge_state(sid, {"shortlisted_candidate_ids": ["cand-1"], "current_step": PipelineStep.CV_SCREENING_DONE})

    # Step: Interview questions generated
    session_manager.merge_state(sid, {"interview_questions": {"cand-1": {"technical": [], "behavioral": [], "situational": []}}, "current_step": PipelineStep.INTERVIEW_GENERATION_DONE})

    # Step: Interview responses submitted
    session_manager.merge_state(sid, {"interview_responses": {"cand-1": {"q1": "a1"}}, "current_step": PipelineStep.INTERVIEW_RESPONSES_DONE})

    # Step: Interview analysis completed and final report produced
    final = {
        "interview_evaluations": {"cand-1": {"global_score": 85.0}},
        "recommended_candidate_id": "cand-1",
        "final_report": {"selected_candidate_id": "cand-1"},
        "current_step": PipelineStep.COMPLETED,
    }
    session_manager.merge_state(sid, final)

    record = session_manager.get(sid)
    assert record.state.get("current_step") == PipelineStep.COMPLETED
    assert record.state.get("final_report")["selected_candidate_id"] == "cand-1"
