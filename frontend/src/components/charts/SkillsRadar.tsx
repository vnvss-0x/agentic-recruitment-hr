import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'
import type { Skill } from '../../types'

interface SkillsRadarProps {
  skills: Skill[]
  size?: number
}

export function SkillsRadar({ skills, size = 300 }: SkillsRadarProps) {
  const data = skills.map((s) => ({
    name: s.name,
    value: s.level,
    fullMark: 100,
  }))

  return (
    <div style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="rgba(0, 229, 255, 0.1)" />
          <PolarAngleAxis
            dataKey="name"
            tick={{ fill: '#94A3B8', fontSize: 11, fontFamily: 'Instrument Sans' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#64748B', fontSize: 10 }}
            axisLine={false}
          />
          <Radar
            name="Compétences"
            dataKey="value"
            stroke="#00E5FF"
            fill="#00E5FF"
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
