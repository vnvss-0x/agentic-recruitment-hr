import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Play, Download, RotateCcw, Award, Briefcase, GraduationCap, Users } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { StepHeader } from '../shared/StepHeader'
import { DecisionGauge } from '../charts/DecisionGauge'
import { CompatibilityBar } from '../charts/CompatibilityBar'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

const detailCards = [
  { key: 'experienceScore' as const, label: 'Expérience', icon: Briefcase, color: '#00E5FF' },
  { key: 'skillsScore' as const, label: 'Compétences', icon: Award, color: '#34D399' },
  { key: 'interviewScore' as const, label: 'Entretien', icon: GraduationCap, color: '#FF8A65' },
  { key: 'cultureFitScore' as const, label: 'Culture Fit', icon: Users, color: '#A78BFA' },
]

export function Agent5_FinalReport() {
  const { report, phase, currentStep, generateReport, reset } = useRecruitmentStore()
  const [isProcessing, setIsProcessing] = useState(false)

  const hasReport = report !== null

  async function handleGenerate() {
    setIsProcessing(true)
    await generateReport()
    setIsProcessing(false)
  }

  function handleExportPDF() {
    window.print()
  }

  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        step={5}
        title="Agent 5 — Rapport Final"
        description="Rapport consolidé et export"
        status={isProcessing ? 'processing' : hasReport ? 'complete' : 'pending'}
      />

      <AnimatePresence mode="wait">
        {!hasReport && !isProcessing && (
          <motion.div
            key="start"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="flex flex-col items-center gap-5 py-12"
          >
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[rgba(0,229,255,0.08)] border border-[rgba(0,229,255,0.15)]">
              <FileText className="h-10 w-10 text-[#00E5FF]" />
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-[#F1F5F9]">Générer le rapport final</p>
              <p className="mt-1 text-sm text-[#94A3B8]">Consolidation de toutes les données du pipeline</p>
            </div>
            <button
              onClick={handleGenerate}
              className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
            >
              <Play className="h-4 w-4" />
              Générer le rapport
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
            <p className="text-lg text-[#F1F5F9]">Génération du rapport...</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Agrégation des scores et création du document</p>
          </motion.div>
        )}

        {hasReport && report && (
          <motion.div
            key="report"
            variants={container}
            initial="hidden"
            animate="show"
            className="flex flex-col gap-5"
          >
            {/* Decision summary */}
            <motion.div variants={item} className="glass rounded-2xl p-8">
              <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
                <DecisionGauge score={report.finalScore} decision={report.decision} label="Score final" />
                <div className="flex-1 text-center sm:text-left">
                  <p className="text-xs font-semibold text-[#94A3B8] uppercase tracking-wider mb-1">Candidat Recommandé</p>
                  <h4 className="text-2xl font-bold text-[#F1F5F9]">{report.candidateName}</h4>
                  <p className="mt-1 text-sm text-[#94A3B8]">{report.position}</p>
                  <p className="mt-4 text-sm leading-relaxed text-[#94A3B8]">{report.justification}</p>
                </div>
              </div>
            </motion.div>

            {/* Score breakdown */}
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {detailCards.map(({ key, label, icon: Icon, color }) => (
                <motion.div key={key} variants={item} className="glass rounded-xl p-5 text-center">
                  <div className="mb-3 flex justify-center">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-xl"
                      style={{ backgroundColor: `${color}15` }}
                    >
                      <Icon className="h-5 w-5" style={{ color }} />
                    </div>
                  </div>
                  <p className="text-3xl font-bold text-[#F1F5F9]" style={{ color }}>
                    {report.details[key]}
                  </p>
                  <p className="mt-1 text-xs text-[#94A3B8]">{label}</p>
                </motion.div>
              ))}
            </div>

            {/* Compatibility chart */}
            <motion.div variants={item} className="glass rounded-2xl p-6">
              <h5 className="mb-4 text-sm font-semibold text-[#F1F5F9]">Répartition des scores</h5>
              <CompatibilityBar
                data={detailCards.map(({ key, label }) => ({
                  name: label,
                  score: report.details[key],
                }))}
              />
            </motion.div>

            {/* Action buttons */}
            <motion.div variants={item} className="flex items-center justify-center gap-4">
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
              >
                <Download className="h-4 w-4" />
                Exporter PDF
              </button>
              <button
                onClick={reset}
                className="flex items-center gap-2 rounded-xl border border-[rgba(0,229,255,0.2)] px-6 py-3 text-sm font-medium text-[#94A3B8] transition-all hover:bg-[rgba(0,229,255,0.06)] hover:text-[#F1F5F9]"
              >
                <RotateCcw className="h-4 w-4" />
                Nouveau processus
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
