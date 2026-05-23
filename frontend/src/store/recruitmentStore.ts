import { create } from 'zustand';
import { RecruitmentStore, Candidate, LogEntry, InterviewQuestion } from '../types';
import { jobOffers } from '../data/jobOffers';
import { candidates } from '../data/candidates';
import { interviewQuestions } from '../data/interviews';
import { interviewResults, finalReport } from '../data/reports';

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

let logId = 0;

function makeLog(entry: Omit<LogEntry, 'id' | 'timestamp'>): LogEntry {
  logId++;
  return {
    ...entry,
    id: `log-${logId}`,
    timestamp: new Date().toISOString(),
  };
}

function shuffleAndTake<T>(arr: T[], n: number): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, n);
}

export const useRecruitmentStore = create<RecruitmentStore>((set, get) => ({
  currentStep: 0,
  phase: 'idle',
  hitlType: null,
  jobOffer: null,
  candidates: [],
  shortlist: [],
  validatedCandidates: [],
  interviews: [],
  results: [],
  report: null,
  logs: [],

  addLog: (entry) => {
    set((s) => ({ logs: [...s.logs, makeLog(entry)] }));
  },

  uploadJobOffer: async () => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Agent 1 - Analyse', message: 'Initialisation de l\'analyse sémantique du poste...' });
    store.addLog({ level: 'info', agent: 'Agent 1 - Analyse', message: 'Chargement du fichier offre d\'emploi...' });
    await delay(800);
    store.addLog({ level: 'info', agent: 'Agent 1 - Analyse', message: 'Extraction des métadonnées et structuration...' });
    await delay(600);
    store.addLog({ level: 'info', agent: 'Agent 1 - Analyse', message: 'Analyse des compétences requises (hard & soft)...' });
    await delay(700);
    store.addLog({ level: 'info', agent: 'Agent 1 - Analyse', message: 'Calcul du référentiel de compatibilité...' });
    await delay(500);
    store.addLog({ level: 'success', agent: 'Agent 1 - Analyse', message: `Offre "${jobOffers[0].title}" analysée avec succès (${jobOffers[0].hardSkills.length} hard skills, ${jobOffers[0].softSkills.length} soft skills).` });

    set({
      jobOffer: jobOffers[0],
      candidates: [],
      phase: 'complete',
      currentStep: 0,
    });
  },

  uploadCVs: async () => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Agent 2 - Screening', message: 'Initialisation du pipeline de screening...' });
    await delay(600);
    store.addLog({ level: 'info', agent: 'Agent 2 - Screening', message: 'Analyse des CVs reçus...' });
    await delay(800);
    store.addLog({ level: 'info', agent: 'Agent 2 - Screening', message: 'Comparaison RAG avec la base de données historique...' });
    await delay(700);
    store.addLog({ level: 'info', agent: 'Agent 2 - Screening', message: 'Calcul des scores de compatibilité...' });
    await delay(600);
    const sorted = candidates
      .map((c) => ({ ...c }))
      .sort((a, b) => b.compatibilityScore - a.compatibilityScore);
    set({ candidates: sorted });
    await delay(400);
    store.addLog({ level: 'success', agent: 'Agent 2 - Screening', message: `Screening terminé : ${sorted.length} candidats analysés et classés.` });
    store.addLog({ level: 'info', agent: 'Agent 2 - Screening', message: 'En attente de validation RH pour la shortlist...' });
    set({ phase: 'hitl', hitlType: 'rh', currentStep: 1 });
  },

  validateShortlist: (candidateId, action) => {
    const store = get();
    const candidate = store.candidates.find((c) => c.id === candidateId);
    if (!candidate) return;

    if (action === 'validate') {
      candidate.status = 'validated';
      set({ validatedCandidates: [...store.validatedCandidates, candidate], shortlist: [...store.shortlist, candidate] });
      store.addLog({ level: 'success', agent: 'RH - Validation', message: `${candidate.name} validé(e) pour la suite du processus.` });
    } else if (action === 'reject') {
      candidate.status = 'rejected';
      store.addLog({ level: 'warning', agent: 'RH - Validation', message: `${candidate.name} retiré(e) de la shortlist.` });
    } else if (action === 'modify') {
      candidate.status = 'shortlisted';
      if (!store.shortlist.find((c) => c.id === candidateId)) {
        set({ shortlist: [...store.shortlist, candidate] });
      }
      store.addLog({ level: 'info', agent: 'RH - Validation', message: `${candidate.name} marqué(e) pour entretien (modification manuelle).` });
    }
    set({ candidates: [...store.candidates] });
  },

  proceedAfterValidation: () => {
    const store = get();
    store.addLog({ level: 'success', agent: 'Pipeline', message: 'Validation RH terminée. Passage à l\'étape de génération des entretiens.' });
    set({ phase: 'complete', hitlType: null, currentStep: 2 });
  },

  generateInterviews: async () => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Agent 3 - Entretiens', message: 'Génération des entretiens personnalisés...' });
    await delay(600);
    store.addLog({ level: 'info', agent: 'Agent 3 - Entretiens', message: 'Analyse du profil de chaque candidat...' });
    await delay(800);
    store.addLog({ level: 'info', agent: 'Agent 3 - Entretiens', message: 'Consultation du référentiel de questions...' });
    await delay(700);
    store.addLog({ level: 'info', agent: 'Agent 3 - Entretiens', message: 'Personnalisation des questions techniques et comportementales...' });
    await delay(500);

    const shortlistIds = store.shortlist.map((c) => c.id);
    const generated: InterviewQuestion[] = interviewQuestions.filter((q) =>
      shortlistIds.includes(q.candidateId)
    );
    set({ interviews: generated });
    store.addLog({ level: 'success', agent: 'Agent 3 - Entretiens', message: `${generated.length} questions générées pour ${store.shortlist.length} candidats.` });
    set({ phase: 'complete', currentStep: 2 });
  },

  analyzeResponses: async () => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Agent 4 - Analyse', message: 'Analyse des réponses aux entretiens...' });
    await delay(800);
    store.addLog({ level: 'info', agent: 'Agent 4 - Analyse', message: 'Évaluation par compétence via le modèle de scoring...' });
    await delay(700);
    store.addLog({ level: 'info', agent: 'Agent 4 - Analyse', message: 'Comparaison avec les réponses attendues (RAG)...' });
    await delay(600);
    store.addLog({ level: 'info', agent: 'Agent 4 - Analyse', message: 'Génération des recommandations...' });
    await delay(500);

    const shortlistIds = store.shortlist.map((c) => c.id);
    const results = interviewResults.filter((r) => shortlistIds.includes(r.candidateId));
    set({ results });
    store.addLog({ level: 'success', agent: 'Agent 4 - Analyse', message: 'Analyse terminée. Rapports prêts pour validation manager.' });
    set({ phase: 'hitl', hitlType: 'manager', currentStep: 3 });
  },

  approveDecision: (approved) => {
    const store = get();
    if (approved) {
      store.addLog({ level: 'success', agent: 'Manager - Décision', message: 'Recrutement approuvé. Génération du rapport final...' });
    } else {
      store.addLog({ level: 'warning', agent: 'Manager - Décision', message: 'Recrutement rejeté. Clôture du processus.' });
    }
    set({ phase: 'complete', hitlType: null, currentStep: approved ? 4 : 0 });
  },

  generateReport: async () => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Agent 5 - Rapport', message: 'Génération du rapport final consolidé...' });
    await delay(600);
    store.addLog({ level: 'info', agent: 'Agent 5 - Rapport', message: 'Agrégation des scores et métriques...' });
    await delay(500);
    store.addLog({ level: 'info', agent: 'Agent 5 - Rapport', message: 'Génération des graphiques de performance...' });
    await delay(400);
    store.addLog({ level: 'info', agent: 'Agent 5 - Rapport', message: 'Création du document exportable...' });
    await delay(500);
    set({ report: finalReport });
    store.addLog({ level: 'success', agent: 'Agent 5 - Rapport', message: 'Rapport final prêt. Candidate recommandée : Sarah Chen (score 93.5/100).' });
    set({ phase: 'complete', currentStep: 4 });
  },

  goToStep: (step) => {
    const store = get();
    store.addLog({ level: 'info', agent: 'Pipeline', message: `Passage à l'étape ${step + 1}...` });
    set({ currentStep: step, phase: 'idle' });
  },

  reset: () => {
    logId = 0;
    set({
      currentStep: 0,
      phase: 'idle',
      hitlType: null,
      jobOffer: null,
      candidates: [],
      shortlist: [],
      validatedCandidates: [],
      interviews: [],
      results: [],
      report: null,
      logs: [],
    });
  },
}));
