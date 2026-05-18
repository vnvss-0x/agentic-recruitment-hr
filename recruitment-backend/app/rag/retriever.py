"""
Business retriever for RAG contexts.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.models.job import JobProfile
from app.services.vector_service import (
	COLLECTION_GRIDS,
	COLLECTION_JOBS,
	SearchResult,
	vector_service,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_DOCS = 4


def _run_async(coro):
	try:
		return asyncio.run(coro)
	except RuntimeError:
		logger.warning("RAG retriever called from running event loop; skipping.")
		return []


def _format_results(results: list[SearchResult], source: str) -> list[dict[str, Any]]:
	formatted: list[dict[str, Any]] = []
	for res in results:
		formatted.append(
			{
				"content": res.content,
				"metadata": {**res.metadata, "source": source},
				"score": res.score,
			}
		)
	return formatted


def _merge_results(*batches: list[dict[str, Any]], max_docs: int) -> list[dict[str, Any]]:
	combined: list[dict[str, Any]] = []
	for batch in batches:
		combined.extend(batch)
	combined.sort(key=lambda d: d.get("score", 0.0), reverse=True)
	return combined[:max_docs]


def build_job_query(job_profile: JobProfile) -> str:
	skills = ", ".join(s.name for s in job_profile.technical_skills)
	soft = ", ".join(s.name for s in job_profile.soft_skills)
	return f"{job_profile.job_title}. Skills: {skills}. Soft skills: {soft}."


def retrieve_job_context(
	raw_job_text: str | None,
	job_profile: JobProfile | None = None,
	max_docs: int = DEFAULT_MAX_DOCS,
) -> list[dict[str, Any]]:
	"""Retrieve RAG context for job analysis."""
	query = raw_job_text or (build_job_query(job_profile) if job_profile else "")
	if not query:
		return []

	job_results = _run_async(
		vector_service.similarity_search(
			collection=COLLECTION_JOBS,
			query=query,
			n_results=max_docs,
		)
	)
	grid_results = _run_async(
		vector_service.similarity_search(
			collection=COLLECTION_GRIDS,
			query=query,
			n_results=max_docs,
		)
	)

	return _merge_results(
		_format_results(job_results, COLLECTION_JOBS),
		_format_results(grid_results, COLLECTION_GRIDS),
		max_docs=max_docs,
	)


def retrieve_screening_context(
	job_profile: JobProfile,
	max_docs: int = DEFAULT_MAX_DOCS,
) -> list[dict[str, Any]]:
	"""Retrieve RAG context for CV screening."""
	query = build_job_query(job_profile)
	grid_results = _run_async(
		vector_service.similarity_search(
			collection=COLLECTION_GRIDS,
			query=query,
			n_results=max_docs,
		)
	)
	return _format_results(grid_results, COLLECTION_GRIDS)[:max_docs]


def retrieve_interview_context(
	job_profile: JobProfile,
	max_docs: int = DEFAULT_MAX_DOCS,
) -> list[dict[str, Any]]:
	"""Retrieve RAG context for interview generation and analysis."""
	query = build_job_query(job_profile)
	grid_results = _run_async(
		vector_service.similarity_search(
			collection=COLLECTION_GRIDS,
			query=query,
			n_results=max_docs,
		)
	)
	return _format_results(grid_results, COLLECTION_GRIDS)[:max_docs]


def context_to_text(context: list[dict[str, Any]]) -> list[str]:
	"""Convert context dicts into plain text chunks for prompts."""
	return [doc.get("content", "") for doc in context if doc.get("content")]
