import React, { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react';
import { flocksApi } from '../services/flocksApi';
import { useOrganization } from './OrganizationContext';
import {
  Breed,
  Flock,
  FlockPerformance,
  FlockComparison,
} from '../types';

interface FlockContextType {
  breeds: Breed[];
  flocks: Flock[];
  currentFlock: Flock | null;
  performanceRecords: FlockPerformance[];
  comparisons: FlockComparison[];
  loading: boolean;
  error: string | null;
  setCurrentFlock: (flock: Flock | null) => void;
  fetchBreeds: () => Promise<void>;
  fetchFlocks: (params?: {
    house_id?: number;
    farm_id?: number;
    organization_id?: string;
    status?: string;
    is_active?: boolean;
    breed_id?: number;
  }) => Promise<void>;
  fetchFlock: (id: number) => Promise<Flock>;
  fetchFlockSummary: (id: number) => Promise<any>;
  fetchFlockPerformance: (id: number) => Promise<void>;
  fetchPerformanceRecords: (flockId?: number) => Promise<void>;
  fetchComparisons: (organizationId?: string) => Promise<void>;
  createFlock: (data: Partial<Flock>) => Promise<Flock>;
  updateFlock: (id: number, data: Partial<Flock>) => Promise<Flock>;
  deleteFlock: (id: number) => Promise<void>;
  addPerformanceRecord: (flockId: number, data: Partial<FlockPerformance>) => Promise<FlockPerformance>;
  calculatePerformance: (flockId: number, recordDate?: string) => Promise<FlockPerformance>;
  completeFlock: (id: number, data?: { actual_harvest_date?: string; final_count?: number }) => Promise<Flock>;
  createComparison: (data: Partial<FlockComparison>) => Promise<FlockComparison>;
  calculateComparison: (id: number, metrics?: string[]) => Promise<any>;
  createBreed: (data: Partial<Breed>) => Promise<Breed>;
  updateBreed: (id: number, data: Partial<Breed>) => Promise<Breed>;
}

const FlockContext = createContext<FlockContextType | undefined>(undefined);

export const useFlock = () => {
  const context = useContext(FlockContext);
  if (context === undefined) {
    throw new Error('useFlock must be used within a FlockProvider');
  }
  return context;
};

interface FlockProviderProps {
  children: ReactNode;
}

export const FlockProvider: React.FC<FlockProviderProps> = ({ children }) => {
  const [breeds, setBreeds] = useState<Breed[]>([]);
  const [flocks, setFlocks] = useState<Flock[]>([]);
  const [currentFlock, setCurrentFlock] = useState<Flock | null>(null);
  const [performanceRecords, setPerformanceRecords] = useState<FlockPerformance[]>([]);
  const [comparisons, setComparisons] = useState<FlockComparison[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get current organization from context
  const { currentOrganization } = useOrganization();
  const prevOrgIdRef = useRef<string | null>(null);

  // Clear flocks when organization changes (they will be refetched when needed)
  useEffect(() => {
    const currentOrgId = currentOrganization?.id || null;
    
    if (currentOrgId !== prevOrgIdRef.current) {
      prevOrgIdRef.current = currentOrgId;
      // Clear flocks to trigger refetch with new organization
      setFlocks([]);
      setCurrentFlock(null);
    }
  }, [currentOrganization?.id]);

  const fetchBreeds = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await flocksApi.getBreeds({ is_active: true });
      // getBreeds already returns Breed[], but handle paginated responses just in case
      const breedsArray = Array.isArray(data) ? data : ((data as any)?.results || []);
      setBreeds(breedsArray);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch breeds');
      console.error('Error fetching breeds:', err);
      setBreeds([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFlocks = useCallback(async (params?: {
    house_id?: number;
    farm_id?: number;
    organization_id?: string;
    status?: string;
    is_active?: boolean;
    breed_id?: number;
  }) => {
    try {
      setLoading(true);
      setError(null);
      // Auto-include organization_id if not provided and organization is selected
      const fetchParams = {
        ...params,
        organization_id: params?.organization_id || currentOrganization?.id,
      };
      const data = await flocksApi.getFlocks(fetchParams);
      // getFlocks already handles pagination and returns Flock[]
      const flocksArray = Array.isArray(data) ? data : ((data as any)?.results || []);
      console.log('FlockContext: Fetched flocks:', flocksArray.length, flocksArray);
      setFlocks(flocksArray);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch flocks');
      console.error('Error fetching flocks:', err);
      setFlocks([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFlock = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const flock = await flocksApi.getFlock(id);
      setCurrentFlock(flock);
      return flock;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch flock');
      console.error('Error fetching flock:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFlockSummary = useCallback(async (id: number) => {
    try {
      setError(null);
      const summary = await flocksApi.getFlockSummary(id);
      return summary;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch flock summary');
      console.error('Error fetching flock summary:', err);
      throw err;
    }
  }, []);

  const fetchFlockPerformance = useCallback(async (id: number) => {
    try {
      setError(null);
      const data = await flocksApi.getFlockPerformance(id);
      setPerformanceRecords(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch flock performance');
      console.error('Error fetching flock performance:', err);
    }
  }, []);

  const fetchPerformanceRecords = useCallback(async (flockId?: number) => {
    try {
      setLoading(true);
      setError(null);
      const params = flockId ? { flock_id: flockId } : undefined;
      const data = await flocksApi.getPerformanceRecords(params);
      setPerformanceRecords(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch performance records');
      console.error('Error fetching performance records:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchComparisons = useCallback(async (organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params = organizationId ? { organization_id: organizationId } : undefined;
      const data = await flocksApi.getComparisons(params);
      setComparisons(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch comparisons');
      console.error('Error fetching comparisons:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createFlock = useCallback(async (data: Partial<Flock>): Promise<Flock> => {
    try {
      setLoading(true);
      setError(null);
      const flock = await flocksApi.createFlock(data);
      await fetchFlocks();
      return flock;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create flock';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlocks]);

  const updateFlock = useCallback(async (id: number, data: Partial<Flock>): Promise<Flock> => {
    try {
      setLoading(true);
      setError(null);
      const flock = await flocksApi.updateFlock(id, data);
      await fetchFlocks();
      if (currentFlock?.id === id) {
        setCurrentFlock(flock);
      }
      return flock;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update flock';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlocks, currentFlock]);

  const deleteFlock = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await flocksApi.deleteFlock(id);
      await fetchFlocks();
      if (currentFlock?.id === id) {
        setCurrentFlock(null);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete flock';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlocks, currentFlock]);

  const addPerformanceRecord = useCallback(async (
    flockId: number,
    data: Partial<FlockPerformance>
  ): Promise<FlockPerformance> => {
    try {
      setLoading(true);
      setError(null);
      const record = await flocksApi.addPerformanceRecord(flockId, data);
      await fetchFlockPerformance(flockId);
      return record;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add performance record';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlockPerformance]);

  const calculatePerformance = useCallback(async (
    flockId: number,
    recordDate?: string
  ): Promise<FlockPerformance> => {
    try {
      setLoading(true);
      setError(null);
      const record = await flocksApi.calculatePerformance(flockId, recordDate);
      await fetchFlockPerformance(flockId);
      return record;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to calculate performance';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlockPerformance]);

  const completeFlock = useCallback(async (
    id: number,
    data?: { actual_harvest_date?: string; final_count?: number }
  ): Promise<Flock> => {
    try {
      setLoading(true);
      setError(null);
      const flock = await flocksApi.completeFlock(id, data);
      await fetchFlocks();
      if (currentFlock?.id === id) {
        setCurrentFlock(flock);
      }
      return flock;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to complete flock';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchFlocks, currentFlock]);

  const createComparison = useCallback(async (data: Partial<FlockComparison>): Promise<FlockComparison> => {
    try {
      setLoading(true);
      setError(null);
      const comparison = await flocksApi.createComparison(data);
      await fetchComparisons();
      return comparison;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create comparison';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchComparisons]);

  const calculateComparison = useCallback(async (id: number, metrics?: string[]) => {
    try {
      setError(null);
      const result = await flocksApi.calculateComparison(id, metrics);
      await fetchComparisons();
      return result;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to calculate comparison';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchComparisons]);

  const createBreed = useCallback(async (data: Partial<Breed>): Promise<Breed> => {
    try {
      setLoading(true);
      setError(null);
      const breed = await flocksApi.createBreed(data);
      await fetchBreeds();
      return breed;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create breed';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchBreeds]);

  const updateBreed = useCallback(async (id: number, data: Partial<Breed>): Promise<Breed> => {
    try {
      setLoading(true);
      setError(null);
      const breed = await flocksApi.updateBreed(id, data);
      await fetchBreeds();
      return breed;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update breed';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchBreeds]);

  const value: FlockContextType = {
    breeds,
    flocks,
    currentFlock,
    performanceRecords,
    comparisons,
    loading,
    error,
    setCurrentFlock,
    fetchBreeds,
    fetchFlocks,
    fetchFlock,
    fetchFlockSummary,
    fetchFlockPerformance,
    fetchPerformanceRecords,
    fetchComparisons,
    createFlock,
    updateFlock,
    deleteFlock,
    addPerformanceRecord,
    calculatePerformance,
    completeFlock,
    createComparison,
    calculateComparison,
    createBreed,
    updateBreed,
  };

  return (
    <FlockContext.Provider value={value}>
      {children}
    </FlockContext.Provider>
  );
};

