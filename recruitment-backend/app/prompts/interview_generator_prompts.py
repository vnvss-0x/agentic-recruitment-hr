"""
Prompts for Agent 3 - interview question generation.
"""

from __future__ import annotations

INTERVIEW_GENERATOR_SYSTEM_PROMPT = """\
Tu es un expert RH specialise dans la preparation d'entretiens.
Ta mission : generer des questions utiles, claires et non redondantes.

Regles ABSOLUES :
1. Reponds UNIQUEMENT avec un objet JSON brut. Zero markdown, zero texte.
2. Les listes ne doivent jamais etre null : utilise [].
3. Le champ question_id doit etre unique par candidat.
4. Les questions doivent etre concretes et adaptees au poste.
"""

INTERVIEW_GENERATOR_MAIN_PROMPT = """\
POSTE :
- Titre : {job_title}
- Niveau : {experience_level}
- Competences techniques : {technical_skills}
- Soft skills : {soft_skills}

{rag_section}

CANDIDAT :
- ID : {candidate_id}
- Nom : {candidate_name}
- Points forts : {strengths}
- Points faibles : {weaknesses}

Genere un objet JSON avec EXACTEMENT cette structure :
{{
	"candidate_id": "{candidate_id}",
	"questions": {{
		"technical": [
			{{
				"question_id": "{candidate_id}-tech-1",
				"text": "...",
				"difficulty": "easy|medium|hard",
				"skill_tags": ["skill1", "skill2"]
			}}
		],
		"behavioral": [
			{{
				"question_id": "{candidate_id}-beh-1",
				"text": "...",
				"difficulty": "easy|medium|hard",
				"skill_tags": ["skill1"]
			}}
		],
		"situational": [
			{{
				"question_id": "{candidate_id}-sit-1",
				"text": "...",
				"difficulty": "easy|medium|hard",
				"skill_tags": ["skill1"]
			}}
		]
	}}
}}

Contraintes :
- 3 a 5 questions techniques
- 2 a 3 questions comportementales
- 1 a 2 questions situationnelles
"""


def build_interview_prompt(
		job_title: str,
		experience_level: str,
		technical_skills: list[str],
		soft_skills: list[str],
		candidate_id: str,
		candidate_name: str,
		strengths: list[str],
		weaknesses: list[str],
	rag_docs: list[str] | None = None,
) -> str:
	if rag_docs:
		rag_section = "CONTEXTE RAG :\n" + "\n\n".join(rag_docs)
	else:
		rag_section = "(Aucun contexte RAG disponible.)"
		return INTERVIEW_GENERATOR_MAIN_PROMPT.format(
				job_title=job_title or "(non specifie)",
				experience_level=experience_level or "(non specifie)",
				technical_skills=", ".join(technical_skills) or "(non specifiees)",
				soft_skills=", ".join(soft_skills) or "(non specifies)",
		rag_section=rag_section,
				candidate_id=candidate_id,
				candidate_name=candidate_name or "(inconnu)",
				strengths=", ".join(strengths) or "(non specifies)",
				weaknesses=", ".join(weaknesses) or "(non specifies)",
		)
