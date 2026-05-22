import { motion } from 'framer-motion'
import { Briefcase, FileSearch, MessageSquare, BarChart3, FileText, Check } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'

const steps = [
  { icon: Briefcase, label: 'Analyse du poste', desc: 'Analyse sémantique' },
  { icon: FileSearch, label: 'Screening CV', desc: 'Scoring' },
  { icon: MessageSquare, label: 'Entretiens', desc: 'Génération Q&A' },
  { icon: BarChart3, label: 'Analyse finale', desc: 'Décision' },
  { icon: FileText, label: 'Rapport final', desc: 'Export' },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, x: -20 },
  show: { opacity: 1, x: 0 },
}

export function WorkflowStepper() {
  const currentStep = useRecruitmentStore((s) => s.currentStep)
  const phase = useRecruitmentStore((s) => s.phase)

  return (
    <nav className="flex flex-col gap-0 py-8 px-4">
      <motion.div variants={container} initial="hidden" animate="show" className="relative flex flex-col">
        <div className="absolute left-[19px] top-3 bottom-3 w-px bg-[rgba(0,229,255,0.12)]" />

        {steps.map((step, index) => {
          const Icon = step.icon
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          const isFuture = index > currentStep

          let circleBg = 'bg-[rgba(0,229,255,0.06)]'
          let circleBorder = 'border-[rgba(0,229,255,0.12)]'
          let iconColor = 'text-[#94A3B8]'
          let labelColor = 'text-[#94A3B8]'
          let descColor = 'text-[#64748B]'
          let pulse = false

          if (isCompleted) {
            circleBg = 'bg-[#34D399]/20'
            circleBorder = 'border-[#34D399]/40'
            iconColor = 'text-[#34D399]'
            labelColor = 'text-[#34D399]'
          }

          if (isCurrent) {
            circleBg = 'bg-[rgba(0,229,255,0.15)]'
            circleBorder = 'border-[#00E5FF]'
            iconColor = 'text-[#00E5FF]'
            labelColor = 'text-[#F1F5F9]'
            pulse = true
          }

          return (
            <motion.div
              key={step.label}
              variants={item}
              className="relative flex items-start gap-4 pb-8 last:pb-0"
            >
              <div className="relative z-10 flex-shrink-0">
                <div
                  className={`flex h-[38px] w-[38px] items-center justify-center rounded-full border transition-all duration-300 ${circleBg} ${circleBorder} ${
                    pulse ? 'shadow-[0_0_15px_rgba(0,229,255,0.4)] animate-pulse-glow' : ''
                  }`}
                >
                  {isCompleted ? (
                    <Check className={`h-4 w-4 ${iconColor}`} />
                  ) : (
                    <Icon className={`h-4 w-4 ${iconColor}`} />
                  )}
                </div>
              </div>

              <div className="flex flex-col pt-1.5">
                <span className={`text-sm font-medium leading-tight transition-colors duration-300 ${labelColor} ${
                  isCurrent ? 'drop-shadow-[0_0_6px_rgba(0,229,255,0.5)]' : ''
                }`}>
                  {step.label}
                </span>
                <span className={`mt-0.5 text-xs ${descColor}`}>
                  {step.desc}
                </span>
              </div>
            </motion.div>
          )
        })}
      </motion.div>
    </nav>
  )
}
