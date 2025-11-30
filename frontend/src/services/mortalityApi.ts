import axios from 'axios';
import { MortalityRecord, MortalityRecordCreate, MortalitySummary, MortalityTrend } from '../types';

// Use the same pattern as api.ts - REACT_APP_API_URL already includes /api
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  return 'http://localhost:8002/api';
};

const API_BASE_URL = getApiUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export interface MortalityFilters {
  flock_id?: number;
  house_id?: number;
  farm_id?: number;
  start_date?: string;
  end_date?: string;
}

export const mortalityApi = {
  // Get mortality records with optional filters
  getRecords: async (filters: MortalityFilters = {}): Promise<MortalityRecord[]> => {
    const params = new URLSearchParams();
    if (filters.flock_id) params.append('flock_id', filters.flock_id.toString());
    if (filters.house_id) params.append('house_id', filters.house_id.toString());
    if (filters.farm_id) params.append('farm_id', filters.farm_id.toString());
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    
    const response = await api.get(`/mortality/?${params.toString()}`);
    // Handle paginated response
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    }
    // Handle non-paginated response (direct array)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    // Fallback to empty array
    return [];
  },

  // Get a single mortality record
  getRecord: async (id: number): Promise<MortalityRecord> => {
    const response = await api.get(`/mortality/${id}/`);
    return response.data;
  },

  // Create a new mortality record
  createRecord: async (data: MortalityRecordCreate): Promise<MortalityRecord> => {
    const response = await api.post('/mortality/', data);
    return response.data;
  },

  // Update a mortality record
  updateRecord: async (id: number, data: Partial<MortalityRecordCreate>): Promise<MortalityRecord> => {
    const response = await api.patch(`/mortality/${id}/`, data);
    return response.data;
  },

  // Delete a mortality record
  deleteRecord: async (id: number): Promise<void> => {
    await api.delete(`/mortality/${id}/`);
  },

  // Quick entry (just total count)
  quickEntry: async (data: {
    flock_id: number;
    house_id: number;
    total_deaths: number;
    record_date?: string;
    notes?: string;
  }): Promise<{ record: MortalityRecord; created: boolean; message: string }> => {
    const response = await api.post('/mortality/quick-entry/', data);
    return response.data;
  },

  // Get mortality summary for a flock
  getSummary: async (flockId: number): Promise<MortalitySummary> => {
    const response = await api.get(`/mortality/summary/?flock_id=${flockId}`);
    return response.data;
  },

  // Get mortality trends
  getTrends: async (params: {
    flock_id?: number;
    house_id?: number;
    days?: number;
  }): Promise<{
    start_date: string;
    end_date: string;
    data: MortalityTrend[];
    total_records: number;
  }> => {
    const queryParams = new URLSearchParams();
    if (params.flock_id) queryParams.append('flock_id', params.flock_id.toString());
    if (params.house_id) queryParams.append('house_id', params.house_id.toString());
    if (params.days) queryParams.append('days', params.days.toString());
    
    const response = await api.get(`/mortality/trends/?${queryParams.toString()}`);
    return response.data;
  },
};

export default mortalityApi;

