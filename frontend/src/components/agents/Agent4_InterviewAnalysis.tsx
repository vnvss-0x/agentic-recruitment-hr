import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart3, Play, User, ThumbsUp, Clock, ThumbsDown } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { StepHeader } from '../shared/StepHeader'
import { ScoreGauge } from '../shared/ScoreGauge'
import { SkillsRadar } from '../charts/SkillsRadar'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

const recBadge = {
  hire: { icon: ThumbsUp, label: 'Recruter', color: '#34D399', bg: 'rgba(52,211,153,0.1)', border: 'rgba(52,211,153,0.3)' },
  pending: { icon: Clock, label: 'En attente', color: '#FF8A65', bg: 'rgba(255,138,101,0.1)', border: 'rgba(255,138,101,0.3)' },
  reject: { icon: ThumbsDown, label: 'Rejeter', color: '#EF4444', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' },
}

export function Agent4_InterviewAnalysis() {
  const { results, interviews, shortlist, phase, currentStep, analyzeResponses } = useRecruitmentStore()
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeCandidate, setActiveCandidate] = useState<string | null>(null)

  const hasResults = results.length > 0
  const displayId = activeCandidate || 
    (hasResults ? results[0].candidateId : (shortlist.length > 0 ? shortlist[0].id : null))

  const activeResult = results.find((r) => r.candidateId === displayId)
  const activeCandidateInfo = shortlist.find((c) => c.id === displayId)
  const candidateInterviews = interviews.filter((q) => q.candidateId === displayId)

  async function handleAnalyze() {
    setIsProcessing(true)
    await analyzeResponses()
    setIsProcessing(false)
  }

  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        step={4}
        title="Agent 4 — Analyse des Entretiens"
        description="Évaluation des réponses et recommandations"
        status={isProcessing ? 'processing' : hasResults ? 'complete' : 'pending'}
      />

      <AnimatePresence mode="wait">
        {/* Phase 1: Processing Animation */}
        {isProcessing && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-16"
          >
            <div className="mb-6 h-16 w-16 rounded-full border-4 border-[rgba(0,229,255,0.12)] border-t-[#00E5FF] animate-spin" />
            <p className="text-lg text-[#F1F5F9]">Analyse des réponses en cours...</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Évaluation sémantique et scoring par compétence via le modèle de scoring IA</p>
          </motion.div>
        )}

        {/* Phase 2: Raw Responses Preview (before LLM evaluation) */}
        {!hasResults && !isProcessing && (
          <motion.div
            key="raw-responses"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col gap-5"
          >
            {/* Candidate tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {shortlist.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setActiveCandidate(c.id)}
                  className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all whitespace-nowrap ${
                    displayId === c.id
                      ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
                      : 'bg-[rgba(0,229,255,0.04)] text-[#94A3B8] border border-transparent hover:border-[rgba(0,229,255,0.15)]'
                  }`}
                >
                  <User className="h-3.5 w-3.5" />
                  {c.name}
                  <span className="rounded-full bg-[rgba(255,138,101,0.15)] border border-[#FF8A65]/30 px-1.5 py-0.5 text-[9px] text-[#FF8A65]">
                    À évaluer
                  </span>
                </button>
              ))}
            </div>

            {/* Active candidate raw responses */}
            {activeCandidateInfo && (
              <motion.div
                variants={container}
                initial="hidden"
                animate="show"
                key={displayId}
                className="flex flex-col gap-4"
              >
                {/* Header card with action trigger */}
                <motion.div
                  variants={item}
                  className="glass rounded-2xl p-6 border border-[#FF8A65]/20 bg-gradient-to-br from-[#131827] via-[#131827] to-[#FF8A65]/5"
                >
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                      <h4 className="text-xl font-bold text-[#F1F5F9]">{activeCandidateInfo.name}</h4>
                      <p className="mt-1 text-sm text-[#94A3B8]">{activeCandidateInfo.title} · {activeCandidateInfo.yearsExperience} ans d'expérience</p>
                      <p className="mt-2 text-xs text-[#FF8A65] font-semibold flex items-center gap-1.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#FF8A65] animate-pulse" />
                        Réponses reçues — Prêtes pour l'évaluation sémantique et le RAG scoring
                      </p>
                    </div>
                    <button
                      onClick={handleAnalyze}
                      className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95 flex-shrink-0"
                    >
                      <Play className="h-4 w-4" />
                      Lancer l'évaluation IA
                    </button>
                  </div>
                </motion.div>

                {/* Candidate Interview Q&A (Unscored) */}
                {candidateInterviews.length > 0 && (
                  <motion.div variants={item} className="glass rounded-2xl p-6">
                    <h5 className="mb-4 text-sm font-semibold text-[#F1F5F9]">Réponses brutes soumises</h5>
                    <div className="flex flex-col gap-5">
                      {candidateInterviews.map((q, idx) => (
                        <div key={q.id} className="border-b border-[rgba(0,229,255,0.06)] pb-5 last:border-0 last:pb-0">
                          <div className="flex items-start gap-2.5 mb-2.5">
                            <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-[#00E5FF]/10 text-[10px] font-bold text-[#00E5FF] mt-0.5">
                              Q{idx + 1}
                            </span>
                            <div>
                              <p className="text-sm font-medium text-[#F1F5F9]">{q.question}</p>
                              <p className="mt-1 text-xs text-[#64748B] italic">Attente de score pour cette réponse</p>
                            </div>
                          </div>
                          <div className="ml-7 rounded-xl bg-[rgba(0,229,255,0.02)] border border-[rgba(0,229,255,0.05)] p-4 text-sm text-[#94A3B8] leading-relaxed whitespace-pre-wrap">
                            {q.candidateAnswer}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Phase 3: Scored & Analyzed Dashboard */}
        {hasResults && activeResult && !isProcessing && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col gap-5"
          >
            {/* Candidate tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {results.map((r) => {
                const badge = recBadge[r.recommendation]
                return (
                  <button
                    key={r.candidateId}
                    onClick={() => setActiveCandidate(r.candidateId)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all whitespace-nowrap ${
                      displayId === r.candidateId
                        ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
                        : 'bg-[rgba(0,229,255,0.04)] text-[#94A3B8] border border-transparent hover:border-[rgba(0,229,255,0.15)]'
                    }`}
                  >
                    <User className="h-3.5 w-3.5" />
                    {r.candidateName}
                    <span
                      className="ml-1 h-2 w-2 rounded-full"
                      style={{ backgroundColor: badge.color }}
                    />
                  </button>
                )
              })}
            </div>

            {/* Active candidate analysis */}
            <motion.div variants={container} initial="hidden" animate="show" key={displayId} className="flex flex-col gap-4">
              {/* Header card */}
              <motion.div variants={item} className="glass rounded-2xl p-6">
                <div className="flex items-start justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-4">
                    <div className="relative flex-shrink-0">
                      <ScoreGauge score={activeResult.overallScore} size="lg" label="Score global" />
                    </div>
                    <div>
                      <h4 className="text-xl font-bold text-[#F1F5F9]">{activeResult.candidateName}</h4>
                      <div className="mt-2 flex items-center gap-2">
                        {(() => {
                          const badge = recBadge[activeResult.recommendation]
                          const Icon = badge.icon
                          return (
                            <span
                              className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold border"
                              style={{ color: badge.color, backgroundColor: badge.bg, borderColor: badge.border }}
                            >
                              <Icon className="h-3.5 w-3.5" />
                              {badge.label}
                            </span>
                          )
                        })()}
                      </div>
                    </div>
                  </div>

                  {/* Radar */}
                  <div className="flex-shrink-0">
                    <SkillsRadar
                      skills={activeResult.scores.map((s) => ({ name: s.skill, level: s.score }))}
                      size={220}
                    />
                  </div>
                </div>
              </motion.div>

              {/* Skill bars */}
              <motion.div variants={item} className="glass rounded-2xl p-6">
                <h5 className="mb-4 text-sm font-semibold text-[#F1F5F9]">Détail par compétence</h5>
                <div className="flex flex-col gap-3">
                  {activeResult.scores.map((s) => (
                    <div key={s.skill} className="flex items-center gap-3">
                      <span className="w-40 text-sm text-[#94A3B8] truncate">{s.skill}</span>
                      <div className="flex-1 h-2 rounded-full bg-[rgba(0,229,255,0.08)]">
                        <motion.div
                          className="h-full rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${s.score}%` }}
                          transition={{ duration: 0.8, delay: 0.2 }}
                          style={{
                            backgroundColor: s.score >= 85 ? '#00E5FF' : s.score >= 70 ? '#34D399' : '#FF8A65',
                          }}
                        />
                      </div>
                      <span className="w-10 text-right text-sm font-medium text-[#F1F5F9]">{s.score}</span>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Justification */}
              <motion.div variants={item} className="glass rounded-2xl p-6">
                <h5 className="mb-3 text-sm font-semibold text-[#F1F5F9]">Justification</h5>
                <p className="text-sm leading-relaxed text-[#94A3B8]">{activeResult.justification}</p>
              </motion.div>

              {/* Interview Q&A */}
              {candidateInterviews.length > 0 && (
                <motion.div variants={item} className="glass rounded-2xl p-6">
                  <h5 className="mb-4 text-sm font-semibold text-[#F1F5F9]">Évaluation des réponses</h5>
                  <div className="flex flex-col gap-4">
                    {candidateInterviews.map((q, idx) => (
                      <div key={q.id} className="border-b border-[rgba(0,229,255,0.06)] pb-4 last:border-0 last:pb-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-bold text-[#00E5FF]">Q{idx + 1}</span>
                          <span className="text-xs text-[#94A3B8] truncate max-w-[250px] sm:max-w-md">{q.question}</span>
                          <span className="ml-auto rounded-full bg-[rgba(0,229,255,0.1)] px-2 py-0.5 text-[10px] font-bold text-[#00E5FF]">
                            {q.score}/100
                          </span>
                        </div>
                        <p className="text-xs text-[#64748B] leading-relaxed bg-[rgba(0,229,255,0.01)] border border-[rgba(0,229,255,0.03)] p-3 rounded-lg">{q.candidateAnswer}</p>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
