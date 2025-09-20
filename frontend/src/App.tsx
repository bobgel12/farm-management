import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext.tsx';
import { FarmProvider } from './contexts/FarmContext.tsx';
import { TaskProvider } from './contexts/TaskContext.tsx';
import Login from './components/Login.tsx';
import Dashboard from './components/Dashboard.tsx';
import FarmList from './components/FarmList.tsx';
import FarmDetail from './components/FarmDetail.tsx';
import HouseDetail from './components/HouseDetail.tsx';
import TaskList from './components/TaskList.tsx';
import ProtectedRoute from './components/ProtectedRoute.tsx';
import Layout from './components/Layout.tsx';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
    },
    secondary: {
      main: '#ff6f00',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <FarmProvider>
          <TaskProvider>
            <Router>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={
                  <ProtectedRoute>
                    <Layout>
                      <Dashboard />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/farms" element={
                  <ProtectedRoute>
                    <Layout>
                      <FarmList />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/farms/:farmId" element={
                  <ProtectedRoute>
                    <Layout>
                      <FarmDetail />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId" element={
                  <ProtectedRoute>
                    <Layout>
                      <HouseDetail />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="/houses/:houseId/tasks" element={
                  <ProtectedRoute>
                    <Layout>
                      <TaskList />
                    </Layout>
                  </ProtectedRoute>
                } />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Router>
          </TaskProvider>
        </FarmProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
