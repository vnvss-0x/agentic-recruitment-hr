"""
WebSocket message schemas for the recruitment pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.graph.state import PipelineStep


def now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


class WSMessageType(str, Enum):
	CONNECTED = "connected"
	SUBSCRIBED = "subscribed"
	LOG = "log"
	STEP_UPDATE = "step_update"
	ERROR = "error"
	COMPLETE = "complete"
	PING = "ping"
	PONG = "pong"
	SUBSCRIBE = "subscribe"


class WSMessageBase(BaseModel):
	type: WSMessageType
	session_id: Optional[str] = None
	timestamp: str = Field(default_factory=now_iso)


class WSConnectedMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.CONNECTED
	message: str


class WSSubscribedMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.SUBSCRIBED


class WSLogMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.LOG
	message: str


class WSStepUpdateMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.STEP_UPDATE
	step: PipelineStep
	data: Dict[str, Any] = Field(default_factory=dict)


class WSErrorMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.ERROR
	message: str


class WSCompleteMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.COMPLETE
	result: Dict[str, Any]


class WSPongMessage(WSMessageBase):
	type: WSMessageType = WSMessageType.PONG


class WSPingMessage(BaseModel):
	type: WSMessageType = WSMessageType.PING


class WSSubscribeMessage(BaseModel):
	type: WSMessageType = WSMessageType.SUBSCRIBE
	session_id: str
