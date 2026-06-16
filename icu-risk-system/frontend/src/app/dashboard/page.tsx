'use client'
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import { PatientSummary } from '@/lib/types'
import PatientCard from '@/components/PatientCard'
import PatientSearch from '@/components/PatientSearch'
import LoadingSpinner from '@/components/LoadingSpinner'
import { Users, AlertTriangle, Activity } from 'lucide-react'

export default function DashboardPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [systemOk, setSystemOk] = useState<boolean | null>(null)

  const loadPatients = useCallback(async (searchQuery: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getPatients(50, 0, searchQuery)
      setPatients(data.patients)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load patients')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    api.health().then(h => setSystemOk(h.data_loaded)).catch(() => setSystemOk(false))
    loadPatients('')
  }, [loadPatients])

  const handleSearch = useCallback((query: string) => {
    setSearch(query)
    loadPatients(query)
  }, [loadPatients])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-teal-600" />
            Patient Dashboard
          </h1>
          <p className="text-gray-500 mt-1">
            {total > 0 ? `${total} patients in database` : 'Loading patient data...'}
          </p>
        </div>

        {systemOk !== null && (
          <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg border ${
            systemOk
              ? 'bg-green-50 text-green-700 border-green-200'
              : 'bg-red-50 text-red-700 border-red-200'
          }`}>
            <div className={`w-2 h-2 rounded-full ${systemOk ? 'bg-green-500' : 'bg-red-500'}`} />
            {systemOk ? 'System Online' : 'Data Unavailable'}
          </div>
        )}
      </div>

      {/* Search */}
      <div className="mb-6 max-w-md">
        <PatientSearch onSearch={handleSearch} />
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSpinner message="Loading patients..." />
      ) : error ? (
        <div className="card text-center py-12">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-gray-700 font-medium">{error}</p>
          <p className="text-gray-500 text-sm mt-2">
            Make sure the backend is running at http://localhost:8000
          </p>
          <button
            onClick={() => loadPatients(search)}
            className="btn-primary mt-4 inline-flex items-center gap-2"
          >
            <Activity className="w-4 h-4" />
            Retry
          </button>
        </div>
      ) : patients.length === 0 ? (
        <div className="card text-center py-12">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No patients found{search ? ` matching "${search}"` : ''}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {patients.map(patient => (
            <PatientCard key={patient.subject_id} patient={patient} />
          ))}
        </div>
      )}
    </div>
  )
}
