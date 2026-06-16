import Link from 'next/link'
import { PatientSummary } from '@/lib/types'
import { User, Clock, Activity } from 'lucide-react'
import clsx from 'clsx'

interface PatientCardProps {
  patient: PatientSummary
}

const riskClass: Record<string, string> = {
  Low: 'risk-low',
  Medium: 'risk-medium',
  High: 'risk-high',
  Unknown: 'bg-gray-100 text-gray-600 border-gray-200',
}

export default function PatientCard({ patient }: PatientCardProps) {
  const los = patient.los_hours
    ? `${Math.floor(patient.los_hours / 24)}d ${Math.round(patient.los_hours % 24)}h`
    : 'N/A'

  return (
    <Link href={`/patient/${patient.subject_id}`} className="block">
      <div className="card hover:shadow-md transition-all hover:border-teal-200 cursor-pointer group">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-teal-50 rounded-full flex items-center justify-center group-hover:bg-teal-100 transition-colors">
              <User className="w-5 h-5 text-teal-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">Patient #{patient.subject_id}</p>
              <p className="text-sm text-gray-500">
                {patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : 'Unknown'}{' '}
                {patient.age ? `• ${patient.age}y` : ''}
              </p>
            </div>
          </div>
          <span className={clsx(
            'text-xs font-bold px-2.5 py-1 rounded-full border uppercase tracking-wide',
            riskClass[patient.current_risk] ?? riskClass.Unknown
          )}>
            {patient.current_risk}
          </span>
        </div>

        {patient.diagnosis && (
          <p className="text-sm text-gray-700 mb-3 line-clamp-1 font-medium">
            {patient.diagnosis}
          </p>
        )}

        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Activity className="w-3.5 h-3.5" />
            {patient.icu_stays} ICU {patient.icu_stays === 1 ? 'stay' : 'stays'}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            LOS: {los}
          </span>
        </div>
      </div>
    </Link>
  )
}
