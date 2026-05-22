import { useEffect, useRef } from 'react'
import { Monitor } from 'lucide-react'
import { useRecruitmentStore } from '../../store/recruitmentStore'
import type { LogEntry } from '../../types'

const levelColor: Record<LogEntry['level'], string> = {
  info: '#00E5FF',
  success: '#34D399',
  warning: '#FF8A65',
  error: '#EF4444',
}

function formatTime(ts: string) {
  const d = new Date(ts)
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

export function TerminalFeed() {
  const logs = useRecruitmentStore((s) => s.logs)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div className="flex h-40 flex-col border-t border-[rgba(0,229,255,0.12)] bg-[#0a0e17]">
      <div className="flex items-center gap-2 border-b border-[rgba(0,229,255,0.08)] px-4 py-1.5">
        <Monitor className="h-3.5 w-3.5 text-[#00E5FF]" />
        <span className="font-mono text-xs tracking-wide text-[#00E5FF]">Terminal ▸ Logs</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-2 font-mono text-xs leading-relaxed">
        {logs.length === 0 ? (
          <div className="flex h-full items-center text-[#64748B]">
            <span>En attente des données du pipeline...</span>
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="whitespace-nowrap">
              <span className="text-[#64748B]">[{formatTime(log.timestamp)}]</span>{' '}
              <span style={{ color: levelColor[log.level] }}>[{log.agent}]</span>{' '}
              <span className="text-[#00E580]">▸</span>{' '}
              <span style={{ color: levelColor[log.level] }}>{log.message}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
