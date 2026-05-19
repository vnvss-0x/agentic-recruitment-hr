"""
Helpers to dispatch pipeline events over WebSocket.
"""

from __future__ import annotations

from typing import Any

from app.api.ws_manager import ws_manager
from app.graph.state import PipelineStep, RecruitmentState


def _model_to_dict(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {"value": value}


def _extract_new_items(prev: list, current: list) -> list:
    if not prev:
        return current
    if len(current) <= len(prev):
        return []
    return current[len(prev) :]


async def dispatch_state_events(
    session_id: str,
    prev_state: RecruitmentState | None,
    new_state: RecruitmentState,
) -> None:
    prev_logs = prev_state.get("activity_log") if prev_state else []
    new_logs = new_state.get("activity_log") or []
    for entry in _extract_new_items(prev_logs or [], new_logs):
        await ws_manager.broadcast_log(session_id, entry)

    prev_step = prev_state.get("current_step") if prev_state else None
    new_step = new_state.get("current_step")
    if new_step and new_step != prev_step:
        await ws_manager.broadcast_step(session_id, new_step)

    prev_errors = prev_state.get("errors") if prev_state else []
    new_errors = new_state.get("errors") or []
    for err in _extract_new_items(prev_errors or [], new_errors):
        message = err.get("message", "error") if isinstance(err, dict) else str(err)
        await ws_manager.broadcast_error(session_id, message)

    if new_step == PipelineStep.COMPLETED or new_state.get("final_report"):
        report = new_state.get("final_report")
        payload = _model_to_dict(report) if report else {}
        await ws_manager.broadcast_complete(session_id, payload)
