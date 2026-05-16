"""
Agent 4 - Interview analysis (baseline implementation).
"""

from __future__ import annotations

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RecruitmentDecision

AGENT_NAME = "InterviewAnalyzer"


def _build_default_evaluation() -> dict:
	return {
		"technical_score": 0.0,
		"behavioral_score": 0.0,
		"global_score": 0.0,
		"recommendation": RecruitmentDecision.PENDING,
		"justification": "No interview responses available.",
		"strengths": [],
		"concerns": ["Missing interview responses."],
	}


def interview_analyzer_node(state: RecruitmentState) -> dict:
	"""Analyze interview responses and produce evaluations."""
	log = log_activity(state, AGENT_NAME, "Analyzing interview responses.")

	candidate_ids = state.get("validated_shortlist_ids") or state.get(
		"shortlisted_candidate_ids"
	)
	if not candidate_ids:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.INTERVIEW_ANALYSIS,
			AGENT_NAME,
			"No candidates available for interview analysis.",
			recoverable=False,
			critical=True,
		)

	errors = state.get("errors") or []
	responses = state.get("interview_responses") or {}
	if not responses:
		errors.append(
			build_error(
				PipelineStep.INTERVIEW_ANALYSIS,
				AGENT_NAME,
				"Interview responses missing; default evaluations applied.",
				recoverable=True,
			)
		)

	evaluations: dict[str, dict] = {}
	for candidate_id in candidate_ids:
		evaluations[candidate_id] = _build_default_evaluation()

	recommended_candidate_id = candidate_ids[0] if candidate_ids else None

	log = log_activity(
		{**state, "activity_log": log},
		AGENT_NAME,
		f"Interview analysis completed for {len(evaluations)} candidates.",
	)

	return {
		"current_step": PipelineStep.INTERVIEW_ANALYSIS_DONE,
		"interview_evaluations": evaluations,
		"recommended_candidate_id": recommended_candidate_id,
		"errors": errors,
		"activity_log": log,
	}
