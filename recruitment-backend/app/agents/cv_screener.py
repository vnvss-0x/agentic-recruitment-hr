"""
Agent 2 - CV screening and scoring (baseline implementation).
"""

from __future__ import annotations

from app.graph.nodes import apply_error, log_activity
from app.graph.state import PipelineStep, RecruitmentState
from app.models.candidate import CandidateProfile, CandidateStatus

AGENT_NAME = "CVScreener"


def cv_screener_node(state: RecruitmentState) -> dict:
    """Screen CVs and produce a basic shortlist without LLM scoring."""
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

    candidate_profiles: list[CandidateProfile] = []
    for raw in raw_cvs:
        candidate_profiles.append(
            CandidateProfile(
                candidate_id=raw.candidate_id,
                full_name=raw.full_name or "Unknown",
                email=raw.email,
                phone=raw.phone,
                status=CandidateStatus.ANALYZED,
            )
        )

    shortlist_size = min(3, len(candidate_profiles))
    shortlisted_ids = [p.candidate_id for p in candidate_profiles[:shortlist_size]]

    for profile in candidate_profiles:
        profile.is_shortlisted = profile.candidate_id in shortlisted_ids
        if profile.is_shortlisted:
            profile.status = CandidateStatus.SHORTLISTED

    summary = (
        f"Screening completed. Candidates: {len(candidate_profiles)}, "
        f"shortlist: {len(shortlisted_ids)}."
    )

    log = log_activity({**state, "activity_log": log}, AGENT_NAME, summary)

    return {
        "current_step": PipelineStep.CV_SCREENING_DONE,
        "candidate_profiles": candidate_profiles,
        "shortlisted_candidate_ids": shortlisted_ids,
        "screening_summary": summary,
        "activity_log": log,
    }
