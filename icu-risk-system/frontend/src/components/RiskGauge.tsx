'use client'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'

interface RiskGaugeProps {
  riskLevel: string
  riskValue: number
  trend?: string
  size?: number
}

const riskColors: Record<string, string> = {
  Low: '#22c55e',
  Medium: '#f59e0b',
  High: '#ef4444',
  Unknown: '#94a3b8',
}

const trendIcons: Record<string, string> = {
  improving: '↓',
  worsening: '↑',
  stable: '→',
}

export default function RiskGauge({ riskLevel, riskValue, trend = 'stable', size = 200 }: RiskGaugeProps) {
  const color = riskColors[riskLevel] || riskColors.Unknown
  const data = [{ value: riskValue, fill: color }]

  return (
    <div className="flex flex-col items-center gap-2">
      <div style={{ width: size, height: size / 1.5 }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="90%"
            innerRadius="60%"
            outerRadius="100%"
            startAngle={180}
            endAngle={0}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: '#f1f5f9' }}
              dataKey="value"
              angleAxisId={0}
              cornerRadius={8}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
          <span className="text-3xl font-bold" style={{ color }}>
            {riskLevel}
          </span>
          <span className="text-sm text-gray-500">{Math.round(riskValue)}/100</span>
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 text-sm text-gray-600">
          <span className={
            trend === 'worsening' ? 'text-red-500' :
            trend === 'improving' ? 'text-green-500' : 'text-gray-400'
          }>
            {trendIcons[trend] || '→'}
          </span>
          <span className="capitalize">{trend}</span>
        </div>
      )}
    </div>
  )
}
