import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Activity, Lock, User } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 8 }}>
            <Activity size={32} color="var(--teal)" />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--teal)' }}>Pulse Guardian</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>ICU Clinical AI System</div>
            </div>
          </div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 12 }}>
            Sign in to access the clinical dashboard
          </p>
        </div>

        <div className="demo-banner">
          <span>⚠</span>
          <span>Academic demo — default login: <strong>admin / admin123</strong></span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <div style={{ position: 'relative' }}>
              <User size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                className="input" style={{ paddingLeft: 32 }}
                value={username} onChange={e => setUsername(e.target.value)}
                placeholder="Enter username" required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input
                className="input" type="password" style={{ paddingLeft: 32 }}
                value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Enter password" required
              />
            </div>
          </div>

          {error && <div className="error-msg">{error}</div>}

          <button
            type="submit" className="btn btn-primary"
            style={{ width: '100%', marginTop: 20, justifyContent: 'center', padding: '11px' }}
            disabled={loading}
          >
            {loading ? <><span className="spinner" style={{ width: 14, height: 14 }}></span> Signing in...</> : 'Sign In'}
          </button>
        </form>

        <p style={{ fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', marginTop: 20 }}>
          FOR ACADEMIC/DEMO USE ONLY · Not for clinical decisions
        </p>
      </div>
    </div>
  );
}
