"""
Helpers for running the LangGraph pipeline in API endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.graph.state import RecruitmentState
from app.graph.workflow import recruitment_graph

logger = logging.getLogger(__name__)


def build_graph_config(session_id: str) -> dict[str, Any]:
    return {
        "configurable": {"thread_id": session_id},
        "recursion_limit": settings.langgraph_recursion_limit,
    }


def run_pipeline(
    session_id: str,
    base_state: RecruitmentState,
    state_update: dict[str, Any] | None = None,
) -> RecruitmentState:
    update = state_update or {}
    updated_state: RecruitmentState = {**base_state, **update}
    config = build_graph_config(session_id)

    update_fn = getattr(recruitment_graph, "update_state", None)
    if update_fn and update:
        try:
            try:
                update_fn(config, update)
            except TypeError:
                update_fn(config=config, values=update)
            return recruitment_graph.invoke(None, config)
        except Exception as exc:
            logger.warning("update_state failed, fallback to invoke: %s", exc)

    return recruitment_graph.invoke(updated_state, config)
