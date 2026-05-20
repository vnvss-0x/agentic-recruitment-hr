"""Unit tests for Agent 4 (Interview Analyzer) prompt builders and validation."""
from __future__ import annotations

from app.prompts.interview_analyzer_prompts import build_interview_analysis_prompt


def test_build_interview_analysis_prompt_includes_job_title():
    prompt = build_interview_analysis_prompt(
        job_title="Backend Engineer",
        experience_level="senior",
        technical_skills=["python", "sql"],
        soft_skills=["communication"],
        candidate_id="cand-1",
        candidate_name="Alice",
        qa_block="Q1: A1",
        rag_docs=None,
    )
    assert "Backend Engineer" in prompt
    assert "Q1: A1" in prompt


def test_build_interview_analysis_prompt_with_rag():
    rag = ["Doc A content", "Doc B content"]
    prompt = build_interview_analysis_prompt(
        job_title="Backend Engineer",
        experience_level="mid",
        technical_skills=["python"],
        soft_skills=[],
        candidate_id="cand-2",
        candidate_name="Bob",
        qa_block="Q: A",
        rag_docs=rag,
    )
    assert "CONTEXTE RAG" in prompt or "Doc A content" in prompt
