"""
Agent 4 - Interview analysis using Gemini.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RecruitmentDecision
from app.models.evaluation import InterviewEvaluation
from app.prompts.interview_analyzer_prompts import (
	INTERVIEW_ANALYZER_SYSTEM_PROMPT,
	build_interview_analysis_prompt,
)
from app.utils.json_parser import extract_text, parse_json_response

logger = logging.getLogger(__name__)

AGENT_NAME = "InterviewAnalyzer"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 4096


def _build_llm() -> ChatGoogleGenerativeAI:
	return ChatGoogleGenerativeAI(
		model=MODEL_NAME,
		temperature=TEMPERATURE,
		max_output_tokens=MAX_OUTPUT_TOKENS,
		convert_system_message_to_human=False,
		thinking={"thinking_budget": 0},
	)


def _sanitize_evaluation(data: dict[str, Any], candidate_id: str) -> InterviewEvaluation:
	data = data or {}
	def to_score(value: Any) -> float:
		try:
			return float(value)
		except (TypeError, ValueError):
			return 0.0

	recommendation = data.get("recommendation")
	if isinstance(recommendation, str):
		recommendation = recommendation.lower().strip()
		if recommendation == "recruter":
			recommendation = RecruitmentDecision.HIRE
		elif recommendation == "liste_attente":
			recommendation = RecruitmentDecision.WAITLIST
		elif recommendation == "rejeter":
			recommendation = RecruitmentDecision.REJECT
		else:
			recommendation = RecruitmentDecision.PENDING
	elif not isinstance(recommendation, RecruitmentDecision):
		recommendation = RecruitmentDecision.PENDING

	strengths = data.get("strengths") if isinstance(data.get("strengths"), list) else []
	concerns = data.get("concerns") if isinstance(data.get("concerns"), list) else []

	return InterviewEvaluation(
		candidate_id=candidate_id,
		technical_score=to_score(data.get("technical_score")),
		behavioral_score=to_score(data.get("behavioral_score")),
		global_score=to_score(data.get("global_score")),
		recommendation=recommendation,
		justification=data.get("justification") or "",
		strengths=strengths,
		concerns=concerns,
	)


def _build_qa_block(questions: list[dict], responses: dict[str, str]) -> str:
	lines: list[str] = []
	for question in questions:
		qid = question.get("question_id") or ""
		text = question.get("text") or ""
		answer = responses.get(qid, "") if responses else ""
		lines.append(f"Q: {text}\nA: {answer}\n")
	return "\n".join(lines).strip()


def interview_analyzer_node(state: RecruitmentState) -> dict:
	"""Analyze interview responses and produce evaluations."""
	log = log_activity(state, AGENT_NAME, "Analyzing interview responses.")

	job_profile = state.get("job_profile")
	if not job_profile:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.INTERVIEW_ANALYSIS,
			AGENT_NAME,
			"Missing job_profile in state.",
			recoverable=False,
			critical=True,
		)

	candidate_profiles = state.get("candidate_profiles") or []
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

	responses = state.get("interview_responses") or {}
	questions_by_candidate = state.get("interview_questions") or {}
	errors = state.get("errors") or []

	llm = _build_llm()
	evaluations: dict[str, InterviewEvaluation] = {}

	skill_names = [s.name for s in job_profile.technical_skills]
	soft_names = [s.name for s in job_profile.soft_skills]

	for candidate_id in candidate_ids:
		profile = next((p for p in candidate_profiles if p.candidate_id == candidate_id), None)
		questions_set = questions_by_candidate.get(candidate_id)
		response_set = responses.get(candidate_id)

		if not questions_set or not response_set:
			errors.append(
				build_error(
					PipelineStep.INTERVIEW_ANALYSIS,
					AGENT_NAME,
					f"Missing interview data for candidate {candidate_id}.",
					recoverable=True,
				)
			)
			evaluations[candidate_id] = InterviewEvaluation(
				candidate_id=candidate_id,
				technical_score=0.0,
				behavioral_score=0.0,
				global_score=0.0,
				recommendation=RecruitmentDecision.PENDING,
				justification="Missing interview data.",
				strengths=[],
				concerns=["Missing interview data."],
			)
			continue

		all_questions = (
			questions_set.technical
			+ questions_set.behavioral
			+ questions_set.situational
		)
		qa_block = _build_qa_block(
			[q.model_dump() for q in all_questions],
			response_set.answers,
		)

		user_prompt = build_interview_analysis_prompt(
			job_title=job_profile.job_title,
			experience_level=job_profile.experience_level.value,
			technical_skills=skill_names,
			soft_skills=soft_names,
			candidate_id=candidate_id,
			candidate_name=(profile.full_name if profile else ""),
			qa_block=qa_block,
		)

		try:
			response = llm.invoke(
				[
					("system", INTERVIEW_ANALYZER_SYSTEM_PROMPT),
					("human", user_prompt),
				]
			)
			raw_content = extract_text(response.content)
			parsed = parse_json_response(raw_content)
			evaluations[candidate_id] = _sanitize_evaluation(parsed, candidate_id)
		except Exception as exc:
			logger.warning("[%s] Evaluation failed for %s: %s", AGENT_NAME, candidate_id, exc)
			errors.append(
				build_error(
					PipelineStep.INTERVIEW_ANALYSIS,
					AGENT_NAME,
					f"Interview evaluation failed for candidate {candidate_id}.",
					recoverable=True,
				)
			)
			evaluations[candidate_id] = InterviewEvaluation(
				candidate_id=candidate_id,
				technical_score=0.0,
				behavioral_score=0.0,
				global_score=0.0,
				recommendation=RecruitmentDecision.PENDING,
				justification="Evaluation failed.",
				strengths=[],
				concerns=["Evaluation failed."],
			)

	recommended_candidate_id = None
	if evaluations:
		recommended_candidate_id = max(
			evaluations.values(), key=lambda e: e.global_score
		).candidate_id

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
