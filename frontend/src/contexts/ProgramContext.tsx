import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import api from '../services/api';

export interface ProgramTask {
  id: number;
  day: number;
  task_type: 'daily' | 'weekly' | 'one_time' | 'recurring';
  title: string;
  description: string;
  instructions: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  estimated_duration: number;
  is_required: boolean;
  requires_confirmation: boolean;
  recurring_days: number[];
  is_recurring: boolean;
  is_setup_task: boolean;
  created_at: string;
  updated_at: string;
}

export interface Program {
  id: number;
  name: string;
  description: string;
  duration_days: number;
  is_active: boolean;
  is_default: boolean;
  total_tasks: number;
  tasks?: ProgramTask[];
  created_at: string;
  updated_at: string;
}

interface ProgramContextType {
  programs: Program[];
  loading: boolean;
  error: string | null;
  fetchPrograms: () => Promise<void>;
  createProgram: (programData: Partial<Program>) => Promise<boolean>;
  updateProgram: (id: number, programData: Partial<Program>) => Promise<boolean>;
  deleteProgram: (id: number) => Promise<boolean>;
  copyProgram: (id: number, newName?: string) => Promise<boolean>;
  getProgramTasks: (programId: number) => Promise<ProgramTask[]>;
  createProgramTask: (programId: number, taskData: Partial<ProgramTask>) => Promise<boolean>;
  updateProgramTask: (id: number, taskData: Partial<ProgramTask>) => Promise<boolean>;
  deleteProgramTask: (id: number) => Promise<boolean>;
  getDefaultProgram: () => Promise<Program | null>;
}

const ProgramContext = createContext<ProgramContextType | undefined>(undefined);

export const useProgram = () => {
  const context = useContext(ProgramContext);
  if (context === undefined) {
    throw new Error('useProgram must be used within a ProgramProvider');
  }
  return context;
};

interface ProgramProviderProps {
  children: ReactNode;
}

export const ProgramProvider: React.FC<ProgramProviderProps> = ({ children }) => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPrograms = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/programs/');
      setPrograms(Array.isArray(response.data) ? response.data : response.data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch programs');
      console.error('Error fetching programs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createProgram = useCallback(async (programData: Partial<Program>): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.post('/api/programs/', programData);
      setPrograms(prev => [...prev, response.data]);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create program');
      console.error('Error creating program:', err);
      return false;
    }
  }, []);

  const updateProgram = useCallback(async (id: number, programData: Partial<Program>): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.put(`/api/programs/${id}/`, programData);
      setPrograms(prev => prev.map(program => 
        program.id === id ? response.data : program
      ));
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update program');
      console.error('Error updating program:', err);
      return false;
    }
  }, []);

  const deleteProgram = useCallback(async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.delete(`/api/programs/${id}/`);
      setPrograms(prev => prev.filter(program => program.id !== id));
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete program');
      console.error('Error deleting program:', err);
      return false;
    }
  }, []);

  const copyProgram = useCallback(async (id: number, newName?: string): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.post(`/api/programs/${id}/copy/`, { name: newName });
      setPrograms(prev => [...prev, response.data]);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to copy program');
      console.error('Error copying program:', err);
      return false;
    }
  }, []);

  const getProgramTasks = useCallback(async (programId: number): Promise<ProgramTask[]> => {
    try {
      setError(null);
      const response = await api.get(`/api/programs/${programId}/tasks/`);
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch program tasks');
      console.error('Error fetching program tasks:', err);
      return [];
    }
  }, []);

  const createProgramTask = useCallback(async (programId: number, taskData: Partial<ProgramTask>): Promise<boolean> => {
    try {
      setError(null);
      await api.post('/api/program-tasks/', { ...taskData, program_id: programId });
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create program task');
      console.error('Error creating program task:', err);
      return false;
    }
  }, []);

  const updateProgramTask = useCallback(async (id: number, taskData: Partial<ProgramTask>): Promise<boolean> => {
    try {
      setError(null);
      await api.put(`/api/program-tasks/${id}/`, taskData);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update program task');
      console.error('Error updating program task:', err);
      return false;
    }
  }, []);

  const deleteProgramTask = useCallback(async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.delete(`/api/program-tasks/${id}/`);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete program task');
      console.error('Error deleting program task:', err);
      return false;
    }
  }, []);

  const getDefaultProgram = useCallback(async (): Promise<Program | null> => {
    try {
      setError(null);
      const response = await api.get('/api/programs/default/');
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch default program');
      console.error('Error fetching default program:', err);
      return null;
    }
  }, []);

  const value: ProgramContextType = {
    programs,
    loading,
    error,
    fetchPrograms,
    createProgram,
    updateProgram,
    deleteProgram,
    copyProgram,
    getProgramTasks,
    createProgramTask,
    updateProgramTask,
    deleteProgramTask,
    getDefaultProgram,
  };

  return (
    <ProgramContext.Provider value={value}>
      {children}
    </ProgramContext.Provider>
  );
};
