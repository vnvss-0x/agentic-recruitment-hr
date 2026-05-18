"""
Embedding utilities for RAG health checks.
"""

from __future__ import annotations

import asyncio
import logging

from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)


def vector_store_ready() -> bool:
	"""Return True if the vector store can be queried."""
	try:
		asyncio.run(vector_service.get_all_stats())
		return True
	except RuntimeError:
		logger.warning("Vector store check skipped inside running loop.")
		return False
	except Exception as exc:
		logger.error("Vector store unavailable: %s", exc)
		return False
