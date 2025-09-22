import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
import api from '../services/api';

interface Worker {
  id: number;
  farm: number;
  name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
  receive_daily_tasks: boolean;
  created_at: string;
  updated_at: string;
}

interface WorkerContextType {
  workers: Worker[];
  loading: boolean;
  error: string | null;
  fetchWorkers: (_farmId?: number) => Promise<void>;
  createWorker: (_workerData: Partial<Worker>) => Promise<boolean>;
  updateWorker: (_id: number, _workerData: Partial<Worker>) => Promise<boolean>;
  deleteWorker: (_id: number) => Promise<boolean>;
  getFarmWorkers: (_farmId: number) => Promise<Worker[]>;
}

const WorkerContext = createContext<WorkerContextType | undefined>(undefined);

export const useWorker = () => {
  const context = useContext(WorkerContext);
  if (context === undefined) {
    throw new Error('useWorker must be used within a WorkerProvider');
  }
  return context;
};

interface WorkerProviderProps {
  children: ReactNode;
}

export const WorkerProvider: React.FC<WorkerProviderProps> = ({ children }) => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkers = useCallback(async (farmId?: number) => {
    setLoading(true);
    setError(null);
    try {
      const url = farmId ? `/workers/?farm_id=${farmId}` : '/workers/';
      const response = await api.get(url);
      
      // Handle paginated response format
      let workersData = [];
      if (response.data && typeof response.data === 'object') {
        if (Array.isArray(response.data)) {
          // Direct array response
          workersData = response.data;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          // Paginated response with results array
          workersData = response.data.results;
        }
      }
      
      setWorkers(workersData);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch workers');
      setWorkers([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, []);

  const createWorker = useCallback(async (workerData: Partial<Worker>): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/workers/', workerData);
      setWorkers(prev => Array.isArray(prev) ? [...prev, response.data] : [response.data]);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create worker');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateWorker = useCallback(async (id: number, workerData: Partial<Worker>): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.put(`/workers/${id}/`, workerData);
      setWorkers(prev => Array.isArray(prev) ? prev.map(worker => 
        worker.id === id ? response.data : worker
      ) : []);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update worker');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteWorker = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/workers/${id}/`);
      setWorkers(prev => Array.isArray(prev) ? prev.filter(worker => worker.id !== id) : []);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete worker');
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const getFarmWorkers = useCallback(async (farmId: number): Promise<Worker[]> => {
    try {
      const response = await api.get(`/farms/${farmId}/workers/`);
      
      // Handle paginated response format
      if (response.data && typeof response.data === 'object') {
        if (Array.isArray(response.data)) {
          // Direct array response
          return response.data;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          // Paginated response with results array
          return response.data.results;
        }
      }
      
      return [];
    } catch (err: any) {
      return [];
    }
  }, []);

  const value: WorkerContextType = useMemo(() => ({
    workers,
    loading,
    error,
    fetchWorkers,
    createWorker,
    updateWorker,
    deleteWorker,
    getFarmWorkers,
  }), [
    workers,
    loading,
    error,
    fetchWorkers,
    createWorker,
    updateWorker,
    deleteWorker,
    getFarmWorkers,
  ]);

  return (
    <WorkerContext.Provider value={value}>
      {children}
    </WorkerContext.Provider>
  );
};
