'use client'
import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { PatientDetail, RiskScore, AlertsResponse, TimelineResponse } from '@/lib/types'
import RiskGauge from '@/components/RiskGauge'
import AlertPanel from '@/components/AlertPanel'
import TrendChart from '@/components/TrendChart'
import Timeline from '@/components/Timeline'
import LoadingSpinner from '@/components/LoadingSpinner'
import { ArrowLeft, User, Calendar, Clock, MapPin, Activity, AlertTriangle, TrendingUp } from 'lucide-react'
import clsx from 'clsx'

type TabKey = 'overview' | 'vitals' | 'labs' | 'alerts'

function formatDate(s: string | null) {
  if (!s) return 'N/A'
  try { return new Date(s).toLocaleString() } catch { return s }
}

function StatBox({ label, value, unit = '' }: { label: string; value: string | number | null; unit?: string }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">
        {value !== null && value !== undefined ? `${value}` : 'N/A'}
        {value !== null && unit && <span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>}
      </p>
    </div>
  )
}

export default function PatientPage() {
  const { id } = useParams()
  const router = useRouter()
  const patientId = Number(id)
  const [activeTab, setActiveTab] = useState<TabKey>('overview')

  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [risk, setRisk] = useState<RiskScore | null>(null)
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null)
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!patientId) return
    setLoading(true)
    setError(null)

    Promise.all([
      api.getPatient(patientId),
      api.getRisk(patientId).catch(() => null),
      api.getAlerts(patientId).catch(() => null),
      api.getTimeline(patientId, 168).catch(() => null),
    ]).then(([p, r, a, t]) => {
      setPatient(p)
      setRisk(r)
      setAlertsData(a)
      setTimeline(t)
    }).catch(err => {
      setError(err instanceof Error ? err.message : 'Failed to load patient data')
    }).finally(() => setLoading(false))
  }, [patientId])

  if (loading) return <LoadingSpinner message="Loading patient data..." />
  if (error) return (
    <div className="max-w-7xl mx-auto px-4 py-12 text-center">
      <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
      <p className="text-gray-700 font-medium">{error}</p>
      <button onClick={() => router.back()} className="btn-secondary mt-4 inline-flex items-center gap-2">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>
    </div>
  )
  if (!patient) return null

  const hourlyData = timeline?.hourly_data ?? []
  const tabs: { key: TabKey; label: string; icon: React.ElementType }[] = [
    { key: 'overview', label: 'Overview', icon: User },
    { key: 'vitals', label: 'Vital Signs', icon: Activity },
    { key: 'labs', label: 'Lab Values', icon: TrendingUp },
    { key: 'alerts', label: `Alerts (${alertsData?.total_alerts ?? 0})`, icon: AlertTriangle },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-800 mb-6 text-sm font-medium transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Patient Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-14 h-14 bg-teal-100 rounded-2xl flex items-center justify-center">
                <User className="w-7 h-7 text-teal-700" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Patient #{patient.subject_id}</h1>
                <p className="text-gray-500">
                  {patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : 'Unknown'}
                  {patient.age ? ` • ${patient.age} years old` : ''}
                  {patient.icu_unit ? ` • ${patient.icu_unit}` : ''}
                </p>
              </div>
            </div>

            {patient.diagnosis && (
              <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-2 mb-4 inline-block">
                <p className="text-blue-800 font-medium text-sm">{patient.diagnosis}</p>
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatBox label="Admitted" value={formatDate(patient.admittime)} />
              <StatBox label="Discharged" value={formatDate(patient.dischtime)} />
              <StatBox label="ICU In" value={formatDate(patient.icu_intime)} />
              <StatBox
                label="LOS"
                value={patient.los_hours ? `${Math.floor(patient.los_hours / 24)}d ${Math.round(patient.los_hours % 24)}h` : null}
              />
            </div>
          </div>

          {/* Risk Gauge */}
          {risk && (
            <div className="flex flex-col items-center justify-center min-w-[200px]">
              <RiskGauge
                riskLevel={risk.risk_level}
                riskValue={risk.risk_value}
                trend={risk.trend}
                size={200}
              />
              {risk.triggers.length > 0 && (
                <div className="mt-2 text-sm text-center max-w-48">
                  <p className="text-xs text-gray-500 mb-1">Active Triggers</p>
                  {risk.triggers.slice(0, 2).map((t, i) => (
                    <p key={i} className="text-xs text-red-600 line-clamp-1">{t}</p>
                  ))}
                  {risk.triggers.length > 2 && (
                    <p className="text-xs text-gray-400">+{risk.triggers.length - 2} more</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Timeline Bar */}
      {hourlyData.length > 0 && (
        <div className="card mb-6">
          <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-600" />
            Risk Timeline ({hourlyData.length} hours)
          </h2>
          <Timeline data={hourlyData} />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={clsx(
              'flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-sm font-medium transition-all',
              activeTab === key
                ? 'bg-white text-teal-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Patient Details</h3>
            <div className="space-y-3">
              {[
                { label: 'Patient ID', value: patient.subject_id },
                { label: 'Gender', value: patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : 'Unknown' },
                { label: 'Age', value: patient.age ? `${patient.age} years` : null },
                { label: 'Ethnicity', value: patient.ethnicity },
                { label: 'Diagnosis', value: patient.diagnosis },
                { label: 'ICU Unit', value: patient.icu_unit },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-medium text-gray-900 text-right max-w-48">{value || 'N/A'}</span>
                </div>
              ))}
            </div>
          </div>

          {risk && (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Current Risk Assessment</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Risk Level</span>
                  <span className={clsx('font-bold', {
                    'text-green-600': risk.risk_level === 'Low',
                    'text-yellow-600': risk.risk_level === 'Medium',
                    'text-red-600': risk.risk_level === 'High',
                  })}>{risk.risk_level}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Risk Score</span>
                  <span className="font-medium">{risk.risk_value}/100</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Trend</span>
                  <span className={clsx('font-medium capitalize', {
                    'text-green-600': risk.trend === 'improving',
                    'text-red-600': risk.trend === 'worsening',
                    'text-gray-600': risk.trend === 'stable',
                  })}>{risk.trend}</span>
                </div>
                {Object.entries(risk.abnormal_values).map(([k, v]) => (
                  <div key={k} className="flex justify-between text-sm">
                    <span className="text-gray-500 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className="font-medium">{typeof v === 'number' ? v.toFixed(2) : v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'vitals' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { metric: 'heart_rate' as const, label: 'Heart Rate', color: '#ef4444', normalMin: 60, normalMax: 100, unit: ' bpm' },
            { metric: 'resp_rate' as const, label: 'Respiratory Rate', color: '#f97316', normalMin: 12, normalMax: 20, unit: ' br/min' },
            { metric: 'spo2' as const, label: 'SpO2', color: '#3b82f6', normalMin: 95, unit: '%' },
            { metric: 'temperature' as const, label: 'Temperature', color: '#8b5cf6', normalMin: 36, normalMax: 38, unit: '°C' },
            { metric: 'sbp' as const, label: 'Systolic BP', color: '#0d9488', normalMin: 90, normalMax: 140, unit: ' mmHg' },
            { metric: 'dbp' as const, label: 'Diastolic BP', color: '#06b6d4', normalMin: 60, normalMax: 90, unit: ' mmHg' },
          ].map(props => (
            <div key={props.metric} className="card">
              <h3 className="font-semibold text-gray-900 text-sm mb-3">{props.label}</h3>
              <TrendChart data={hourlyData} {...props} />
            </div>
          ))}
        </div>
      )}

      {activeTab === 'labs' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { metric: 'wbc' as const, label: 'WBC', color: '#10b981', normalMin: 4, normalMax: 11, unit: ' K/uL' },
            { metric: 'creatinine' as const, label: 'Creatinine', color: '#f59e0b', normalMax: 1.2, unit: ' mg/dL' },
            { metric: 'lactate' as const, label: 'Lactate', color: '#ef4444', normalMax: 2, unit: ' mmol/L' },
            { metric: 'hemoglobin' as const, label: 'Hemoglobin', color: '#8b5cf6', normalMin: 7, unit: ' g/dL' },
            { metric: 'platelets' as const, label: 'Platelets', color: '#ec4899', normalMin: 150, unit: ' K/uL' },
          ].map(props => (
            <div key={props.metric} className="card">
              <h3 className="font-semibold text-gray-900 text-sm mb-3">{props.label}</h3>
              <TrendChart data={hourlyData} {...props} />
            </div>
          ))}
        </div>
      )}

      {activeTab === 'alerts' && alertsData && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Clinical Alerts ({alertsData.total_alerts})
          </h3>
          <AlertPanel alerts={alertsData.alerts} />
        </div>
      )}
    </div>
  )
}
