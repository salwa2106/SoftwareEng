'use client'
import { Alert } from '@/lib/types'
import { AlertTriangle, AlertCircle, Clock } from 'lucide-react'

interface AlertPanelProps {
  alerts: Alert[]
}

function formatTimestamp(ts: string) {
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}

export default function AlertPanel({ alerts }: AlertPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <AlertCircle className="w-10 h-10 mx-auto mb-2 text-gray-300" />
        <p>No alerts generated for this patient</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.alert_id}
          className={`rounded-lg border p-4 ${
            alert.severity === 'critical'
              ? 'bg-red-50 border-red-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}
        >
          <div className="flex items-start gap-3">
            <div className={`mt-0.5 ${alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded-full ${
                  alert.severity === 'critical'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {alert.severity}
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Hour {alert.hour} &mdash; {formatTimestamp(alert.timestamp)}
                </span>
                <span className="text-xs text-gray-500">
                  Risk: <span className="font-medium">{alert.risk_before}</span>
                  {' → '}
                  <span className="font-medium text-red-600">{alert.risk_after}</span>
                </span>
              </div>
              <ul className="space-y-0.5">
                {alert.triggers.map((trigger, i) => (
                  <li key={i} className="text-sm text-gray-700">• {trigger}</li>
                ))}
              </ul>
              {Object.keys(alert.details).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(alert.details).map(([key, val]) => {
                    if (val === null || val === undefined) return null
                    const label = key.replace(/_/g, ' ')
                    return (
                      <span key={key} className="text-xs bg-white border border-gray-200 rounded px-2 py-0.5 text-gray-600">
                        {label}: <span className="font-medium">{typeof val === 'number' ? val.toFixed(1) : val}</span>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
