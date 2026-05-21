"""Tests for the JSON parser used by LLM agents."""
from __future__ import annotations

from app.utils.json_parser import extract_text, parse_json_response


def test_extract_text_from_list_payload():
	content = [{"type": "text", "text": "hello"}, {"text": " world"}]
	assert extract_text(content) == "hello\n world"


def test_parse_json_response_from_fenced_block():
	raw = "```json\n{\"score\": 42}\n```"
	assert parse_json_response(raw) == {"score": 42}


def test_parse_json_response_returns_empty_dict_on_invalid_text():
	raw = "I could not produce structured JSON for this answer."
	assert parse_json_response(raw) == {}
