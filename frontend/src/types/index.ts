export interface JobOffer {
  id: string;
  title: string;
  department: string;
  location: string;
  contractType: string;
  experience: string;
  salary_range: string;
  description: string;
  hardSkills: string[];
  softSkills: string[];
  requirements: string[];
  responsibilities: string[];
}

export interface Skill {
  name: string;
  level: number;
  isMissing?: boolean;
}

export interface Education {
  degree: string;
  school: string;
  year: number;
}

export interface RAGSource {
  id: string;
  label: string;
  type: 'historical' | 'reference' | 'benchmark';
  description: string;
}

export interface Candidate {
  id: string;
  name: string;
  email: string;
  phone: string;
  title: string;
  avatar: string;
  yearsExperience: number;
  education: Education[];
  skills: Skill[];
  certifications: string[];
  languages: string[];
  compatibilityScore: number;
  ragSources: RAGSource[];
  status: 'pending' | 'shortlisted' | 'validated' | 'rejected';
}

export interface InterviewQuestion {
  id: string;
  candidateId: string;
  type: 'technical' | 'behavioral' | 'situational';
  question: string;
  expectedAnswer: string;
  candidateAnswer: string;
  score: number;
}

export interface InterviewResult {
  candidateId: string;
  candidateName: string;
  scores: { skill: string; score: number }[];
  overallScore: number;
  recommendation: 'hire' | 'pending' | 'reject';
  justification: string;
}

export interface FinalReport {
  candidateId: string;
  candidateName: string;
  position: string;
  finalScore: number;
  decision: 'approved' | 'rejected';
  justification: string;
  details: {
    experienceScore: number;
    skillsScore: number;
    interviewScore: number;
    cultureFitScore: number;
  };
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  agent: string;
  message: string;
}

export interface RecruitmentStore {
  currentStep: number;
  phase: 'idle' | 'processing' | 'complete' | 'hitl';
  hitlType: 'rh' | 'manager' | null;
  jobOffer: JobOffer | null;
  candidates: Candidate[];
  shortlist: Candidate[];
  validatedCandidates: Candidate[];
  interviews: InterviewQuestion[];
  results: InterviewResult[];
  report: FinalReport | null;
  logs: LogEntry[];
  uploadJobOffer: () => Promise<void>;
  uploadCVs: () => Promise<void>;
  validateShortlist: (candidateId: string, action: 'validate' | 'reject' | 'modify') => void;
  proceedAfterValidation: () => void;
  generateInterviews: () => Promise<void>;
  analyzeResponses: () => Promise<void>;
  approveDecision: (approved: boolean) => void;
  generateReport: () => Promise<void>;
  addLog: (entry: Omit<LogEntry, 'id' | 'timestamp'>) => void;
  goToStep: (step: number) => void;
  reset: () => void;
}
