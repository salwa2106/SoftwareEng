import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { Search, ChevronLeft, ChevronRight, X } from 'lucide-react';

function RiskBadge({ level }) {
  if (!level) return <span style={{ color: 'var(--text-dim)' }}>—</span>;
  return <span className={`risk-badge ${level}`}>{level}</span>;
}

const SEARCH_OPTIONS = [
  { value: 'subject_id',  label: 'Patient ID (SUBJECT_ID)'  },
  { value: 'hadm_id',     label: 'Admission ID (HADM_ID)'   },
  { value: 'icustay_id',  label: 'ICU Stay ID (ICUSTAY_ID)' },
];

export default function PatientsPage() {
  const [patients,      setPatients]      = useState([]);
  const [total,         setTotal]         = useState(0);
  const [pages,         setPages]         = useState(1);
  const [page,          setPage]          = useState(1);
  const [loading,       setLoading]       = useState(false);
  const [careUnits,     setCareUnits]     = useState([]);
  const [admTypes,      setAdmTypes]      = useState([]);

  // Search state
  const [searchBy,      setSearchBy]      = useState('subject_id');
  const [searchValue,   setSearchValue]   = useState('');

  // Filter state
  const [genderFilter,  setGenderFilter]  = useState('');
  const [admTypeFilter, setAdmTypeFilter] = useState('');
  const [careUnitFilter,setCareUnitFilter]= useState('');
  const [riskFilter,    setRiskFilter]    = useState('');

  const navigate = useNavigate();

  // Load dropdown options once
  useEffect(() => {
    api.get('/patients/stats').then(r => {
      setCareUnits(r.data.care_units     || []);
      setAdmTypes (r.data.admission_types || []);
    }).catch(() => {});
  }, []);

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, per_page: 20 };

      if (searchValue.trim()) {
        params.search    = searchValue.trim();
        params.search_by = searchBy;
      }
      if (riskFilter)     params.risk_level     = riskFilter;
      if (genderFilter)   params.gender         = genderFilter;
      if (admTypeFilter)  params.admission_type = admTypeFilter;
      if (careUnitFilter) params.care_unit      = careUnitFilter;

      const res = await api.get('/patients/', { params });
      setPatients(res.data.patients);
      setTotal(res.data.total);
      setPages(res.data.pages);
    } finally {
      setLoading(false);
    }
  }, [page, searchValue, searchBy, riskFilter, genderFilter, admTypeFilter, careUnitFilter]);

  useEffect(() => { fetchPatients(); }, [fetchPatients]);

  // Reset to page 1 whenever filters/search change
  useEffect(() => { setPage(1); }, [searchValue, searchBy, riskFilter, genderFilter, admTypeFilter, careUnitFilter]);

  const clearAll = () => {
    setSearchValue('');
    setSearchBy('subject_id');
    setGenderFilter('');
    setAdmTypeFilter('');
    setCareUnitFilter('');
    setRiskFilter('');
    setPage(1);
  };

  const hasActiveFilters = searchValue || genderFilter || admTypeFilter || careUnitFilter || riskFilter;

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <div className="page-title">Patient List</div>
          <div className="page-subtitle">{total.toLocaleString()} patients found</div>
        </div>
        {hasActiveFilters && (
          <button className="btn btn-ghost btn-sm" onClick={clearAll}>
            <X size={13} /> Clear all filters
          </button>
        )}
      </div>

      {/* ── Search bar ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
        {/* Dropdown: which ID to search by */}
        <select
          className="input"
          style={{ width: 220, flexShrink: 0 }}
          value={searchBy}
          onChange={e => { setSearchBy(e.target.value); setSearchValue(''); }}
        >
          {SEARCH_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        {/* Search input */}
        <div className="search-bar" style={{ flex: 1 }}>
          <Search size={14} className="search-icon" />
          <input
            className="input"
            placeholder={`Enter ${SEARCH_OPTIONS.find(o => o.value === searchBy)?.label}...`}
            value={searchValue}
            onChange={e => setSearchValue(e.target.value)}
            type="number"
            min="0"
          />
        </div>
      </div>

      {/* ── Filters row ────────────────────────────────────────────── */}
      <div className="filters-bar" style={{ marginBottom: 20 }}>
        {/* Gender */}
        <select className="input" value={genderFilter} onChange={e => setGenderFilter(e.target.value)}>
          <option value="">All Genders</option>
          <option value="M">Male (M)</option>
          <option value="F">Female (F)</option>
        </select>

        {/* Admission type */}
        <select className="input" value={admTypeFilter} onChange={e => setAdmTypeFilter(e.target.value)}>
          <option value="">All Admissions</option>
          {admTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>

        {/* Care unit */}
        <select className="input" value={careUnitFilter} onChange={e => setCareUnitFilter(e.target.value)}>
          <option value="">All Care Units</option>
          {careUnits.map(u => <option key={u} value={u}>{u}</option>)}
        </select>

        {/* Risk level */}
        <select className="input" value={riskFilter} onChange={e => setRiskFilter(e.target.value)}>
          <option value="">All Risk Levels</option>
          <option value="High">🔴 High</option>
          <option value="Medium">🟡 Medium</option>
          <option value="Low">🟢 Low</option>
        </select>

        {/* Active filter chips */}
        {hasActiveFilters && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            {searchValue && (
              <span style={chipStyle}>
                {SEARCH_OPTIONS.find(o => o.value === searchBy)?.label}: {searchValue}
                <X size={11} style={{ cursor: 'pointer', marginLeft: 4 }} onClick={() => setSearchValue('')} />
              </span>
            )}
            {genderFilter && (
              <span style={chipStyle}>
                Gender: {genderFilter}
                <X size={11} style={{ cursor: 'pointer', marginLeft: 4 }} onClick={() => setGenderFilter('')} />
              </span>
            )}
            {admTypeFilter && (
              <span style={chipStyle}>
                Admission: {admTypeFilter}
                <X size={11} style={{ cursor: 'pointer', marginLeft: 4 }} onClick={() => setAdmTypeFilter('')} />
              </span>
            )}
            {careUnitFilter && (
              <span style={chipStyle}>
                Care Unit: {careUnitFilter}
                <X size={11} style={{ cursor: 'pointer', marginLeft: 4 }} onClick={() => setCareUnitFilter('')} />
              </span>
            )}
            {riskFilter && (
              <span style={chipStyle}>
                Risk: {riskFilter}
                <X size={11} style={{ cursor: 'pointer', marginLeft: 4 }} onClick={() => setRiskFilter('')} />
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Table ──────────────────────────────────────────────────── */}
      <div className="card" style={{ padding: 0 }}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Admission</th>
                <th>Care Unit</th>
                <th>Risk Level</th>
                <th>Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 40 }}>
                    <div className="spinner" style={{ margin: '0 auto' }}></div>
                  </td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No patients found. Try adjusting your search or filters.
                  </td>
                </tr>
              ) : (
                patients.map(p => (
                  <tr
                    key={`${p.subject_id}-${p.hadm_id}`}
                    onClick={() => navigate(`/patients/${p.subject_id}`)}
                  >
                    {/* Patient ID */}
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--teal)' }}>
                      {p.subject_id}
                    </td>

                    {/* Age */}
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {p.age ? Math.round(p.age) : '—'}
                    </td>

                    {/* Gender */}
                    <td>
                      {p.gender === 'M'
                        ? <span style={{ color: '#60a5fa' }}>♂ Male</span>
                        : p.gender === 'F'
                        ? <span style={{ color: '#f472b6' }}>♀ Female</span>
                        : p.gender || '—'}
                    </td>

                    {/* Admission */}
                    <td>
                      <span style={{
                        fontSize: 11, background: 'var(--bg-elevated)',
                        padding: '2px 8px', borderRadius: 4,
                        color: 'var(--text-secondary)'
                      }}>
                        {p.admission_type || '—'}
                      </span>
                    </td>

                    {/* Care Unit */}
                    <td style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                      {p.first_careunit || '—'}
                    </td>

                    {/* Risk Level */}
                    <td>
                      <RiskBadge level={p.risk_level} />
                    </td>

                    {/* Risk Score */}
                    <td>
                      {p.risk_score != null ? (
                        <span style={{
                          fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 15,
                          color: p.risk_level === 'High'   ? 'var(--risk-high)'
                               : p.risk_level === 'Medium' ? 'var(--risk-medium)'
                               : 'var(--risk-low)'
                        }}>
                          {p.risk_score.toFixed(0)}
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 16px', borderTop: '1px solid var(--border)'
        }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Page {page} of {pages} · {total.toLocaleString()} total records
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} /> Prev
            </button>
            <button className="btn btn-ghost btn-sm" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Small chip style for active filters
const chipStyle = {
  display: 'inline-flex', alignItems: 'center',
  background: 'var(--teal-glow)', color: 'var(--teal)',
  border: '1px solid rgba(20,184,166,0.3)',
  borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 500,
};
