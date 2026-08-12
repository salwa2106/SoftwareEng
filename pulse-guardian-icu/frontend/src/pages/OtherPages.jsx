
import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { AlertTriangle, Check, BarChart2, Database, Upload } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

// ── Alerts Page ───────────────────────────────────────────────────────────
export function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    const params = { limit: 100, acknowledged: false };
    if (filter) params.severity = filter;
    const res = await api.get('/alerts/', { params });
    setAlerts(res.data);
    setLoading(false);
  };

  useEffect(() => { fetchAlerts(); }, [filter]);

  const acknowledge = async (id) => {
    await api.patch(`/alerts/${id}/acknowledge`);
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Clinical Alerts</div>
          <div className="page-subtitle">{alerts.length} active alerts</div>
        </div>
      </div>

      <div className="filters-bar">
        <select className="input" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
        </select>
      </div>

      <div className="card">
        {loading
          ? <div className="loading-screen"><div className="spinner"></div></div>
          : alerts.length === 0
            ? <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <Check size={32} style={{ marginBottom: 12, color: 'var(--risk-low)' }} />
                <p>No active alerts at this time.</p>
              </div>
            : alerts.map(a => (
                <div key={a.id} className={`alert-item ${a.severity}`}>
                  <AlertTriangle size={16} color={a.severity === 'critical' ? 'var(--risk-high)' : 'var(--warning)'} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{a.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      Admission #{a.hadm_id} · {a.indicator?.replace(/_/g, ' ')} · {a.created_at?.slice(0, 19)}
                    </div>
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => acknowledge(a.id)}>
                    <Check size={12} /> Acknowledge
                  </button>
                </div>
              ))
        }
      </div>
    </div>
  );
}

// ── Model Metrics Page ─────────────────────────────────────────────────────
export function MetricsPage() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    api.get('/risk/metrics').then(r => setMetrics(r.data));
  }, []);

  if (!metrics) return <div className="loading-screen"><div className="spinner"></div></div>;

  if (metrics.error) {
    return (
      <div className="page-container">
        <div className="page-header">
          <div>
            <div className="page-title">Model Evaluation Metrics</div>
            <div className="page-subtitle">Risk prediction engine performance — academic demo</div>
          </div>
        </div>
        <div className="demo-banner">
          <span>ℹ</span>
          <span>{metrics.error}</span>
        </div>
      </div>
    );
  }

  const { baseline_rule_engine: baseline, ml_model: ml, dataset, comparison } = metrics;

  const barData = [
    { name: 'Accuracy',  value: +(ml.accuracy    * 100).toFixed(1), color: '#14b8a6' },
    { name: 'Precision', value: +(ml.precision   * 100).toFixed(1), color: '#3b82f6' },
    { name: 'Recall',    value: +(ml.recall      * 100).toFixed(1), color: '#8b5cf6' },
    { name: 'F1-Score',  value: +(ml.f1_score    * 100).toFixed(1), color: '#f59e0b' },
    { name: 'AUC-ROC',   value: +(ml.test_auc_roc * 100).toFixed(1), color: '#22c55e' },
  ];

  const aucCompareData = [
    { name: 'Rule Baseline', value: +(baseline.auc_roc * 100).toFixed(1), color: '#64748b' },
    { name: 'Trained ML Model', value: +(ml.test_auc_roc * 100).toFixed(1), color: '#22c55e' },
  ];

  const featureData = (ml.feature_importance || []).slice(0, 8).map(f => ({
    name: f.feature.replace(/_/g, ' ').replace('mean', '').trim(),
    value: +(f.importance * 100).toFixed(1),
  }));

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Model Evaluation Metrics</div>
          <div className="page-subtitle">Risk prediction engine performance — validated against real outcomes</div>
        </div>
      </div>

      <div className="demo-banner">
        <span>ℹ</span>
        <span>
          Trained on {dataset.n_rows.toLocaleString()} real ICU stays, label = {dataset.label}
          ({(dataset.positive_rate * 100).toFixed(1)}% positive rate). {comparison.note}
        </span>
      </div>

      <div className="metric-grid" style={{ marginBottom: 24 }}>
        {barData.map(m => (
          <div key={m.name} className="metric-card">
            <div className="metric-val" style={{ color: m.color }}>{m.value}%</div>
            <div className="metric-label">{m.name}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div className="card">
          <div className="card-header"><div className="card-title">ML Model Performance</div></div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData} margin={{ top: 5, right: 20, bottom: 5, left: -10 }}>
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }}
                formatter={v => [`${v}%`]}
              />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {barData.map(d => <Cell key={d.name} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><div className="card-title">Baseline vs. Trained Model (AUC-ROC)</div></div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={aucCompareData} margin={{ top: 5, right: 20, bottom: 5, left: -10 }}>
              <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }}
                formatter={v => [`${v}%`]}
              />
              <Bar dataKey="value" radius={[4,4,0,0]}>
                {aucCompareData.map(d => <Cell key={d.name} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><div className="card-title">Top Feature Importance (Trained Model)</div></div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={featureData} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
            <XAxis type="number" domain={[0, 'dataMax']} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" width={90} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }}
              formatter={v => [`${v}%`]}
            />
            <Bar dataKey="value" fill="#2dd4bf" radius={[0,4,4,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── Data Import Page ───────────────────────────────────────────────────────
export function DataPage() {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [file, setFile] = useState(null);

  const fetchStatus = async () => {
    const res = await api.get('/data/status');
    setStatus(res.data);
  };

  useEffect(() => { fetchStatus(); }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setMessage('');
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await api.post('/data/import', form);
      setMessage(`✓ Imported successfully: ${JSON.stringify(res.data.stats)}`);
      fetchStatus();
    } catch (e) { setMessage('✗ Import failed: ' + e.response?.data?.detail); }
    finally { setUploading(false); }
  };

  const handleGenerateDemo = async () => {
    setGenerating(true);
    setMessage('');
    try {
      const res = await api.post('/data/generate-demo');
      setMessage(`✓ Demo data generated: ${JSON.stringify(res.data.stats)}`);
      fetchStatus();
    } catch (e) { setMessage('✗ ' + e.response?.data?.detail); }
    finally { setGenerating(false); }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Data Management</div>
          <div className="page-subtitle">Import MIMIC-III dataset or generate demo data</div>
        </div>
      </div>

      {/* Current status */}
      {status && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header"><div className="card-title">Database Status</div></div>
          <div className="metric-grid">
            {Object.entries(status).map(([k, v]) => (
              <div key={k} className="metric-card">
                <div className="metric-val">{v.toLocaleString()}</div>
                <div className="metric-label">{k.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Upload CSV */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Upload size={14} style={{ marginRight: 6 }} />Import MIMIC-III CSV</div>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Upload your cleaned MIMIC-III CSV file. The system will auto-detect column names.
          </p>
          <div className="form-group">
            <label className="form-label">CSV File</label>
            <input type="file" accept=".csv" className="input" onChange={e => setFile(e.target.files[0])} />
          </div>
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading || !file}>
            {uploading ? <><span className="spinner" style={{ width: 14, height: 14 }}></span> Importing...</> : 'Import Dataset'}
          </button>
        </div>

        {/* Generate demo */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Database size={14} style={{ marginRight: 6 }} />Generate Demo Data</div>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
            Generate 200 synthetic ICU patients with realistic medical distributions for demo purposes.
          </p>
          <button className="btn btn-ghost" onClick={handleGenerateDemo} disabled={generating}>
            {generating ? <><span className="spinner" style={{ width: 14, height: 14 }}></span> Generating...</> : 'Generate Demo Data'}
          </button>
        </div>
      </div>

      {message && (
        <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius)', fontFamily: 'var(--font-mono)', fontSize: 12, color: message.startsWith('✓') ? 'var(--risk-low)' : 'var(--risk-high)' }}>
          {message}
        </div>
      )}
    </div>
  );
}