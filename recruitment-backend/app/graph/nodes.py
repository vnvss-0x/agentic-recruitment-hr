"""
Shared helpers for LangGraph nodes.
"""

from __future__ import annotations

from datetime import datetime

from app.graph.state import PipelineError, PipelineStep, RecruitmentState


def log_activity(state: RecruitmentState, agent: str, message: str) -> list[str]:
	"""Append a timestamped activity log entry."""
	timestamp = datetime.now().strftime("%H:%M:%S")
	entry = f"[{timestamp}] [{agent}] {message}"
	existing = state.get("activity_log") or []
	return existing + [entry]


def build_error(
	step: PipelineStep,
	agent: str,
	message: str,
	recoverable: bool,
) -> PipelineError:
	"""Build a consistent PipelineError entry."""
	return PipelineError(
		step=step.value,
		agent=agent,
		message=message,
		recoverable=recoverable,
	)


def apply_error(
	state: RecruitmentState,
	step: PipelineStep,
	agent: str,
	message: str,
	recoverable: bool,
	critical: bool,
) -> dict:
	"""Return a partial state update for an error situation."""
	log = log_activity(state, agent, f"ERROR: {message}")
	errors = state.get("errors") or []
	errors.append(build_error(step, agent, message, recoverable))

	update: dict = {
		"errors": errors,
		"activity_log": log,
	}

	if critical:
		update["has_critical_error"] = True
		update["current_step"] = PipelineStep.ERROR

	return update
