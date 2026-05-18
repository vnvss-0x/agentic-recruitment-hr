"""
Agent 2 - CV screening and scoring using Gemini.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from app.graph.nodes import apply_error, build_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import CandidateProfile, CandidateStatus
from app.prompts.cv_screener_prompts import (
    CV_SCREENER_SYSTEM_PROMPT,
    build_cv_prompt,
    build_summary_prompt,
)
from app.rag.retriever import context_to_text, retrieve_screening_context
from app.utils.json_parser import extract_text, parse_json_response

logger = logging.getLogger(__name__)

AGENT_NAME = "CVScreener"
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 4096
SHORTLIST_MAX = 3


def _build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        convert_system_message_to_human=False,
        thinking={"thinking_budget": 0},
    )


def _sanitize_scoring_data(data: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    data = data or {}
    data["candidate_id"] = data.get("candidate_id") or candidate_id

    for field in ["missing_skills", "strengths", "weaknesses"]:
        if not isinstance(data.get(field), list):
            data[field] = []

    for field in ["compatibility_score", "technical_score", "experience_score"]:
        try:
            data[field] = float(data.get(field) or 0.0)
        except (TypeError, ValueError):
            data[field] = 0.0

    data["score_justification"] = data.get("score_justification") or ""
    return data


def cv_screener_node(state: RecruitmentState) -> dict:
    """Screen CVs and produce scoring + shortlist."""
    log = log_activity(state, AGENT_NAME, "Starting CV screening.")

    job_profile = state.get("job_profile")
    if not job_profile:
        return apply_error(
            {**state, "activity_log": log},
            PipelineStep.CV_SCREENING,
            AGENT_NAME,
            "Missing job_profile in state.",
            recoverable=False,
            critical=True,
        )

    raw_cvs = state.get("raw_cvs") or []
    if not raw_cvs:
        return apply_error(
            {**state, "activity_log": log},
            PipelineStep.CV_SCREENING,
            AGENT_NAME,
            "No CVs provided for screening.",
            recoverable=False,
            critical=True,
        )

    llm = _build_llm()
    errors = state.get("errors") or []

    mandatory_skills = [
        s.name for s in job_profile.technical_skills if s.is_mandatory
    ]
    optional_skills = [
        s.name for s in job_profile.technical_skills if not s.is_mandatory
    ]
    soft_skills = [s.name for s in job_profile.soft_skills]

    candidate_profiles: list[CandidateProfile] = []
    rag_context = retrieve_screening_context(job_profile)
    rag_docs = context_to_text(rag_context)

    for raw in raw_cvs:
        user_prompt = build_cv_prompt(
            job_title=job_profile.job_title,
            experience_level=job_profile.experience_level.value,
            years_min=job_profile.years_of_experience_min,
            mandatory_skills=mandatory_skills,
            optional_skills=optional_skills,
            soft_skills=soft_skills,
            ideal_summary=job_profile.ideal_candidate_summary,
            candidate_id=raw.candidate_id,
            cv_text=raw.raw_text,
            rag_docs=rag_docs,
        )

        try:
            response = llm.invoke(
                [
                    ("system", CV_SCREENER_SYSTEM_PROMPT),
                    ("human", user_prompt),
                ]
            )
            raw_content = extract_text(response.content)
            parsed = parse_json_response(raw_content)
            parsed = _sanitize_scoring_data(parsed, raw.candidate_id)
        except Exception as exc:
            logger.warning("[%s] Scoring failed for %s: %s", AGENT_NAME, raw.candidate_id, exc)
            errors.append(
                build_error(
                    PipelineStep.CV_SCREENING,
                    AGENT_NAME,
                    f"Scoring failed for candidate {raw.candidate_id}.",
                    recoverable=True,
                )
            )
            parsed = _sanitize_scoring_data({}, raw.candidate_id)

        candidate_profiles.append(
            CandidateProfile(
                candidate_id=raw.candidate_id,
                full_name=raw.full_name or "Unknown",
                email=raw.email,
                phone=raw.phone,
                compatibility_score=parsed["compatibility_score"],
                technical_score=parsed["technical_score"],
                experience_score=parsed["experience_score"],
                missing_skills=parsed["missing_skills"],
                strengths=parsed["strengths"],
                weaknesses=parsed["weaknesses"],
                score_justification=parsed["score_justification"],
                status=CandidateStatus.ANALYZED,
            )
        )

    candidate_profiles.sort(
        key=lambda c: c.compatibility_score, reverse=True
    )

    shortlist_size = min(SHORTLIST_MAX, len(candidate_profiles))
    shortlisted_ids = [p.candidate_id for p in candidate_profiles[:shortlist_size]]

    for profile in candidate_profiles:
        profile.is_shortlisted = profile.candidate_id in shortlisted_ids
        if profile.is_shortlisted:
            profile.status = CandidateStatus.SHORTLISTED

    ranking_lines = [
        f"{idx+1}. {p.candidate_id} - {p.compatibility_score:.1f}"
        for idx, p in enumerate(candidate_profiles)
    ]
    ranking_text = "\n".join(ranking_lines)

    summary_prompt = build_summary_prompt(
        job_title=job_profile.job_title,
        rankings_text=ranking_text,
        n=len(candidate_profiles),
    )

    screening_summary = (
        f"Screening completed. Candidates: {len(candidate_profiles)}, "
        f"shortlist: {len(shortlisted_ids)}."
    )

    try:
        summary_response = llm.invoke(
            [
                ("system", "You are a concise HR assistant."),
                ("human", summary_prompt),
            ]
        )
        summary_text = extract_text(summary_response.content).strip()
        if summary_text:
            screening_summary = summary_text
    except Exception as exc:
        logger.warning("[%s] Summary generation failed: %s", AGENT_NAME, exc)
        errors.append(
            build_error(
                PipelineStep.CV_SCREENING,
                AGENT_NAME,
                "Screening summary generation failed.",
                recoverable=True,
            )
        )

    log = log_activity(
        {**state, "activity_log": log},
        AGENT_NAME,
        f"Screening done. Shortlist size: {len(shortlisted_ids)}.",
    )

    return {
        "current_step": PipelineStep.CV_SCREENING_DONE,
        "candidate_profiles": candidate_profiles,
        "shortlisted_candidate_ids": shortlisted_ids,
        "screening_summary": screening_summary,
        "errors": errors,
        "activity_log": log,
    }
