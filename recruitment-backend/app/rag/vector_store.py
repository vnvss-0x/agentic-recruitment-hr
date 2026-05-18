"""
Thin wrapper around the vector service for RAG modules.
"""

from __future__ import annotations

from app.services.vector_service import vector_service


async def add_documents(collection: str, documents: list[dict]) -> list:
	return await vector_service.add_documents_batch(
		collection=collection,
		documents=documents,
	)


async def similarity_search(
	collection: str,
	query: str,
	n_results: int,
	metadata_filter: dict | None = None,
	min_score: float = 0.0,
) -> list:
	return await vector_service.similarity_search(
		collection=collection,
		query=query,
		n_results=n_results,
		metadata_filter=metadata_filter,
		min_score=min_score,
	)
