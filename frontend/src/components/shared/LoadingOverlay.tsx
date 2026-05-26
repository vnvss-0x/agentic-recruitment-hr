import { AnimatePresence, motion } from 'framer-motion'

interface LoadingOverlayProps {
  isVisible: boolean
  message?: string
}

export function LoadingOverlay({ isVisible, message }: LoadingOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#0B0F1A]/80 backdrop-blur-sm"
        >
          <div className="mb-6 h-12 w-12 rounded-full border-4 border-[rgba(0,229,255,0.12)] border-t-cyan animate-spin" />
          {message && (
            <p className="text-lg text-[#F1F5F9]">{message}</p>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
