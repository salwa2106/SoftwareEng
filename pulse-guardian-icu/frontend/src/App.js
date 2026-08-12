import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Sidebar from './components/common/Sidebar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PatientsPage from './pages/PatientsPage';
import PatientDetailPage from './pages/PatientDetailPage';
import { AlertsPage, MetricsPage, DataPage } from './pages/OtherPages';
import api from './utils/api';
import './index.css';

function ProtectedLayout() {
  const { user } = useAuth();
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    if (user) {
      api.get('/patients/stats').then(r => setAlertCount(r.data.critical_alerts || 0)).catch(() => {});
    }
  }, [user]);

  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-layout">
      <Sidebar alertCount={alertCount} />
      <div className="main-content">
        <Routes>
          <Route path="/dashboard"         element={<DashboardPage />} />
          <Route path="/patients"          element={<PatientsPage />} />
          <Route path="/patients/:subjectId" element={<PatientDetailPage />} />
          <Route path="/alerts"            element={<AlertsPage />} />
          <Route path="/metrics"           element={<MetricsPage />} />
          <Route path="/data"              element={<DataPage />} />
          <Route path="*"                  element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginAuthRedirect />} />
          <Route path="/*"     element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

function LoginAuthRedirect() {
  const { user } = useAuth();
  if (user) return <Navigate to="/dashboard" replace />;
  return <LoginPage />;
}

export default App;
