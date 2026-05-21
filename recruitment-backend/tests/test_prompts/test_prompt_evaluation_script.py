"""
Tests unitaires pour le script d'évaluation des prompts (evaluate_prompts.py).
Vérifie la robustesse des fonctions d'agrégation et de génération de rapports.
"""

from __future__ import annotations

import pytest
from scripts.evaluate_prompts import aggregate_results, generate_report


def _print_proof(title: str, payload: object) -> None:
    print(f"\n[PROOF] {title}")
    print(payload)

def test_aggregate_results_with_mock_data():
    # Créer des résultats fictifs simulant 2 essais par couple candidat-prompt
    mock_results = [
        # Variante A
        {
            "variant_id": "A",
            "candidate_id": "cand-1-alice",
            "trial": 1,
            "latency_ms": 120.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 90.0,
            "technical_score": 95.0,
            "experience_score": 85.0,
            "missing_skills": [],
            "strengths": ["Python", "FastAPI"],
            "weaknesses": [],
            "justification": "Alice est une excellente candidate avec de solides compétences.",
            "justification_len": 10,
            "missing_skills_accuracy": 1.0,
            "error": None
        },
        {
            "variant_id": "A",
            "candidate_id": "cand-1-alice",
            "trial": 2,
            "latency_ms": 140.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 92.0,
            "technical_score": 96.0,
            "experience_score": 86.0,
            "missing_skills": [],
            "strengths": ["Python", "FastAPI"],
            "weaknesses": [],
            "justification": "Alice est une excellente candidate avec de solides compétences.",
            "justification_len": 10,
            "missing_skills_accuracy": 1.0,
            "error": None
        },
        {
            "variant_id": "A",
            "candidate_id": "cand-2-bob",
            "trial": 1,
            "latency_ms": 110.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 60.0,
            "technical_score": 50.0,
            "experience_score": 70.0,
            "missing_skills": ["FastAPI"],
            "strengths": ["Python"],
            "weaknesses": ["FastAPI absent"],
            "justification": "Bob a un niveau intermédiaire mais manque de maîtrise sur FastAPI.",
            "justification_len": 11,
            "missing_skills_accuracy": 0.66,
            "error": None
        },
        {
            "variant_id": "A",
            "candidate_id": "cand-3-charlie",
            "trial": 1,
            "latency_ms": 130.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 15.0,
            "technical_score": 10.0,
            "experience_score": 20.0,
            "missing_skills": ["Python", "FastAPI"],
            "strengths": [],
            "weaknesses": ["Totalement hors sujet"],
            "justification": "Charlie est designer et n'a aucune des compétences requises en développement.",
            "justification_len": 12,
            "missing_skills_accuracy": 0.5,
            "error": None
        },
        
        # Variante B
        {
            "variant_id": "B",
            "candidate_id": "cand-1-alice",
            "trial": 1,
            "latency_ms": 90.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 95.0,
            "technical_score": 98.0,
            "experience_score": 90.0,
            "missing_skills": [],
            "strengths": ["Python", "FastAPI", "Kubernetes"],
            "weaknesses": [],
            "justification": "Excellente candidate.",
            "justification_len": 2,
            "missing_skills_accuracy": 1.0,
            "error": None
        },
        {
            "variant_id": "B",
            "candidate_id": "cand-2-bob",
            "trial": 1,
            "latency_ms": 80.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 55.0,
            "technical_score": 45.0,
            "experience_score": 65.0,
            "missing_skills": ["FastAPI", "Docker"],
            "strengths": ["Python"],
            "weaknesses": ["Pas de FastAPI ni Docker"],
            "justification": "Bob a des manques importants.",
            "justification_len": 5,
            "missing_skills_accuracy": 1.0,
            "error": None
        },
        {
            "variant_id": "B",
            "candidate_id": "cand-3-charlie",
            "trial": 1,
            "latency_ms": 95.0,
            "json_ok": True,
            "schema_ok": True,
            "quality_score": 1.0,
            "compatibility_score": 10.0,
            "technical_score": 5.0,
            "experience_score": 15.0,
            "missing_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "strengths": [],
            "weaknesses": ["Inadéquat"],
            "justification": "Charlie est designer UI/UX.",
            "justification_len": 4,
            "missing_skills_accuracy": 1.0,
            "error": None
        }
    ]
    
    aggregated = aggregate_results(mock_results, num_trials=2)

    _print_proof("Aggregated summary", aggregated["summary"])
    
    assert "summary" in aggregated
    assert "A" in aggregated["summary"]
    assert "B" in aggregated["summary"]
    
    var_a = aggregated["summary"]["A"]
    var_b = aggregated["summary"]["B"]
    
    # Vérifications de structure
    assert var_a["json_success_rate"] == 100.0
    assert var_a["schema_compliance_rate"] == 100.0
    assert var_a["avg_quality_score"] == 100.0
    
    # Alice sous Variante A : moyenne de 90.0 et 92.0 -> 91.0
    alice_a = var_a["candidate_stats"]["cand-1-alice"]
    assert alice_a["avg_compatibility_score"] == 91.0
    # Écart-type entre 90.0 et 92.0 est 1.41
    assert alice_a["std_compatibility_score"] == 1.41
    
    # Alice sous Variante B : moyenne de 95.0 (un seul essai)
    alice_b = var_b["candidate_stats"]["cand-1-alice"]
    assert alice_b["avg_compatibility_score"] == 95.0
    assert alice_b["std_compatibility_score"] == 0.0

def test_generate_report_format():
    # Créer un dictionnaire agrégé simulé
    mock_aggregated = {
        "summary": {
            "A": {
                "json_success_rate": 100.0,
                "schema_compliance_rate": 100.0,
                "avg_quality_score": 100.0,
                "avg_latency_ms": 125.0,
                "candidate_stats": {
                    "cand-1-alice": {
                        "avg_compatibility_score": 91.0,
                        "std_compatibility_score": 1.41,
                        "avg_missing_skills_accuracy": 100.0,
                        "avg_justification_words": 10.0
                    },
                    "cand-2-bob": {
                        "avg_compatibility_score": 60.0,
                        "std_compatibility_score": 0.0,
                        "avg_missing_skills_accuracy": 66.0,
                        "avg_justification_words": 11.0
                    },
                    "cand-3-charlie": {
                        "avg_compatibility_score": 15.0,
                        "std_compatibility_score": 0.0,
                        "avg_missing_skills_accuracy": 50.0,
                        "avg_justification_words": 12.0
                    }
                }
            },
            "B": {
                "json_success_rate": 100.0,
                "schema_compliance_rate": 100.0,
                "avg_quality_score": 100.0,
                "avg_latency_ms": 88.3,
                "candidate_stats": {
                    "cand-1-alice": {
                        "avg_compatibility_score": 95.0,
                        "std_compatibility_score": 0.0,
                        "avg_missing_skills_accuracy": 100.0,
                        "avg_justification_words": 2.0
                    },
                    "cand-2-bob": {
                        "avg_compatibility_score": 55.0,
                        "std_compatibility_score": 0.0,
                        "avg_missing_skills_accuracy": 100.0,
                        "avg_justification_words": 5.0
                    },
                    "cand-3-charlie": {
                        "avg_compatibility_score": 10.0,
                        "std_compatibility_score": 0.0,
                        "avg_missing_skills_accuracy": 100.0,
                        "avg_justification_words": 4.0
                    }
                }
            }
        }
    }
    
    report = generate_report(mock_aggregated)

    _print_proof("Generated report preview", report[:1200])
    
    # Vérifier que le rapport contient les éléments clés du Markdown
    assert "# Rapport d'Évaluation des Prompts et Test A/B (CVScreener)" in report
    assert "Variante A (Expert Direct)" in report
    assert "Variante B (Concise & Factual)" in report
    assert "Alice Lemoine" in report
    assert "Bob Martin" in report
    assert "Charlie Dubois" in report
    assert "Taux de respect du schéma" or "Respect du Schéma Requis" in report
