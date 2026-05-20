"""
Prompt evaluation utilities (A/B selection and metrics).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptVariant:
	variant_id: str
	system_prompt: str
	weight: float = 1.0


def select_prompt_variant(
	agent_name: str,
	session_id: str | None,
	variants: list[PromptVariant],
) -> PromptVariant:
	if not variants:
		raise ValueError("No prompt variants provided")
	if len(variants) == 1:
		return variants[0]

	seed = f"{agent_name}:{session_id or ''}".encode("utf-8")
	digest = hashlib.sha256(seed).hexdigest()
	bucket = int(digest[:8], 16) / 0xFFFFFFFF

	total_weight = sum(v.weight for v in variants)
	if total_weight <= 0:
		return variants[0]

	threshold = bucket * total_weight
	running = 0.0
	for variant in variants:
		running += variant.weight
		if threshold <= running:
			return variant
	return variants[-1]


def append_prompt_metrics(
	prompt_metrics: dict[str, Any] | None,
	agent_name: str,
	entry: dict[str, Any],
) -> dict[str, Any]:
	metrics = dict(prompt_metrics or {})
	agent_entries = list(metrics.get(agent_name, []))
	agent_entries.append(entry)
	metrics[agent_name] = agent_entries
	return metrics


def _score_range(value: Any) -> bool:
	try:
		return 0.0 <= float(value) <= 100.0
	except (TypeError, ValueError):
		return False


def compute_cv_scoring_metrics(parsed: dict[str, Any]) -> dict[str, Any]:
	scores_ok = all(
		_score_range(parsed.get(field))
		for field in ["compatibility_score", "technical_score", "experience_score"]
	)
	justification = parsed.get("score_justification") or ""
	justification_ok = len(justification.split()) >= 12

	strengths = parsed.get("strengths") or []
	weaknesses = parsed.get("weaknesses") or []
	missing = parsed.get("missing_skills") or []

	quality_score = (float(scores_ok) + float(justification_ok)) / 2.0
	coherence_score = 1.0 if scores_ok else 0.0
	stability_score = 1.0 if scores_ok else 0.0

	return {
		"quality_score": quality_score,
		"coherence_score": coherence_score,
		"stability_score": stability_score,
		"strengths_count": len(strengths) if isinstance(strengths, list) else 0,
		"weaknesses_count": len(weaknesses) if isinstance(weaknesses, list) else 0,
		"missing_skills_count": len(missing) if isinstance(missing, list) else 0,
		"justification_words": len(justification.split()),
	}


def compute_question_metrics(question_set: Any) -> dict[str, Any]:
	tech = getattr(question_set, "technical", [])
	beh = getattr(question_set, "behavioral", [])
	sit = getattr(question_set, "situational", [])

	tech_ok = 3 <= len(tech) <= 5
	beh_ok = 2 <= len(beh) <= 3
	sit_ok = 1 <= len(sit) <= 2

	quality_score = (float(tech_ok) + float(beh_ok) + float(sit_ok)) / 3.0
	coherence_score = quality_score
	stability_score = 1.0 if (tech or beh or sit) else 0.0

	return {
		"quality_score": quality_score,
		"coherence_score": coherence_score,
		"stability_score": stability_score,
		"technical_count": len(tech),
		"behavioral_count": len(beh),
		"situational_count": len(sit),
	}


def compute_interview_eval_metrics(eval_data: Any) -> dict[str, Any]:
	scores_ok = all(
		_score_range(getattr(eval_data, field, None))
		for field in ["technical_score", "behavioral_score", "global_score"]
	)
	justification = getattr(eval_data, "justification", "") or ""
	justification_ok = len(justification.split()) >= 10

	quality_score = (float(scores_ok) + float(justification_ok)) / 2.0
	coherence_score = 1.0 if scores_ok else 0.0
	stability_score = 1.0 if scores_ok else 0.0

	return {
		"quality_score": quality_score,
		"coherence_score": coherence_score,
		"stability_score": stability_score,
		"justification_words": len(justification.split()),
	}


def compute_report_metrics(report_data: dict[str, Any], valid_ids: list[str]) -> dict[str, Any]:
	summary = report_data.get("executive_summary") or ""
	summary_ok = len(summary.split()) >= 20

	selected_id = report_data.get("selected_candidate_id") or ""
	selection_ok = selected_id in valid_ids if valid_ids else False

	quality_score = (float(summary_ok) + float(selection_ok)) / 2.0
	coherence_score = quality_score
	stability_score = 1.0 if summary_ok else 0.0

	return {
		"quality_score": quality_score,
		"coherence_score": coherence_score,
		"stability_score": stability_score,
		"summary_words": len(summary.split()),
		"selection_ok": selection_ok,
	}


def build_prompt_report(prompt_metrics: dict[str, Any]) -> dict[str, Any]:
	report: dict[str, Any] = {}
	for agent_name, entries in (prompt_metrics or {}).items():
		if not entries:
			continue
		count = len(entries)
		avg_quality = sum(e.get("quality_score", 0.0) for e in entries) / count
		avg_coherence = sum(e.get("coherence_score", 0.0) for e in entries) / count
		avg_stability = sum(e.get("stability_score", 0.0) for e in entries) / count
		avg_latency = sum(e.get("latency_ms", 0.0) for e in entries) / count
		report[agent_name] = {
			"count": count,
			"avg_quality_score": round(avg_quality, 4),
			"avg_coherence_score": round(avg_coherence, 4),
			"avg_stability_score": round(avg_stability, 4),
			"avg_latency_ms": round(avg_latency, 2),
		}
	return report
