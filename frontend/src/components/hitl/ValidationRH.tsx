import { motion } from 'framer-motion'
import { ShieldCheck, UserCheck, UserX, ArrowRight } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { ScoreGauge } from '../shared/ScoreGauge'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

export function ValidationRH() {
  const { candidates, validateShortlist, proceedAfterValidation } = useRecruitmentStore()

  const validatedCount = candidates.filter((c) => c.status === 'validated').length
  const rejectedCount = candidates.filter((c) => c.status === 'rejected').length
  const pendingCount = candidates.filter((c) => c.status === 'pending' || c.status === 'shortlisted').length

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#FF8A65]/15 shadow-[0_0_15px_rgba(255,138,101,0.2)]">
          <ShieldCheck className="h-6 w-6 text-[#FF8A65]" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-[#F1F5F9]">
            Sélection des Candidats pour l'Entretien
          </h3>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Sélectionnez les candidats qui passeront à l'étape d'entretien. Les candidats non sélectionnés seront retirés du processus.
          </p>
        </div>
      </div>

      {/* Pipeline blocked alert */}
      <div className="flex items-center gap-3 rounded-xl border border-[#FF8A65]/30 bg-[#FF8A65]/5 px-5 py-3">
        <div className="h-2 w-2 rounded-full bg-[#FF8A65] animate-pulse" />
        <p className="text-sm text-[#FF8A65]">
          Action requise — sélectionnez au moins un candidat pour débloquer l'étape suivante
        </p>
      </div>

      {/* Selection stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="glass rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-[#34D399]">{validatedCount}</p>
          <p className="text-[10px] text-[#94A3B8] mt-0.5">Sélectionné{validatedCount > 1 ? 's' : ''}</p>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-[#EF4444]">{rejectedCount}</p>
          <p className="text-[10px] text-[#94A3B8] mt-0.5">Retiré{rejectedCount > 1 ? 's' : ''}</p>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <p className="text-xl font-bold text-[#94A3B8]">{pendingCount}</p>
          <p className="text-[10px] text-[#94A3B8] mt-0.5">En attente</p>
        </div>
      </div>

      {/* Candidate list */}
      <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-3">
        {candidates.map((candidate) => {
          const isSelected = candidate.status === 'validated'
          const isRejected = candidate.status === 'rejected'

          return (
            <motion.div
              key={candidate.id}
              variants={item}
              className={`glass rounded-xl p-4 transition-all ${
                isSelected
                  ? 'border-[#34D399]/40 bg-[#34D399]/[0.03]'
                  : isRejected
                  ? 'border-[#EF4444]/20 opacity-50'
                  : ''
              }`}
            >
              <div className="flex items-center gap-4">
                {/* Avatar */}
                <div className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold ${
                  isSelected
                    ? 'bg-[#34D399]/20 text-[#34D399]'
                    : isRejected
                    ? 'bg-[#EF4444]/10 text-[#EF4444]/60'
                    : 'bg-gradient-to-br from-[#00E5FF]/20 to-[#00E5FF]/5 text-[#00E5FF]'
                }`}>
                  {candidate.avatar}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-semibold text-[#F1F5F9]">{candidate.name}</h4>
                  <p className="text-xs text-[#94A3B8]">{candidate.title} · {candidate.yearsExperience} ans d'expérience</p>
                </div>

                {/* Score */}
                <div className="flex-shrink-0">
                  <ScoreGauge score={candidate.compatibilityScore} size="sm" />
                </div>

                {/* Action buttons */}
                {isSelected ? (
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 rounded-full bg-[#34D399]/15 px-3 py-1.5 text-xs font-semibold text-[#34D399] border border-[#34D399]/30">
                      <UserCheck className="h-3.5 w-3.5" />
                      Sélectionné
                    </span>
                    <button
                      onClick={() => validateShortlist(candidate.id, 'reject')}
                      className="rounded-lg p-1.5 text-[#64748B] transition-colors hover:bg-[#EF4444]/10 hover:text-[#EF4444]"
                      title="Retirer"
                    >
                      <UserX className="h-4 w-4" />
                    </button>
                  </div>
                ) : isRejected ? (
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 rounded-full bg-[#EF4444]/15 px-3 py-1.5 text-xs font-semibold text-[#EF4444] border border-[#EF4444]/30">
                      <UserX className="h-3.5 w-3.5" />
                      Retiré
                    </span>
                    <button
                      onClick={() => validateShortlist(candidate.id, 'validate')}
                      className="rounded-lg p-1.5 text-[#64748B] transition-colors hover:bg-[#34D399]/10 hover:text-[#34D399]"
                      title="Sélectionner"
                    >
                      <UserCheck className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => validateShortlist(candidate.id, 'validate')}
                      className="flex items-center gap-1.5 rounded-lg bg-[#34D399]/10 px-3 py-1.5 text-xs font-medium text-[#34D399] border border-[#34D399]/20 transition-all hover:bg-[#34D399]/20 hover:scale-105 active:scale-95"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      Sélectionner
                    </button>
                    <button
                      onClick={() => validateShortlist(candidate.id, 'reject')}
                      className="flex items-center gap-1.5 rounded-lg bg-[#EF4444]/10 px-3 py-1.5 text-xs font-medium text-[#EF4444] border border-[#EF4444]/20 transition-all hover:bg-[#EF4444]/20 hover:scale-105 active:scale-95"
                    >
                      <UserX className="h-3.5 w-3.5" />
                      Retirer
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Proceed button */}
      {validatedCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between rounded-xl border border-[rgba(0,229,255,0.2)] bg-[rgba(0,229,255,0.04)] px-6 py-4"
        >
          <p className="text-sm text-[#F1F5F9]">
            <span className="font-bold text-[#00E5FF]">{validatedCount}</span> candidat{validatedCount > 1 ? 's' : ''} sélectionné{validatedCount > 1 ? 's' : ''} pour l'entretien
          </p>
          <button
            onClick={proceedAfterValidation}
            className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-5 py-2.5 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
          >
            Passer aux entretiens
            <ArrowRight className="h-4 w-4" />
          </button>
        </motion.div>
      )}
    </div>
  )
}
