// Global type definitions for the Chicken House Management system

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
}

export interface Worker {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
  receive_daily_tasks: boolean;
  created_at: string;
  updated_at: string;
}

export interface Farm {
  id: number;
  organization?: string; // UUID
  name: string;
  location: string;
  description?: string;
  contact_person?: string;
  contact_email: string;
  contact_phone: string;
  is_active: boolean;
  total_houses?: number;
  active_houses?: number;
  workers?: Worker[];
  created_at: string;
  updated_at: string;
  owner: number;
  // Integration fields
  has_system_integration: boolean;
  integration_type: 'none' | 'rotem' | 'future_system';
  integration_status: 'active' | 'inactive' | 'error' | 'not_configured';
  last_sync?: string;
  is_integrated?: boolean;
  integration_display_name?: string;
  // Rotem-specific fields
  rotem_farm_id?: string;
  rotem_username?: string;
  rotem_password?: string;
  rotem_gateway_name?: string;
  rotem_gateway_alias?: string;
}

export interface House {
  id: number;
  farm_id: number;
  name?: string;
  house_number?: number;
  capacity: number;
  current_population: number;
  created_at: string;
  updated_at: string;
  // Age tracking fields
  current_day?: number | null;  // Calculated from chicken_in_date
  current_age_days?: number;    // Stored value (from Rotem integration)
  age_days?: number;            // Unified age (prefers current_age_days, fallback to current_day)
  days_remaining?: number | null;
  status?: string;
  // Integration fields
  is_integrated?: boolean;
  batch_start_date?: string | null;
  expected_harvest_date?: string | null;
  chicken_in_date?: string;
  chicken_out_date?: string | null;
}

export interface Task {
  id: number;
  title: string;
  description: string;
  due_date: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  farm: number;
  house?: number;
  created_at: string;
  updated_at: string;
}

export interface RecurringTask {
  id: number;
  title: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  day_of_week?: number;
  day_of_month?: number;
  farm: number;
  house?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface ErrorResponse {
  detail: string;
  errors?: Record<string, string[]>;
}

// Form types
export interface FarmFormData {
  name: string;
  location: string;
  contact_email: string;
  contact_phone: string;
}

export interface HouseFormData {
  name: string;
  capacity: number;
  farm: number;
}

export interface TaskFormData {
  title: string;
  description: string;
  due_date: string;
  priority: 'low' | 'medium' | 'high';
  farm: number;
  house?: number;
}

// Context types
export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterRequest) => Promise<void>;
  loading: boolean;
}

export interface FarmContextType {
  farms: Farm[];
  selectedFarm: Farm | null;
  loading: boolean;
  fetchFarms: () => Promise<void>;
  createFarm: (farmData: FarmFormData) => Promise<Farm>;
  updateFarm: (id: number, farmData: Partial<FarmFormData>) => Promise<Farm>;
  deleteFarm: (id: number) => Promise<void>;
  selectFarm: (farm: Farm | null) => void;
}

export interface TaskContextType {
  tasks: Task[];
  loading: boolean;
  fetchTasks: (farmId?: number) => Promise<void>;
  createTask: (taskData: TaskFormData) => Promise<Task>;
  updateTask: (id: number, taskData: Partial<TaskFormData>) => Promise<Task>;
  deleteTask: (id: number) => Promise<void>;
  markComplete: (id: number) => Promise<void>;
}

// ==================== Multi-tenancy Types ====================

export interface Organization {
  id: string; // UUID
  name: string;
  slug: string;
  description?: string;
  contact_email: string;
  contact_phone?: string;
  website?: string;
  address?: string;
  is_active: boolean;
  is_trial: boolean;
  trial_expires_at?: string;
  subscription_tier: 'trial' | 'basic' | 'standard' | 'premium' | 'enterprise';
  subscription_status: 'active' | 'suspended' | 'cancelled' | 'expired';
  max_farms: number;
  max_users: number;
  max_houses_per_farm: number;
  logo?: string;
  primary_color: string;
  secondary_color: string;
  custom_domain?: string;
  created_at: string;
  updated_at: string;
  // Computed fields
  total_farms?: number;
  total_users?: number;
  total_houses?: number;
  is_trial_expired?: boolean;
}

export interface OrganizationUser {
  id: number;
  organization: string; // UUID
  organization_name?: string;
  user: User;
  user_id?: number;
  role: 'owner' | 'admin' | 'manager' | 'worker' | 'viewer';
  is_active: boolean;
  can_manage_farms: boolean;
  can_manage_users: boolean;
  can_view_reports: boolean;
  can_export_data: boolean;
  joined_at: string;
  updated_at: string;
  invited_by?: number;
  // Computed fields
  is_owner?: boolean;
  is_admin?: boolean;
}

export interface OrganizationMembership {
  id: number;
  organization: Organization;
  role: 'owner' | 'admin' | 'manager' | 'worker' | 'viewer';
  is_active: boolean;
  can_manage_farms: boolean;
  can_manage_users: boolean;
  can_view_reports: boolean;
  can_export_data: boolean;
  joined_at: string;
  is_owner?: boolean;
  is_admin?: boolean;
}

export interface OrganizationInvite {
  id: string; // UUID
  organization: string; // UUID
  organization_name?: string;
  email: string;
  token: string;
  role: 'owner' | 'admin' | 'manager' | 'worker' | 'viewer';
  can_manage_farms: boolean;
  can_manage_users: boolean;
  can_view_reports: boolean;
  can_export_data: boolean;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  expires_at: string;
  invited_by?: number;
  invited_by_name?: string;
  created_at: string;
  updated_at: string;
  accepted_at?: string;
  accepted_by?: number;
  is_expired?: boolean;
  is_valid?: boolean;
}

export interface InviteInfo {
  organization_name: string;
  email: string;
  role: string;
  is_valid: boolean;
  is_expired: boolean;
  status: string;
  has_existing_user: boolean;
  invited_by?: string;
}

// ==================== Flock Management Types ====================

export interface Breed {
  id: number;
  name: string;
  code: string;
  description?: string;
  average_weight_gain_per_week?: number;
  average_feed_conversion_ratio?: number;
  average_mortality_rate?: number;
  typical_harvest_age_days?: number;
  typical_harvest_weight_grams?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Flock {
  id: number;
  house: number;
  house_name?: string;
  farm_name?: string;
  breed?: number;
  breed_name?: string;
  batch_number: string;
  flock_code: string;
  arrival_date: string;
  expected_harvest_date?: string;
  actual_harvest_date?: string;
  start_date?: string;
  end_date?: string;
  initial_chicken_count: number;
  current_chicken_count?: number;
  status: 'setup' | 'arrival' | 'growing' | 'production' | 'harvesting' | 'completed' | 'cancelled';
  is_active: boolean;
  supplier?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: number;
  // Computed fields
  current_age_days?: number;
  days_until_harvest?: number;
  mortality_count?: number;
  mortality_rate?: number;
  livability?: number;
  performance_records?: FlockPerformance[];
}

export interface FlockPerformance {
  id: number;
  flock: number;
  flock_code?: string;
  batch_number?: string;
  record_date: string;
  flock_age_days: number;
  average_weight_grams?: number;
  total_weight_kg?: number;
  feed_consumed_kg?: number;
  daily_feed_consumption_kg?: number;
  feed_conversion_ratio?: number;
  daily_water_consumption_liters?: number;
  current_chicken_count: number;
  mortality_count: number;
  mortality_rate?: number;
  livability?: number;
  average_temperature?: number;
  average_humidity?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  recorded_by?: number;
}

export interface FlockComparison {
  id: number;
  name: string;
  description?: string;
  flocks: Flock[];
  flock_ids?: number[];
  comparison_metrics: string[];
  comparison_results?: {
    flocks: Array<Record<string, any>>;
    metrics: Record<string, {
      min: number;
      max: number;
      average: number;
      count: number;
    }>;
    summary: {
      total_flocks: number;
      flocks_with_data: number;
    };
  };
  created_by: number;
  creator_name?: string;
  created_at: string;
  updated_at: string;
}

// ==================== Reporting Types ====================

export type ReportType = 'flock_performance' | 'farm_summary' | 'house_status' | 'task_completion' | 'financial' | 'custom';
export type ExportFormat = 'pdf' | 'excel' | 'csv' | 'json' | 'html';
export type ReportFrequency = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'custom';
export type ReportExecutionStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type ScheduledReportStatus = 'active' | 'paused' | 'completed' | 'failed';

export interface ReportTemplate {
  id: number;
  name: string;
  description?: string;
  report_type: ReportType;
  template_config: Record<string, any>;
  data_source: Record<string, any>;
  default_format: ExportFormat;
  include_charts: boolean;
  include_summary: boolean;
  organization?: string; // UUID
  organization_name?: string;
  is_active: boolean;
  is_public: boolean;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ScheduledReport {
  id: number;
  name: string;
  description?: string;
  template: number;
  template_id?: number;
  frequency: ReportFrequency;
  schedule_config: Record<string, any>;
  recipients: number[];
  email_recipients: string[];
  report_filters: Record<string, any>;
  status: ScheduledReportStatus;
  next_run_at?: string;
  last_run_at?: string;
  organization?: string; // UUID
  organization_name?: string;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ReportExecution {
  id: number;
  scheduled_report?: number;
  template: number;
  template_name?: string;
  status: ReportExecutionStatus;
  parameters: Record<string, any>;
  report_file?: string;
  export_format: ExportFormat;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  execution_time_seconds?: number;
  organization?: string; // UUID
  organization_name?: string;
  created_by?: number;
}

export interface ReportBuilderQuery {
  id: number;
  name: string;
  description?: string;
  query_config: Record<string, any>;
  organization?: string; // UUID
  organization_name?: string;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

// ==================== Analytics Types ====================

export type DashboardType = 'executive' | 'operational' | 'farm' | 'house' | 'flock' | 'custom';
export type KPIType = 'flock_performance' | 'farm_efficiency' | 'cost_management' | 'growth' | 'health' | 'productivity' | 'custom';
export type MetricType = 'count' | 'sum' | 'average' | 'percentage' | 'ratio' | 'trend' | 'comparison';
export type BenchmarkType = 'industry' | 'organization' | 'farm' | 'breed' | 'custom';
export type KPIStatus = 'normal' | 'warning' | 'critical';

export interface Dashboard {
  id: number;
  name: string;
  description?: string;
  dashboard_type: DashboardType;
  layout_config: Record<string, any>;
  default_filters: Record<string, any>;
  organization?: string; // UUID
  organization_name?: string;
  is_public: boolean;
  is_active: boolean;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface KPI {
  id: number;
  name: string;
  description?: string;
  kpi_type: KPIType;
  metric_type: MetricType;
  calculation_config: Record<string, any>;
  unit?: string;
  target_value?: number;
  warning_threshold?: number;
  critical_threshold?: number;
  organization?: string; // UUID
  organization_name?: string;
  is_active: boolean;
  is_public: boolean;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface KPICalculation {
  id: number;
  kpi: number;
  kpi_name?: string;
  value: number;
  unit?: string;
  calculation_date: string;
  calculation_period_start?: string;
  calculation_period_end?: string;
  filters: Record<string, any>;
  previous_value?: number;
  change_percentage?: number;
  status: KPIStatus;
  organization?: string; // UUID
  organization_name?: string;
  calculated_at: string;
  calculated_by?: number;
}

export interface AnalyticsQuery {
  id: number;
  name: string;
  description?: string;
  query_config: Record<string, any>;
  organization?: string; // UUID
  organization_name?: string;
  created_by: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface Benchmark {
  id: number;
  name: string;
  description?: string;
  benchmark_type: BenchmarkType;
  metric_name: string;
  average_value: number;
  min_value?: number;
  max_value?: number;
  percentile_25?: number;
  percentile_75?: number;
  unit?: string;
  period_start?: string;
  period_end?: string;
  filters: Record<string, any>;
  organization?: string; // UUID
  organization_name?: string;
  is_active: boolean;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface TrendAnalysis {
  values: (number | null)[];
  dates: string[];
  trend_direction: 'increasing' | 'decreasing' | 'stable';
  change_percentage: number;
  period_days: number;
  flock_id?: number;
  flock_name?: string;
}

export interface CorrelationAnalysis {
  metric1: string;
  metric2: string;
  correlation_coefficient: number;
  strength: 'strong' | 'moderate' | 'weak' | 'negligible';
  period_days: number;
  data_points: number;
}

export interface FlockComparisonResult {
  flocks: Array<{
    id: number;
    flock_code: string;
    batch_number: string;
    house: string;
    arrival_date: string;
    [key: string]: any; // Dynamic metric values
  }>;
  metrics: Record<string, {
    min: number;
    max: number;
    average: number;
    count: number;
  }>;
  summary: {
    total_flocks: number;
    flocks_with_data: number;
  };
}

export interface BenchmarkComparison {
  flock_id: number;
  flock_name: string;
  metric_name: string;
  flock_value: number;
  benchmark_average: number;
  benchmark_min?: number;
  benchmark_max?: number;
  deviation: number;
  deviation_percentage: number;
  performance_category: 'above_expectation' | 'within_expectation' | 'below_expectation';
  unit?: string;
}
