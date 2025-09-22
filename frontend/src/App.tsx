import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import { FarmProvider } from './contexts/FarmContext';
import { TaskProvider } from './contexts/TaskContext';
import { WorkerProvider } from './contexts/WorkerContext';
import { ProgramProvider } from './contexts/ProgramContext';
import Login from './components/Login';
import ProfessionalDashboard from './components/dashboard/ProfessionalDashboard';
import ProfessionalFarmList from './components/farms/ProfessionalFarmList';
import FarmDetail from './components/FarmDetail';
import HouseDetail from './components/HouseDetail';
import TaskList from './components/TaskList';
import ProfessionalProgramManager from './components/programs/ProfessionalProgramManager';
import ProtectedRoute from './components/ProtectedRoute';
import ProfessionalLayout from './components/layout/ProfessionalLayout';
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
                <Router>
              <Routes>
                <Route path="/login" element={<Login />} />
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
                      <FarmDetail />
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
                      <TaskList />
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
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
                </Router>
              </ProgramProvider>
            </WorkerProvider>
          </TaskProvider>
        </FarmProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
