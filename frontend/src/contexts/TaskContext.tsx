import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';

interface Task {
  id: number;
  house_name: string;
  farm_name: string;
  day_offset: number;
  task_name: string;
  description: string;
  task_type: string;
  is_completed: boolean;
  completed_at: string | null;
  completed_by: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

interface TaskContextType {
  tasks: Task[];
  todayTasks: Task[];
  upcomingTasks: Task[];
  loading: boolean;
  error: string | null;
  fetchTasks: (houseId?: number) => Promise<void>;
  fetchTodayTasks: (houseId: number) => Promise<void>;
  fetchUpcomingTasks: (houseId: number, days?: number) => Promise<void>;
  completeTask: (taskId: number, completedBy?: string, notes?: string) => Promise<boolean>;
  generateTasks: (houseId: number) => Promise<boolean>;
}

const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const useTask = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTask must be used within a TaskProvider');
  }
  return context;
};

interface TaskProviderProps {
  children: ReactNode;
}

export const TaskProvider: React.FC<TaskProviderProps> = ({ children }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [todayTasks, setTodayTasks] = useState<Task[]>([]);
  const [upcomingTasks, setUpcomingTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async (houseId?: number) => {
    setLoading(true);
    setError(null);
    try {
      const url = houseId ? `/houses/${houseId}/tasks/` : '/tasks/';
      const response = await api.get(url);
      setTasks(response.data);
    } catch (err) {
      setError('Failed to fetch tasks');
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTodayTasks = async (houseId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/houses/${houseId}/tasks/today/`);
      setTodayTasks(response.data);
    } catch (err) {
      setError('Failed to fetch today\'s tasks');
      console.error('Error fetching today\'s tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUpcomingTasks = async (houseId: number, days: number = 7) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/houses/${houseId}/tasks/upcoming/?days=${days}`);
      setUpcomingTasks(response.data);
    } catch (err) {
      setError('Failed to fetch upcoming tasks');
      console.error('Error fetching upcoming tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId: number, completedBy: string = '', notes: string = ''): Promise<boolean> => {
    try {
      const response = await api.post(`/tasks/${taskId}/complete/`, {
        completed_by: completedBy,
        notes: notes
      });
      
      // Update the task in all relevant state arrays
      const updateTaskInArray = (taskArray: Task[]) => 
        taskArray.map(task => task.id === taskId ? response.data : task);
      
      setTasks(updateTaskInArray);
      setTodayTasks(updateTaskInArray);
      setUpcomingTasks(updateTaskInArray);
      
      return true;
    } catch (err) {
      setError('Failed to complete task');
      console.error('Error completing task:', err);
      return false;
    }
  };

  const generateTasks = async (houseId: number): Promise<boolean> => {
    try {
      await api.post(`/houses/${houseId}/tasks/generate/`);
      // Refresh tasks after generation
      await fetchTasks(houseId);
      return true;
    } catch (err) {
      setError('Failed to generate tasks');
      console.error('Error generating tasks:', err);
      return false;
    }
  };

  const value = {
    tasks,
    todayTasks,
    upcomingTasks,
    loading,
    error,
    fetchTasks,
    fetchTodayTasks,
    fetchUpcomingTasks,
    completeTask,
    generateTasks,
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
};
