import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface CompatibilityBarProps {
  data: { name: string; score: number }[]
}

function getBarColor(score: number): string {
  if (score >= 90) return '#00E5FF'
  if (score >= 80) return '#34D399'
  if (score >= 70) return '#FF8A65'
  return '#EF4444'
}

export function CompatibilityBar({ data }: CompatibilityBarProps) {
  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 229, 255, 0.06)" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: '#64748B', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(0,229,255,0.12)' }}
          />
          <YAxis
            dataKey="name"
            type="category"
            tick={{ fill: '#F1F5F9', fontSize: 12, fontFamily: 'Instrument Sans' }}
            axisLine={false}
            tickLine={false}
            width={75}
          />
          <Tooltip
            contentStyle={{
              background: '#131827',
              border: '1px solid rgba(0,229,255,0.2)',
              borderRadius: '8px',
              color: '#F1F5F9',
              fontFamily: 'Instrument Sans',
              fontSize: '13px',
            }}
            formatter={(value: number) => [`${value}%`, 'Compatibilité']}
            cursor={{ fill: 'rgba(0,229,255,0.05)' }}
          />
          <Bar dataKey="score" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
