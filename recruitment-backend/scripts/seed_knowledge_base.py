"""Seed the RAG knowledge base into ChromaDB."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.rag.ingestion import ingest_knowledge_base


async def main() -> None:
	base_dir = Path("data/knowledge_base")
	results = await ingest_knowledge_base(base_dir)

	total = 0
	for folder, batch in results.items():
		print(f"{folder}: {len(batch)} items")
		total += len(batch)

	print(f"Total ingested documents: {total}")


if __name__ == "__main__":
	asyncio.run(main())
