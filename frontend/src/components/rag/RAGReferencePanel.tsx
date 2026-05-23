import { motion, AnimatePresence } from 'framer-motion'
import { Database, BookOpen, TrendingUp, X } from 'lucide-react'
import type { RAGSource } from '../../types'

interface RAGReferencePanelProps {
  sources: RAGSource[]
  candidateName?: string
  onClose?: () => void
}

const typeConfig: Record<RAGSource['type'], { icon: typeof Database; color: string; label: string }> = {
  historical: { icon: Database, color: '#00E5FF', label: 'Historique' },
  reference: { icon: BookOpen, color: '#FF8A65', label: 'Référentiel' },
  benchmark: { icon: TrendingUp, color: '#34D399', label: 'Benchmark' },
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
}

const item = {
  hidden: { opacity: 0, x: 20 },
  show: { opacity: 1, x: 0 },
}

export function RAGReferencePanel({ sources, candidateName, onClose }: RAGReferencePanelProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-[rgba(0,229,255,0.12)] px-5 py-4">
        <div>
          <h2 className="font-sans text-sm font-medium text-[#F1F5F9]">Sources RAG</h2>
          {candidateName && (
            <p className="text-xs text-[#94A3B8] mt-0.5">{candidateName}</p>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[#94A3B8] transition-colors hover:bg-[rgba(0,229,255,0.1)] hover:text-[#F1F5F9]"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {sources.length === 0 ? (
            <div className="flex items-center justify-center p-8 text-xs text-[#64748B]">
              Aucune référence disponible
            </div>
          ) : (
            <motion.div
              variants={container}
              initial="hidden"
              animate="show"
              className="flex flex-col gap-3"
            >
              {sources.map((source) => {
                const cfg = typeConfig[source.type]
                const Icon = cfg.icon
                return (
                  <motion.div
                    key={source.id}
                    variants={item}
                    className="glass rounded-xl p-4 transition-all hover:border-[rgba(0,229,255,0.25)]"
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg"
                        style={{ backgroundColor: `${cfg.color}15` }}
                      >
                        <Icon className="h-4 w-4" style={{ color: cfg.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-[#F1F5F9] truncate">{source.label}</span>
                          <span
                            className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium border"
                            style={{
                              color: cfg.color,
                              borderColor: `${cfg.color}40`,
                              backgroundColor: `${cfg.color}10`,
                            }}
                          >
                            {cfg.label}
                          </span>
                        </div>
                        <p className="text-xs text-[#94A3B8] leading-relaxed">{source.description}</p>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
