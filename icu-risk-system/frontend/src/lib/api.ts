const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchAPI<import('./types').HealthResponse>('/api/health'),

  getPatients: (limit = 50, offset = 0, search = '') =>
    fetchAPI<import('./types').PatientsResponse>(
      `/api/patients?limit=${limit}&offset=${offset}${search ? `&search=${encodeURIComponent(search)}` : ''}`
    ),

  getPatient: (id: number) =>
    fetchAPI<import('./types').PatientDetail>(`/api/patients/${id}`),

  getTimeline: (id: number, maxHours = 72) =>
    fetchAPI<import('./types').TimelineResponse>(`/api/patients/${id}/timeline?max_hours=${maxHours}`),

  getRisk: (id: number) =>
    fetchAPI<import('./types').RiskScore>(`/api/patients/${id}/risk`),

  getAlerts: (id: number) =>
    fetchAPI<import('./types').AlertsResponse>(`/api/patients/${id}/alerts`),
};
