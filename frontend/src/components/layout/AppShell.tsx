import type { ReactNode } from 'react'
import { WorkflowStepper } from './WorkflowStepper'
import { TerminalFeed } from './TerminalFeed'
import { RAGReferencePanel } from '../rag/RAGReferencePanel'
import { useRecruitmentStore } from '../../store/recruitmentStore'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const candidates = useRecruitmentStore((s) => s.candidates)
  const shortlist = useRecruitmentStore((s) => s.shortlist)
  const currentStep = useRecruitmentStore((s) => s.currentStep)

  // Pick RAG sources based on context
  const contextSources = currentStep >= 1 && shortlist.length > 0
    ? shortlist[0].ragSources
    : currentStep >= 1 && candidates.length > 0
    ? candidates[0].ragSources
    : []

  const contextName = currentStep >= 1 && shortlist.length > 0
    ? shortlist[0].name
    : currentStep >= 1 && candidates.length > 0
    ? candidates[0].name
    : undefined

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-[#0B0F1A] bg-grid">
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 flex-shrink-0 border-r border-[rgba(0,229,255,0.12)] bg-[#131827] shadow-[2px_0_20px_rgba(0,229,255,0.05)] overflow-y-auto">
          <div className="border-b border-[rgba(0,229,255,0.12)] px-6 py-5">
            <h1 className="font-sans text-lg font-semibold tracking-tight text-[#F1F5F9] drop-shadow-[0_0_8px_rgba(0,229,255,0.3)]">
              Recruitment<span className="text-[#00E5FF]">AI</span>
            </h1>
            <p className="mt-0.5 text-xs text-[#94A3B8]">Pipeline Agentique</p>
          </div>
          <WorkflowStepper />
        </aside>

        <main className="flex flex-1 flex-col overflow-hidden">
          <div className="flex flex-1 overflow-hidden">
            <div className="flex-1 overflow-y-auto p-6">
              {children}
            </div>
            <aside className="w-80 flex-shrink-0 border-l border-[rgba(0,229,255,0.12)] bg-[#131827] overflow-y-auto">
              <RAGReferencePanel
                sources={contextSources}
                candidateName={contextName}
              />
            </aside>
          </div>
        </main>
      </div>

      <TerminalFeed />
    </div>
  )
}
