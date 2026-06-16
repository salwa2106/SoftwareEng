'use client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from 'recharts'
import { HourlyFeatures } from '@/lib/types'

interface TrendChartProps {
  data: HourlyFeatures[]
  metric: keyof HourlyFeatures
  label: string
  color?: string
  normalMin?: number
  normalMax?: number
  unit?: string
}

export default function TrendChart({
  data,
  metric,
  label,
  color = '#0d9488',
  normalMin,
  normalMax,
  unit = '',
}: TrendChartProps) {
  const chartData = data
    .filter(h => h[metric] !== null && h[metric] !== undefined)
    .map(h => ({
      hour: h.hour,
      value: h[metric] as number,
      timestamp: h.timestamp,
    }))

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No {label} data available
      </div>
    )
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
          <p className="font-medium text-gray-700">Hour {payload[0]?.payload?.hour}</p>
          <p style={{ color }}>
            {label}: <span className="font-bold">{payload[0]?.value?.toFixed(1)}{unit}</span>
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="hour"
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          label={{ value: 'Hour', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#94a3b8' }}
        />
        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} width={40} />
        <Tooltip content={<CustomTooltip />} />
        {normalMin !== undefined && (
          <ReferenceLine y={normalMin} stroke="#fbbf24" strokeDasharray="4 4" strokeWidth={1.5} />
        )}
        {normalMax !== undefined && (
          <ReferenceLine y={normalMax} stroke="#fbbf24" strokeDasharray="4 4" strokeWidth={1.5} />
        )}
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          dot={false}
          strokeWidth={2}
          name={label}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
