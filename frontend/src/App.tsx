import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import { FarmProvider } from './contexts/FarmContext';
import { TaskProvider } from './contexts/TaskContext';
import { WorkerProvider } from './contexts/WorkerContext';
import { ProgramProvider } from './contexts/ProgramContext';
import { RotemProvider } from './contexts/RotemContext';
import Login from './components/Login';
import ProfessionalDashboard from './components/dashboard/ProfessionalDashboard';
import ProfessionalFarmList from './components/farms/ProfessionalFarmList';
import UnifiedFarmDashboard from './components/farms/UnifiedFarmDashboard';
import HouseDetail from './components/HouseDetail';
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
import theme from './theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <FarmProvider>
          <TaskProvider>
            <WorkerProvider>
              <ProgramProvider>
                <RotemProvider>
                  <Router>
              <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/forgot-password" element={<PasswordResetRequest />} />
                        <Route path="/reset-password" element={<PasswordResetForm />} />
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
                      <HouseDetail />
                    </ProfessionalLayout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId" element={
                  <ProtectedRoute>
                    <ProfessionalLayout>
                      <HouseDetail />
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
                </RotemProvider>
              </ProgramProvider>
            </WorkerProvider>
          </TaskProvider>
        </FarmProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
