import { motion } from 'framer-motion'

interface DecisionGaugeProps {
  score: number
  decision: 'approved' | 'rejected'
  label?: string
}

function getColor(score: number): string {
  if (score >= 85) return '#00E5FF'
  if (score >= 70) return '#34D399'
  if (score >= 50) return '#FF8A65'
  return '#EF4444'
}

export function DecisionGauge({ score, decision, label }: DecisionGaugeProps) {
  const color = getColor(score)
  const radius = 80
  const strokeWidth = 12
  const cx = 100
  const cy = 100
  const halfCircumference = Math.PI * radius
  const offset = halfCircumference - (Math.min(Math.max(score, 0), 100) / 100) * halfCircumference

  return (
    <div className="flex flex-col items-center">
      <svg width={200} height={120} viewBox="0 0 200 120">
        {/* Background arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="rgba(0, 229, 255, 0.08)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Score arc */}
        <motion.path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={halfCircumference}
          initial={{ strokeDashoffset: halfCircumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut', delay: 0.3 }}
        />
        {/* Score text */}
        <text x={cx} y={cy - 10} textAnchor="middle" fill={color} fontSize="28" fontWeight="700" fontFamily="Instrument Sans">
          {score.toFixed(1)}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" fill="#94A3B8" fontSize="12" fontFamily="Instrument Sans">
          /100
        </text>
      </svg>
      <div className="mt-2 flex flex-col items-center gap-1">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${
            decision === 'approved'
              ? 'bg-[#34D399]/15 text-[#34D399] border border-[#34D399]/30'
              : 'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30'
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${decision === 'approved' ? 'bg-[#34D399]' : 'bg-[#EF4444]'}`} />
          {decision === 'approved' ? 'Approuvé' : 'Rejeté'}
        </span>
        {label && <span className="text-sm text-[#94A3B8] mt-1">{label}</span>}
      </div>
    </div>
  )
}
