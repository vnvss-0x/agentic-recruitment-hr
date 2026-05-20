"""
WebSocket manager shared across API modules.
"""

from __future__ import annotations

import logging
from collections import deque
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

DEFAULT_BUFFER_SIZE = 500


class WebSocketManager:
    """Manage WebSocket connections and per-session event replay buffers."""

    def __init__(self, buffer_size: int = DEFAULT_BUFFER_SIZE) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._buffers: dict[str, deque[dict[str, Any]]] = {}
        self._buffer_size = buffer_size

    def _buffer_for(self, session_id: str) -> deque[dict[str, Any]]:
        if session_id not in self._buffers:
            self._buffers[session_id] = deque(maxlen=self._buffer_size)
        return self._buffers[session_id]

    def record_event(self, session_id: str, payload: dict[str, Any]) -> None:
        """Store an event for late WebSocket subscribers."""
        self._buffer_for(session_id).append(payload)

    def clear_buffer(self, session_id: str) -> None:
        self._buffers.pop(session_id, None)

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        logger.info("[WS] Connection opened - session %s", session_id)

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        logger.info("[WS] Connection closed - session %s", session_id)

    async def emit(self, session_id: str, payload: dict[str, Any]) -> None:
        """Buffer then deliver to the active connection if any."""
        self.record_event(session_id, payload)
        await self.send(session_id, payload)

    async def replay_buffer(self, session_id: str) -> int:
        """Send buffered events to a client that connected after pipeline activity."""
        ws = self._connections.get(session_id)
        if not ws:
            return 0

        buffer = self._buffers.get(session_id)
        if not buffer:
            return 0

        count = 0
        for payload in buffer:
            try:
                await ws.send_json(payload)
                count += 1
            except Exception as exc:
                logger.warning(
                    "[WS] Replay failed for session %s: %s", session_id, exc
                )
                self.disconnect(session_id)
                break
        return count

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
        await self.emit(session_id, payload)

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
        await self.emit(session_id, payload)

    async def broadcast_error(self, session_id: str, message: str) -> None:
        payload = WSErrorMessage(session_id=session_id, message=message).model_dump(
            mode="json"
        )
        await self.emit(session_id, payload)

    async def broadcast_complete(self, session_id: str, result: dict[str, Any]) -> None:
        payload = WSCompleteMessage(session_id=session_id, result=result).model_dump(
            mode="json"
        )
        await self.emit(session_id, payload)

    @property
    def active_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()
