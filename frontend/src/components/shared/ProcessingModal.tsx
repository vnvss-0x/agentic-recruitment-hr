import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'

interface LogEntry {
  level: string
  message: string
  agent: string
}

interface ProcessingModalProps {
  isOpen: boolean
  title: string
  logs: LogEntry[]
  onClose?: () => void
}

const logColors: Record<string, string> = {
  info: 'text-cyan',
  success: 'text-[#34D399]',
  warning: 'text-[#FF8A65]',
  error: 'text-[#EF4444]',
}

export function ProcessingModal({ isOpen, title, logs, onClose }: ProcessingModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B0F1A]/60 backdrop-blur-sm p-4"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="glass glow-cyan relative flex max-h-[80vh] w-full max-w-lg flex-col rounded-2xl border"
          >
            <div className="flex items-center justify-between border-b border-[rgba(0,229,255,0.12)] px-6 py-4">
              <h2 className="text-lg font-semibold text-[#F1F5F9]">{title}</h2>
              {onClose && (
                <button
                  onClick={onClose}
                  className="rounded-lg p-1 text-[#94A3B8] transition-colors hover:bg-[rgba(0,229,255,0.1)] hover:text-[#F1F5F9]"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-2">
              {logs.length === 0 && (
                <p className="text-center text-[#94A3B8] italic">Aucun log pour le moment...</p>
              )}
              {logs.map((log, i) => (
                <div key={i} className="font-mono text-sm leading-relaxed">
                  <span className="text-[#94A3B8]">[{log.agent}]</span>{' '}
                  <span className={logColors[log.level] ?? 'text-[#F1F5F9]'}>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
