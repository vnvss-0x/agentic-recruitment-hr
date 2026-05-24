import { motion } from 'framer-motion'
import { Shield, ThumbsUp, ThumbsDown, User, Clock, ArrowRight } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { ScoreGauge } from '../shared/ScoreGauge'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

const recConfig = {
  hire: { label: 'Recruter', color: '#34D399', icon: ThumbsUp },
  pending: { label: 'En attente', color: '#FF8A65', icon: Clock },
  reject: { label: 'Rejeter', color: '#EF4444', icon: ThumbsDown },
}

export function ValidationManager() {
  const { results, approveDecision } = useRecruitmentStore()

  const hireCount = results.filter((r) => r.recommendation === 'hire').length
  const bestCandidate = [...results].sort((a, b) => b.overallScore - a.overallScore)[0]

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#FF8A65]/15 shadow-[0_0_15px_rgba(255,138,101,0.2)]">
          <Shield className="h-6 w-6 text-[#FF8A65]" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[#F1F5F9]">
            Validation Manager — Décision finale
          </h3>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Revue du résumé décisionnel. Approuvez ou rejetez les recommandations du pipeline.
          </p>
        </div>
      </div>

      {/* Pipeline blocked alert */}
      <div className="flex items-center gap-3 rounded-xl border border-[#FF8A65]/30 bg-[#FF8A65]/5 px-5 py-3">
        <div className="h-2 w-2 rounded-full bg-[#FF8A65] animate-pulse" />
        <p className="text-sm text-[#FF8A65]">
          Décision manager requise — le rapport final ne sera généré qu'après approbation
        </p>
      </div>

      {/* Summary cards */}
      <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-4">
        {/* Best candidate highlight */}
        {bestCandidate && (
          <motion.div variants={item} className="glass rounded-2xl p-6 border-[#00E5FF]/20 glow-cyan-sm">
            <p className="text-xs font-semibold text-[#00E5FF] uppercase tracking-wider mb-3">Meilleur candidat</p>
            <div className="flex items-center gap-5">
              <ScoreGauge score={bestCandidate.overallScore} size="md" />
              <div className="flex-1">
                <h4 className="text-xl font-bold text-[#F1F5F9]">{bestCandidate.candidateName}</h4>
                <div className="mt-2 flex items-center gap-2">
                  {(() => {
                    const cfg = recConfig[bestCandidate.recommendation]
                    const Icon = cfg.icon
                    return (
                      <span
                        className="flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold border"
                        style={{ color: cfg.color, backgroundColor: `${cfg.color}15`, borderColor: `${cfg.color}30` }}
                      >
                        <Icon className="h-3 w-3" />
                        {cfg.label}
                      </span>
                    )
                  })()}
                </div>
                <p className="mt-3 text-sm text-[#94A3B8] leading-relaxed">{bestCandidate.justification}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* All candidates summary */}
        <motion.div variants={item} className="glass rounded-2xl p-6">
          <h5 className="mb-4 text-sm font-semibold text-[#F1F5F9]">Résumé de tous les candidats</h5>
          <div className="flex flex-col gap-3">
            {results
              .sort((a, b) => b.overallScore - a.overallScore)
              .map((r) => {
                const cfg = recConfig[r.recommendation]
                const Icon = cfg.icon
                return (
                  <div key={r.candidateId} className="flex items-center gap-3 rounded-lg bg-[rgba(0,229,255,0.02)] p-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[rgba(0,229,255,0.1)] text-xs font-bold text-[#00E5FF]">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h6 className="text-sm font-medium text-[#F1F5F9] truncate">{r.candidateName}</h6>
                    </div>
                    <span className="text-sm font-bold text-[#F1F5F9]">{r.overallScore}/100</span>
                    <span
                      className="flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold border"
                      style={{ color: cfg.color, backgroundColor: `${cfg.color}10`, borderColor: `${cfg.color}30` }}
                    >
                      <Icon className="h-3 w-3" />
                      {cfg.label}
                    </span>
                  </div>
                )
              })}
          </div>
        </motion.div>

        {/* Stats */}
        <motion.div variants={item} className="grid grid-cols-3 gap-4">
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-[#34D399]">{hireCount}</p>
            <p className="text-xs text-[#94A3B8] mt-1">Recommandé(s)</p>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-[#FF8A65]">{results.filter((r) => r.recommendation === 'pending').length}</p>
            <p className="text-xs text-[#94A3B8] mt-1">En attente</p>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-[#EF4444]">{results.filter((r) => r.recommendation === 'reject').length}</p>
            <p className="text-xs text-[#94A3B8] mt-1">Rejeté(s)</p>
          </div>
        </motion.div>

        {/* Decision buttons */}
        <motion.div variants={item} className="flex items-center justify-center gap-4 pt-4">
          <button
            onClick={() => approveDecision(true)}
            className="flex items-center gap-2 rounded-xl bg-[#34D399] px-8 py-3.5 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(52,211,153,0.3)] transition-all hover:shadow-[0_0_30px_rgba(52,211,153,0.5)] hover:scale-105 active:scale-95"
          >
            <ThumbsUp className="h-4 w-4" />
            Approuver le recrutement
          </button>
          <button
            onClick={() => approveDecision(false)}
            className="flex items-center gap-2 rounded-xl border border-[#EF4444]/30 bg-[#EF4444]/10 px-8 py-3.5 text-sm font-semibold text-[#EF4444] transition-all hover:bg-[#EF4444]/20 hover:scale-105 active:scale-95"
          >
            <ThumbsDown className="h-4 w-4" />
            Rejeter
          </button>
        </motion.div>
      </motion.div>
    </div>
  )
}
