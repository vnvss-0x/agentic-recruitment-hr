"""Initialize ChromaDB collections and show stats."""

from __future__ import annotations

import asyncio

from app.services.vector_service import vector_service


async def main() -> None:
	stats = await vector_service.get_all_stats()
	for item in stats:
		print(item)


if __name__ == "__main__":
	asyncio.run(main())
