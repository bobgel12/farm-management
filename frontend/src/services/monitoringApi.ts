import api from './api';
import {
  HouseMonitoringSnapshot,
  HouseMonitoringStats,
  MonitoringHistoryResponse,
  FarmHousesMonitoringResponse,
  MonitoringDashboardData,
  HouseMonitoringKpis,
  FarmWaterHistoryComparisonResponse,
  WaterConsumptionAlert,
  WaterConsumptionForecast,
  FarmDataQualityResponse,
  MonitoringTrendsResponse,
  FlockRiskScore,
  FarmMonitoringCacheStatus,
  MonitoringCacheRefreshRun,
  MonitoringCacheMeta,
  MonitoringDataMode,
} from '../types/monitoring';

export const MONITORING_DATA_MODE_STORAGE_KEY = 'monitoringDataMode';

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

  getMonitoringDataMode(): MonitoringDataMode {
    if (typeof window === 'undefined') return 'cache_only';
    const stored = window.sessionStorage.getItem(MONITORING_DATA_MODE_STORAGE_KEY);
    return stored === 'cached_then_live' ? 'cached_then_live' : 'cache_only';
  }

  setMonitoringDataMode(mode: MonitoringDataMode) {
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem(MONITORING_DATA_MODE_STORAGE_KEY, mode);
    }
  }

  private unwrapMonitoringResponse<T extends Record<string, any>>(payload: any): T & { meta?: MonitoringCacheMeta } {
    const inner = payload?.success && payload?.data ? payload.data : payload;
    if (inner?.data && typeof inner.data === 'object') {
      return {
        ...inner.data,
        meta: inner.meta || payload?.meta?.freshness,
      };
    }
    if (payload?.success && payload?.data && typeof payload.data === 'object') {
      return {
        ...payload.data,
        meta: payload.meta?.freshness || payload.meta,
      };
    }
    return inner;
  }

  /**
   * Get latest monitoring snapshot for a house
   */
  async getHouseLatestMonitoring(houseId: number, mode: MonitoringDataMode = this.getMonitoringDataMode()): Promise<HouseMonitoringSnapshot> {
    const response = await api.get(`/houses/${houseId}/monitoring/latest/`, {
      params: { mode },
      headers: this.getAuthHeaders()
    });
    return this.unwrapMonitoringResponse<HouseMonitoringSnapshot>(response.data);
  }

  /**
   * Get historical monitoring snapshots for a house
   */
  async getHouseMonitoringHistory(
    houseId: number,
    startDate?: string,
    endDate?: string,
    limit: number = 100,
    mode?: 'cached' | 'cache_only' | 'live' | 'cached_then_live'
  ): Promise<MonitoringHistoryResponse> {
    const params: any = { limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (mode) params.mode = mode;

    const response = await api.get(`/houses/${houseId}/monitoring/history/`, {
      params,
      headers: this.getAuthHeaders()
    });
    return this.unwrapMonitoringResponse<MonitoringHistoryResponse>(response.data);
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
   * @param options.cacheBust Unique value per logical request so browsers/proxies cannot serve a stale GET.
   */
  async getHouseMonitoringKpis(
    houseId: number,
    options?: { dodReferenceDate?: string | null; cacheBust?: string | number; mode?: MonitoringDataMode }
  ): Promise<HouseMonitoringKpis> {
    const params: Record<string, string> = { mode: options?.mode || this.getMonitoringDataMode() };
    if (options?.dodReferenceDate) {
      params.dod_reference_date = options.dodReferenceDate;
    }
    if (options?.cacheBust != null) {
      params._ = String(options.cacheBust);
    }
    const response = await api.get(`/houses/${houseId}/monitoring/kpis/`, {
      headers: this.getAuthHeaders(),
      params,
    });
    return this.unwrapMonitoringResponse<HouseMonitoringKpis>(response.data);
  }

  /**
   * Get latest monitoring data for all houses in a farm
   */
  async getFarmHousesMonitoring(farmId: number, mode: MonitoringDataMode = this.getMonitoringDataMode()): Promise<FarmHousesMonitoringResponse> {
    const response = await api.get(`/farms/${farmId}/houses/monitoring/all/`, {
      params: { mode },
      headers: this.getAuthHeaders()
    });
    return this.unwrapMonitoringResponse<FarmHousesMonitoringResponse>(response.data);
  }

  /**
   * Get dashboard data with alerts and summaries for all houses
   */
  async getFarmMonitoringDashboard(farmId: number, mode: MonitoringDataMode = this.getMonitoringDataMode()): Promise<MonitoringDashboardData> {
    const response = await api.get(`/farms/${farmId}/houses/monitoring/dashboard/`, {
      params: { mode },
      headers: this.getAuthHeaders()
    });
    return this.unwrapMonitoringResponse<MonitoringDashboardData>(response.data);
  }

  async getFarmMonitoringCacheStatus(farmId: number): Promise<FarmMonitoringCacheStatus> {
    const response = await api.get(`/farms/${farmId}/houses/monitoring/cache-status/`, {
      headers: this.getAuthHeaders(),
    });
    return response.data?.data ?? response.data;
  }

  async queueMonitoringCacheRefresh(): Promise<MonitoringCacheRefreshRun> {
    const response = await api.post(`/farms/monitoring/cache-refresh/`, {}, {
      headers: this.getAuthHeaders(),
    });
    return response.data?.data ?? response.data;
  }

  async getMonitoringCacheRefreshRun(runId: string): Promise<MonitoringCacheRefreshRun> {
    const response = await api.get(`/farms/monitoring/cache-refresh/${runId}/`, {
      headers: this.getAuthHeaders(),
    });
    return response.data?.data ?? response.data;
  }

  async getFarmWaterHistoryComparison(
    farmId: number,
    options?: { days?: number; dodReferenceDate?: string | null; mode?: 'cached' | 'live' | 'cached_then_live' }
  ): Promise<FarmWaterHistoryComparisonResponse> {
    const params: Record<string, string> = {
      mode: options?.mode || 'cached_then_live',
    };
    if (options?.days != null) {
      params.days = String(options.days);
    }
    if (options?.dodReferenceDate) {
      params.dod_reference_date = options.dodReferenceDate;
    }
    const response = await api.get(`/farms/${farmId}/houses/water-history-comparison/`, {
      params,
      headers: this.getAuthHeaders(),
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
   * @param cacheBust Optional unique value so repeated GETs are not served from HTTP cache.
   */
  async getHouseHeaterHistory(
    houseId: number,
    cacheBust?: string | number,
    mode: MonitoringDataMode = this.getMonitoringDataMode()
  ): Promise<{ heater_history: Record<string, unknown> }> {
    const params: Record<string, string> = { mode };
    if (cacheBust != null) {
      params._ = String(cacheBust);
    }
    const response = await api.get(`/houses/${houseId}/heater-history/`, {
      headers: this.getAuthHeaders(),
      params,
    });
    return this.unwrapMonitoringResponse<{ heater_history: Record<string, unknown> }>(response.data);
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

  async getFarmDataQuality(farmId: number, days = 1): Promise<FarmDataQualityResponse> {
    const response = await api.get(`/farms/${farmId}/monitoring/data-quality/`, {
      params: { days },
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async getHouseMonitoringTrends(
    houseId: number,
    period = 14,
    compareGrowthDay?: number
  ): Promise<MonitoringTrendsResponse> {
    const params: Record<string, number> = { period };
    if (compareGrowthDay !== undefined) {
      params.compare_growth_day = compareGrowthDay;
    }
    const response = await api.get(`/houses/${houseId}/monitoring/trends/`, {
      params,
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  async getHouseFlockRiskScores(houseId: number, riskType = 'mortality_3d'): Promise<FlockRiskScore[]> {
    const response = await api.get(`/houses/${houseId}/flock-risk-scores/`, {
      params: { risk_type: riskType },
      headers: this.getAuthHeaders(),
    });
    return response.data.risk_scores ?? [];
  }
}

const monitoringApiService = new MonitoringApiService();
export default monitoringApiService;
