"""
Reusable test fixtures: sample CVs, job offers, interview responses.
"""
from __future__ import annotations

from app.graph.state import create_initial_state
from app.models.job import RawJobOffer
from app.models.candidate import RawCV
from datetime import datetime, timezone


def sample_raw_job_offer() -> RawJobOffer:
    return RawJobOffer(
        title="Backend Engineer",
        raw_text=("We are hiring a backend engineer with 3+ years experience in Python, "
                  "APIs and cloud. Responsibilities include building services."),
        source_filename="job.txt",
        company_name="Acme Corp",
    )


def sample_raw_cvs(n: int = 2) -> list[RawCV]:
    cvs: list[RawCV] = []
    for i in range(1, n + 1):
        cvs.append(
            RawCV(
                candidate_id=f"cand-{i}",
                full_name=f"Candidate {i}",
                raw_text=("Experienced engineer with Python and cloud skills. " * 10),
                source_filename=f"cand-{i}.txt",
                email=None,
                phone=None,
            )
        )
    return cvs


def initial_state_for_tests(session_id: str):
    now = datetime.now(timezone.utc).isoformat()
    return create_initial_state(
        session_id=session_id,
        raw_job_offer=sample_raw_job_offer(),
        raw_cvs=sample_raw_cvs(2),
        created_at=now,
    )
