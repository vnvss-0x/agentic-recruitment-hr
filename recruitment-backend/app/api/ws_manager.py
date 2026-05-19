"""
WebSocket manager shared across API modules.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket

from app.api.websocket import (
    WSCompleteMessage,
    WSErrorMessage,
    WSLogMessage,
    WSStepUpdateMessage,
)
from app.graph.state import PipelineStep

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage active WebSocket connections per session_id."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        logger.info("[WS] Connection opened - session %s", session_id)

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        logger.info("[WS] Connection closed - session %s", session_id)

    async def send(self, session_id: str, payload: dict[str, Any]) -> None:
        ws = self._connections.get(session_id)
        if not ws:
            return
        try:
            await ws.send_json(payload)
        except Exception as exc:
            logger.warning("[WS] Send failed for session %s: %s", session_id, exc)
            self.disconnect(session_id)

    async def broadcast_log(self, session_id: str, message: str) -> None:
        payload = WSLogMessage(session_id=session_id, message=message).model_dump(
            mode="json"
        )
        await self.send(session_id, payload)

    async def broadcast_step(
        self,
        session_id: str,
        step: PipelineStep,
        data: dict[str, Any] | None = None,
    ) -> None:
        payload = WSStepUpdateMessage(
            session_id=session_id,
            step=step,
            data=data or {},
        ).model_dump(mode="json")
        await self.send(session_id, payload)

    async def broadcast_error(self, session_id: str, message: str) -> None:
        payload = WSErrorMessage(session_id=session_id, message=message).model_dump(
            mode="json"
        )
        await self.send(session_id, payload)

    async def broadcast_complete(self, session_id: str, result: dict[str, Any]) -> None:
        payload = WSCompleteMessage(session_id=session_id, result=result).model_dump(
            mode="json"
        )
        await self.send(session_id, payload)

    @property
    def active_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
