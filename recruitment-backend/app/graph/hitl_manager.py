"""
Human-in-the-loop node handlers.
"""

from __future__ import annotations

from app.graph.nodes import log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.hitl import HITLStatus, HRShortlistValidation, ManagerFinalValidation

AGENT_HR = "HITL-HR"
AGENT_MANAGER = "HITL-Manager"


def _resolve_shortlist_ids(
	state: RecruitmentState, validation: HRShortlistValidation
) -> list[str]:
	"""Compute the final shortlist after HR adjustments."""
	base_ids = state.get("shortlisted_candidate_ids") or []
	shortlist = list(validation.approved_candidate_ids or base_ids)

	if validation.removed_candidate_ids:
		shortlist = [cid for cid in shortlist if cid not in validation.removed_candidate_ids]

	for cid in validation.added_candidate_ids or []:
		if cid not in shortlist:
			shortlist.append(cid)

	return shortlist


def hitl_hr_node(state: RecruitmentState) -> dict:
	"""HITL 1 - HR validation of the shortlist."""
	log = log_activity(state, AGENT_HR, "Awaiting HR shortlist validation.")

	validation = state.get("hr_validation")
	if validation is None:
		validation = HRShortlistValidation(status=HITLStatus.PENDING)
		return {
			"current_step": PipelineStep.HITL_1_PENDING,
			"hr_validation": validation,
			"activity_log": log,
		}

	if validation.status == HITLStatus.PENDING:
		return {
			"current_step": PipelineStep.HITL_1_PENDING,
			"activity_log": log,
		}

	validated_ids = _resolve_shortlist_ids(state, validation)
	log = log_activity(
		{**state, "activity_log": log},
		AGENT_HR,
		f"HR validation received (status={validation.status}).",
	)

	return {
		"current_step": PipelineStep.HITL_1_DONE,
		"validated_shortlist_ids": validated_ids,
		"activity_log": log,
	}


def hitl_manager_node(state: RecruitmentState) -> dict:
	"""HITL 2 - Manager final decision."""
	log = log_activity(state, AGENT_MANAGER, "Awaiting manager decision.")

	validation = state.get("manager_validation")
	if validation is None:
		validation = ManagerFinalValidation(status=HITLStatus.PENDING)
		return {
			"current_step": PipelineStep.HITL_2_PENDING,
			"manager_validation": validation,
			"activity_log": log,
		}

	if validation.status == HITLStatus.PENDING:
		return {
			"current_step": PipelineStep.HITL_2_PENDING,
			"activity_log": log,
		}

	log = log_activity(
		{**state, "activity_log": log},
		AGENT_MANAGER,
		f"Manager validation received (status={validation.status}).",
	)

	return {
		"current_step": PipelineStep.HITL_2_DONE,
		"activity_log": log,
	}
