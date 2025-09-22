import axios from 'axios';

// Determine API URL based on environment
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Production detection
  if (process.env.NODE_ENV === 'production') {
    // This will be set by Vercel environment variable
    return 'https://farm-management-production.up.railway.app/api'; // Production API URL
  }
  
  // Development
  return 'http://localhost:8000/api';
};

const API_BASE_URL = getApiUrl();

// Debug logging
// console.log('API Configuration:', {
//   NODE_ENV: process.env.NODE_ENV,
//   REACT_APP_API_URL: process.env.REACT_APP_API_URL,
//   API_BASE_URL
// });

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token if needed
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    } else if (error.code === 'NETWORK_ERROR' || !error.response) {
      // Handle network errors or API unavailable
      // You could show a toast notification here
    }
    return Promise.reject(error);
  }
);

export default api;
