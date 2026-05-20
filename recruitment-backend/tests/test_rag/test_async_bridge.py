"""Tests for async_bridge utility."""

from __future__ import annotations

import asyncio

from app.utils.async_bridge import run_coroutine_sync


async def _sample_coro(value: int) -> int:
	await asyncio.sleep(0)
	return value + 1


def test_run_coroutine_sync_without_running_loop():
	assert run_coroutine_sync(_sample_coro(41)) == 42


def test_run_coroutine_sync_from_running_loop():
	async def runner():
		return run_coroutine_sync(_sample_coro(10))

	assert asyncio.run(runner()) == 11
