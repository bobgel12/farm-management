import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import {
  IntegratedFarm,
  RotemDataPoint,
  FarmDataSummary,
  RotemScrapeLog,
  MLPrediction,
  FarmDashboardData
} from '../types/rotem';
import { rotemApi } from '../services/rotemApi';
import { useAuth } from './AuthContext';

interface RotemState {
  farms: IntegratedFarm[];
  dataSummary: FarmDataSummary[];
  recentData: RotemDataPoint[];
  scrapeLogs: RotemScrapeLog[];
  predictions: MLPrediction[];
  selectedFarm: string | null;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

type RotemAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_FARMS'; payload: IntegratedFarm[] }
  | { type: 'ADD_FARM'; payload: IntegratedFarm }
  | { type: 'UPDATE_FARM'; payload: IntegratedFarm }
  | { type: 'DELETE_FARM'; payload: string }
  | { type: 'SET_DATA_SUMMARY'; payload: FarmDataSummary[] }
  | { type: 'SET_RECENT_DATA'; payload: RotemDataPoint[] }
  | { type: 'SET_SCRAPE_LOGS'; payload: RotemScrapeLog[] }
  | { type: 'SET_PREDICTIONS'; payload: MLPrediction[] }
  | { type: 'SET_SELECTED_FARM'; payload: string | null }
  | { type: 'SET_LAST_UPDATE'; payload: string }
  | { type: 'REFRESH_DATA' };

const initialState: RotemState = {
  farms: [],
  dataSummary: [],
  recentData: [],
  scrapeLogs: [],
  predictions: [],
  selectedFarm: null,
  loading: false,
  error: null,
  lastUpdate: null,
};

function rotemReducer(state: RotemState, action: RotemAction): RotemState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_FARMS':
      return { ...state, farms: action.payload, loading: false };
    case 'ADD_FARM':
      return { ...state, farms: [...state.farms, action.payload] };
    case 'UPDATE_FARM':
      return {
        ...state,
        farms: state.farms.map(farm =>
          farm.farm_id === action.payload.farm_id ? action.payload : farm
        ),
      };
    case 'DELETE_FARM':
      return {
        ...state,
        farms: state.farms.filter(farm => farm.farm_id !== action.payload),
      };
    case 'SET_DATA_SUMMARY':
      return { ...state, dataSummary: action.payload };
    case 'SET_RECENT_DATA':
      return { ...state, recentData: action.payload };
    case 'SET_SCRAPE_LOGS':
      return { ...state, scrapeLogs: action.payload };
    case 'SET_PREDICTIONS':
      return { ...state, predictions: action.payload };
    case 'SET_SELECTED_FARM':
      return { ...state, selectedFarm: action.payload };
    case 'SET_LAST_UPDATE':
      return { ...state, lastUpdate: action.payload };
    case 'REFRESH_DATA':
      return { ...state, loading: true };
    default:
      return state;
  }
}

interface RotemContextType {
  state: RotemState;
  // Farm Management
  loadFarms: () => Promise<void>;
  addFarm: (farmData: any) => Promise<void>;
  updateFarm: (farmId: string, farmData: any) => Promise<void>;
  deleteFarm: (farmId: string) => Promise<void>;
  // Data Management
  loadDataSummary: () => Promise<void>;
  loadRecentData: () => Promise<void>;
  loadFarmData: (farmId: string) => Promise<RotemDataPoint[]>;
  // Scraper Operations
  scrapeFarm: (farmId: string) => Promise<void>;
  scrapeAllFarms: () => Promise<void>;
  loadScrapeLogs: () => Promise<void>;
  // Predictions
  loadPredictions: () => Promise<void>;
  loadAnomalies: () => Promise<void>;
  // Utility
  selectFarm: (farmId: string | null) => void;
  refreshAllData: () => Promise<void>;
  getFarmDashboard: (farmId: string) => Promise<FarmDashboardData>;
  clearError: () => void;
}

const RotemContext = createContext<RotemContextType | undefined>(undefined);

export const useRotem = () => {
  const context = useContext(RotemContext);
  if (context === undefined) {
    throw new Error('useRotem must be used within a RotemProvider');
  }
  return context;
};

interface RotemProviderProps {
  children: ReactNode;
}

export const RotemProvider: React.FC<RotemProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(rotemReducer, initialState);
  const { user } = useAuth();

  // Farm Management
  const loadFarms = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await rotemApi.getFarms();
      // Handle paginated response - extract results array
      const farms = Array.isArray(response) ? response : ((response as any).results || []);
      dispatch({ type: 'SET_FARMS', payload: farms });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load farms' });
    }
  }, []);

  const addFarm = async (farmData: any) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const newFarm = await rotemApi.addFarm(farmData);
      dispatch({ type: 'ADD_FARM', payload: newFarm });
      await loadDataSummary(); // Refresh summary
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to add farm' });
    }
  };

  const updateFarm = async (farmId: string, farmData: any) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const updatedFarm = await rotemApi.updateFarm(farmId, farmData);
      dispatch({ type: 'UPDATE_FARM', payload: updatedFarm });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to update farm' });
    }
  };

  const deleteFarm = async (farmId: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      await rotemApi.deleteFarm(farmId);
      dispatch({ type: 'DELETE_FARM', payload: farmId });
      await loadDataSummary(); // Refresh summary
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete farm' });
    }
  };

  // Data Management
  const loadDataSummary = useCallback(async () => {
    try {
      const summary = await rotemApi.getDataSummary();
      dispatch({ type: 'SET_DATA_SUMMARY', payload: summary });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load data summary' });
    }
  }, []);

  const loadRecentData = useCallback(async () => {
    try {
      const data = await rotemApi.getRecentData();
      dispatch({ type: 'SET_RECENT_DATA', payload: data });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load recent data' });
    }
  }, []);

  const loadFarmData = async (farmId: string): Promise<RotemDataPoint[]> => {
    try {
      return await rotemApi.getDataByFarm(farmId);
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load farm data' });
      return [];
    }
  };

  // Scraper Operations
  const scrapeFarm = async (farmId: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      await rotemApi.scrapeFarm(farmId);
      await loadDataSummary();
      await loadRecentData();
      await loadScrapeLogs();
      dispatch({ type: 'SET_LAST_UPDATE', payload: new Date().toISOString() });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to scrape farm data' });
    }
  };

  const scrapeAllFarms = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      await rotemApi.scrapeAllFarms();
      await loadDataSummary();
      await loadRecentData();
      await loadScrapeLogs();
      dispatch({ type: 'SET_LAST_UPDATE', payload: new Date().toISOString() });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to scrape all farms' });
    }
  };

  const loadScrapeLogs = async () => {
    try {
      const logs = await rotemApi.getRecentLogs();
      dispatch({ type: 'SET_SCRAPE_LOGS', payload: logs });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load scrape logs' });
    }
  };

  // Predictions
  const loadPredictions = async () => {
    try {
      const predictions = await rotemApi.getPredictions();
      dispatch({ type: 'SET_PREDICTIONS', payload: predictions });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load predictions' });
    }
  };

  const loadAnomalies = async () => {
    try {
      const anomalies = await rotemApi.getAnomalies();
      dispatch({ type: 'SET_PREDICTIONS', payload: anomalies });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load anomalies' });
    }
  };

  // Utility Functions
  const selectFarm = (farmId: string | null) => {
    dispatch({ type: 'SET_SELECTED_FARM', payload: farmId });
  };

  const refreshAllData = async () => {
    try {
      dispatch({ type: 'REFRESH_DATA' });
      await Promise.all([
        loadFarms(),
        loadDataSummary(),
        loadRecentData(),
        loadScrapeLogs(),
        loadPredictions(),
      ]);
      dispatch({ type: 'SET_LAST_UPDATE', payload: new Date().toISOString() });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Failed to refresh data' });
    }
  };

  const getFarmDashboard = useCallback(async (farmId: string): Promise<FarmDashboardData> => {
    try {
      // Removed debug console.log statements
      const result = await rotemApi.getFarmDashboard(farmId);
      return result;
    } catch (error) {
      console.error('getFarmDashboard error:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load farm dashboard' });
      throw error;
    }
  }, []);

  const clearError = () => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  // Auto-refresh data every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      if (state.farms.length > 0) {
        loadDataSummary();
        loadRecentData();
      }
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, []); // Remove state.farms.length dependency to prevent infinite loop

  // Load initial data only when user is authenticated
  useEffect(() => {
    if (user) {
      refreshAllData();
    }
  }, [user?.id]); // Use user.id instead of entire user object to prevent infinite loop

  const value: RotemContextType = {
    state,
    loadFarms,
    addFarm,
    updateFarm,
    deleteFarm,
    loadDataSummary,
    loadRecentData,
    loadFarmData,
    scrapeFarm,
    scrapeAllFarms,
    loadScrapeLogs,
    loadPredictions,
    loadAnomalies,
    selectFarm,
    refreshAllData,
    getFarmDashboard,
    clearError,
  };

  return (
    <RotemContext.Provider value={value}>
      {children}
    </RotemContext.Provider>
  );
};
