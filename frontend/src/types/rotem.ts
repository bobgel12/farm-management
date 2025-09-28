// Rotem Integration Types
export interface RotemFarm {
  id: string;
  farm_id: string;
  farm_name: string;
  gateway_name: string;
  gateway_alias: string;
  rotem_username: string;
  rotem_password: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RotemUser {
  id: number;
  user_id: number;
  username: string;
  display_name: string;
  email: string;
  phone_number: string;
  is_farm_admin: boolean;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

export interface RotemController {
  id: number;
  controller_id: string;
  farm: number;
  farm_name?: string; // Added from API response
  controller_name: string;
  controller_type: string;
  is_connected: boolean;
  last_seen: string | null;
  created_at: string;
}

export interface RotemDataPoint {
  id: number;
  controller: number;
  timestamp: string;
  data_type: string;
  value: number;
  unit: string;
  quality: string;
  target_value?: number;
  low_alarm_value?: number;
  high_alarm_value?: number;
  created_at: string;
}

export interface RotemScrapeLog {
  id: number;
  scrape_id: string;
  started_at: string;
  completed_at: string | null;
  status: 'success' | 'failed' | 'partial' | 'running';
  data_points_collected: number;
  error_message: string | null;
  created_at: string;
}

export interface MLPrediction {
  id: number;
  controller: number;
  prediction_type: string;
  predicted_at: string;
  confidence_score: number;
  prediction_data: any;
  is_active: boolean;
  created_at: string;
}

export interface MLModel {
  id: number;
  name: string;
  version: string;
  model_type: string;
  is_active: boolean;
  accuracy_score: number | null;
  training_data_size: number | null;
  last_trained: string | null;
  model_file_path: string;
  created_at: string;
}

// API Response Types
export interface FarmDataSummary {
  farm_id: string;
  farm_name: string;
  total_data_points: number;
  recent_data_points: number;
  controllers: number;
}

export interface ScraperResult {
  status: string;
  data_points_collected: number;
  completed_at: string | null;
  error_message: string | null;
}

export interface ScraperAllResult {
  results: Array<{
    farm: string;
    status: string;
    data_points?: number;
    error?: string;
  }>;
  total_farms: number;
}

// Form Types
export interface AddFarmFormData {
  farm_name: string;
  gateway_name: string;
  username: string;
  password: string;
  gateway_alias?: string;
}

export interface FarmCredentials {
  username: string;
  password: string;
}

// Chart Data Types
export interface SensorChartData {
  timestamp: string;
  value: number;
  data_type: string;
  unit: string;
}

export interface FarmDashboardData {
  farm: RotemFarm;
  controllers: RotemController[];
  recent_data: RotemDataPoint[];
  summary: FarmDataSummary;
  last_scrape: RotemScrapeLog | null;
}

// Real Sensor Data Types
export interface HouseSensorData {
  house_number: number;
  temperature: number;
  outside_temperature: number;
  humidity: number;
  pressure: number;
  ventilation_level: number;
  target_temperature: number;
  feed_consumption: number;
  water_consumption: number;
  airflow_cfm: number;
  airflow_percentage: number;
  bird_count: number;
  livability: number;
  connection_status: number;
  growth_day: number;
  temperature_sensors: {
    sensor_1: number;
    sensor_2: number;
    sensor_3: number;
    sensor_4: number;
    sensor_5: number;
    sensor_6: number;
    sensor_7: number;
    sensor_8: number;
    sensor_9: number;
  };
  tunnel_temperature: number;
  wind_chill_temperature: number;
  wind_speed: number;
  wind_direction: number;
}

export interface RealTimeFarmData {
  farm_id: string;
  farm_name: string;
  houses: HouseSensorData[];
  last_updated: string;
  total_data_points: number;
}

// API Endpoint Types
export interface RotemApiEndpoints {
  farms: string;
  data: string;
  predictions: string;
  controllers: string;
  users: string;
  logs: string;
  scraper: string;
}
