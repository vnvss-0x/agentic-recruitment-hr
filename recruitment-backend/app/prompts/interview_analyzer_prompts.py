"""
Prompts for Agent 4 - interview response analysis.
"""

from __future__ import annotations

INTERVIEW_ANALYZER_SYSTEM_PROMPT = """\
Tu es un expert RH charge d'evaluer des entretiens.
Tu dois donner des scores coherents et des justifications factuelles.

Regles ABSOLUES :
1. Reponds UNIQUEMENT avec un objet JSON brut. Zero markdown, zero texte.
2. Les scores sont entre 0 et 100.
3. Les listes ne doivent jamais etre null : utilise [].
4. recommendation doit etre : "recruter", "liste_attente", "rejeter", "en_attente".
"""

INTERVIEW_ANALYZER_SYSTEM_PROMPT_B = """\
Tu es un evaluateur RH charge d'analyser des entretiens.
Tu dois donner des scores coherents et des justifications concises.

Regles ABSOLUES :
1. Reponds UNIQUEMENT avec un objet JSON brut.
2. Les scores sont entre 0 et 100.
3. Les listes ne doivent jamais etre null : utilise [].
"""

INTERVIEW_ANALYZER_MAIN_PROMPT = """\
POSTE :
- Titre : {job_title}
- Niveau : {experience_level}
- Competences techniques : {technical_skills}
- Soft skills : {soft_skills}

{rag_section}

CANDIDAT :
- ID : {candidate_id}
- Nom : {candidate_name}

QUESTIONS ET REPONSES :
{qa_block}

Produis un objet JSON avec EXACTEMENT cette structure :
{{
  "candidate_id": "{candidate_id}",
  "technical_score": <float 0-100>,
  "behavioral_score": <float 0-100>,
  "global_score": <float 0-100>,
  "recommendation": "recruter|liste_attente|rejeter|en_attente",
  "justification": "3 a 5 phrases factuelles",
  "strengths": ["points forts"],
  "concerns": ["points faibles ou risques"]
}}
"""


def build_interview_analysis_prompt(
	job_title: str,
	experience_level: str,
	technical_skills: list[str],
	soft_skills: list[str],
	candidate_id: str,
	candidate_name: str,
	qa_block: str,
	rag_docs: list[str] | None = None,
) -> str:
	if rag_docs:
		rag_section = "CONTEXTE RAG :\n" + "\n\n".join(rag_docs)
	else:
		rag_section = "(Aucun contexte RAG disponible.)"
	return INTERVIEW_ANALYZER_MAIN_PROMPT.format(
		job_title=job_title or "(non specifie)",
		experience_level=experience_level or "(non specifie)",
		technical_skills=", ".join(technical_skills) or "(non specifiees)",
		soft_skills=", ".join(soft_skills) or "(non specifies)",
		rag_section=rag_section,
		candidate_id=candidate_id,
		candidate_name=candidate_name or "(inconnu)",
		qa_block=qa_block or "(aucune reponse fournie)",
	)
