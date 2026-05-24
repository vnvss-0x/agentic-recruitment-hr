import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileSearch, AlertTriangle, ChevronDown, ChevronUp, GraduationCap, Globe, Award, Play, FileUp } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import { StepHeader } from '../shared/StepHeader'
import { FileDropzone } from '../shared/FileDropzone'
import { ScoreGauge } from '../shared/ScoreGauge'
import { candidates as allCandidates } from '../../data/candidates'
import type { Candidate } from '../../types'

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
}

const item = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
}

interface CandidateRowProps {
  candidate: Candidate
  index: number
  onSelect: (c: Candidate) => void
  isSelected: boolean
  showScore: boolean
}

function CandidateRow({ candidate, index, onSelect, isSelected, showScore }: CandidateRowProps) {
  const missingSkills = candidate.skills.filter((s) => s.isMissing)

  return (
    <motion.div
      variants={item}
      className={`glass rounded-xl transition-all cursor-pointer ${
        isSelected ? 'border-[#00E5FF]/40 glow-cyan-sm' : 'hover:border-[rgba(0,229,255,0.25)]'
      }`}
      onClick={() => onSelect(candidate)}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Rank */}
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(0,229,255,0.1)] text-xs font-bold text-[#00E5FF]">
          {index + 1}
        </span>

        {/* Avatar */}
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#00E5FF]/20 to-[#00E5FF]/5 text-sm font-bold text-[#00E5FF]">
          {candidate.avatar}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-[#F1F5F9] truncate">{candidate.name}</h4>
            {candidate.status === 'validated' && (
              <span className="rounded-full bg-[#34D399]/15 px-2 py-0.5 text-[10px] font-medium text-[#34D399] border border-[#34D399]/30">Validé</span>
            )}
            {candidate.status === 'rejected' && (
              <span className="rounded-full bg-[#EF4444]/15 px-2 py-0.5 text-[10px] font-medium text-[#EF4444] border border-[#EF4444]/30">Retiré</span>
            )}
          </div>
          <p className="text-xs text-[#94A3B8] truncate">{candidate.title} · {candidate.yearsExperience} ans</p>
        </div>

        {/* Score gauge - only when screening is done */}
        {showScore && (
          <div className="relative flex-shrink-0">
            <ScoreGauge score={candidate.compatibilityScore} size="sm" />
          </div>
        )}

        {/* Missing skills indicators */}
        {showScore && missingSkills.length > 0 && (
          <div className="flex items-center gap-1 flex-shrink-0">
            <AlertTriangle className="h-3.5 w-3.5 text-[#FF8A65]" />
            <span className="text-[10px] text-[#FF8A65]">{missingSkills.length} manquantes</span>
          </div>
        )}

        {/* Expand */}
        <div className="flex-shrink-0 text-[#64748B]">
          {isSelected ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </div>

      {/* Expanded details */}
      <AnimatePresence>
        {isSelected && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="border-t border-[rgba(0,229,255,0.08)] px-4 pb-4 pt-3">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {/* Skills */}
                <div>
                  <h6 className="mb-2 text-xs font-semibold text-[#94A3B8] uppercase tracking-wider">Compétences</h6>
                  <div className="flex flex-col gap-1.5">
                    {candidate.skills.map((skill) => (
                      <div key={skill.name} className="flex items-center gap-2">
                        <span className={`text-xs flex-1 truncate ${skill.isMissing ? 'text-[#FF8A65]' : 'text-[#F1F5F9]'}`}>
                          {skill.name}
                        </span>
                        <div className="h-1.5 w-20 rounded-full bg-[rgba(0,229,255,0.08)]">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${skill.level}%`,
                              backgroundColor: skill.isMissing ? '#FF8A65' : skill.level >= 80 ? '#00E5FF' : '#34D399',
                            }}
                          />
                        </div>
                        <span className="w-8 text-right text-[10px] text-[#64748B]">{skill.level}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Education & Certs */}
                <div>
                  <h6 className="mb-2 text-xs font-semibold text-[#94A3B8] uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="h-3 w-3" /> Formation
                  </h6>
                  <div className="flex flex-col gap-1.5">
                    {candidate.education.map((edu, i) => (
                      <p key={i} className="text-xs text-[#F1F5F9]">
                        {edu.degree} <span className="text-[#64748B]">— {edu.school} ({edu.year})</span>
                      </p>
                    ))}
                  </div>

                  {candidate.certifications.length > 0 && (
                    <>
                      <h6 className="mt-3 mb-2 text-xs font-semibold text-[#94A3B8] uppercase tracking-wider flex items-center gap-1.5">
                        <Award className="h-3 w-3" /> Certifications
                      </h6>
                      <div className="flex flex-wrap gap-1.5">
                        {candidate.certifications.map((cert) => (
                          <span key={cert} className="rounded bg-[rgba(0,229,255,0.06)] px-2 py-0.5 text-[10px] text-[#94A3B8]">{cert}</span>
                        ))}
                      </div>
                    </>
                  )}
                </div>

                {/* Languages */}
                <div>
                  <h6 className="mb-2 text-xs font-semibold text-[#94A3B8] uppercase tracking-wider flex items-center gap-1.5">
                    <Globe className="h-3 w-3" /> Langues
                  </h6>
                  <div className="flex flex-col gap-1">
                    {candidate.languages.map((lang) => (
                      <span key={lang} className="text-xs text-[#F1F5F9]">{lang}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

type LocalPhase = 'upload' | 'uploaded' | 'screening' | 'screened'

export function Agent2_CVScreening() {
  const { candidates, phase, currentStep, uploadCVs } = useRecruitmentStore()
  const [localPhase, setLocalPhase] = useState<LocalPhase>('upload')
  const [uploadedCVs, setUploadedCVs] = useState<Candidate[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)

  // If store already transitioned to HITL or beyond, we're past screening
  const isScreened = candidates.length > 0 && currentStep >= 1

  function handleUpload() {
    // Simulate loading the CVs (show them as uploaded, no scores yet)
    setUploadedCVs(allCandidates.map((c) => ({ ...c })))
    setLocalPhase('uploaded')
  }

  async function handleRunScreening() {
    setLocalPhase('screening')
    await uploadCVs()
    setLocalPhase('screened')
  }

  function handleSelect(c: Candidate) {
    setSelectedId(selectedId === c.id ? null : c.id)
  }

  // Determine what to show
  const showUpload = !isScreened && localPhase === 'upload'
  const showUploaded = !isScreened && localPhase === 'uploaded'
  const showScreening = !isScreened && localPhase === 'screening'
  const showResults = isScreened

  return (
    <div className="flex flex-col gap-6">
      <StepHeader
        step={2}
        title="Agent 2 — Screening des CVs"
        description="Upload des CVs, analyse RAG et classement des candidats"
        status={showScreening ? 'processing' : showResults ? 'complete' : 'pending'}
      />

      <AnimatePresence mode="wait">
        {/* Phase 1: Upload dropzone */}
        {showUpload && (
          <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
            <FileDropzone
              onDrop={handleUpload}
              label="Déposez les CVs des candidats"
              accept=".pdf,.docx"
              multiple={true}
            />
            <p className="mt-3 text-center text-xs text-[#64748B]">Les CVs seront analysés et comparés avec le profil du poste</p>
          </motion.div>
        )}

        {/* Phase 2: Uploaded CVs list (no scores yet) */}
        {showUploaded && (
          <motion.div key="uploaded" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="flex flex-col gap-4">
            {/* Upload summary */}
            <div className="flex items-center gap-3 rounded-xl border border-[#34D399]/30 bg-[#34D399]/5 px-5 py-3">
              <FileUp className="h-5 w-5 text-[#34D399]" />
              <p className="text-sm text-[#34D399]">
                <span className="font-semibold">{uploadedCVs.length} CVs</span> chargés avec succès — prêts pour le screening
              </p>
            </div>

            {/* CV list without scores */}
            <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-3">
              <p className="text-sm text-[#94A3B8]">
                <span className="font-semibold text-[#F1F5F9]">{uploadedCVs.length}</span> candidats détectés
              </p>
              {uploadedCVs.map((candidate, index) => (
                <CandidateRow
                  key={candidate.id}
                  candidate={candidate}
                  index={index}
                  onSelect={handleSelect}
                  isSelected={selectedId === candidate.id}
                  showScore={false}
                />
              ))}
            </motion.div>

            {/* Run screening button */}
            <div className="flex justify-center pt-2">
              <button
                onClick={handleRunScreening}
                className="flex items-center gap-2 rounded-xl bg-[#00E5FF] px-6 py-3 text-sm font-semibold text-[#0B0F1A] shadow-[0_0_20px_rgba(0,229,255,0.3)] transition-all hover:shadow-[0_0_30px_rgba(0,229,255,0.5)] hover:scale-105 active:scale-95"
              >
                <Play className="h-4 w-4" />
                Lancer le screening IA
              </button>
            </div>
          </motion.div>
        )}

        {/* Phase 3: Screening in progress */}
        {showScreening && (
          <motion.div key="screening" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center py-16">
            <div className="mb-6 h-16 w-16 rounded-full border-4 border-[rgba(0,229,255,0.12)] border-t-[#00E5FF] animate-spin" />
            <p className="text-lg text-[#F1F5F9]">Screening en cours...</p>
            <p className="mt-1 text-sm text-[#94A3B8]">Comparaison RAG et calcul des scores de compatibilité</p>
          </motion.div>
        )}

        {/* Phase 4: Screening results (with scores) */}
        {showResults && (
          <motion.div key="results" variants={container} initial="hidden" animate="show" className="flex flex-col gap-3">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm text-[#94A3B8]">
                <span className="font-semibold text-[#F1F5F9]">{candidates.length}</span> candidats analysés — classés par compatibilité
              </p>
              <div className="flex items-center gap-1">
                <FileSearch className="h-4 w-4 text-[#00E5FF]" />
                <span className="text-xs text-[#00E5FF]">RAG scoring</span>
              </div>
            </div>
            {candidates.map((candidate, index) => (
              <CandidateRow
                key={candidate.id}
                candidate={candidate}
                index={index}
                onSelect={handleSelect}
                isSelected={selectedId === candidate.id}
                showScore={true}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
