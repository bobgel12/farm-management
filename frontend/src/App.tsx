import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { FarmProvider } from './contexts/FarmContext';
import { TaskProvider } from './contexts/TaskContext';
import { WorkerProvider } from './contexts/WorkerContext';
import { ProgramProvider } from './contexts/ProgramContext';
import { RotemProvider } from './contexts/RotemContext';
import { FlockProvider } from './contexts/FlockContext';
import { AnalyticsProvider } from './contexts/AnalyticsContext';
import { ReportingProvider } from './contexts/ReportingContext';
import Login from './components/Login';
import ProfessionalDashboard from './components/dashboard/ProfessionalDashboard';
import ProfessionalFarmList from './components/farms/ProfessionalFarmList';
import UnifiedFarmDashboard from './components/farms/UnifiedFarmDashboard';
import HouseDetail from './components/HouseDetail';
import HouseDetailPage from './components/houses/HouseDetailPage';
import ProfessionalTaskList from './components/tasks/ProfessionalTaskList';
import ProfessionalProgramManager from './components/programs/ProfessionalProgramManager';
import ProfessionalWorkerList from './components/workers/ProfessionalWorkerList';
import EmailManager from './components/EmailManager';
import PasswordResetRequest from './components/PasswordResetRequest';
import PasswordResetForm from './components/PasswordResetForm';
import SecuritySettings from './components/SecuritySettings';
import ProtectedRoute from './components/ProtectedRoute';
import ProfessionalLayout from './components/layout/ProfessionalLayout';
import RotemDashboard from './components/rotem/RotemDashboard';
import FarmDetailPage from './components/rotem/FarmDetailPage';
import HouseMonitoringDashboard from './components/houses/HouseMonitoringDashboard';
import FarmHousesMonitoring from './components/houses/FarmHousesMonitoring';
import ComparisonDashboard from './components/houses/ComparisonDashboard';
import ProfessionalFlockList from './components/flocks/ProfessionalFlockList';
import FlockForm from './components/flocks/FlockForm';
import FlockDetail from './components/flocks/FlockDetail';
import BIDashboard from './components/analytics/BIDashboard';
import OrganizationSettings from './components/organizations/OrganizationSettings';
import OrganizationList from './components/organizations/OrganizationList';
import OrganizationForm from './components/organizations/OrganizationForm';
import AcceptInvite from './components/organizations/AcceptInvite';
import ReportList from './components/reporting/ReportList';
import PerformanceRecordForm from './components/flocks/PerformanceRecordForm';
import theme from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <OrganizationProvider>
          <FarmProvider>
            <TaskProvider>
              <WorkerProvider>
                <ProgramProvider>
                  <RotemProvider>
                    <FlockProvider>
                      <AnalyticsProvider>
                        <ReportingProvider>
                  <Router
                    future={{
                      v7_startTransition: true,
                      v7_relativeSplatPath: true,
                    }}
                  >
              <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/forgot-password" element={<PasswordResetRequest />} />
                        <Route path="/reset-password" element={<PasswordResetForm />} />
                        <Route path="/accept-invite/:token" element={<AcceptInvite />} />
                        <Route path="/" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <ProfessionalDashboard />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                <Route path="/farms" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ProfessionalFarmList />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <UnifiedFarmDashboard />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId/houses/:houseId" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <HouseDetailPage />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <HouseDetailPage />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId/tasks" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ProfessionalTaskList />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId/monitoring" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <HouseMonitoringDashboard />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId/workers" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ProfessionalWorkerList />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId/monitoring" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <FarmHousesMonitoring />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/comparison" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ComparisonDashboard />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId/houses/comparison" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ComparisonDashboard />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/programs" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ProfessionalProgramManager />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/workers" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <ProfessionalWorkerList />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                        <Route path="/email" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <EmailManager />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/security" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <SecuritySettings />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/flocks" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <ProfessionalFlockList />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/flocks/new" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <FlockForm />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/flocks/:id" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <FlockDetail />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/flocks/:id/edit" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <FlockForm />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/flocks/:flockId/performance/new" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <PerformanceRecordForm />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/organizations" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <OrganizationList />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/organizations/new" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <OrganizationForm />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/organizations/:id/edit" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <OrganizationForm />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/organization/settings" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <OrganizationSettings />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/analytics" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <BIDashboard />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/reports" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <ReportList />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/rotem" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <RotemDashboard />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="/rotem/farms/:farmId" element={
                          <ProtectedRoute>
                            <ProfessionalLayout>
                              <FarmDetailPage />
                            </ProfessionalLayout>
                          </ProtectedRoute>
                        } />
                        <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
                  </Router>
                        </ReportingProvider>
                      </AnalyticsProvider>
                    </FlockProvider>
                  </RotemProvider>
                </ProgramProvider>
              </WorkerProvider>
            </TaskProvider>
          </FarmProvider>
        </OrganizationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
