import { FinalReport, InterviewResult } from '../types';

export const interviewResults: InterviewResult[] = [
  {
    candidateId: 'cand-001',
    candidateName: 'Sarah Chen',
    scores: [
      { skill: 'Expertise technique', score: 95 },
      { skill: 'Communication', score: 90 },
      { skill: 'Leadership', score: 88 },
      { skill: 'Résolution de problèmes', score: 92 },
      { skill: 'Culture fit', score: 94 },
    ],
    overallScore: 93,
    recommendation: 'hire',
    justification:
      'Profil exceptionnel. Sarah combine une expertise technique pointue (React, TypeScript, architecture) avec des soft skills remarquables. Son expérience chez Google, son leadership naturel et sa capacité à expliquer des concepts complexes en font la candidate idéale pour ce poste.',
  },
  {
    candidateId: 'cand-002',
    candidateName: 'Marc Dubois',
    scores: [
      { skill: 'Expertise technique', score: 82 },
      { skill: 'Communication', score: 80 },
      { skill: 'Leadership', score: 72 },
      { skill: 'Résolution de problèmes', score: 85 },
      { skill: 'Culture fit', score: 78 },
    ],
    overallScore: 80,
    recommendation: 'hire',
    justification:
      'Profil solide avec une bonne double compétence frontend/backend. Sa connaissance de GraphQL et des architectures microservices est un atout. Quelques lacunes sur les aspects avancés du rendering React. Bon potentiel de progression.',
  },
  {
    candidateId: 'cand-003',
    candidateName: 'Léa Moreau',
    scores: [
      { skill: 'Expertise technique', score: 78 },
      { skill: 'Communication', score: 85 },
      { skill: 'Leadership', score: 60 },
      { skill: 'Résolution de problèmes', score: 75 },
      { skill: 'Culture fit', score: 82 },
    ],
    overallScore: 76,
    recommendation: 'pending',
    justification:
      'Candidate prometteuse avec une solide base technique et une excellente curiosité. Son expérience de 3 ans est en dessous du minimum requis (5 ans), mais sa progression rapide et sa soif d\'apprentissage compensent en partie. À considérer pour un profil plus junior.',
  },
  {
    candidateId: 'cand-004',
    candidateName: 'Thomas Bernard',
    scores: [
      { skill: 'Expertise technique', score: 94 },
      { skill: 'Communication', score: 92 },
      { skill: 'Leadership', score: 97 },
      { skill: 'Résolution de problèmes', score: 95 },
      { skill: 'Culture fit', score: 90 },
    ],
    overallScore: 94,
    recommendation: 'hire',
    justification:
      'Profil de leader technique exceptionnel. Thomas apporte une expertise architecturelle rare, une expérience de mentoring solide et une maturité professionnelle évidente. Sa vision stratégique et sa capacité à fédérer les équipes en font un candidat de premier choix.',
  },
  {
    candidateId: 'cand-005',
    candidateName: 'Emma Petit',
    scores: [
      { skill: 'Expertise technique', score: 76 },
      { skill: 'Communication', score: 78 },
      { skill: 'Leadership', score: 65 },
      { skill: 'Résolution de problèmes', score: 72 },
      { skill: 'Culture fit', score: 80 },
    ],
    overallScore: 74,
    recommendation: 'pending',
    justification:
      'Profil correct avec une expérience solide chez Doctolib. Ses résultats sur l\'optimisation du parcours utilisateur sont impressionnants. Cependant, son niveau technique sur les technologies clés (Next.js, GraphQL) est en dessous des attentes pour un poste senior.',
  },
  {
    candidateId: 'cand-006',
    candidateName: 'Antoine Roux',
    scores: [
      { skill: 'Expertise technique', score: 85 },
      { skill: 'Communication', score: 82 },
      { skill: 'Leadership', score: 75 },
      { skill: 'Résolution de problèmes', score: 86 },
      { skill: 'Culture fit', score: 84 },
    ],
    overallScore: 83,
    recommendation: 'hire',
    justification:
      'Très bon profil technique avec une expertise notable en monitoring et performances. Son expérience chez Datadog est un plus pour notre stack. Bonne maturité professionnelle et communication claire. Légèrement en retrait sur le leadership.',
  },
  {
    candidateId: 'cand-007',
    candidateName: 'Camille Fontaine',
    scores: [
      { skill: 'Expertise technique', score: 80 },
      { skill: 'Communication', score: 78 },
      { skill: 'Leadership', score: 85 },
      { skill: 'Résolution de problèmes', score: 88 },
      { skill: 'Culture fit', score: 72 },
    ],
    overallScore: 81,
    recommendation: 'pending',
    justification:
      'Profil d\'architecte avec une vision intéressante, mais son positioning est plus orienté infrastructure/cloud que frontend pur. Ses compétences React/Next.js sont en dessous du niveau senior attendu. Excellente pour un poste d\'architecte solution.',
  },
  {
    candidateId: 'cand-008',
    candidateName: 'Lucas Girard',
    scores: [
      { skill: 'Expertise technique', score: 70 },
      { skill: 'Communication', score: 75 },
      { skill: 'Leadership', score: 55 },
      { skill: 'Résolution de problèmes', score: 68 },
      { skill: 'Culture fit', score: 76 },
    ],
    overallScore: 68,
    recommendation: 'reject',
    justification:
      'Profil junior avec des lacunes significatives sur les technologies clés du poste (Next.js, GraphQL, testing). L\'expérience et la maturité technique ne correspondent pas au niveau senior requis. Ne correspond pas au poste actuel.',
  },
];

export const finalReport: FinalReport = {
  candidateId: 'cand-001',
  candidateName: 'Sarah Chen',
  position: 'Senior Frontend Engineer',
  finalScore: 93.5,
  decision: 'approved',
  justification:
    'Suite à l\'analyse complète du dossier de Sarah Chen par notre pipeline multi-agents, incluant l\'évaluation du CV, les tests techniques, l\'entretien comportemental et les références croisées avec notre base de données historique, le comité de recrutement recommande l\'embauche. Sarah obtient le score global le plus élevé (93.5/100) et satisfait à tous les critères requis pour le poste de Senior Frontend Engineer.',
  details: {
    experienceScore: 92,
    skillsScore: 95,
    interviewScore: 93,
    cultureFitScore: 94,
  },
};
