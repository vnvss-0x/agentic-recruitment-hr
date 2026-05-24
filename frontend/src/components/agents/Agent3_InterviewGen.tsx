import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Play, User, HelpCircle, ArrowRight } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { StepHeader } from '../shared/StepHeader'
import { TypewriterText } from '../shared/TypewriterText'
import type { InterviewQuestion } from '../../types'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

const typeBadge: Record<InterviewQuestion['type'], { label: string; color: string; bg: string }> = {
  technical: { label: 'Technique', color: '#00E5FF', bg: 'rgba(0,229,255,0.1)' },
  behavioral: { label: 'Comportemental', color: '#FF8A65', bg: 'rgba(255,138,101,0.1)' },
  situational: { label: 'Mise en situation', color: '#34D399', bg: 'rgba(52,211,153,0.1)' },
}

export function Agent3_InterviewGen() {
  const { interviews, shortlist, phase, currentStep, generateInterviews, goToStep } = useRecruitmentStore()
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeCandidate, setActiveCandidate] = useState<string | null>(null)
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set())

  const hasInterviews = interviews.length > 0
  const candidateIds = [...new Set(interviews.map((q) => q.candidateId))]
  const displayCandidate = activeCandidate || candidateIds[0]

  async function handleGenerate() {
    setIsProcessing(true)
    await generateInterviews()
    setIsProcessing(false)
    if (candidateIds.length > 0) {
      setActiveCandidate(candidateIds[0])
    }
  }

  function handleQuestionRevealed(id: string) {
    setRevealedQuestions((prev) => new Set(prev).add(id))
  }

  const candidateQuestions = interviews.filter((q) => q.candidateId === displayCandidate)
  const candidateName = shortlist.find((c) => c.id === displayCandidate)?.name || 'Candidat'

  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        step={3}
        title="Agent 3 — Génération des Entretiens"
        description="Questions personnalisées pour chaque candidat shortlisté"
        status={isProcessing ? 'processing' : hasInterviews ? 'complete' : 'pending'}
      />

      <AnimatePresence mode="wait">
        {!hasInterviews && !isProcessing && (
          <motion.div
            key="generate"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col items-center gap-5 py-12"
          >
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[rgba(0,229,255,0.08)] border border-[rgba(0,229,255,0.15)]">
              <MessageSquare className="h-10 w-10 text-[#00E5FF]" />
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-[#F1F5F9]">Prêt à générer les entretiens</p>
              <p className="mt-1 text-sm text-[#94A3B8]">{shortlist.length} candidats validés dans la shortlist</p>
            </div>
            <button
              onClick={handleGenerate}
              className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
            >
              <Play className="h-4 w-4" />
              Générer les entretiens
            </button>
          </motion.div>
        )}

        {isProcessing && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-16"
          >
            <div className="mb-6 h-16 w-16 rounded-full border-4 border-[rgba(0,229,255,0.12)] border-t-[#00E5FF] animate-spin" />
            <p className="text-lg text-[#F1F5F9]">Génération personnalisée...</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Analyse des profils et création des questions</p>
          </motion.div>
        )}

        {hasInterviews && (
          <motion.div key="interviews" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-4">
            {/* Candidate tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {candidateIds.map((cid) => {
                const cand = shortlist.find((c) => c.id === cid)
                if (!cand) return null
                return (
                  <button
                    key={cid}
                    onClick={() => setActiveCandidate(cid)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all whitespace-nowrap ${
                      displayCandidate === cid
                        ? 'bg-[#00E5FF]/15 text-[#00E5FF] border border-[#00E5FF]/30'
                        : 'bg-[rgba(0,229,255,0.04)] text-[#94A3B8] border border-transparent hover:border-[rgba(0,229,255,0.15)]'
                    }`}
                  >
                    <User className="h-3.5 w-3.5" />
                    {cand.name}
                  </button>
                )
              })}
            </div>

            {/* Questions list */}
            <motion.div variants={container} initial="hidden" animate="show" key={displayCandidate} className="flex flex-col gap-4">
              {candidateQuestions.map((q, idx) => {
                const badge = typeBadge[q.type]
                const isRevealed = revealedQuestions.has(q.id)
                return (
                  <motion.div key={q.id} variants={item} className="glass rounded-xl p-5">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(0,229,255,0.1)] text-xs font-bold text-[#00E5FF]">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span
                            className="rounded-full px-2.5 py-0.5 text-[10px] font-semibold border"
                            style={{ color: badge.color, backgroundColor: badge.bg, borderColor: `${badge.color}30` }}
                          >
                            {badge.label}
                          </span>
                        </div>
                        <div className="flex items-start gap-2">
                          <HelpCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-[#00E5FF]" />
                          <div className="text-sm text-[#F1F5F9] leading-relaxed">
                            {!isRevealed ? (
                              <TypewriterText text={q.question} speed={15} onComplete={() => handleQuestionRevealed(q.id)} />
                            ) : (
                              q.question
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {isRevealed && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="mt-3 border-t border-[rgba(0,229,255,0.08)] pt-3"
                      >
                        <p className="text-xs font-semibold text-[#94A3B8] mb-1 uppercase tracking-wider">Réponse attendue</p>
                        <p className="text-xs text-[#64748B] leading-relaxed">{q.expectedAnswer}</p>
                      </motion.div>
                    )}
                  </motion.div>
                )
              })}
            </motion.div>

            {/* Continue button */}
            <div className="flex justify-end pt-2">
              <button
                onClick={() => goToStep(3)}
                className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
              >
                Continuer vers l'analyse
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
