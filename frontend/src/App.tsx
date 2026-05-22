import { AnimatePresence, motion } from 'framer-motion'
import { useRecruitmentStore } from './store/recruitmentStore'
import { AppShell } from './components/layout/AppShell'
import { Agent1_JobAnalysis } from './components/agents/Agent1_JobAnalysis'
import { Agent2_CVScreening } from './components/agents/Agent2_CVScreening'
import { Agent3_InterviewGen } from './components/agents/Agent3_InterviewGen'
import { Agent4_InterviewAnalysis } from './components/agents/Agent4_InterviewAnalysis'
import { Agent5_FinalReport } from './components/agents/Agent5_FinalReport'
import { ValidationRH } from './components/hitl/ValidationRH'
import { ValidationManager } from './components/hitl/ValidationManager'

function StepContent() {
  const currentStep = useRecruitmentStore((s) => s.currentStep)
  const phase = useRecruitmentStore((s) => s.phase)
  const hitlType = useRecruitmentStore((s) => s.hitlType)

  // HITL overrides
  if (phase === 'hitl' && hitlType === 'rh') {
    return (
      <motion.div key="hitl-rh" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
        <ValidationRH />
      </motion.div>
    )
  }

  if (phase === 'hitl' && hitlType === 'manager') {
    return (
      <motion.div key="hitl-manager" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
        <ValidationManager />
      </motion.div>
    )
  }

  // Regular agent steps
  switch (currentStep) {
    case 0:
      return (
        <motion.div key="step-0" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent1_JobAnalysis />
        </motion.div>
      )
    case 1:
      return (
        <motion.div key="step-1" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent2_CVScreening />
        </motion.div>
      )
    case 2:
      return (
        <motion.div key="step-2" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent3_InterviewGen />
        </motion.div>
      )
    case 3:
      return (
        <motion.div key="step-3" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent4_InterviewAnalysis />
        </motion.div>
      )
    case 4:
      return (
        <motion.div key="step-4" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent5_FinalReport />
        </motion.div>
      )
    default:
      return (
        <motion.div key="step-0" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          <Agent1_JobAnalysis />
        </motion.div>
      )
  }
}

export default function App() {
  return (
    <AppShell>
      <AnimatePresence mode="wait">
        <StepContent />
      </AnimatePresence>
    </AppShell>
  )
}
