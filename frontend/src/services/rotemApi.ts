import axios from 'axios';
import {
  RotemFarm,
  RotemUser,
  RotemController,
  RotemDataPoint,
  RotemScrapeLog,
  MLPrediction,
  FarmDataSummary,
  ScraperResult,
  ScraperAllResult,
  AddFarmFormData,
  SensorChartData,
  FarmDashboardData
} from '../types/rotem';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002/api';

class RotemApiService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/rotem`;
  }

  // Helper method to get auth headers
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json',
    };
  }

  // Farm Management
  async getFarms(): Promise<RotemFarm[]> {
    const response = await axios.get(`${this.baseURL}/farms/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getFarm(farmId: string): Promise<RotemFarm> {
    const response = await axios.get(`${this.baseURL}/farms/${farmId}/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async addFarm(farmData: AddFarmFormData): Promise<RotemFarm> {
    const response = await axios.post(`${this.baseURL}/farms/`, farmData, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async updateFarm(farmId: string, farmData: Partial<RotemFarm>): Promise<RotemFarm> {
    const response = await axios.put(`${this.baseURL}/farms/${farmId}/`, farmData, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async deleteFarm(farmId: string): Promise<void> {
    await axios.delete(`${this.baseURL}/farms/${farmId}/`, {
      headers: this.getAuthHeaders()
    });
  }

  // Data Management
  async getDataSummary(): Promise<FarmDataSummary[]> {
    const response = await axios.get(`${this.baseURL}/data/summary/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getDataByFarm(farmId: string): Promise<RotemDataPoint[]> {
    const response = await axios.get(`${this.baseURL}/data/by_farm/?farm_id=${farmId}`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getLatestData(): Promise<RotemDataPoint[]> {
    const response = await axios.get(`${this.baseURL}/data/latest_data/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getControllerData(controllerId: string): Promise<RotemDataPoint[]> {
    const response = await axios.get(`${this.baseURL}/data/controller_data/?controller_id=${controllerId}`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getRecentData(): Promise<RotemDataPoint[]> {
    const response = await axios.get(`${this.baseURL}/data/recent/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Controllers
  async getControllers(): Promise<RotemController[]> {
    const response = await axios.get(`${this.baseURL}/controllers/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getController(controllerId: string): Promise<RotemController> {
    const response = await axios.get(`${this.baseURL}/controllers/${controllerId}/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Users
  async getUsers(): Promise<RotemUser[]> {
    const response = await axios.get(`${this.baseURL}/users/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Scraper Operations
  async scrapeFarm(farmId: string): Promise<ScraperResult> {
    const response = await axios.post(`${this.baseURL}/scraper/scrape_farm/`, {
      farm_id: farmId
    }, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async scrapeAllFarms(): Promise<ScraperAllResult> {
    const response = await axios.post(`${this.baseURL}/scraper/scrape_all/`, {}, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Logs
  async getScrapeLogs(): Promise<RotemScrapeLog[]> {
    const response = await axios.get(`${this.baseURL}/logs/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getRecentLogs(): Promise<RotemScrapeLog[]> {
    const response = await axios.get(`${this.baseURL}/logs/recent/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Predictions
  async getPredictions(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/predictions/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getActivePredictions(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/predictions/active_predictions/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getAnomalies(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/predictions/anomalies/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getPredictionsByFarm(farmId: string): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/predictions/by_farm/?farm_id=${farmId}`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Utility Methods
  async getFarmDashboard(farmId: string): Promise<FarmDashboardData> {
    try {
      console.log('DEBUG: getFarmDashboard starting for farmId:', farmId);
      
      const [farm, controllers, recentData, summary, logs] = await Promise.all([
        this.getFarm(farmId).catch(err => {
          console.error('DEBUG: getFarm error:', err);
          throw err;
        }),
        this.getControllers().then(controllers => {
          console.log('DEBUG: all controllers:', controllers);
          const filtered = controllers.filter(c => c.farm_name && c.farm_name.includes(farmId));
          console.log('DEBUG: filtered controllers:', filtered);
          return filtered;
        }).catch(err => {
          console.error('DEBUG: getControllers error:', err);
          return [];
        }),
        this.getDataByFarm(farmId).then(data => {
          console.log('DEBUG: farm data points:', data.length);
          return data.slice(0, 10);
        }).catch(err => {
          console.error('DEBUG: getDataByFarm error:', err);
          return [];
        }),
        this.getDataSummary().then(summaries => {
          console.log('DEBUG: data summaries:', summaries);
          return summaries.find(s => s.farm_id === farmId);
        }).catch(err => {
          console.error('DEBUG: getDataSummary error:', err);
          return null;
        }),
        this.getRecentLogs().then(logs => {
          console.log('DEBUG: recent logs:', logs);
          return logs.find(log => log.scrape_id.includes(farmId));
        }).catch(err => {
          console.error('DEBUG: getRecentLogs error:', err);
          return null;
        })
      ]);

      const result = {
        farm,
        controllers,
        recent_data: recentData,
        summary: summary || {
          farm_id: farmId,
          farm_name: farm.farm_name,
          total_data_points: 0,
          recent_data_points: 0,
          controllers: 0
        },
        last_scrape: logs || null
      };
      
      console.log('DEBUG: getFarmDashboard result:', result);
      return result;
    } catch (error) {
      console.error('DEBUG: getFarmDashboard error:', error);
      throw error;
    }
  }

  // Chart Data Processing
  processChartData(dataPoints: RotemDataPoint[], dataType: string): SensorChartData[] {
    return dataPoints
      .filter(point => point.data_type === dataType)
      .map(point => ({
        timestamp: point.timestamp,
        value: point.value,
        data_type: point.data_type,
        unit: point.unit
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }

  // Data Type Utilities
  getDataTypes(dataPoints: RotemDataPoint[]): string[] {
    return Array.from(new Set(dataPoints.map(point => point.data_type)));
  }

  getLatestValue(dataPoints: RotemDataPoint[], dataType: string): number | null {
    const filtered = dataPoints
      .filter(point => point.data_type === dataType)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    return filtered.length > 0 ? filtered[0].value : null;
  }

  getAverageValue(dataPoints: RotemDataPoint[], dataType: string, hours: number = 24): number | null {
    const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
    const filtered = dataPoints
      .filter(point => 
        point.data_type === dataType && 
        new Date(point.timestamp) >= cutoff
      );
    
    if (filtered.length === 0) return null;
    
    const sum = filtered.reduce((acc, point) => acc + point.value, 0);
    return sum / filtered.length;
  }
}

export const rotemApi = new RotemApiService();
export default rotemApi;
