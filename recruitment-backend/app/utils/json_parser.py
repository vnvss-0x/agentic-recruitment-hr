"""
Utilities for parsing JSON responses from LLMs.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _first_json_object(content: str) -> str | None:
	"""Return the first brace-delimited JSON object substring if present."""
	start = content.find("{")
	end = content.rfind("}")
	if start == -1 or end == -1 or end <= start:
		return None
	return content[start : end + 1].strip()


def extract_text(content: Any) -> str:
	"""Extract text from an LLM response content payload."""
	if isinstance(content, str):
		return content

	if isinstance(content, list):
		parts: list[str] = []
		for block in content:
			if isinstance(block, dict):
				if block.get("type") == "text":
					parts.append(block.get("text", ""))
				elif "text" in block:
					parts.append(block.get("text", ""))
			elif isinstance(block, str):
				parts.append(block)
		return "\n".join(p for p in parts if p).strip()

	return str(content)


def parse_json_response(raw_content: str) -> dict[str, Any]:
	"""Parse a JSON object from raw LLM output."""
	content = raw_content.strip()
	if not content:
		return {}

	try:
		return json.loads(content)
	except json.JSONDecodeError:
		pass

	fence_pattern = re.compile(
		r"```(?:json)?\s*\n?(.*?)\n?\s*```",
		re.DOTALL | re.IGNORECASE,
	)
	for match in fence_pattern.finditer(content):
		candidate = match.group(1).strip()
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			continue

	candidate = _first_json_object(content)
	if candidate is not None:
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			pass

	return {}
