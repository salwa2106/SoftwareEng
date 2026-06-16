'use client'
import { HourlyFeatures } from '@/lib/types'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, BarChart, Bar } from 'recharts'

interface TimelineProps {
  data: HourlyFeatures[]
}

const riskColors: Record<string, string> = {
  Low: '#22c55e',
  Medium: '#f59e0b',
  High: '#ef4444',
}

export default function Timeline({ data }: TimelineProps) {
  const chartData = data.map(h => ({
    hour: h.hour,
    risk_value: h.risk_value ?? 0,
    risk_score: h.risk_score ?? 'Low',
    abnormal_count: h.abnormal_count,
  }))

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0]?.payload
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
          <p className="font-medium text-gray-700 mb-1">Hour {d?.hour}</p>
          <p>
            Risk:{' '}
            <span className="font-bold" style={{ color: riskColors[d?.risk_score] ?? '#94a3b8' }}>
              {d?.risk_score}
            </span>
          </p>
          <p className="text-gray-500">Abnormal: {d?.abnormal_count}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-1">
      <p className="text-xs text-gray-500 mb-2">Risk score over ICU stay (hourly)</p>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={chartData} margin={{ top: 0, right: 5, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="hour" tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="risk_value" radius={[2, 2, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={riskColors[entry.risk_score] ?? '#94a3b8'}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="flex gap-4 text-xs text-gray-500 mt-1">
        {Object.entries(riskColors).map(([level, color]) => (
          <span key={level} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm inline-block" style={{ backgroundColor: color }} />
            {level}
          </span>
        ))}
      </div>
    </div>
  )
}
