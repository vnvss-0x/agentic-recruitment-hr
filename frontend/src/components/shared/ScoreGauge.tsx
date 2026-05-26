interface ScoreGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

const sizeMap = {
  sm: { outer: 80, stroke: 6, fontSize: 'text-lg', labelSize: 'text-xs' },
  md: { outer: 120, stroke: 8, fontSize: 'text-2xl', labelSize: 'text-sm' },
  lg: { outer: 160, stroke: 10, fontSize: 'text-3xl', labelSize: 'text-base' },
}

function getColor(score: number): string {
  if (score < 60) return '#EF4444'
  if (score < 80) return '#FF8A65'
  return '#00E5FF'
}

export function ScoreGauge({ score, size = 'md', label }: ScoreGaugeProps) {
  const cfg = sizeMap[size]
  const radius = (cfg.outer - cfg.stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.min(Math.max(score, 0), 100) / 100) * circumference
  const color = getColor(score)
  const center = cfg.outer / 2

  return (
    <div className="flex flex-col items-center gap-2">
      <svg
        width={cfg.outer}
        height={cfg.outer}
        viewBox={`0 0 ${cfg.outer} ${cfg.outer}`}
        className="transform -rotate-90"
      >
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgba(0, 229, 255, 0.08)"
          strokeWidth={cfg.stroke}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={cfg.stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div
        className="absolute flex flex-col items-center justify-center"
        style={{ width: cfg.outer, height: cfg.outer }}
      >
        <span className={`${cfg.fontSize} font-bold text-[#F1F5F9]`} style={{ color }}>
          {Math.round(score)}%
        </span>
      </div>
      {label && (
        <span className={`${cfg.labelSize} text-[#94A3B8]`}>{label}</span>
      )}
    </div>
  )
}
