import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import { FarmProvider } from './contexts/FarmContext';
import { TaskProvider } from './contexts/TaskContext';
import { WorkerProvider } from './contexts/WorkerContext';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import FarmList from './components/FarmList';
import FarmDetail from './components/FarmDetail';
import HouseDetail from './components/HouseDetail';
import TaskList from './components/TaskList';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
    },
    secondary: {
      main: '#ff6f00',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '2rem',
      },
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '1.75rem',
      },
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '1.5rem',
      },
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '1.25rem',
      },
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '1.1rem',
      },
    },
    h6: {
      fontSize: '1.1rem',
      fontWeight: 600,
      '@media (max-width:600px)': {
        fontSize: '1rem',
      },
    },
    body1: {
      fontSize: '1rem',
      '@media (max-width:600px)': {
        fontSize: '0.875rem',
      },
    },
    body2: {
      fontSize: '0.875rem',
      '@media (max-width:600px)': {
        fontSize: '0.8rem',
      },
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: 8,
          '@media (max-width:600px)': {
            minHeight: 44,
            fontSize: '0.875rem',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '@media (max-width:600px)': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '@media (max-width:600px)': {
            '& .MuiInputBase-root': {
              fontSize: '16px', // Prevent zoom on iOS
            },
          },
        },
      },
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      xl: 1536,
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
            <WorkerProvider>
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
            </WorkerProvider>
          </TaskProvider>
        </FarmProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
