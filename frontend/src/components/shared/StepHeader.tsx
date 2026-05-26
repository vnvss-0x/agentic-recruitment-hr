import { Check, Loader } from 'lucide-react'

interface StepHeaderProps {
  step: number
  title: string
  description?: string
  status: 'pending' | 'processing' | 'complete'
}

export function StepHeader({ step, title, description, status }: StepHeaderProps) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex-shrink-0">
        {status === 'complete' ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#34D399]/20">
            <Check className="h-5 w-5 text-[#34D399]" />
          </div>
        ) : status === 'processing' ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan/10 shadow-[0_0_15px_rgba(0,229,255,0.3)] animate-pulse-glow">
            <Loader className="h-5 w-5 text-cyan animate-spin" />
          </div>
        ) : (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[rgba(0,229,255,0.06)]">
            <span className="text-lg font-semibold text-[#94A3B8]">{step}</span>
          </div>
        )}
      </div>
      <div className="flex flex-col">
        <h3
          className={`text-lg font-semibold ${
            status === 'pending' ? 'text-[#94A3B8]' : 'text-[#F1F5F9]'
          }`}
        >
          {title}
        </h3>
        {description && (
          <p className="mt-1 text-sm text-[#94A3B8]">{description}</p>
        )}
      </div>
    </div>
  )
}
