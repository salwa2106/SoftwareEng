import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell, LineChart, Line
} from 'recharts';
import api from '../utils/api';
import { ArrowLeft, FileText, AlertTriangle, Clock, Activity, FlaskConical, Radio } from 'lucide-react';

function LiveMonitor({ icustayId }) {
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState([]);
  const [latest, setLatest] = useState(null);
  const [liveAlerts, setLiveAlerts] = useState([]);
  const abortRef = useRef(null);

  useEffect(() => {
    if (!icustayId) return;
    const controller = new AbortController();
    abortRef.current = controller;
    setHistory([]);
    setLiveAlerts([]);
    setConnected(false);

    async function run() {
      const token = localStorage.getItem('token');
      const resp = await fetch(`/api/monitor/${icustayId}/stream`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      if (!resp.ok || !resp.body) return;
      setConnected(true);
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop();
        for (const chunk of chunks) {
          const line = chunk.split('\n').find(l => l.startsWith('data: '));
          if (!line) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.vitals) {
              setLatest(payload);
              setHistory(h => [...h.slice(-29), {
                t: payload.tick,
                heart_rate: payload.vitals.heart_rate,
                spo2: payload.vitals.spo2,
                score: payload.score,
              }]);
              if (payload.alerts?.length) {
                setLiveAlerts(a => [
                  ...payload.alerts.map(al => ({ ...al, tick: payload.tick })),
                  ...a,
                ].slice(0, 20));
              }
            }
          } catch { /* ignore malformed chunk */ }
        }
      }
    }
    run().catch(() => {}).finally(() => setConnected(false));
    return () => controller.abort();
  }, [icustayId]);

  return (
    <div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
        background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.35)',
        borderRadius: 8, fontSize: 12.5, color: 'var(--text-primary)', marginBottom: 16,
      }}>
        <Radio size={14} color="#f59e0b" />
        <span>
          <strong>Simulated live monitor (demo).</strong> This MIMIC-III derived dataset only has
          per-stay aggregated vitals, not a raw device waveform, so this view synthesizes a
          physiologically plausible trajectory within this patient's own recorded min/max range.
          It is not a real-time device feed.
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <span style={{
          width: 8, height: 8, borderRadius: '50%',
          background: connected ? 'var(--risk-low)' : 'var(--text-dim)',
          boxShadow: connected ? '0 0 8px var(--risk-low)' : 'none',
        }} />
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          {connected ? 'Streaming simulated vitals…' : 'Connecting…'}
        </span>
      </div>

      {latest && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Heart Rate', val: latest.vitals.heart_rate, unit: 'bpm' },
            { label: 'Resp. Rate', val: latest.vitals.resp_rate, unit: '/min' },
            { label: 'SpO₂', val: latest.vitals.spo2, unit: '%' },
            { label: 'BP Systolic', val: latest.vitals.bp_systolic, unit: 'mmHg' },
          ].map(({ label, val, unit }) => (
            <div key={label} className="vital-chip">
              <span className="vital-chip-label">{label}</span>
              <span className="vital-chip-value">{val?.toFixed(1)} <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{unit}</span></span>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-header"><div className="card-title">Live Heart Rate &amp; SpO₂</div></div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={history} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
              <XAxis dataKey="t" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }} />
              <Line type="monotone" dataKey="heart_rate" stroke="#ef4444" dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="spo2" stroke="#8b5cf6" dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <div className="card-header"><div className="card-title">Live Risk Score</div></div>
          {latest && (
            <div style={{ textAlign: 'center', marginBottom: 8 }}>
              <div className={`score-value ${latest.risk_level}`}>{latest.score?.toFixed(0)}</div>
              <span className={`risk-badge ${latest.risk_level}`}>{latest.risk_level} Risk</span>
            </div>
          )}
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={history} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
              <XAxis dataKey="t" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }} />
              <Line type="monotone" dataKey="score" stroke="#14b8a6" dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-header"><div className="card-title">Live Alerts</div></div>
          {liveAlerts.length === 0
            ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No alerts triggered yet in this session.</p>
            : liveAlerts.map((a, i) => (
                <div key={i} className={`alert-item ${a.severity}`}>
                  <AlertTriangle size={16} color={a.severity === 'critical' ? 'var(--risk-high)' : 'var(--warning)'} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{a.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>tick {a.tick} · {a.severity.toUpperCase()}</div>
                  </div>
                </div>
              ))
          }
        </div>
      </div>
    </div>
  );
}

const STATUS_COLOR = { normal: '#22c55e', abnormal_low: '#f59e0b', abnormal_high: '#f59e0b', critical_low: '#ef4444', critical_high: '#ef4444', unknown: '#64748b' };

function IndicatorRow({ label, value, unit, status, contribution }) {
  const pct = Math.min(100, (contribution || 0) * 3);
  return (
    <div className="indicator-row">
      <span className="indicator-label">{label}</span>
      <span className="indicator-value" style={{ color: STATUS_COLOR[status] || 'var(--text-primary)' }}>
        {value != null ? `${typeof value === 'number' ? value.toFixed(1) : value}${unit || ''}` : '—'}
      </span>
      <div className="indicator-bar-wrap">
        <div className={`indicator-bar ${status}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`indicator-status ${status}`}>{status?.replace('_', ' ') || '—'}</span>
    </div>
  );
}

function VitalChart({ title, data, color = '#14b8a6', normalLow, normalHigh, unit }) {
  return (
    <div className="card">
      <div className="card-header"><div className="card-title">{title}</div></div>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
          <XAxis dataKey="label" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }}
            formatter={v => [`${v} ${unit}`, title]}
          />
          {normalLow  && <ReferenceLine y={normalLow}  stroke="rgba(34,197,94,0.4)"  strokeDasharray="3 3" />}
          {normalHigh && <ReferenceLine y={normalHigh} stroke="rgba(34,197,94,0.4)"  strokeDasharray="3 3" />}
          <Bar dataKey="value" fill={color} radius={[3,3,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function PatientDetailPage() {
  const { subjectId } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [report, setReport] = useState(null);
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get(`/patients/${subjectId}`),
      api.get(`/patients/${subjectId}/timeline`)
    ]).then(([p, t]) => {
      setPatient(p.data);
      setTimeline(t.data.events);
    }).finally(() => setLoading(false));
  }, [subjectId]);

  if (loading) return <div className="loading-screen"><div className="spinner"></div> Loading patient...</div>;
  if (!patient) return <div className="page-container"><p style={{ color: 'var(--text-muted)' }}>Patient not found.</p></div>;

  // Use first admission + first ICU stay
  const adm = patient.admissions?.[0];
  const icu = adm?.icu_stays?.[0];
  const risk = adm?.risk;
  const factors = risk?.contributing_factors || [];

  const vitalsCharts = icu ? [
    { title: 'Heart Rate', unit: 'bpm', normalLow: 60, normalHigh: 100, color: '#ef4444',
      data: [{ label: 'Min', value: icu.vitals.heart_rate.min }, { label: 'Mean', value: icu.vitals.heart_rate.mean }, { label: 'Max', value: icu.vitals.heart_rate.max }] },
    { title: 'Respiratory Rate', unit: '/min', normalLow: 12, normalHigh: 20, color: '#3b82f6',
      data: [{ label: 'Min', value: icu.vitals.resp_rate.min }, { label: 'Mean', value: icu.vitals.resp_rate.mean }, { label: 'Max', value: icu.vitals.resp_rate.max }] },
    { title: 'SpO₂', unit: '%', normalLow: 95, normalHigh: 100, color: '#8b5cf6',
      data: [{ label: 'Min', value: icu.vitals.spo2.min }, { label: 'Mean', value: icu.vitals.spo2.mean }, { label: 'Max', value: icu.vitals.spo2.max }] },
    { title: 'BP Systolic', unit: 'mmHg', normalLow: 90, normalHigh: 140, color: '#f59e0b',
      data: [{ label: 'Min', value: icu.vitals.bp_systolic.min }, { label: 'Mean', value: icu.vitals.bp_systolic.mean }, { label: 'Max', value: icu.vitals.bp_systolic.max }] },
  ] : [];

  const labsCharts = icu ? [
    { title: 'Creatinine', unit: 'mg/dL', normalLow: 0.6, normalHigh: 1.2, color: '#14b8a6',
      data: [{ label: 'Mean', value: icu.labs.creatinine.mean }, { label: 'Max', value: icu.labs.creatinine.max }] },
    { title: 'Glucose', unit: 'mg/dL', normalLow: 70, normalHigh: 140, color: '#f97316',
      data: [{ label: 'Mean', value: icu.labs.glucose.mean }, { label: 'Max', value: icu.labs.glucose.max }] },
    { title: 'Hemoglobin', unit: 'g/dL', normalLow: 12, normalHigh: 17, color: '#ec4899',
      data: [{ label: 'Mean', value: icu.labs.hemoglobin.mean }, { label: 'Min', value: icu.labs.hemoglobin.min }] },
    { title: 'WBC', unit: 'K/uL', normalLow: 4.5, normalHigh: 11, color: '#06b6d4',
      data: [{ label: 'Mean', value: icu.labs.wbc.mean }, { label: 'Max', value: icu.labs.wbc.max }] },
  ] : [];

  const radarData = factors.slice(0, 8).map(f => ({
    indicator: f.indicator.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: f.contribution
  }));

  const handleGenerateReport = async () => {
    if (!adm) return;
    setGenerating(true);
    try {
      const res = await api.post(`/reports/${adm.hadm_id}/generate`);
      setReport(res.data.content);
      setTab('report');
    } catch (e) { alert('Failed to generate report'); }
    finally { setGenerating(false); }
  };

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/patients')}>
            <ArrowLeft size={14} /> Back
          </button>
          <div>
            <div className="page-title">Patient #{patient.subject_id}</div>
            <div className="page-subtitle">{patient.gender === 'M' ? 'Male' : 'Female'} · {patient.age ? Math.round(patient.age) + ' years' : ''} · {adm?.diagnosis}</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {risk && <span className={`risk-badge ${risk.risk_level}`} style={{ fontSize: 13, padding: '6px 14px' }}>{risk.risk_level} Risk</span>}
          <button className="btn btn-primary" onClick={handleGenerateReport} disabled={generating}>
            <FileText size={14} /> {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['overview', 'vitals', 'labs', 'risk', 'live', 'timeline', 'alerts', 'report'].map(t => (
          <div key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </div>
        ))}
      </div>

      {/* Overview tab */}
      {tab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="card">
            <div className="card-header"><div className="card-title">Patient Info</div></div>
            {[
              ['Subject ID', patient.subject_id], ['Gender', patient.gender === 'M' ? 'Male' : 'Female'],
              ['Age', patient.age ? Math.round(patient.age) + ' years' : '—'],
              ['Admission Type', adm?.admission_type], ['Diagnosis', adm?.diagnosis],
              ['Insurance', adm?.insurance], ['Marital Status', adm?.marital_status],
              ['Ethnicity', adm?.ethnicity],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                <span style={{ fontWeight: 500 }}>{v || '—'}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-header"><div className="card-title">ICU Stay</div></div>
            {icu ? [
              ['ICU Stay ID', icu.icustay_id], ['Care Unit', icu.first_careunit],
              ['ICU LOS', `${icu.los?.toFixed(1)} days`],
              ['Hospital LOS', `${adm?.hospital_los?.toFixed(1)} days`],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                <span style={{ fontWeight: 500 }}>{v || '—'}</span>
              </div>
            )) : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No ICU stay data.</p>}

            {risk && (
              <div style={{ marginTop: 20, textAlign: 'center' }}>
                <div className={`score-value ${risk.risk_level}`}>{risk.score?.toFixed(0)}</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Risk Score / 100</div>
                <span className={`risk-badge ${risk.risk_level}`} style={{ marginTop: 8, display: 'inline-flex' }}>{risk.risk_level} Risk</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Vitals tab */}
      {tab === 'vitals' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
            {icu && [
              { label: 'Heart Rate', val: icu.vitals.heart_rate.mean, unit: 'bpm', lo: 60, hi: 100 },
              { label: 'Resp. Rate', val: icu.vitals.resp_rate.mean, unit: '/min', lo: 12, hi: 20 },
              { label: 'SpO₂', val: icu.vitals.spo2.mean, unit: '%', lo: 95, hi: 100 },
              { label: 'BP Systolic', val: icu.vitals.bp_systolic.mean, unit: 'mmHg', lo: 90, hi: 140 },
            ].map(({ label, val, unit, lo, hi }) => {
              const ok = val != null && val >= lo && val <= hi;
              return (
                <div key={label} className="vital-chip">
                  <span className="vital-chip-label">{label}</span>
                  <span className="vital-chip-value" style={{ color: ok ? 'var(--risk-low)' : 'var(--risk-high)' }}>
                    {val?.toFixed(1) ?? '—'} <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{unit}</span>
                  </span>
                  <span className="vital-chip-range">Normal: {lo}–{hi} {unit}</span>
                </div>
              );
            })}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {vitalsCharts.map(c => <VitalChart key={c.title} {...c} />)}
          </div>
        </div>
      )}

      {/* Labs tab */}
      {tab === 'labs' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
            {icu && [
              { label: 'Creatinine', val: icu.labs.creatinine.mean, unit: 'mg/dL', lo: 0.6, hi: 1.2 },
              { label: 'Glucose', val: icu.labs.glucose.mean, unit: 'mg/dL', lo: 70, hi: 140 },
              { label: 'Hemoglobin', val: icu.labs.hemoglobin.mean, unit: 'g/dL', lo: 12, hi: 17 },
              { label: 'Potassium', val: icu.labs.potassium.mean, unit: 'mEq/L', lo: 3.5, hi: 5.0 },
              { label: 'Sodium', val: icu.labs.sodium.mean, unit: 'mEq/L', lo: 136, hi: 145 },
              { label: 'WBC', val: icu.labs.wbc.mean, unit: 'K/uL', lo: 4.5, hi: 11 },
            ].map(({ label, val, unit, lo, hi }) => {
              const ok = val != null && val >= lo && val <= hi;
              return (
                <div key={label} className="vital-chip">
                  <span className="vital-chip-label"><FlaskConical size={12} style={{ display: 'inline', marginRight: 4 }} />{label}</span>
                  <span className="vital-chip-value" style={{ color: ok ? 'var(--risk-low)' : 'var(--risk-high)' }}>
                    {val?.toFixed(2) ?? '—'} <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{unit}</span>
                  </span>
                  <span className="vital-chip-range">Normal: {lo}–{hi} {unit}</span>
                </div>
              );
            })}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {labsCharts.map(c => <VitalChart key={c.title} {...c} />)}
          </div>
        </div>
      )}

      {/* Risk tab */}
      {tab === 'risk' && risk && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <div className="card-title" style={{ marginBottom: 20 }}>Risk Score</div>
            <div className={`score-value ${risk.risk_level}`}>{risk.score?.toFixed(0)}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', margin: '8px 0' }}>out of 100</div>
            <span className={`risk-badge ${risk.risk_level}`} style={{ fontSize: 14, padding: '8px 20px' }}>{risk.risk_level} Risk</span>
            <div style={{ margin: '20px 0' }}>
              <div className="progress-bar"><div className="progress-fill" style={{ width: `${risk.score}%`, background: risk.risk_level === 'High' ? 'var(--risk-high)' : risk.risk_level === 'Medium' ? 'var(--risk-medium)' : 'var(--risk-low)' }} /></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-dim)', marginTop: 4 }}>
                <span>0 Low</span><span>40 Med</span><span>70 High</span><span>100</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><div className="card-title">Contributing Factors</div></div>
            {factors.length === 0
              ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No abnormal indicators detected.</p>
              : factors.map(f => (
                  <IndicatorRow key={f.indicator}
                    label={f.indicator.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    value={f.value} status={f.status} contribution={f.contribution}
                  />
                ))
            }
          </div>

          {radarData.length > 0 && (
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div className="card-header"><div className="card-title">Risk Factor Radar</div></div>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis dataKey="indicator" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 30]} tick={{ fill: 'var(--text-dim)', fontSize: 10 }} />
                  <Radar name="Contribution" dataKey="value" stroke="var(--teal)" fill="var(--teal)" fillOpacity={0.25} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)', fontSize: 12 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Live monitor tab */}
      {tab === 'live' && icu && <LiveMonitor icustayId={icu.icustay_id} />}

      {/* Timeline tab */}
      {tab === 'timeline' && (
        <div className="card">
          <div className="card-header"><div className="card-title"><Clock size={14} style={{ marginRight: 6 }} />Clinical Timeline</div></div>
          <div className="timeline">
            {timeline.length === 0
              ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No timeline events.</p>
              : timeline.map((ev, i) => (
                  <div key={i} className={`timeline-item ${ev.type}`}>
                    <div className="timeline-date">{ev.date ? ev.date.slice(0, 19).replace('T', ' ') : ''}</div>
                    <div className="timeline-title">{ev.title}</div>
                    <div className="timeline-detail">{ev.detail}</div>
                  </div>
                ))
            }
          </div>
        </div>
      )}

      {/* Alerts tab */}
      {tab === 'alerts' && (
        <div className="card">
          <div className="card-header"><div className="card-title">Patient Alerts</div></div>
          {(adm?.alerts || []).length === 0
            ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No alerts for this patient.</p>
            : (adm?.alerts || []).map(a => (
                <div key={a.id} className={`alert-item ${a.severity}`}>
                  <AlertTriangle size={16} color={a.severity === 'critical' ? 'var(--risk-high)' : 'var(--warning)'} style={{ flexShrink: 0, marginTop: 2 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{a.message}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {a.indicator?.replace(/_/g, ' ')} · {a.severity.toUpperCase()} · {a.created_at?.slice(0, 19)}
                    </div>
                  </div>
                  <span style={{ fontSize: 11, color: a.acknowledged ? 'var(--text-dim)' : 'var(--risk-high)' }}>
                    {a.acknowledged ? 'Acknowledged' : 'Active'}
                  </span>
                </div>
              ))
          }
        </div>
      )}

      {/* Report tab */}
      {tab === 'report' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Clinical Report</div>
            <button className="btn btn-primary btn-sm" onClick={handleGenerateReport} disabled={generating}>
              <FileText size={12} /> Regenerate
            </button>
          </div>
          {report
            ? <pre className="report-content">{report}</pre>
            : <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <FileText size={32} style={{ marginBottom: 12, opacity: 0.4 }} />
                <p>No report generated yet.</p>
                <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={handleGenerateReport}>Generate Report</button>
              </div>
          }
        </div>
      )}
    </div>
  );
}
