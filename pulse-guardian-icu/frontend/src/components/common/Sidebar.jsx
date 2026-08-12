import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  Activity, Users, LayoutDashboard, Bell, FileText,
  Clock, BarChart3, LogOut, Database, ShieldAlert
} from 'lucide-react';

export default function Sidebar({ alertCount = 0 }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Activity size={22} color="var(--teal)" />
          <div>
            <div className="logo-text">Pulse Guardian</div>
            <div className="logo-sub">ICU · Clinical AI</div>
          </div>
        </div>
      </div>

      <nav style={{ flex: 1, overflow: 'auto' }}>
        <div className="nav-section">
          <div className="nav-label">Overview</div>
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={16} /> Dashboard
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-label">Patients</div>
          <NavLink to="/patients" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Users size={16} /> Patient List
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-label">Clinical</div>
          <NavLink to="/alerts" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Bell size={16} /> Alerts
            {alertCount > 0 && <span className="nav-badge">{alertCount > 99 ? '99+' : alertCount}</span>}
          </NavLink>
          <NavLink to="/metrics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <BarChart3 size={16} /> Model Metrics
          </NavLink>
        </div>

        {user?.role === 'admin' && (
          <div className="nav-section">
            <div className="nav-label">Admin</div>
            <NavLink to="/data" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Database size={16} /> Data Import
            </NavLink>
          </div>
        )}
      </nav>

      <div style={{ padding: '12px 8px', borderTop: '1px solid var(--border)' }}>
        <div style={{ padding: '8px 10px', marginBottom: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>{user?.full_name || user?.username}</div>
          <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{user?.role}</div>
        </div>
        <button className="nav-item" onClick={handleLogout} style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer' }}>
          <LogOut size={16} /> Sign out
        </button>
      </div>
    </aside>
  );
}
