"""
Session manager for recruitment pipeline executions.

Storage: in-memory dict (thread-safe). Sessions are lost on server restart.
For production, replace with Redis or a database and align LangGraph checkpointer
(e.g. SqliteSaver / PostgresSaver).

Responsibilities:
1) Create and track session records
2) Store the latest RecruitmentState per session
3) Allow safe read/update operations
4) Expose basic listing and cleanup hooks
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Dict, Iterable, Optional

from app.graph.state import RecruitmentState


@dataclass
class SessionRecord:
	session_id: str
	state: RecruitmentState
	created_at: datetime
	updated_at: datetime

	def to_dict(self) -> dict:
		return {
			"session_id": self.session_id,
			"created_at": self.created_at.isoformat(),
			"updated_at": self.updated_at.isoformat(),
			"state": self.state,
		}


class SessionManager:
	"""In-memory session store with basic lifecycle operations."""

	def __init__(self) -> None:
		self._sessions: Dict[str, SessionRecord] = {}
		self._lock = RLock()

	def create(self, session_id: str, state: RecruitmentState) -> SessionRecord:
		with self._lock:
			if session_id in self._sessions:
				raise ValueError(f"Session already exists: {session_id}")
			now = datetime.now(timezone.utc)
			record = SessionRecord(
				session_id=session_id,
				state=state,
				created_at=now,
				updated_at=now,
			)
			self._sessions[session_id] = record
			return record

	def get(self, session_id: str) -> Optional[SessionRecord]:
		with self._lock:
			return self._sessions.get(session_id)

	def update_state(
		self, session_id: str, new_state: RecruitmentState
	) -> SessionRecord:
		with self._lock:
			record = self._sessions.get(session_id)
			if not record:
				raise KeyError(f"Session not found: {session_id}")
			record.state = new_state
			record.updated_at = datetime.now(timezone.utc)
			return record

	def merge_state(
		self, session_id: str, delta: dict
	) -> SessionRecord:
		"""Merge a partial state update into the stored state."""
		with self._lock:
			record = self._sessions.get(session_id)
			if not record:
				raise KeyError(f"Session not found: {session_id}")
			record.state = {**record.state, **delta}
			record.updated_at = datetime.now(timezone.utc)
			return record

	def delete(self, session_id: str) -> bool:
		with self._lock:
			return self._sessions.pop(session_id, None) is not None

	def list(self) -> Iterable[SessionRecord]:
		with self._lock:
			return list(self._sessions.values())

	def count(self) -> int:
		with self._lock:
			return len(self._sessions)


session_manager = SessionManager()
