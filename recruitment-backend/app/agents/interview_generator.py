"""
Agent 3 - Interview question generator (baseline implementation).
"""

from __future__ import annotations

from app.graph.nodes import apply_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.interview import (
	InterviewQuestion,
	InterviewQuestionSet,
	InterviewQuestionType,
)

AGENT_NAME = "InterviewGenerator"


def _default_questions(candidate_id: str) -> InterviewQuestionSet:
	"""Return a basic question set to keep the pipeline moving."""
	return InterviewQuestionSet(
		technical=[
			InterviewQuestion(
				question_id=f"{candidate_id}-tech-1",
				text="Explain a recent technical challenge you solved.",
				question_type=InterviewQuestionType.TECHNICAL,
				skill_tags=[],
			),
			InterviewQuestion(
				question_id=f"{candidate_id}-tech-2",
				text="Describe how you would improve an existing codebase.",
				question_type=InterviewQuestionType.TECHNICAL,
				skill_tags=[],
			),
		],
		behavioral=[
			InterviewQuestion(
				question_id=f"{candidate_id}-beh-1",
				text="Tell us about a time you handled conflicting priorities.",
				question_type=InterviewQuestionType.BEHAVIORAL,
			),
		],
		situational=[
			InterviewQuestion(
				question_id=f"{candidate_id}-sit-1",
				text="How would you respond to a critical production issue?",
				question_type=InterviewQuestionType.SITUATIONAL,
			),
		],
	)


def interview_generator_node(state: RecruitmentState) -> dict:
	"""Generate interview questions for shortlisted candidates."""
	log = log_activity(state, AGENT_NAME, "Generating interview questions.")

	shortlist_ids = state.get("validated_shortlist_ids") or state.get(
		"shortlisted_candidate_ids"
	)
	if not shortlist_ids:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.INTERVIEW_GENERATION,
			AGENT_NAME,
			"No shortlisted candidates available.",
			recoverable=False,
			critical=True,
		)

	questions: dict[str, InterviewQuestionSet] = {}
	for candidate_id in shortlist_ids:
		questions[candidate_id] = _default_questions(candidate_id)

	log = log_activity(
		{**state, "activity_log": log},
		AGENT_NAME,
		f"Generated questions for {len(questions)} candidates.",
	)

	return {
		"current_step": PipelineStep.INTERVIEW_GENERATION_DONE,
		"interview_questions": questions,
		"activity_log": log,
	}
