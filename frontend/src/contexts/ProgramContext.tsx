import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
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
  farm_count?: number;
  tasks?: ProgramTask[];
  created_at: string;
  updated_at: string;
}

interface ProgramContextType {
  programs: Program[];
  loading: boolean;
  error: string | null;
  fetchPrograms: () => Promise<void>;
  createProgram: (_programData: Partial<Program>) => Promise<boolean>;
  updateProgram: (_id: number, _programData: Partial<Program>) => Promise<{ success: boolean; changeData?: any }>;
  deleteProgram: (_id: number) => Promise<boolean>;
  copyProgram: (_id: number, _newName?: string) => Promise<boolean>;
  getProgramTasks: (_programId: number) => Promise<ProgramTask[]>;
  createProgramTask: (_programId: number, _taskData: Partial<ProgramTask>) => Promise<boolean>;
  updateProgramTask: (_id: number, _taskData: Partial<ProgramTask>) => Promise<boolean>;
  deleteProgramTask: (_id: number) => Promise<boolean>;
  getDefaultProgram: () => Promise<Program | null>;
  handleProgramChange: (_changeLogId: number, _choice: 'retroactive' | 'next_flock') => Promise<boolean>;
  getPendingChanges: () => Promise<any[]>;
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
      const response = await api.get('/programs/');
      setPrograms(Array.isArray(response.data) ? response.data : response.data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch programs');
    } finally {
      setLoading(false);
    }
  }, []);

  const createProgram = useCallback(async (programData: Partial<Program>): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.post('/programs/', programData);
      setPrograms(prev => [...prev, response.data]);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create program');
      return false;
    }
  }, []);

  const updateProgram = useCallback(async (id: number, programData: Partial<Program>): Promise<{ success: boolean; changeData?: any }> => {
    try {
      setError(null);
      const response = await api.put(`/programs/${id}/`, programData);
      setPrograms(prev => prev.map(program => 
        program.id === id ? response.data : program
      ));
      
      return {
        success: true,
        changeData: response.data.change_detected ? {
          change_detected: response.data.change_detected,
          change_log_id: response.data.change_log_id,
          impact_analysis: response.data.impact_analysis
        } : undefined
      };
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update program');
      return { success: false };
    }
  }, []);

  const deleteProgram = useCallback(async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.delete(`/programs/${id}/`);
      setPrograms(prev => prev.filter(program => program.id !== id));
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete program');
      return false;
    }
  }, []);

  const copyProgram = useCallback(async (id: number, newName?: string): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.post(`/programs/${id}/copy/`, { name: newName });
      setPrograms(prev => [...prev, response.data]);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to copy program');
      return false;
    }
  }, []);

  const getProgramTasks = useCallback(async (programId: number): Promise<ProgramTask[]> => {
    try {
      setError(null);
      const response = await api.get(`/programs/${programId}/tasks/`);
      return Array.isArray(response.data) ? response.data : response.data.results || [];
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch program tasks');
      return [];
    }
  }, []);

  const createProgramTask = useCallback(async (programId: number, taskData: Partial<ProgramTask>): Promise<boolean> => {
    try {
      setError(null);
      await api.post('/program-tasks/', { ...taskData, program_id: programId });
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create program task');
      return false;
    }
  }, []);

  const updateProgramTask = useCallback(async (id: number, taskData: Partial<ProgramTask>): Promise<boolean> => {
    try {
      setError(null);
      await api.put(`/program-tasks/${id}/`, taskData);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update program task');
      return false;
    }
  }, []);

  const deleteProgramTask = useCallback(async (id: number): Promise<boolean> => {
    try {
      setError(null);
      await api.delete(`/program-tasks/${id}/`);
      return true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete program task');
      return false;
    }
  }, []);

  const getDefaultProgram = useCallback(async (): Promise<Program | null> => {
    try {
      setError(null);
      const response = await api.get('/programs/default/');
      return response.data;
    } catch (err: any) {
      // If default program doesn't exist, try to create one
      if (err.response?.status === 404) {
        try {
          // Try to trigger default program creation
          await api.post('/programs/ensure-default/');
          // Retry fetching
          const retryResponse = await api.get('/programs/default/');
          return retryResponse.data;
        } catch (retryErr: any) {
          setError('No default program found and unable to create one');
          return null;
        }
      }
      setError(err.response?.data?.error || 'Failed to fetch default program');
      return null;
    }
  }, []);

  const handleProgramChange = useCallback(async (changeLogId: number, choice: 'retroactive' | 'next_flock'): Promise<boolean> => {
    try {
      setError(null);
      const response = await api.post(`/program-changes/${changeLogId}/handle/`, { choice });
      return response.data.processed || true;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to handle program change');
      return false;
    }
  }, []);

  const getPendingChanges = useCallback(async (): Promise<any[]> => {
    try {
      setError(null);
      const response = await api.get('/program-changes/pending/');
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch pending changes');
      return [];
    }
  }, []);

  const value: ProgramContextType = useMemo(() => ({
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
    handleProgramChange,
    getPendingChanges,
  }), [
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
    handleProgramChange,
    getPendingChanges,
  ]);

  return (
    <ProgramContext.Provider value={value}>
      {children}
    </ProgramContext.Provider>
  );
};
