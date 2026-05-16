"""
Agent 5 - Final report generation (baseline implementation).
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.graph.nodes import apply_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import RecruitmentDecision
from app.models.report import FinalReport, RankingEntry

AGENT_NAME = "ReportGenerator"


def report_generator_node(state: RecruitmentState) -> dict:
	"""Generate a consolidated final report."""
	log = log_activity(state, AGENT_NAME, "Generating final report.")

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

	evaluations = state.get("interview_evaluations") or {}

	ranking: list[RankingEntry] = []
	for profile in candidate_profiles:
		eval_data = evaluations.get(profile.candidate_id, {})
		global_score = float(eval_data.get("global_score", profile.compatibility_score))
		recommendation = eval_data.get("recommendation", profile.final_decision)
		if not isinstance(recommendation, RecruitmentDecision):
			recommendation = RecruitmentDecision.PENDING

		ranking.append(
			RankingEntry(
				candidate_id=profile.candidate_id,
				full_name=profile.full_name or "Unknown",
				global_score=global_score,
				recommendation=recommendation,
			)
		)

	ranking.sort(key=lambda r: r.global_score, reverse=True)

	manager_validation = state.get("manager_validation")
	selected_id = None
	if manager_validation and manager_validation.selected_candidate_id:
		selected_id = manager_validation.selected_candidate_id
	elif state.get("recommended_candidate_id"):
		selected_id = state.get("recommended_candidate_id")
	elif ranking:
		selected_id = ranking[0].candidate_id

	selected_profile = next(
		(p for p in candidate_profiles if p.candidate_id == selected_id), None
	)

	report = FinalReport(
		executive_summary=(
			"Final report generated with baseline scoring. "
			"Review details before making a decision."
		),
		selected_candidate_id=selected_id,
		selected_candidate=selected_profile,
		ranking_table=ranking,
		process_timeline=[],
		recommendations="Validate top candidates and confirm final decision.",
		generated_at=datetime.now(timezone.utc).isoformat(),
	)

	log = log_activity({**state, "activity_log": log}, AGENT_NAME, "Report ready.")

	return {
		"current_step": PipelineStep.COMPLETED,
		"final_report": report,
		"activity_log": log,
	}
