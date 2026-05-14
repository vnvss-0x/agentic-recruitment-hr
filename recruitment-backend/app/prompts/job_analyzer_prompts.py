"""
Prompts de l'Agent 1 — Analyse du Poste.

Ce module centralise tous les prompts utilisés par job_analyzer.py.
Les séparer du code agent permet :
- de versionner et tester les prompts indépendamment,
- de faire des tests A/B via prompt_evaluator.py,
- de modifier les instructions sans toucher à la logique métier.
"""

from __future__ import annotations

# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────

JOB_ANALYZER_SYSTEM_PROMPT = """Tu es un expert en recrutement RH et en analyse de postes avec 15 ans d'expérience.
Ta mission est d'analyser des offres d'emploi et d'en extraire une structure précise
pour guider le processus de recrutement.

Règles ABSOLUES - a respecter sans exception :
1. Reponds UNIQUEMENT avec un objet JSON brut. Aucun bloc markdown (pas de ```json).
   Aucun texte avant ou apres le JSON. Commence directement par { et termine par }.
2. Les champs suivants ne peuvent JAMAIS etre null - utilise "" si absent :
   job_title, ideal_candidate_summary.
3. Les champs liste ne peuvent JAMAIS etre null - utilise [] si vide :
   technical_skills, soft_skills, education_requirements, key_responsibilities, rag_keywords.
4. Pour les champs OPTIONNELS (company_name, location, salary_range) : utilise null.
5. Sois precis sur les niveaux d'experience : ne sur-qualifie pas les postes.
6. Distingue competences obligatoires (is_mandatory: true) et souhaitables (false).
7. ideal_candidate_summary : toujours 3 a 5 phrases completes en francais, jamais vide.
"""

# ─────────────────────────────────────────────
# Prompt principal d'analyse
# ─────────────────────────────────────────────

JOB_ANALYZER_MAIN_PROMPT = """\
Analyse l'offre d'emploi suivante et produis un profil structuré en JSON.

{rag_context_section}

OFFRE D'EMPLOI À ANALYSER :
---
{raw_job_text}
---

Produis un objet JSON avec EXACTEMENT cette structure :
{{
  "job_title": "string — intitulé normalisé du poste",
  "company_name": "string | null",
  "location": "string | null",
  "contract_type": "CDI | CDD | freelance | stage | alternance | autre",
  "work_mode": "présentiel | télétravail | hybride",
  "experience_level": "junior | mid | senior | lead | executive",
  "years_of_experience_min": integer | null,
  "years_of_experience_max": integer | null,
  "technical_skills": [
    {{
      "name": "string",
      "level": "débutant | intermédiaire | expert | null",
      "is_mandatory": true | false
    }}
  ],
  "soft_skills": [
    {{
      "name": "string",
      "description": "string | null"
    }}
  ],
  "education_requirements": ["string"],
  "key_responsibilities": ["string"],
  "salary_range": {{
    "min_value": number | null,
    "max_value": number | null,
    "currency": "EUR",
    "is_estimated": true | false
  }} | null,
  "ideal_candidate_summary": "string — 3 à 5 phrases décrivant le profil idéal",
  "rag_keywords": ["string — 8 à 15 mots-clés pour la recherche vectorielle"],
  "analysis_confidence": float entre 0.0 et 1.0,
  "analysis_notes": "string | null — ambiguïtés ou hypothèses faites"
}}
"""

# ─────────────────────────────────────────────
# Section contextuelle RAG (insérée si disponible)
# ─────────────────────────────────────────────

RAG_CONTEXT_SECTION_TEMPLATE = """\
CONTEXTE ISSU DE POSTES SIMILAIRES (base de connaissances RH) :
---
{rag_documents}
---
Utilise ce contexte pour affiner ton analyse : compare les compétences,
ajuste le niveau d'expérience, et enrichis l'ideal_candidate_summary.
"""

RAG_CONTEXT_EMPTY = """\
(Aucun poste similaire trouvé dans la base de connaissances.)
"""


def build_main_prompt(raw_job_text: str, rag_documents: list[str] | None = None) -> str:
    """
    Construit le prompt final en injectant le texte de l'offre
    et le contexte RAG (si disponible).

    Args:
        raw_job_text: Texte brut de l'offre d'emploi.
        rag_documents: Documents similaires récupérés depuis ChromaDB.

    Returns:
        Prompt complet prêt à être envoyé à Gemini.
    """
    if rag_documents:
        rag_content = "\n\n".join(
            f"[Document {i+1}]\n{doc}" for i, doc in enumerate(rag_documents)
        )
        rag_section = RAG_CONTEXT_SECTION_TEMPLATE.format(rag_documents=rag_content)
    else:
        rag_section = RAG_CONTEXT_EMPTY

    return JOB_ANALYZER_MAIN_PROMPT.format(
        rag_context_section=rag_section,
        raw_job_text=raw_job_text,
    )
