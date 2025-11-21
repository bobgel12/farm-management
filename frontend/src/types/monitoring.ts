// Monitoring data types for house monitoring snapshots

export interface HouseMonitoringSnapshot {
  id: number;
  house: number;
  house_number: number;
  farm_name: string;
  timestamp: string;
  
  // Key metrics
  average_temperature: number | null;
  outside_temperature: number | null;
  humidity: number | null;
  static_pressure: number | null;
  target_temperature: number | null;
  ventilation_level: number | null;
  
  // Growth and bird info
  growth_day: number | null;
  bird_count: number | null;
  livability: number | null;
  
  // Consumption
  water_consumption: number | null;
  feed_consumption: number | null;
  
  // Airflow
  airflow_cfm: number | null;
  airflow_percentage: number | null;
  
  // Status indicators
  connection_status: number | null;
  alarm_status: 'normal' | 'warning' | 'critical';
  has_alarms: boolean;
  is_connected: boolean;
  
  // Raw data
  sensor_data: {
    temperature_sensors?: Record<string, TemperatureSensorData>;
    wind?: WindData;
    consumption?: ConsumptionData;
  };
  raw_data?: any;
  alarms?: HouseAlarm[];
}

export interface TemperatureSensorData {
  name: string;
  display_name: string;
  value: number;
  unit: string;
}

export interface WindData {
  wind_speed?: number;
  wind_direction?: number;
  wind_chill_temperature?: number;
}

export interface ConsumptionData {
  water_consumption?: number;
  feed_consumption?: number;
}

export interface HouseAlarm {
  id: number;
  alarm_type: 'temperature' | 'humidity' | 'pressure' | 'connection' | 'consumption' | 'equipment' | 'other';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  parameter_name?: string | null;
  parameter_value?: number | null;
  threshold_value?: number | null;
  is_active: boolean;
  is_resolved: boolean;
  resolved_at?: string | null;
  resolved_by?: string | null;
  timestamp: string;
}

export interface HouseMonitoringSummary {
  id: number;
  timestamp: string;
  average_temperature: number | null;
  outside_temperature: number | null;
  humidity: number | null;
  static_pressure: number | null;
  target_temperature: number | null;
  ventilation_level: number | null;
  growth_day: number | null;
  bird_count: number | null;
  livability: number | null;
  water_consumption: number | null;
  feed_consumption: number | null;
  airflow_cfm: number | null;
  airflow_percentage: number | null;
  connection_status: number | null;
  alarm_status: 'normal' | 'warning' | 'critical';
  has_alarms: boolean;
  is_connected: boolean;
}

export interface HouseMonitoringStats {
  temperature: {
    avg: number | null;
    max: number | null;
    min: number | null;
  };
  humidity: {
    avg: number | null;
    max: number | null;
    min: number | null;
  };
  pressure: {
    avg: number | null;
    max: number | null;
    min: number | null;
  };
  total_snapshots: number;
  period_days: number;
}

export interface MonitoringHistoryResponse {
  count: number;
  start_date: string;
  end_date: string;
  results: HouseMonitoringSummary[];
}

export interface FarmHousesMonitoringResponse {
  farm_id: number;
  farm_name: string;
  houses_count: number;
  houses: (HouseMonitoringSummary | {
    house_id: number;
    house_number: number;
    status: 'no_data';
    message: string;
  })[];
}

export interface MonitoringDashboardData {
  farm_id: number;
  farm_name: string;
  total_houses: number;
  houses: Array<{
    house_id: number;
    house_number: number;
    current_day: number | null;
    status: string;
    active_alarms_count: number;
  } & HouseMonitoringSummary>;
  alerts_summary: {
    total_active: number;
    critical: number;
    warning: number;
    normal: number;
  };
  connection_summary: {
    connected: number;
    disconnected: number;
  };
}

