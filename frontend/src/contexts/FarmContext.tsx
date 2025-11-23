import React, { createContext, useContext, useState, useCallback, useMemo, useEffect, ReactNode } from 'react';
import api from '../services/api';

interface Farm {
  id: number;
  name: string;
  location: string;
  description?: string;
  contact_person?: string;
  contact_phone: string;
  contact_email: string;
  is_active: boolean;
  total_houses?: number;
  active_houses?: number;
  workers?: Worker[];
  created_at: string;
  updated_at: string;
  owner: number;
  // Integration fields
  has_system_integration: boolean;
  integration_type: 'none' | 'rotem' | 'future_system';
  integration_status: 'active' | 'inactive' | 'error' | 'not_configured';
  last_sync?: string;
  is_integrated?: boolean;
  integration_display_name?: string;
  // Rotem-specific fields
  rotem_farm_id?: string;
  rotem_username?: string;
  rotem_password?: string;
  rotem_gateway_name?: string;
  rotem_gateway_alias?: string;
}

interface Worker {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
  receive_daily_tasks: boolean;
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
  fetchHouses: (_farmId?: number) => Promise<House[]>;
  fetchFarmTaskSummary: (_farmId: number) => Promise<void>;
  completeTask: (_taskId: number, _completedBy?: string, _notes?: string) => Promise<boolean>;
  createFarm: (_farmData: Partial<Farm>) => Promise<Farm | null>;
  createHouse: (_houseData: Partial<House>) => Promise<House | null>;
  updateFarm: (_id: number, _farmData: Partial<Farm>) => Promise<Farm | null>;
  updateHouse: (_id: number, _houseData: Partial<House>) => Promise<House | null>;
  deleteFarm: (_id: number) => Promise<boolean>;
  deleteHouse: (_id: number) => Promise<boolean>;
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

  // Fetch farms on mount if not already loaded
  useEffect(() => {
    if (farms.length === 0) {
      console.log('FarmProvider: Fetching farms on mount...');
      fetchFarms();
    }
  }, []);

  const fetchFarms = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('FarmContext: Fetching farms from API...');
      const response = await api.get('/farms/');
      console.log('FarmContext: API response:', response.data);
      // Handle paginated response - farms are in the 'results' property
      const farmsData = response.data.results || response.data;
      const farmsArray = Array.isArray(farmsData) ? farmsData : [];
      console.log('FarmContext: Processed farms:', farmsArray.length, farmsArray);
      setFarms(farmsArray);
    } catch (err: any) {
      console.error('FarmContext: Error fetching farms:', err);
      setError('Failed to fetch farms');
      setFarms([]); // Ensure farms is always an array
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHouses = useCallback(async (farmId?: number) => {
    setLoading(true);
    setError(null);
    try {
      const url = farmId ? `/farms/${farmId}/houses/` : '/houses/';
      console.log('FarmContext: Fetching houses from:', url);
      const response = await api.get(url);
      console.log('FarmContext: Houses API response:', response.data);
      // Handle paginated response - houses are in the 'results' property
      const housesData = response.data.results || response.data;
      const housesArray = Array.isArray(housesData) ? housesData : [];
      // Add farm_id to each house if not present (since we fetched for specific farm)
      const housesWithFarmId = housesArray.map(house => ({
        ...house,
        farm_id: house.farm_id || farmId || (house.farm && house.farm.id) || null
      }));
      console.log('FarmContext: Processed houses:', housesWithFarmId.length, housesWithFarmId);
      setHouses(housesWithFarmId);
      return housesWithFarmId;
    } catch (err: any) {
      console.error('FarmContext: Error fetching houses:', err);
      setError('Failed to fetch houses');
      setHouses([]); // Ensure houses is always an array
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFarmTaskSummary = useCallback(async (farmId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/farms/${farmId}/task-summary/`);
      setFarmTaskSummary(response.data);
    } catch (err) {
      setError('Failed to fetch farm task summary');
      setFarmTaskSummary(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const completeTask = useCallback(async (taskId: number, completedBy?: string, notes?: string): Promise<boolean> => {
    try {
      await api.post(`/tasks/${taskId}/complete/`, {
        completed_by: completedBy || 'user',
        notes: notes || ''
      });
      
      // Note: Farm task summary will be refreshed when the user navigates back to the farm detail page
      
      return true;
    } catch (err) {
      setError('Failed to complete task');
      return false;
    }
  }, []);

  const createFarm = useCallback(async (farmData: Partial<Farm>): Promise<Farm | null> => {
    try {
      const response = await api.post('/farms/', farmData);
      setFarms(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError('Failed to create farm');
      return null;
    }
  }, []);

  const createHouse = useCallback(async (houseData: Partial<House>): Promise<House | null> => {
    try {
      const response = await api.post('/houses/', houseData);
      setHouses(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError('Failed to create house');
      return null;
    }
  }, []);

  const updateFarm = useCallback(async (id: number, farmData: Partial<Farm>): Promise<Farm | null> => {
    try {
      const response = await api.put(`/farms/${id}/`, farmData);
      setFarms(prev => prev.map(farm => farm.id === id ? response.data : farm));
      return response.data;
    } catch (err) {
      setError('Failed to update farm');
      return null;
    }
  }, []);

  const updateHouse = useCallback(async (id: number, houseData: Partial<House>): Promise<House | null> => {
    try {
      const response = await api.put(`/houses/${id}/`, houseData);
      setHouses(prev => prev.map(house => house.id === id ? response.data : house));
      return response.data;
    } catch (err) {
      setError('Failed to update house');
      return null;
    }
  }, []);

  const deleteFarm = useCallback(async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/farms/${id}/`);
      setFarms(prev => prev.filter(farm => farm.id !== id));
      return true;
    } catch (err) {
      setError('Failed to delete farm');
      return false;
    }
  }, []);

  const deleteHouse = useCallback(async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/houses/${id}/`);
      setHouses(prev => prev.filter(house => house.id !== id));
      return true;
    } catch (err) {
      setError('Failed to delete house');
      return false;
    }
  }, []);

  const value = useMemo(() => ({
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
  }), [
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
  ]);

  return (
    <FarmContext.Provider value={value}>
      {children}
    </FarmContext.Provider>
  );
};
