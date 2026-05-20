"""
Agent 3 - Interview question generator using Gemini.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.interview import (
	InterviewQuestion,
	InterviewQuestionSet,
	InterviewQuestionType,
)
from app.prompts.interview_generator_prompts import (
	INTERVIEW_GENERATOR_SYSTEM_PROMPT,
	INTERVIEW_GENERATOR_SYSTEM_PROMPT_B,
	build_interview_prompt,
)
from app.prompts.prompt_evaluator import (
	PromptVariant,
	append_prompt_metrics,
	compute_question_metrics,
	select_prompt_variant,
)
from app.rag.retriever import context_to_text, retrieve_interview_context
from app.utils.json_parser import extract_text, parse_json_response

logger = logging.getLogger(__name__)

AGENT_NAME = "InterviewGenerator"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.3
MAX_OUTPUT_TOKENS = 4096


def _build_llm() -> ChatGoogleGenerativeAI:
	return ChatGoogleGenerativeAI(
		model=MODEL_NAME,
		temperature=TEMPERATURE,
		max_output_tokens=MAX_OUTPUT_TOKENS,
		convert_system_message_to_human=False,
		thinking={"thinking_budget": 0},
	)


def _sanitize_questions(data: dict[str, Any], candidate_id: str) -> InterviewQuestionSet:
	questions = data.get("questions") if isinstance(data, dict) else None
	if not isinstance(questions, dict):
		questions = {}

	def build_list(items: Any, qtype: InterviewQuestionType, prefix: str) -> list[InterviewQuestion]:
		if not isinstance(items, list):
			items = []
		result: list[InterviewQuestion] = []
		for idx, item in enumerate(items):
			if not isinstance(item, dict):
				continue
			qid = item.get("question_id") or f"{candidate_id}-{prefix}-{idx+1}"
			text = item.get("text") or ""
			difficulty = item.get("difficulty")
			skill_tags = item.get("skill_tags") if isinstance(item.get("skill_tags"), list) else []
			result.append(
				InterviewQuestion(
					question_id=qid,
					text=text,
					question_type=qtype,
					difficulty=difficulty,
					skill_tags=skill_tags,
				)
			)
		return result

	return InterviewQuestionSet(
		technical=build_list(questions.get("technical"), InterviewQuestionType.TECHNICAL, "tech"),
		behavioral=build_list(questions.get("behavioral"), InterviewQuestionType.BEHAVIORAL, "beh"),
		situational=build_list(questions.get("situational"), InterviewQuestionType.SITUATIONAL, "sit"),
	)


def interview_generator_node(state: RecruitmentState) -> dict:
	"""Generate interview questions for shortlisted candidates."""
	log = log_activity(state, AGENT_NAME, "Generating interview questions.")

	job_profile = state.get("job_profile")
	if not job_profile:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.INTERVIEW_GENERATION,
			AGENT_NAME,
			"Missing job_profile in state.",
			recoverable=False,
			critical=True,
		)

	candidate_profiles = state.get("candidate_profiles") or []
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

	llm = _build_llm()
	errors = state.get("errors") or []
	prompt_metrics = state.get("prompt_metrics") or {}
	questions: dict[str, InterviewQuestionSet] = {}

	variants = [
		PromptVariant("A", INTERVIEW_GENERATOR_SYSTEM_PROMPT, weight=1.0),
		PromptVariant("B", INTERVIEW_GENERATOR_SYSTEM_PROMPT_B, weight=1.0),
	]
	variant = select_prompt_variant(AGENT_NAME, state.get("session_id"), variants)

	skill_names = [s.name for s in job_profile.technical_skills]
	soft_names = [s.name for s in job_profile.soft_skills]

	rag_context = retrieve_interview_context(job_profile)
	rag_docs = context_to_text(rag_context)

	for candidate_id in shortlist_ids:
		profile = next((p for p in candidate_profiles if p.candidate_id == candidate_id), None)
		user_prompt = build_interview_prompt(
			job_title=job_profile.job_title,
			experience_level=job_profile.experience_level.value,
			technical_skills=skill_names,
			soft_skills=soft_names,
			candidate_id=candidate_id,
			candidate_name=(profile.full_name if profile else ""),
			strengths=(profile.strengths if profile else []),
			weaknesses=(profile.weaknesses if profile else []),
			rag_docs=rag_docs,
		)

		try:
			start = time.perf_counter()
			response = llm.invoke(
				[
					("system", variant.system_prompt),
					("human", user_prompt),
				]
			)
			raw_content = extract_text(response.content)
			parsed = parse_json_response(raw_content)
			questions[candidate_id] = _sanitize_questions(parsed, candidate_id)
			latency_ms = (time.perf_counter() - start) * 1000
		except Exception as exc:
			logger.warning("[%s] Question generation failed for %s: %s", AGENT_NAME, candidate_id, exc)
			errors.append(
				build_error(
					PipelineStep.INTERVIEW_GENERATION,
					AGENT_NAME,
					f"Question generation failed for candidate {candidate_id}.",
					recoverable=True,
				)
			)
			questions[candidate_id] = InterviewQuestionSet()
			latency_ms = 0.0

		metrics = compute_question_metrics(questions[candidate_id])
		metrics.update(
			{
				"variant_id": variant.variant_id,
				"latency_ms": round(latency_ms, 2),
				"candidate_id": candidate_id,
			}
		)
		prompt_metrics = append_prompt_metrics(prompt_metrics, AGENT_NAME, metrics)

	log = log_activity(
		{**state, "activity_log": log},
		AGENT_NAME,
		f"Generated questions for {len(questions)} candidates.",
	)

	return {
		"current_step": PipelineStep.INTERVIEW_GENERATION_DONE,
		"interview_questions": questions,
		"errors": errors,
		"prompt_metrics": prompt_metrics,
		"activity_log": log,
	}
