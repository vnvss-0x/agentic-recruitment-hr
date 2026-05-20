"""
Tests for prompt evaluation and A/B selection mechanisms.
"""

from __future__ import annotations

import pytest

from app.prompts.prompt_evaluator import (
    PromptVariant,
    append_prompt_metrics,
    build_prompt_report,
    compute_cv_scoring_metrics,
    compute_interview_eval_metrics,
    compute_question_metrics,
    compute_report_metrics,
    select_prompt_variant,
)


class TestPromptVariantSelection:
    def test_single_variant_returns_itself(self):
        variants = [PromptVariant("A", "prompt_a")]
        selected = select_prompt_variant("Agent1", "session-1", variants)
        assert selected.variant_id == "A"

    def test_multiple_variants_deterministic(self):
        variants = [
            PromptVariant("A", "prompt_a", weight=1.0),
            PromptVariant("B", "prompt_b", weight=1.0),
        ]
        session_id = "test-session"
        agent_name = "TestAgent"
        
        # Same session and agent should select same variant
        selected1 = select_prompt_variant(agent_name, session_id, variants)
        selected2 = select_prompt_variant(agent_name, session_id, variants)
        assert selected1.variant_id == selected2.variant_id

    def test_different_sessions_may_select_different_variants(self):
        variants = [
            PromptVariant("A", "prompt_a", weight=1.0),
            PromptVariant("B", "prompt_b", weight=1.0),
        ]
        selected1 = select_prompt_variant("Agent", "session-1", variants)
        selected2 = select_prompt_variant("Agent", "session-2", variants)
        # They may or may not be different, but both should be valid
        assert selected1.variant_id in ("A", "B")
        assert selected2.variant_id in ("A", "B")

    def test_empty_variants_raises_error(self):
        with pytest.raises(ValueError):
            select_prompt_variant("Agent", "session", [])

    def test_weighted_variants(self):
        variants = [
            PromptVariant("A", "prompt_a", weight=10.0),
            PromptVariant("B", "prompt_b", weight=1.0),
        ]
        selected = select_prompt_variant("Agent", "session", variants)
        assert selected.variant_id in ("A", "B")


class TestMetricsComputation:
    def test_cv_scoring_metrics_valid_scores(self):
        parsed = {
            "compatibility_score": 85.5,
            "technical_score": 90.0,
            "experience_score": 80.0,
            "score_justification": "This is a good candidate with strong experience in the field.",
                "strengths": ["Leadership", "Communication"],
                "weaknesses": ["Lack of experience in X"],
                "missing_skills": [],
            }
        metrics = compute_cv_scoring_metrics(parsed)
        assert metrics["strengths_count"] == 2
        assert metrics["weaknesses_count"] == 1

    def test_cv_scoring_metrics_invalid_scores(self):
        parsed = {
            "compatibility_score": 150.0,  # Invalid: > 100
            "technical_score": -10.0,  # Invalid: < 0
            "experience_score": "not_a_number",
            "score_justification": "Short",  # Too short
            "strengths": [],
            "weaknesses": [],
            "missing_skills": [],
        }
        metrics = compute_cv_scoring_metrics(parsed)
        assert metrics["quality_score"] == 0.0
        assert metrics["coherence_score"] == 0.0

    def test_question_metrics_valid_distribution(self):
        from app.models.interview import InterviewQuestion, InterviewQuestionSet, InterviewQuestionType

        questions = InterviewQuestionSet(
            technical=[
                InterviewQuestion(question_id="t1", text="Q1", question_type=InterviewQuestionType.TECHNICAL),
                InterviewQuestion(question_id="t2", text="Q2", question_type=InterviewQuestionType.TECHNICAL),
                InterviewQuestion(question_id="t3", text="Q3", question_type=InterviewQuestionType.TECHNICAL),
                InterviewQuestion(question_id="t4", text="Q4", question_type=InterviewQuestionType.TECHNICAL),
            ],
            behavioral=[
                InterviewQuestion(question_id="b1", text="Q1", question_type=InterviewQuestionType.BEHAVIORAL),
                InterviewQuestion(question_id="b2", text="Q2", question_type=InterviewQuestionType.BEHAVIORAL),
            ],
            situational=[
                InterviewQuestion(question_id="s1", text="Q1", question_type=InterviewQuestionType.SITUATIONAL),
            ],
        )
        metrics = compute_question_metrics(questions)
        assert metrics["quality_score"] == 1.0
        assert metrics["technical_count"] == 4
        assert metrics["behavioral_count"] == 2
        assert metrics["situational_count"] == 1

    def test_interview_eval_metrics_valid(self):
        from app.models.evaluation import InterviewEvaluation
        from app.models.candidate import RecruitmentDecision

        evaluation = InterviewEvaluation(
            candidate_id="cand-1",
            technical_score=85.0,
            behavioral_score=80.0,
            global_score=82.5,
            recommendation=RecruitmentDecision.HIRE,
            justification="Strong technical skills and good communication to address the evaluation needs.",
            strengths=["Detail-oriented"],
            concerns=["Needs more experience"],
        )
        metrics = compute_interview_eval_metrics(evaluation)
        assert metrics["quality_score"] == 1.0
        assert metrics["coherence_score"] == 1.0

    def test_report_metrics_valid(self):
        report_data = {
            "executive_summary": "This is a comprehensive summary with enough words to pass validation and provide useful insights to the hiring team about the final decision.",
            "selected_candidate_id": "cand-1",
            "recommendations": "Hire immediately.",
        }
        valid_ids = ["cand-1", "cand-2", "cand-3"]
        metrics = compute_report_metrics(report_data, valid_ids)
        assert metrics["quality_score"] == 1.0
        assert metrics["selection_ok"] is True

    def test_report_metrics_invalid_selection(self):
        report_data = {
            "executive_summary": "This is a comprehensive summary with enough words to pass validation and provide complete information for the decision making process.",
            "selected_candidate_id": "unknown-cand",
        }
        valid_ids = ["cand-1", "cand-2"]
        metrics = compute_report_metrics(report_data, valid_ids)
        assert metrics["selection_ok"] is False
        assert metrics["quality_score"] == 0.5


class TestMetricsAppend:
    def test_append_first_metric(self):
        result = append_prompt_metrics(None, "Agent1", {"quality": 0.9})
        assert "Agent1" in result
        assert len(result["Agent1"]) == 1
        assert result["Agent1"][0]["quality"] == 0.9

    def test_append_multiple_metrics(self):
        metrics = {"Agent1": [{"quality": 0.9}]}
        result = append_prompt_metrics(metrics, "Agent1", {"quality": 0.8})
        assert len(result["Agent1"]) == 2
        assert result["Agent1"][0]["quality"] == 0.9
        assert result["Agent1"][1]["quality"] == 0.8

    def test_append_different_agents(self):
        metrics = {"Agent1": [{"quality": 0.9}]}
        result = append_prompt_metrics(metrics, "Agent2", {"quality": 0.7})
        assert "Agent1" in result
        assert "Agent2" in result


class TestPromptReport:
    def test_build_prompt_report_aggregation(self):
        metrics = {
            "CVScreener": [
                {"quality_score": 0.9, "coherence_score": 0.95, "stability_score": 1.0, "latency_ms": 150.5},
                {"quality_score": 0.85, "coherence_score": 0.90, "stability_score": 0.95, "latency_ms": 160.2},
            ],
            "InterviewGenerator": [
                {"quality_score": 0.8, "coherence_score": 0.85, "stability_score": 0.90, "latency_ms": 200.0},
            ],
        }
        report = build_prompt_report(metrics)
        
        assert "CVScreener" in report
        assert "InterviewGenerator" in report
        
        cv_report = report["CVScreener"]
        assert cv_report["count"] == 2
        assert cv_report["avg_quality_score"] == round(0.875, 4)
        assert cv_report["avg_coherence_score"] == round(0.925, 4)
        assert cv_report["avg_latency_ms"] == round(155.35, 2)

    def test_build_prompt_report_empty(self):
        report = build_prompt_report({})
        assert report == {}

    def test_build_prompt_report_empty_agent(self):
        metrics = {"Agent1": []}
        report = build_prompt_report(metrics)
        assert "Agent1" not in report
