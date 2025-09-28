import axios from 'axios';
import {
  RotemFarm,
  RotemUser,
  RotemController,
  RotemDataPoint,
  RotemScrapeLog,
  MLPrediction,
  MLModel,
  MLSummary,
  AnomalyData,
  FailureData,
  OptimizationData,
  PerformanceData,
  FarmDataSummary,
  ScraperResult,
  ScraperAllResult,
  AddFarmFormData,
  SensorChartData,
  FarmDashboardData,
  HouseSensorData,
  RealTimeFarmData
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

  // Real-time sensor data methods
  async getRealTimeFarmData(farmId: string): Promise<RealTimeFarmData> {
    try {
      // Get all data points for the farm
      const dataPoints = await this.getDataByFarm(farmId);
      
      // Group data points by house and data type
      const houseData: { [houseNumber: string]: any } = {};
      
      dataPoints.forEach((point: RotemDataPoint) => {
        const houseMatch = point.data_type.match(/_house_(\d+)$/);
        if (houseMatch) {
          const houseNumber = houseMatch[1];
          const dataType = point.data_type.replace(/_house_\d+$/, '');
          
          if (!houseData[houseNumber]) {
            houseData[houseNumber] = { house_number: parseInt(houseNumber) };
          }
          
          houseData[houseNumber][dataType] = point.value;
        }
      });
      
      // Convert to HouseSensorData format
      const houses: HouseSensorData[] = Object.values(houseData).map((house: any) => ({
        house_number: house.house_number,
        temperature: house.temperature || 0,
        outside_temperature: house.outside_temperature || 0,
        humidity: house.humidity || 0,
        pressure: house.pressure || 0,
        ventilation_level: house.ventilation_level || 0,
        target_temperature: house.target_temperature || 0,
        feed_consumption: house.feed_consumption || 0,
        water_consumption: house.water_consumption || 0,
        airflow_cfm: house.airflow_cfm || 0,
        airflow_percentage: house.airflow_percentage || 0,
        bird_count: house.bird_count || 0,
        livability: house.livability || 0,
        connection_status: house.connection_status || 0,
        growth_day: house.growth_day || 0,
        temperature_sensors: {
          sensor_1: house.temp_sensor_1 || 0,
          sensor_2: house.temp_sensor_2 || 0,
          sensor_3: house.temp_sensor_3 || 0,
          sensor_4: house.temp_sensor_4 || 0,
          sensor_5: house.temp_sensor_5 || 0,
          sensor_6: house.temp_sensor_6 || 0,
          sensor_7: house.temp_sensor_7 || 0,
          sensor_8: house.temp_sensor_8 || 0,
          sensor_9: house.temp_sensor_9 || 0,
        },
        tunnel_temperature: house.tunnel_temperature || 0,
        wind_chill_temperature: house.wind_chill_temperature || 0,
        wind_speed: house.wind_speed || 0,
        wind_direction: house.wind_direction || 0,
      }));
      
      // Get farm info
      const farm = await this.getFarm(farmId);
      
      return {
        farm_id: farmId,
        farm_name: farm.farm_name,
        houses,
        last_updated: new Date().toISOString(),
        total_data_points: dataPoints.length
      };
    } catch (error) {
      console.error('Error getting real-time farm data:', error);
      throw error;
    }
  }

  async getHouseSensorData(farmId: string, houseNumber: number): Promise<HouseSensorData | null> {
    try {
      const realTimeData = await this.getRealTimeFarmData(farmId);
      return realTimeData.houses.find(house => house.house_number === houseNumber) || null;
    } catch (error) {
      console.error('Error getting house sensor data:', error);
      return null;
    }
  }

  async getTemperatureHistory(farmId: string, houseNumber: number, hours: number = 24): Promise<SensorChartData[]> {
    try {
      const dataPoints = await this.getDataByFarm(farmId);
      const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
      
      return dataPoints
        .filter((point: RotemDataPoint) => 
          point.data_type === `temperature_house_${houseNumber}` &&
          new Date(point.timestamp) >= cutoff
        )
        .map((point: RotemDataPoint) => ({
          timestamp: point.timestamp,
          value: point.value,
          data_type: point.data_type,
          unit: point.unit
        }))
        .sort((a: SensorChartData, b: SensorChartData) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    } catch (error) {
      console.error('Error getting temperature history:', error);
      return [];
    }
  }

  async getHumidityHistory(farmId: string, houseNumber: number, hours: number = 24): Promise<SensorChartData[]> {
    try {
      const dataPoints = await this.getDataByFarm(farmId);
      const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
      
      return dataPoints
        .filter((point: RotemDataPoint) => 
          point.data_type === `humidity_house_${houseNumber}` &&
          new Date(point.timestamp) >= cutoff
        )
        .map((point: RotemDataPoint) => ({
          timestamp: point.timestamp,
          value: point.value,
          data_type: point.data_type,
          unit: point.unit
        }))
        .sort((a: SensorChartData, b: SensorChartData) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    } catch (error) {
      console.error('Error getting humidity history:', error);
      return [];
    }
  }

  // ML Prediction Methods
  async getMLPredictions(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/`, {
      headers: this.getAuthHeaders()
    });
    return response.data.results;
  }

  async getActivePredictions(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/active_predictions/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getAnomalies(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/anomalies/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getFailures(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/failures/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getOptimizations(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/optimizations/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getPerformance(): Promise<MLPrediction[]> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/performance/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async getMLSummary(): Promise<MLSummary> {
    const response = await axios.get(`${this.baseURL}/rotem/predictions/summary/`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // ML Model Methods
  async getMLModels(): Promise<MLModel[]> {
    const response = await axios.get(`${this.baseURL}/rotem/ml-models/`, {
      headers: this.getAuthHeaders()
    });
    return response.data.results;
  }

  async trainMLModels(): Promise<{ message: string; task_id: string }> {
    const response = await axios.post(`${this.baseURL}/rotem/ml-models/train_models/`, {}, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  async runMLAnalysis(): Promise<{ message: string; task_id: string }> {
    const response = await axios.post(`${this.baseURL}/rotem/ml-models/run_analysis/`, {}, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }
}

export const rotemApi = new RotemApiService();
export default rotemApi;
