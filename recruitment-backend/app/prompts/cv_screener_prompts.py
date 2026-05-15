"""
Prompts for Agent 2 - CV screening and scoring.
"""

from __future__ import annotations

CV_SCREENER_SYSTEM_PROMPT = """\
Tu es un expert en evaluation de candidatures RH avec 15 ans d'experience.
Ta mission : analyser un CV par rapport a une fiche de poste et produire
un scoring objectif et justifie.

Regles ABSOLUES :
1. Reponds UNIQUEMENT avec un objet JSON brut. Zero markdown, zero texte
   autour. Commence par { et termine par }.
2. Les scores sont des nombres entre 0 et 100 (decimales autorisees).
3. Les champs liste ne peuvent jamais etre null : utilise [].
4. Les champs string obligatoires ne peuvent jamais etre null : utilise "".
5. Sois factuel : base-toi uniquement sur ce qui est ecrit dans le CV.
   N'invente pas de competences absentes.
6. score_justification : 3 a 5 phrases precises citant des elements du CV.
"""

CV_SCREENER_MAIN_PROMPT = """\
FICHE DE POSTE :
---
Titre : {job_title}
Niveau requis : {experience_level}
Experience min : {years_min} ans

Competences techniques obligatoires :
{mandatory_skills}

Competences techniques souhaitables :
{optional_skills}

Soft skills recherches :
{soft_skills}

Profil ideal :
{ideal_summary}
---

{rag_section}

CV DU CANDIDAT (ID: {candidate_id}) :
---
{cv_text}
---

Produis un objet JSON avec EXACTEMENT cette structure :
{{
  "candidate_id": "{candidate_id}",
  "compatibility_score": <float 0-100, score global pondere>,
  "technical_score": <float 0-100, competences techniques uniquement>,
  "experience_score": <float 0-100, adequation experience/seniorite>,
  "missing_skills": ["competences obligatoires absentes du CV"],
  "strengths": ["3 a 5 points forts concrets tires du CV"],
  "weaknesses": ["2 a 3 points faibles ou manques identifies"],
  "score_justification": "3 a 5 phrases factuelles justifiant le score global"
}}

Ponderation du compatibility_score :
  - technical_score  x 0.50
  - experience_score x 0.35
  - soft skills      x 0.15 (evalues implicitement depuis le CV)
"""

RAG_SECTION_TEMPLATE = """\
CONTEXTE ISSU DE LA BASE DE CONNAISSANCES RH :
---
{rag_docs}
---
Utilise ce contexte pour calibrer tes scores par rapport a des candidats
ou grilles d'evaluation historiques pour ce type de poste.
"""

RAG_SECTION_EMPTY = "(Aucun contexte RAG disponible pour ce poste.)\n"

SCREENING_SUMMARY_PROMPT = """\
Tu es un expert RH. Voici le classement de {n} candidats pour le poste
de "{job_title}" :

{rankings_text}

Redige un resume executif de 3 a 5 phrases en francais synthetisant :
- La qualite globale du pool de candidats
- Les points forts et faiblesses recurrents
- Une recommandation sur le nombre de candidats a retenir pour les entretiens

Reponds UNIQUEMENT avec le texte du resume, sans titre ni formatage.
"""


def build_cv_prompt(
	job_title: str,
	experience_level: str,
	years_min: int | None,
	mandatory_skills: list[str],
	optional_skills: list[str],
	soft_skills: list[str],
	ideal_summary: str,
	candidate_id: str,
	cv_text: str,
	rag_docs: list[str] | None = None,
) -> str:
	"""Build the prompt for a single CV scoring request."""
	mandatory_str = (
		"\n".join(f"  - {s}" for s in mandatory_skills) or "  (non specifiees)"
	)
	optional_str = (
		"\n".join(f"  - {s}" for s in optional_skills) or "  (non specifiees)"
	)
	soft_str = "\n".join(f"  - {s}" for s in soft_skills) or "  (non specifiees)"

	if rag_docs:
		rag_content = "\n\n".join(f"[Ref {i+1}]\n{d}" for i, d in enumerate(rag_docs))
		rag_section = RAG_SECTION_TEMPLATE.format(rag_docs=rag_content)
	else:
		rag_section = RAG_SECTION_EMPTY

	return CV_SCREENER_MAIN_PROMPT.format(
		job_title=job_title,
		experience_level=experience_level,
		years_min=years_min or "non specifie",
		mandatory_skills=mandatory_str,
		optional_skills=optional_str,
		soft_skills=soft_str,
		ideal_summary=ideal_summary or "(non specifie)",
		candidate_id=candidate_id,
		cv_text=cv_text,
		rag_section=rag_section,
	)


def build_summary_prompt(job_title: str, rankings_text: str, n: int) -> str:
	"""Build the prompt for the screening summary."""
	return SCREENING_SUMMARY_PROMPT.format(
		job_title=job_title,
		rankings_text=rankings_text,
		n=n,
	)
