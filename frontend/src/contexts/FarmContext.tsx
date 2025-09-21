import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../services/api';

interface Farm {
  id: number;
  name: string;
  location: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  is_active: boolean;
  total_houses: number;
  active_houses: number;
  created_at: string;
  updated_at: string;
}

interface House {
  id: number;
  farm_id: number;
  farm_name: string;
  house_number: number;
  chicken_in_date: string;
  chicken_out_date: string | null;
  current_day: number | null;
  days_remaining: number | null;
  status: string;
  is_active: boolean;
}

interface TaskSummary {
  total: number;
  completed: number;
  pending: number;
  overdue: number;
  today: number;
}

interface PendingTask {
  id: number;
  task_name: string;
  description: string;
  day_offset: number;
  task_type: string;
  is_today: boolean;
}

interface HouseTaskSummary {
  id: number;
  house_number: number;
  current_day: number | null;
  status: string;
  chicken_in_date: string;
  chicken_out_date: string | null;
  tasks: TaskSummary;
  pending_tasks: PendingTask[];
}

interface FarmTaskSummary {
  farm_name: string;
  total_houses: number;
  houses: HouseTaskSummary[];
}

interface FarmContextType {
  farms: Farm[];
  houses: House[];
  farmTaskSummary: FarmTaskSummary | null;
  loading: boolean;
  error: string | null;
  fetchFarms: () => Promise<void>;
  fetchHouses: (farmId?: number) => Promise<void>;
  fetchFarmTaskSummary: (farmId: number) => Promise<void>;
  completeTask: (taskId: number, completedBy?: string, notes?: string) => Promise<boolean>;
  createFarm: (farmData: Partial<Farm>) => Promise<Farm | null>;
  createHouse: (houseData: Partial<House>) => Promise<House | null>;
  updateFarm: (id: number, farmData: Partial<Farm>) => Promise<Farm | null>;
  updateHouse: (id: number, houseData: Partial<House>) => Promise<House | null>;
  deleteFarm: (id: number) => Promise<boolean>;
  deleteHouse: (id: number) => Promise<boolean>;
}

const FarmContext = createContext<FarmContextType | undefined>(undefined);

export const useFarm = () => {
  const context = useContext(FarmContext);
  if (context === undefined) {
    throw new Error('useFarm must be used within a FarmProvider');
  }
  return context;
};

interface FarmProviderProps {
  children: ReactNode;
}

export const FarmProvider: React.FC<FarmProviderProps> = ({ children }) => {
  const [farms, setFarms] = useState<Farm[]>([]);
  const [houses, setHouses] = useState<House[]>([]);
  const [farmTaskSummary, setFarmTaskSummary] = useState<FarmTaskSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFarms = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/farms/');
      // Handle paginated response - farms are in the 'results' property
      const farmsData = response.data.results || response.data;
      setFarms(Array.isArray(farmsData) ? farmsData : []);
    } catch (err) {
      setError('Failed to fetch farms');
      console.error('Error fetching farms:', err);
      setFarms([]); // Ensure farms is always an array
    } finally {
      setLoading(false);
    }
  };

  const fetchHouses = async (farmId?: number) => {
    setLoading(true);
    setError(null);
    try {
      const url = farmId ? `/farms/${farmId}/houses/` : '/houses/';
      const response = await api.get(url);
      // Handle paginated response - houses are in the 'results' property
      const housesData = response.data.results || response.data;
      setHouses(Array.isArray(housesData) ? housesData : []);
    } catch (err) {
      setError('Failed to fetch houses');
      console.error('Error fetching houses:', err);
      setHouses([]); // Ensure houses is always an array
    } finally {
      setLoading(false);
    }
  };

  const fetchFarmTaskSummary = async (farmId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/farms/${farmId}/task-summary/`);
      setFarmTaskSummary(response.data);
    } catch (err) {
      setError('Failed to fetch farm task summary');
      console.error('Error fetching farm task summary:', err);
      setFarmTaskSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const completeTask = async (taskId: number, completedBy?: string, notes?: string): Promise<boolean> => {
    try {
      const response = await api.post(`/tasks/${taskId}/complete/`, {
        completed_by: completedBy || 'user',
        notes: notes || ''
      });
      
      // Note: Farm task summary will be refreshed when the user navigates back to the farm detail page
      
      return true;
    } catch (err) {
      setError('Failed to complete task');
      console.error('Error completing task:', err);
      return false;
    }
  };

  const createFarm = async (farmData: Partial<Farm>): Promise<Farm | null> => {
    try {
      const response = await api.post('/farms/', farmData);
      setFarms(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError('Failed to create farm');
      console.error('Error creating farm:', err);
      return null;
    }
  };

  const createHouse = async (houseData: Partial<House>): Promise<House | null> => {
    try {
      const response = await api.post('/houses/', houseData);
      setHouses(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError('Failed to create house');
      console.error('Error creating house:', err);
      return null;
    }
  };

  const updateFarm = async (id: number, farmData: Partial<Farm>): Promise<Farm | null> => {
    try {
      const response = await api.put(`/farms/${id}/`, farmData);
      setFarms(prev => prev.map(farm => farm.id === id ? response.data : farm));
      return response.data;
    } catch (err) {
      setError('Failed to update farm');
      console.error('Error updating farm:', err);
      return null;
    }
  };

  const updateHouse = async (id: number, houseData: Partial<House>): Promise<House | null> => {
    try {
      const response = await api.put(`/houses/${id}/`, houseData);
      setHouses(prev => prev.map(house => house.id === id ? response.data : house));
      return response.data;
    } catch (err) {
      setError('Failed to update house');
      console.error('Error updating house:', err);
      return null;
    }
  };

  const deleteFarm = async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/farms/${id}/`);
      setFarms(prev => prev.filter(farm => farm.id !== id));
      return true;
    } catch (err) {
      setError('Failed to delete farm');
      console.error('Error deleting farm:', err);
      return false;
    }
  };

  const deleteHouse = async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/houses/${id}/`);
      setHouses(prev => prev.filter(house => house.id !== id));
      return true;
    } catch (err) {
      setError('Failed to delete house');
      console.error('Error deleting house:', err);
      return false;
    }
  };

  const value = {
    farms,
    houses,
    farmTaskSummary,
    loading,
    error,
    fetchFarms,
    fetchHouses,
    fetchFarmTaskSummary,
    completeTask,
    createFarm,
    createHouse,
    updateFarm,
    updateHouse,
    deleteFarm,
    deleteHouse,
  };

  return (
    <FarmContext.Provider value={value}>
      {children}
    </FarmContext.Provider>
  );
};
