import api from './api';
import {
  Dashboard,
  KPI,
  KPICalculation,
  AnalyticsQuery,
  Benchmark,
  TrendAnalysis,
  CorrelationAnalysis,
  BenchmarkComparison,
  PaginatedResponse
} from '../types';

/**
 * Analytics API service
 */
export const analyticsApi = {
  // ==================== Dashboards ====================

  /**
   * Get all dashboards
   */
  async getDashboards(params?: {
    organization_id?: string;
    dashboard_type?: string;
    is_active?: boolean;
  }): Promise<Dashboard[]> {
    const response = await api.get('/dashboards/', { params });
    return response.data;
  },

  /**
   * Get dashboard by ID
   */
  async getDashboard(id: number): Promise<Dashboard> {
    const response = await api.get(`/dashboards/${id}/`);
    return response.data;
  },

  /**
   * Get dashboard data
   */
  async getDashboardData(id: number): Promise<any> {
    const response = await api.get(`/dashboards/${id}/data/`);
    return response.data;
  },

  /**
   * Create a new dashboard
   */
  async createDashboard(data: Partial<Dashboard>): Promise<Dashboard> {
    const response = await api.post('/dashboards/', data);
    return response.data;
  },

  /**
   * Update a dashboard
   */
  async updateDashboard(id: number, data: Partial<Dashboard>): Promise<Dashboard> {
    const response = await api.patch(`/dashboards/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a dashboard
   */
  async deleteDashboard(id: number): Promise<void> {
    await api.delete(`/dashboards/${id}/`);
  },

  // ==================== KPIs ====================

  /**
   * Get all KPIs
   */
  async getKPIs(params?: {
    organization_id?: string;
    kpi_type?: string;
    is_active?: boolean;
  }): Promise<KPI[]> {
    const response = await api.get('/kpis/', { params });
    return response.data;
  },

  /**
   * Get KPI by ID
   */
  async getKPI(id: number): Promise<KPI> {
    const response = await api.get(`/kpis/${id}/`);
    return response.data;
  },

  /**
   * Create a new KPI
   */
  async createKPI(data: Partial<KPI>): Promise<KPI> {
    const response = await api.post('/kpis/', data);
    return response.data;
  },

  /**
   * Update a KPI
   */
  async updateKPI(id: number, data: Partial<KPI>): Promise<KPI> {
    const response = await api.patch(`/kpis/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a KPI
   */
  async deleteKPI(id: number): Promise<void> {
    await api.delete(`/kpis/${id}/`);
  },

  /**
   * Calculate KPI value
   */
  async calculateKPI(id: number, data?: {
    calculation_date?: string;
    filters?: Record<string, any>;
  }): Promise<{
    kpi_id: number;
    kpi_name: string;
    value: number | null;
    unit?: string;
    calculation_date: string;
  }> {
    const response = await api.post(`/kpis/${id}/calculate/`, data);
    return response.data;
  },

  // ==================== KPI Calculations ====================

  /**
   * Get all KPI calculations
   */
  async getKPICalculations(params?: {
    kpi_id?: number;
    organization_id?: string;
    calculation_date?: string;
  }): Promise<KPICalculation[]> {
    const response = await api.get('/kpi-calculations/', { params });
    return response.data;
  },

  /**
   * Get KPI calculation by ID
   */
  async getKPICalculation(id: number): Promise<KPICalculation> {
    const response = await api.get(`/kpi-calculations/${id}/`);
    return response.data;
  },

  // ==================== Analytics Queries ====================

  /**
   * Get all analytics queries
   */
  async getAnalyticsQueries(params?: {
    organization_id?: string;
  }): Promise<AnalyticsQuery[]> {
    const response = await api.get('/analytics-queries/', { params });
    return response.data;
  },

  /**
   * Get analytics query by ID
   */
  async getAnalyticsQuery(id: number): Promise<AnalyticsQuery> {
    const response = await api.get(`/analytics-queries/${id}/`);
    return response.data;
  },

  /**
   * Create a new analytics query
   */
  async createAnalyticsQuery(data: Partial<AnalyticsQuery>): Promise<AnalyticsQuery> {
    const response = await api.post('/analytics-queries/', data);
    return response.data;
  },

  /**
   * Update an analytics query
   */
  async updateAnalyticsQuery(id: number, data: Partial<AnalyticsQuery>): Promise<AnalyticsQuery> {
    const response = await api.patch(`/analytics-queries/${id}/`, data);
    return response.data;
  },

  /**
   * Delete an analytics query
   */
  async deleteAnalyticsQuery(id: number): Promise<void> {
    await api.delete(`/analytics-queries/${id}/`);
  },

  /**
   * Execute an analytics query
   */
  async executeAnalyticsQuery(id: number): Promise<any> {
    const response = await api.post(`/analytics-queries/${id}/execute/`);
    return response.data;
  },

  /**
   * Perform trend analysis
   */
  async performTrendAnalysis(data: {
    flock_id: number;
    metric_type?: string;
    period_days?: number;
  }): Promise<TrendAnalysis> {
    const response = await api.post('/analytics-queries/trend_analysis/', data);
    return response.data;
  },

  /**
   * Perform correlation analysis
   */
  async performCorrelationAnalysis(data: {
    flock_id: number;
    metric1?: string;
    metric2?: string;
    period_days?: number;
  }): Promise<CorrelationAnalysis> {
    const response = await api.post('/analytics-queries/correlation_analysis/', data);
    return response.data;
  },

  // ==================== Benchmarks ====================

  /**
   * Get all benchmarks
   */
  async getBenchmarks(params?: {
    organization_id?: string;
    benchmark_type?: string;
    metric_name?: string;
    is_active?: boolean;
  }): Promise<Benchmark[]> {
    const response = await api.get('/benchmarks/', { params });
    return response.data;
  },

  /**
   * Get benchmark by ID
   */
  async getBenchmark(id: number): Promise<Benchmark> {
    const response = await api.get(`/benchmarks/${id}/`);
    return response.data;
  },

  /**
   * Create a new benchmark
   */
  async createBenchmark(data: Partial<Benchmark>): Promise<Benchmark> {
    const response = await api.post('/benchmarks/', data);
    return response.data;
  },

  /**
   * Update a benchmark
   */
  async updateBenchmark(id: number, data: Partial<Benchmark>): Promise<Benchmark> {
    const response = await api.patch(`/benchmarks/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a benchmark
   */
  async deleteBenchmark(id: number): Promise<void> {
    await api.delete(`/benchmarks/${id}/`);
  },

  /**
   * Compare a flock to a benchmark
   */
  async compareFlockToBenchmark(benchmarkId: number, flockId: number): Promise<BenchmarkComparison> {
    const response = await api.post(`/benchmarks/${benchmarkId}/compare_flock/`, {
      flock_id: flockId
    });
    return response.data;
  },
};

