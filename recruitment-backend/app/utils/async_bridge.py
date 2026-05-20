"""
Run async coroutines from synchronous code (e.g. LangGraph nodes under FastAPI).
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async-bridge")


def run_coroutine_sync(coro) -> T:
	"""
	Execute *coro* and return its result.

	- No running loop: uses asyncio.run().
	- Inside uvicorn/FastAPI loop: runs asyncio.run() in a worker thread.
	"""
	try:
		asyncio.get_running_loop()
	except RuntimeError:
		return asyncio.run(coro)

	future = _executor.submit(asyncio.run, coro)
	return future.result(timeout=300)
