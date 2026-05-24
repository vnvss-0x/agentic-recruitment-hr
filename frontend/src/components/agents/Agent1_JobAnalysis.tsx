import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Briefcase, MapPin, Clock, DollarSign, Code, Users, ChevronRight, Sparkles, ArrowRight } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { StepHeader } from '../shared/StepHeader'
import { FileDropzone } from '../shared/FileDropzone'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
}

export function Agent1_JobAnalysis() {
  const { jobOffer, phase, uploadJobOffer, currentStep, goToStep } = useRecruitmentStore()
  const [isProcessing, setIsProcessing] = useState(false)

  const isComplete = jobOffer !== null && currentStep >= 0 && phase === 'complete'

  async function handleUpload() {
    setIsProcessing(true)
    await uploadJobOffer()
    setIsProcessing(false)
  }

  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        step={1}
        title="Agent 1 — Analyse du Poste"
        description="Analyse sémantique et extraction du profil de compétences"
        status={isProcessing ? 'processing' : isComplete ? 'complete' : 'pending'}
      />

      <AnimatePresence mode="wait">
        {!isComplete && !isProcessing && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <FileDropzone
              onDrop={handleUpload}
              label="Déposez le fichier d'offre d'emploi"
              accept=".pdf,.docx,.txt"
            />
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
            <p className="text-lg text-[#F1F5F9]">Analyse sémantique en cours...</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Extraction des compétences et structuration du profil</p>
          </motion.div>
        )}

        {isComplete && jobOffer && (
          <motion.div
            key="result"
            variants={container}
            initial="hidden"
            animate="show"
            className="flex flex-col gap-4"
          >
            {/* Job info header */}
            <motion.div variants={item} className="glass rounded-2xl p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-xl font-bold text-[#F1F5F9]">{jobOffer.title}</h4>
                  <p className="mt-1 text-sm text-[#94A3B8]">{jobOffer.department}</p>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#00E5FF]/10">
                  <Sparkles className="h-5 w-5 text-[#00E5FF]" />
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                {[
                  { icon: MapPin, label: jobOffer.location },
                  { icon: Briefcase, label: jobOffer.contractType },
                  { icon: Clock, label: jobOffer.experience },
                  { icon: DollarSign, label: jobOffer.salary_range },
                ].map(({ icon: Icon, label }) => (
                  <div key={label} className="flex items-center gap-2 rounded-lg bg-[rgba(0,229,255,0.04)] px-3 py-2">
                    <Icon className="h-4 w-4 flex-shrink-0 text-[#00E5FF]" />
                    <span className="text-xs text-[#F1F5F9] truncate">{label}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Description */}
            <motion.div variants={item} className="glass rounded-2xl p-6">
              <h5 className="mb-3 text-sm font-semibold text-[#00E5FF] uppercase tracking-wider">Description</h5>
              <p className="text-sm leading-relaxed text-[#94A3B8]">{jobOffer.description}</p>
            </motion.div>

            {/* Skills */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <motion.div variants={item} className="glass rounded-2xl p-6">
                <div className="mb-4 flex items-center gap-2">
                  <Code className="h-4 w-4 text-[#00E5FF]" />
                  <h5 className="text-sm font-semibold text-[#F1F5F9]">Hard Skills</h5>
                  <span className="ml-auto rounded-full bg-[#00E5FF]/10 px-2 py-0.5 text-xs text-[#00E5FF]">{jobOffer.hardSkills.length}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {jobOffer.hardSkills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-lg border border-[rgba(0,229,255,0.2)] bg-[rgba(0,229,255,0.06)] px-3 py-1.5 text-xs font-medium text-[#00E5FF]"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </motion.div>

              <motion.div variants={item} className="glass rounded-2xl p-6">
                <div className="mb-4 flex items-center gap-2">
                  <Users className="h-4 w-4 text-[#FF8A65]" />
                  <h5 className="text-sm font-semibold text-[#F1F5F9]">Soft Skills</h5>
                  <span className="ml-auto rounded-full bg-[#FF8A65]/10 px-2 py-0.5 text-xs text-[#FF8A65]">{jobOffer.softSkills.length}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {jobOffer.softSkills.map((skill) => (
                    <span
                      key={skill}
                      className="rounded-lg border border-[#FF8A65]/20 bg-[#FF8A65]/6 px-3 py-1.5 text-xs font-medium text-[#FF8A65]"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </motion.div>
            </div>

            {/* Requirements + Responsibilities */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <motion.div variants={item} className="glass rounded-2xl p-6">
                <h5 className="mb-3 text-sm font-semibold text-[#F1F5F9]">Prérequis</h5>
                <ul className="flex flex-col gap-2">
                  {jobOffer.requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#94A3B8]">
                      <ChevronRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#00E5FF]" />
                      {req}
                    </li>
                  ))}
                </ul>
              </motion.div>

              <motion.div variants={item} className="glass rounded-2xl p-6">
                <h5 className="mb-3 text-sm font-semibold text-[#F1F5F9]">Responsabilités</h5>
                <ul className="flex flex-col gap-2">
                  {jobOffer.responsibilities.map((resp, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#94A3B8]">
                      <ChevronRight className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#34D399]" />
                      {resp}
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>

            {/* Continue button */}
            <motion.div variants={item} className="flex justify-end pt-2">
              <button
                onClick={() => goToStep(1)}
                className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
              >
                Continuer vers le screening
                <ArrowRight className="h-4 w-4" />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
