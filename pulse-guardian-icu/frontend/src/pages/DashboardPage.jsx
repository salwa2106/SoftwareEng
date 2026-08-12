import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../utils/api';
import { Users, AlertTriangle, Activity, TrendingUp, Bell } from 'lucide-react';

const RISK_COLORS = { High: '#ef4444', Medium: '#f59e0b', Low: '#22c55e' };

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get('/patients/stats'),
      api.get('/alerts/?severity=critical&acknowledged=false&limit=5')
    ]).then(([s, a]) => {
      setStats(s.data);
      setAlerts(a.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-screen"><div className="spinner"></div> Loading dashboard...</div>;

  const riskData = stats ? Object.entries(stats.risk_distribution).map(([k, v]) => ({ name: k, value: v })) : [];

  return (
    <div className="page-container">
      <div className="demo-banner">
        <span>⚠</span>
        <span>ACADEMIC / DEMO SYSTEM — All data is simulated or anonymized. Not for real clinical use.</span>
      </div>

      <div className="page-header">
        <div>
          <div className="page-title">ICU Dashboard</div>
          <div className="page-subtitle">Real-time clinical overview — {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
        </div>
      </div>

      {/* Stats row */}
      <div className="stat-grid" style={{ marginBottom: 24 }}>
        <div className="stat-card teal">
          <Users size={36} className="stat-icon" />
          <div className="stat-value">{stats?.total_patients?.toLocaleString()}</div>
          <div className="stat-label">Total Patients</div>
        </div>
        <div className="stat-card high">
          <AlertTriangle size={36} className="stat-icon" />
          <div className="stat-value" style={{ color: 'var(--risk-high)' }}>{stats?.risk_distribution?.High?.toLocaleString()}</div>
          <div className="stat-label">High Risk</div>
        </div>
        <div className="stat-card medium">
          <Activity size={36} className="stat-icon" />
          <div className="stat-value" style={{ color: 'var(--risk-medium)' }}>{stats?.risk_distribution?.Medium?.toLocaleString()}</div>
          <div className="stat-label">Medium Risk</div>
        </div>
        <div className="stat-card low">
          <TrendingUp size={36} className="stat-icon" />
          <div className="stat-value" style={{ color: 'var(--risk-low)' }}>{stats?.risk_distribution?.Low?.toLocaleString()}</div>
          <div className="stat-label">Low Risk</div>
        </div>
        <div className="stat-card warning">
          <Bell size={36} className="stat-icon" />
          <div className="stat-value" style={{ color: 'var(--warning)' }}>{stats?.critical_alerts}</div>
          <div className="stat-label">Critical Alerts</div>
        </div>
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 20, marginBottom: 24 }}>
        {/* Risk Pie */}
        <div className="card">
          <div className="card-header"><div className="card-title">Risk Distribution</div></div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                   dataKey="value" paddingAngle={3}>
                {riskData.map((entry) => (
                  <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
              />
              <Legend
                formatter={(val) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{val}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Bar */}
        <div className="card">
          <div className="card-header"><div className="card-title">Patient Risk Breakdown</div></div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {riskData.map((entry) => <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Critical Alerts */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Recent Critical Alerts</div>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/alerts')}>View All</button>
        </div>
        {alerts.length === 0
          ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No critical alerts at this time.</p>
          : alerts.map(a => (
              <div key={a.id} className="alert-item critical">
                <AlertTriangle size={16} color="var(--risk-high)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{a.message}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Admission #{a.hadm_id} · {a.indicator?.replace('_', ' ')}</div>
                </div>
              </div>
            ))
        }
      </div>
    </div>
  );
}
