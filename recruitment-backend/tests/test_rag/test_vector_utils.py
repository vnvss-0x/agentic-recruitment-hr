"""Minimal tests for RAG utilities that don't require ChromaDB."""
from __future__ import annotations

from app.services.vector_service import _sanitise_metadata, SearchResult


def test_sanitise_metadata_basic():
    meta = {"role": "dev", "levels": ["senior", "mid"], "none": None, "obj": {"a":1}}
    clean = _sanitise_metadata(meta)
    assert clean["role"] == "dev"
    assert "senior" in clean["levels"]
    assert clean["none"] == ""
    assert isinstance(clean["obj"], str)


def test_searchresult_scoring():
    sr = SearchResult.from_chroma("d1", "content", {"k": "v"}, distance=0.2)
    assert 0.0 <= sr.score <= 1.0
    assert sr.doc_id == "d1"
