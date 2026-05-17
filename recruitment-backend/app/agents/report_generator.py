"""
Agent 5 - Final report generation using Gemini.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RecruitmentDecision
from app.models.evaluation import InterviewEvaluation
from app.models.report import FinalReport, RankingEntry, ReportTimelineEvent
from app.prompts.report_generator_prompts import (
	REPORT_GENERATOR_SYSTEM_PROMPT,
	build_report_prompt,
)
from app.utils.json_parser import extract_text, parse_json_response

logger = logging.getLogger(__name__)

AGENT_NAME = "ReportGenerator"
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


def _sanitize_report_data(data: dict[str, Any], candidate_ids: list[str]) -> dict[str, Any]:
	data = data or {}
	data["executive_summary"] = data.get("executive_summary") or ""
	data["recommendations"] = data.get("recommendations") or ""
	selected_id = data.get("selected_candidate_id") or ""
	if selected_id not in candidate_ids:
		selected_id = ""
	data["selected_candidate_id"] = selected_id
	return data


def report_generator_node(state: RecruitmentState) -> dict:
	"""Generate a consolidated final report."""
	log = log_activity(state, AGENT_NAME, "Generating final report.")

	job_profile = state.get("job_profile")
	if not job_profile:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.REPORT_GENERATION,
			AGENT_NAME,
			"Missing job_profile in state.",
			recoverable=False,
			critical=True,
		)

	candidate_profiles = state.get("candidate_profiles") or []
	if not candidate_profiles:
		return apply_error(
			{**state, "activity_log": log},
			PipelineStep.REPORT_GENERATION,
			AGENT_NAME,
			"No candidate profiles available for report generation.",
			recoverable=False,
			critical=True,
		)

	evaluations: dict[str, InterviewEvaluation] = state.get("interview_evaluations") or {}
	errors = state.get("errors") or []

	ranking: list[RankingEntry] = []
	for profile in candidate_profiles:
		eval_data = evaluations.get(profile.candidate_id)
		global_score = profile.compatibility_score
		recommendation = profile.final_decision
		if eval_data:
			global_score = eval_data.global_score
			recommendation = eval_data.recommendation
		ranking.append(
			RankingEntry(
				candidate_id=profile.candidate_id,
				full_name=profile.full_name or "Unknown",
				global_score=float(global_score),
				recommendation=recommendation
				if isinstance(recommendation, RecruitmentDecision)
				else RecruitmentDecision.PENDING,
			)
		)

	ranking.sort(key=lambda r: r.global_score, reverse=True)
	candidate_ids = [r.candidate_id for r in ranking]

	ranking_lines = [
		f"{idx+1}. {r.candidate_id} - {r.global_score:.1f} - {r.recommendation.value}"
		for idx, r in enumerate(ranking)
	]
	ranking_text = "\n".join(ranking_lines)

	manager_validation = state.get("manager_validation")
	manager_choice = None
	if manager_validation:
		manager_choice = manager_validation.selected_candidate_id

	llm = _build_llm()
	prompt = build_report_prompt(
		job_title=job_profile.job_title,
		ranking_table=ranking_text,
		recommended_id=state.get("recommended_candidate_id"),
		manager_choice=manager_choice,
	)

	report_data: dict[str, Any] = {}
	try:
		response = llm.invoke(
			[
				("system", REPORT_GENERATOR_SYSTEM_PROMPT),
				("human", prompt),
			]
		)
		raw_content = extract_text(response.content)
		parsed = parse_json_response(raw_content)
		report_data = _sanitize_report_data(parsed, candidate_ids)
	except Exception as exc:
		logger.warning("[%s] Report synthesis failed: %s", AGENT_NAME, exc)
		errors.append(
			build_error(
				PipelineStep.REPORT_GENERATION,
				AGENT_NAME,
				"Report synthesis failed.",
				recoverable=True,
			)
		)
		report_data = _sanitize_report_data({}, candidate_ids)

	selected_id = report_data.get("selected_candidate_id")
	if not selected_id:
		if manager_choice:
			selected_id = manager_choice
		elif state.get("recommended_candidate_id"):
			selected_id = state.get("recommended_candidate_id")
		elif ranking:
			selected_id = ranking[0].candidate_id

	selected_profile = next(
		(p for p in candidate_profiles if p.candidate_id == selected_id), None
	)

	timeline = []
	if state.get("created_at"):
		timeline.append(
			ReportTimelineEvent(
				step=PipelineStep.INITIALIZED.value,
				timestamp=state.get("created_at"),
				details="Session created",
			)
		)
	timeline.append(
		ReportTimelineEvent(
			step=PipelineStep.REPORT_GENERATION.value,
			timestamp=datetime.now(timezone.utc).isoformat(),
			details="Final report generated",
		)
	)

	report = FinalReport(
		executive_summary=report_data.get("executive_summary") or "",
		selected_candidate_id=selected_id,
		selected_candidate=selected_profile,
		ranking_table=ranking,
		process_timeline=timeline,
		recommendations=report_data.get("recommendations") or "",
		generated_at=datetime.now(timezone.utc).isoformat(),
	)

	log = log_activity({**state, "activity_log": log}, AGENT_NAME, "Report ready.")

	return {
		"current_step": PipelineStep.COMPLETED,
		"final_report": report,
		"errors": errors,
		"activity_log": log,
	}
