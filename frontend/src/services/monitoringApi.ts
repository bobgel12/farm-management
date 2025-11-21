import api from './api';
import {
  HouseMonitoringSnapshot,
  HouseMonitoringSummary,
  HouseMonitoringStats,
  MonitoringHistoryResponse,
  FarmHousesMonitoringResponse,
  MonitoringDashboardData
} from '../types/monitoring';

class MonitoringApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = '/api';
  }

  // Helper method to get auth headers
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return token ? { Authorization: `Token ${token}` } : {};
  }

  /**
   * Get latest monitoring snapshot for a house
   */
  async getHouseLatestMonitoring(houseId: number): Promise<HouseMonitoringSnapshot> {
    const response = await api.get(`/houses/${houseId}/monitoring/latest/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  /**
   * Get historical monitoring snapshots for a house
   */
  async getHouseMonitoringHistory(
    houseId: number,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<MonitoringHistoryResponse> {
    const params: any = { limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await api.get(`/houses/${houseId}/monitoring/history/`, {
      params,
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  /**
   * Get statistical aggregations for house monitoring data
   */
  async getHouseMonitoringStats(
    houseId: number,
    period: number = 7
  ): Promise<HouseMonitoringStats> {
    const response = await api.get(`/houses/${houseId}/monitoring/stats/`, {
      params: { period },
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  /**
   * Get latest monitoring data for all houses in a farm
   */
  async getFarmHousesMonitoring(farmId: number): Promise<FarmHousesMonitoringResponse> {
    const response = await api.get(`/farms/${farmId}/houses/monitoring/all/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  /**
   * Get dashboard data with alerts and summaries for all houses
   */
  async getFarmMonitoringDashboard(farmId: number): Promise<MonitoringDashboardData> {
    const response = await api.get(`/farms/${farmId}/houses/monitoring/dashboard/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }
}

// Export singleton instance
export default new MonitoringApiService();

