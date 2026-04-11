import api from './api';
import {
  HouseMonitoringSnapshot,
  HouseMonitoringStats,
  MonitoringHistoryResponse,
  FarmHousesMonitoringResponse,
  MonitoringDashboardData,
  HouseMonitoringKpis,
  WaterConsumptionAlert,
  WaterConsumptionForecast,
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
   * Get derived operational KPIs for house overview.
   * @param options.dodReferenceDate ISO date (YYYY-MM-DD) to compare that day vs the prior day for water/feed DOD.
   */
  async getHouseMonitoringKpis(
    houseId: number,
    options?: { dodReferenceDate?: string | null }
  ): Promise<HouseMonitoringKpis> {
    const params: Record<string, string> = {};
    if (options?.dodReferenceDate) {
      params.dod_reference_date = options.dodReferenceDate;
    }
    const response = await api.get(`/houses/${houseId}/monitoring/kpis/`, {
      headers: this.getAuthHeaders(),
      ...(Object.keys(params).length > 0 ? { params } : {}),
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

  async getWaterAlerts(houseId: number): Promise<{ count: number; results: WaterConsumptionAlert[] }> {
    const response = await api.get(`/houses/${houseId}/water/alerts/`, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async acknowledgeWaterAlert(alertId: number): Promise<WaterConsumptionAlert> {
    const response = await api.post(`/houses/water/alerts/${alertId}/acknowledge/`, {}, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async resolveWaterAlert(alertId: number): Promise<WaterConsumptionAlert> {
    const response = await api.post(`/houses/water/alerts/${alertId}/resolve/`, {}, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async snoozeWaterAlert(alertId: number, hours: number): Promise<WaterConsumptionAlert> {
    const response = await api.post(`/houses/water/alerts/${alertId}/snooze/`, { hours }, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async listWaterForecasts(houseId: number): Promise<{ count: number; results: WaterConsumptionForecast[] }> {
    const response = await api.get(`/houses/${houseId}/water/forecasts/`, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async generateWaterForecasts(houseId: number): Promise<{ status: string; generated: number; results: WaterConsumptionForecast[] }> {
    const response = await api.post(`/houses/${houseId}/water/forecasts/generate/`, {}, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  /**
   * Cached CommandID 43 heater history only (fast; no Rotem call).
   */
  async getHouseHeaterHistory(houseId: number): Promise<{ heater_history: Record<string, unknown> }> {
    const response = await api.get(`/houses/${houseId}/heater-history/`, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  /**
   * Fetch CommandID 43 from Rotem and return updated heater history.
   */
  async refreshHouseHeaterHistory(houseId: number): Promise<{
    heater_history: Record<string, unknown>;
    refresh_result?: Record<string, unknown>;
  }> {
    const response = await api.post(
      `/houses/${houseId}/heater-history/refresh/`,
      {},
      { headers: this.getAuthHeaders() }
    );
    return response.data;
  }
}

const monitoringApiService = new MonitoringApiService();
export default monitoringApiService;

