"""
Agent 4 - Interview analysis using Gemini.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, retry_if_exception, stop_after_attempt

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RecruitmentDecision
from app.models.evaluation import InterviewEvaluation
from app.prompts.interview_analyzer_prompts import (
	INTERVIEW_ANALYZER_SYSTEM_PROMPT,
	INTERVIEW_ANALYZER_SYSTEM_PROMPT_B,
	build_interview_analysis_prompt,
)
from app.prompts.prompt_evaluator import (
	PromptVariant,
	append_prompt_metrics,
	compute_interview_eval_metrics,
	select_prompt_variant,
)
from app.rag.retriever import context_to_text, retrieve_interview_context
from app.utils.async_bridge import run_coroutine_sync
from app.utils.json_parser import extract_text, parse_json_response

logger = logging.getLogger(__name__)

AGENT_NAME = "InterviewAnalyzer"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 4096
INTER_CANDIDATE_DELAY_S = 15
QUOTA_BACKOFF_S = 60
MAX_QUOTA_RETRIES = 3


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


def _is_quota_error(exc: Exception) -> bool:
	"""
	Detect Gemini free-tier quota errors.
	We avoid importing provider-specific exception classes and rely on message sniffing.
	"""
	message = str(exc).lower()
	return (
		"429" in message
		or "quota" in message
		or "quota exceeded" in message
		or "generate_content_free_tier_requests" in message
	)


def _build_qa_payload(questions: list[dict[str, Any]], responses: dict[str, str]) -> dict[str, Any]:
	"""
	Build a single JSON payload containing all questions + answers.
	This is sent to the LLM in ONE request per candidate.
	"""
	items: list[dict[str, Any]] = []
	for q in questions:
		qid = q.get("question_id") or ""
		items.append(
			{
				"question_id": qid,
				"text": q.get("text") or "",
				"question_type": q.get("question_type") or q.get("type") or "",
				"difficulty": q.get("difficulty"),
				"skill_tags": q.get("skill_tags") if isinstance(q.get("skill_tags"), list) else [],
				"answer": (responses or {}).get(qid, ""),
			}
		)
	return {"qa": items}


def _quota_retry_predicate(exc: Exception) -> bool:
	return _is_quota_error(exc)


@retry(
	retry=retry_if_exception(_quota_retry_predicate),
	stop=stop_after_attempt(MAX_QUOTA_RETRIES),
	reraise=True,
)
async def _invoke_llm_with_quota_backoff(
	llm: ChatGoogleGenerativeAI,
	system_prompt: str,
	user_prompt: str,
	state: RecruitmentState,
	candidate_id: str,
) -> str:
	"""
	Invoke the LLM with a special backoff on 429/quota errors.
	Tenacity retries only when _is_quota_error() returns True.
	"""
	try:
		response = llm.invoke([("system", system_prompt), ("human", user_prompt)])
		return extract_text(response.content)
	except Exception as exc:
		if _is_quota_error(exc):
			log_activity(
				state,
				AGENT_NAME,
				f"Gemini quota exceeded (429) for candidate {candidate_id}. "
				f"Waiting {QUOTA_BACKOFF_S}s before retry...",
			)
			await asyncio.sleep(QUOTA_BACKOFF_S)
		raise


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
	prompt_metrics = state.get("prompt_metrics") or {}

	llm = _build_llm()
	evaluations: dict[str, InterviewEvaluation] = {}

	variants = [
		PromptVariant("A", INTERVIEW_ANALYZER_SYSTEM_PROMPT, weight=1.0),
		PromptVariant("B", INTERVIEW_ANALYZER_SYSTEM_PROMPT_B, weight=1.0),
	]
	variant = select_prompt_variant(AGENT_NAME, state.get("session_id"), variants)

	skill_names = [s.name for s in job_profile.technical_skills]
	soft_names = [s.name for s in job_profile.soft_skills]

	rag_context = retrieve_interview_context(job_profile)
	rag_docs = context_to_text(rag_context)

	async def evaluate_all_candidates() -> None:
		nonlocal prompt_metrics
		# ONE LLM call per candidate, with rate limiting between candidates.
		for idx, candidate_id in enumerate(candidate_ids):
			profile = next(
				(p for p in candidate_profiles if p.candidate_id == candidate_id), None
			)
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
				# even if missing data, we still rate-limit to avoid bursts
				if idx < len(candidate_ids) - 1:
					await asyncio.sleep(INTER_CANDIDATE_DELAY_S)
				continue

			all_questions = (
				questions_set.technical
				+ questions_set.behavioral
				+ questions_set.situational
			)
			qa_payload = _build_qa_payload(
				[q.model_dump(mode="json") for q in all_questions],
				response_set.answers,
			)
			qa_block = json.dumps(qa_payload, ensure_ascii=False)

			user_prompt = build_interview_analysis_prompt(
				job_title=job_profile.job_title,
				experience_level=job_profile.experience_level.value,
				technical_skills=skill_names,
				soft_skills=soft_names,
				candidate_id=candidate_id,
				candidate_name=(profile.full_name if profile else ""),
				qa_block=qa_block,
				rag_docs=rag_docs,
			)

			try:
				start = time.perf_counter()
				raw_content = await _invoke_llm_with_quota_backoff(
					llm=llm,
					system_prompt=variant.system_prompt,
					user_prompt=user_prompt,
					state={**state, "activity_log": log},
					candidate_id=candidate_id,
				)
				parsed = parse_json_response(raw_content)
				evaluations[candidate_id] = _sanitize_evaluation(parsed, candidate_id)
				latency_ms = (time.perf_counter() - start) * 1000

				metrics = compute_interview_eval_metrics(evaluations[candidate_id])
				metrics.update(
					{
						"variant_id": variant.variant_id,
						"latency_ms": round(latency_ms, 2),
						"candidate_id": candidate_id,
					}
				)
				prompt_metrics = append_prompt_metrics(
					prompt_metrics, AGENT_NAME, metrics
				)
			except Exception as exc:
				logger.warning(
					"[%s] Evaluation failed for %s: %s", AGENT_NAME, candidate_id, exc
				)
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
				latency_ms = 0.0

				metrics = compute_interview_eval_metrics(evaluations[candidate_id])
				metrics.update(
					{
						"variant_id": variant.variant_id,
						"latency_ms": round(latency_ms, 2),
						"candidate_id": candidate_id,
					}
				)
				prompt_metrics = append_prompt_metrics(
					prompt_metrics, AGENT_NAME, metrics
				)

			# Rate limiting between candidates (max 4/minute)
			if idx < len(candidate_ids) - 1:
				await asyncio.sleep(INTER_CANDIDATE_DELAY_S)

	# LangGraph node is sync; run async candidate loop safely even under FastAPI event loop.
	run_coroutine_sync(evaluate_all_candidates())

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
		"prompt_metrics": prompt_metrics,
		"activity_log": log,
	}
