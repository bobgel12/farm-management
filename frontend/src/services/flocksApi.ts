import api from './api';
import {
  Breed,
  Flock,
  FlockPerformance,
  FlockComparison,
  FlockComparisonResult,
  PaginatedResponse
} from '../types';

/**
 * Flocks API service
 */
export const flocksApi = {
  // ==================== Breeds ====================

  /**
   * Get all breeds
   */
  async getBreeds(params?: {
    is_active?: boolean;
  }): Promise<Breed[]> {
    const response = await api.get('/breeds/', { params });
    return response.data;
  },

  /**
   * Get breed by ID
   */
  async getBreed(id: number): Promise<Breed> {
    const response = await api.get(`/breeds/${id}/`);
    return response.data;
  },

  /**
   * Create a new breed
   */
  async createBreed(data: Partial<Breed>): Promise<Breed> {
    const response = await api.post('/breeds/', data);
    return response.data;
  },

  /**
   * Update a breed
   */
  async updateBreed(id: number, data: Partial<Breed>): Promise<Breed> {
    const response = await api.patch(`/breeds/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a breed
   */
  async deleteBreed(id: number): Promise<void> {
    await api.delete(`/breeds/${id}/`);
  },

  // ==================== Flocks ====================

  /**
   * Get all flocks
   */
  async getFlocks(params?: {
    house_id?: number;
    farm_id?: number;
    organization_id?: string;
    status?: string;
    is_active?: boolean;
    breed_id?: number;
  }): Promise<Flock[]> {
    const response = await api.get('/flocks/', { params });
    // Handle paginated responses
    const data = response.data;
    return Array.isArray(data) ? data : (data?.results || []);
  },

  /**
   * Get flock by ID
   */
  async getFlock(id: number): Promise<Flock> {
    const response = await api.get(`/flocks/${id}/`);
    return response.data;
  },

  /**
   * Create a new flock
   */
  async createFlock(data: Partial<Flock>): Promise<Flock> {
    const response = await api.post('/flocks/', data);
    return response.data;
  },

  /**
   * Update a flock
   */
  async updateFlock(id: number, data: Partial<Flock>): Promise<Flock> {
    const response = await api.patch(`/flocks/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a flock
   */
  async deleteFlock(id: number): Promise<void> {
    await api.delete(`/flocks/${id}/`);
  },

  /**
   * Get flock summary
   */
  async getFlockSummary(id: number): Promise<any> {
    const response = await api.get(`/flocks/${id}/summary/`);
    return response.data;
  },

  /**
   * Get flock performance records
   */
  async getFlockPerformance(id: number): Promise<FlockPerformance[]> {
    const response = await api.get(`/flocks/${id}/performance/`);
    return response.data;
  },

  /**
   * Add performance record to a flock
   */
  async addPerformanceRecord(id: number, data: Partial<FlockPerformance>): Promise<FlockPerformance> {
    const response = await api.post(`/flocks/${id}/add_performance_record/`, data);
    return response.data;
  },

  /**
   * Calculate flock performance
   */
  async calculatePerformance(id: number, recordDate?: string): Promise<FlockPerformance> {
    const response = await api.post(`/flocks/${id}/calculate_performance/`, {
      record_date: recordDate
    });
    return response.data;
  },

  /**
   * Complete a flock (harvest)
   */
  async completeFlock(id: number, data?: {
    actual_harvest_date?: string;
    final_count?: number;
  }): Promise<Flock> {
    const response = await api.post(`/flocks/${id}/complete/`, data);
    return response.data;
  },

  // ==================== Flock Performance ====================

  /**
   * Get all performance records
   */
  async getPerformanceRecords(params?: {
    flock_id?: number;
  }): Promise<FlockPerformance[]> {
    const response = await api.get('/flock-performance/', { params });
    return response.data;
  },

  /**
   * Get performance record by ID
   */
  async getPerformanceRecord(id: number): Promise<FlockPerformance> {
    const response = await api.get(`/flock-performance/${id}/`);
    return response.data;
  },

  /**
   * Create a performance record
   */
  async createPerformanceRecord(data: Partial<FlockPerformance>): Promise<FlockPerformance> {
    const response = await api.post('/flock-performance/', data);
    return response.data;
  },

  /**
   * Update a performance record
   */
  async updatePerformanceRecord(id: number, data: Partial<FlockPerformance>): Promise<FlockPerformance> {
    const response = await api.patch(`/flock-performance/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a performance record
   */
  async deletePerformanceRecord(id: number): Promise<void> {
    await api.delete(`/flock-performance/${id}/`);
  },

  // ==================== Flock Comparisons ====================

  /**
   * Get all flock comparisons
   */
  async getComparisons(params?: {
    organization_id?: string;
  }): Promise<FlockComparison[]> {
    const response = await api.get('/flock-comparisons/', { params });
    return response.data;
  },

  /**
   * Get comparison by ID
   */
  async getComparison(id: number): Promise<FlockComparison> {
    const response = await api.get(`/flock-comparisons/${id}/`);
    return response.data;
  },

  /**
   * Create a new comparison
   */
  async createComparison(data: Partial<FlockComparison>): Promise<FlockComparison> {
    const response = await api.post('/flock-comparisons/', data);
    return response.data;
  },

  /**
   * Update a comparison
   */
  async updateComparison(id: number, data: Partial<FlockComparison>): Promise<FlockComparison> {
    const response = await api.patch(`/flock-comparisons/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a comparison
   */
  async deleteComparison(id: number): Promise<void> {
    await api.delete(`/flock-comparisons/${id}/`);
  },

  /**
   * Calculate comparison results
   */
  async calculateComparison(id: number, metrics?: string[]): Promise<{
    comparison: FlockComparison;
    results: FlockComparisonResult;
  }> {
    const response = await api.post(`/flock-comparisons/${id}/calculate/`, { metrics });
    return response.data;
  },
};

