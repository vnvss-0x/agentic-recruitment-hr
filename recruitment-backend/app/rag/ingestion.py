"""
Knowledge base ingestion for RAG.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.services.vector_service import (
	COLLECTION_GRIDS,
	COLLECTION_JOBS,
	IndexResult,
	vector_service,
)

logger = logging.getLogger(__name__)

KB_COLLECTIONS = {
	"job_templates": (COLLECTION_JOBS, {"type": "job_template"}),
	"evaluation_grids": (COLLECTION_GRIDS, {"type": "evaluation_grid"}),
	"competency_frameworks": (COLLECTION_GRIDS, {"type": "competency_framework"}),
}

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json"}


def _read_text(file_path: Path) -> str:
	if file_path.suffix.lower() == ".json":
		data = json.loads(file_path.read_text(encoding="utf-8"))
		return json.dumps(data, ensure_ascii=False, indent=2)
	return file_path.read_text(encoding="utf-8", errors="ignore")


def _build_documents(directory: Path, metadata: dict[str, Any]) -> list[dict[str, Any]]:
	documents: list[dict[str, Any]] = []

	for file_path in directory.rglob("*"):
		if not file_path.is_file():
			continue
		if file_path.name.startswith("."):
			continue
		if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
			continue

		content = _read_text(file_path).strip()
		if not content:
			continue

		doc_id = str(file_path.relative_to(directory.parent)).replace("\\", "/")
		documents.append(
			{
				"id": doc_id,
				"content": content,
				"metadata": {
					**metadata,
					"source_path": doc_id,
					"file_name": file_path.name,
				},
			}
		)

	return documents


async def ingest_knowledge_base(base_dir: Path) -> dict[str, list[IndexResult]]:
	"""Ingest all knowledge base folders into ChromaDB."""
	results: dict[str, list[IndexResult]] = {}

	if not base_dir.exists():
		logger.warning("Knowledge base directory not found: %s", base_dir)
		return results


	async def refresh_knowledge_base(base_dir: Path) -> dict[str, list[IndexResult]]:
		"""Refresh knowledge base by re-ingesting documents."""
		return await ingest_knowledge_base(base_dir)

	for folder_name, (collection, metadata) in KB_COLLECTIONS.items():
		folder_path = base_dir / folder_name
		if not folder_path.exists():
			logger.info("Skipping missing folder: %s", folder_path)
			continue

		docs = _build_documents(folder_path, metadata)
		if not docs:
			logger.info("No documents found in %s", folder_path)
			results[folder_name] = []
			continue

		logger.info(
			"Ingesting %d documents from %s into %s",
			len(docs),
			folder_path,
			collection,
		)
		results[folder_name] = await vector_service.add_documents_batch(
			collection=collection,
			documents=docs,
		)

	return results
