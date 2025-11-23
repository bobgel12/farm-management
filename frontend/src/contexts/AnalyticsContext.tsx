import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { analyticsApi } from '../services/analyticsApi';
import {
  Dashboard,
  KPI,
  KPICalculation,
  Benchmark,
  TrendAnalysis,
  CorrelationAnalysis,
  BenchmarkComparison,
} from '../types';

interface AnalyticsContextType {
  dashboards: Dashboard[];
  currentDashboard: Dashboard | null;
  kpis: KPI[];
  kpiCalculations: KPICalculation[];
  benchmarks: Benchmark[];
  loading: boolean;
  error: string | null;
  setCurrentDashboard: (dashboard: Dashboard | null) => void;
  fetchDashboards: (organizationId?: string) => Promise<void>;
  fetchDashboard: (id: number) => Promise<Dashboard>;
  fetchDashboardData: (id: number) => Promise<any>;
  createDashboard: (data: Partial<Dashboard>) => Promise<Dashboard>;
  updateDashboard: (id: number, data: Partial<Dashboard>) => Promise<Dashboard>;
  deleteDashboard: (id: number) => Promise<void>;
  fetchKPIs: (organizationId?: string) => Promise<void>;
  fetchKPI: (id: number) => Promise<KPI>;
  calculateKPI: (id: number, calculationDate?: string, filters?: Record<string, any>) => Promise<any>;
  fetchKPICalculations: (kpiId?: number, organizationId?: string) => Promise<void>;
  fetchBenchmarks: (organizationId?: string) => Promise<void>;
  compareFlockToBenchmark: (benchmarkId: number, flockId: number) => Promise<BenchmarkComparison>;
  performTrendAnalysis: (flockId: number, metricType?: string, periodDays?: number) => Promise<TrendAnalysis>;
  performCorrelationAnalysis: (flockId: number, metric1?: string, metric2?: string, periodDays?: number) => Promise<CorrelationAnalysis>;
}

const AnalyticsContext = createContext<AnalyticsContextType | undefined>(undefined);

export const useAnalytics = () => {
  const context = useContext(AnalyticsContext);
  if (context === undefined) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  return context;
};

interface AnalyticsProviderProps {
  children: ReactNode;
}

export const AnalyticsProvider: React.FC<AnalyticsProviderProps> = ({ children }) => {
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [currentDashboard, setCurrentDashboard] = useState<Dashboard | null>(null);
  const [kpis, setKPIs] = useState<KPI[]>([]);
  const [kpiCalculations, setKPICalculations] = useState<KPICalculation[]>([]);
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboards = useCallback(async (organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params = organizationId ? { organization_id: organizationId } : undefined;
      const data = await analyticsApi.getDashboards(params);
      setDashboards(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dashboards');
      console.error('Error fetching dashboards:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDashboard = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const dashboard = await analyticsApi.getDashboard(id);
      setCurrentDashboard(dashboard);
      return dashboard;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dashboard');
      console.error('Error fetching dashboard:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDashboardData = useCallback(async (id: number) => {
    try {
      setError(null);
      const data = await analyticsApi.getDashboardData(id);
      return data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch dashboard data');
      console.error('Error fetching dashboard data:', err);
      throw err;
    }
  }, []);

  const createDashboard = useCallback(async (data: Partial<Dashboard>): Promise<Dashboard> => {
    try {
      setLoading(true);
      setError(null);
      const dashboard = await analyticsApi.createDashboard(data);
      await fetchDashboards();
      return dashboard;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create dashboard';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchDashboards]);

  const updateDashboard = useCallback(async (id: number, data: Partial<Dashboard>): Promise<Dashboard> => {
    try {
      setLoading(true);
      setError(null);
      const dashboard = await analyticsApi.updateDashboard(id, data);
      await fetchDashboards();
      if (currentDashboard?.id === id) {
        setCurrentDashboard(dashboard);
      }
      return dashboard;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update dashboard';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchDashboards, currentDashboard]);

  const deleteDashboard = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await analyticsApi.deleteDashboard(id);
      await fetchDashboards();
      if (currentDashboard?.id === id) {
        setCurrentDashboard(null);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete dashboard';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchDashboards, currentDashboard]);

  const fetchKPIs = useCallback(async (organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params = organizationId ? { organization_id: organizationId } : undefined;
      const data = await analyticsApi.getKPIs(params);
      setKPIs(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch KPIs');
      console.error('Error fetching KPIs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchKPI = useCallback(async (id: number) => {
    try {
      setError(null);
      const kpi = await analyticsApi.getKPI(id);
      return kpi;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch KPI');
      console.error('Error fetching KPI:', err);
      throw err;
    }
  }, []);

  const calculateKPI = useCallback(async (
    id: number,
    calculationDate?: string,
    filters?: Record<string, any>
  ) => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.calculateKPI(id, {
        calculation_date: calculationDate,
        filters,
      });
      return result;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to calculate KPI';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchKPICalculations = useCallback(async (kpiId?: number, organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params: any = {};
      if (kpiId) params.kpi_id = kpiId;
      if (organizationId) params.organization_id = organizationId;
      const data = await analyticsApi.getKPICalculations(params);
      setKPICalculations(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch KPI calculations');
      console.error('Error fetching KPI calculations:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchBenchmarks = useCallback(async (organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const params = organizationId ? { organization_id: organizationId } : undefined;
      const data = await analyticsApi.getBenchmarks(params);
      setBenchmarks(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch benchmarks');
      console.error('Error fetching benchmarks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const compareFlockToBenchmark = useCallback(async (
    benchmarkId: number,
    flockId: number
  ): Promise<BenchmarkComparison> => {
    try {
      setLoading(true);
      setError(null);
      const comparison = await analyticsApi.compareFlockToBenchmark(benchmarkId, flockId);
      return comparison;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to compare flock to benchmark';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const performTrendAnalysis = useCallback(async (
    flockId: number,
    metricType: string = 'weight',
    periodDays: number = 30
  ): Promise<TrendAnalysis> => {
    try {
      setLoading(true);
      setError(null);
      const analysis = await analyticsApi.performTrendAnalysis({
        flock_id: flockId,
        metric_type: metricType,
        period_days: periodDays,
      });
      return analysis;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to perform trend analysis';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const performCorrelationAnalysis = useCallback(async (
    flockId: number,
    metric1: string = 'weight',
    metric2: string = 'feed_consumption',
    periodDays: number = 30
  ): Promise<CorrelationAnalysis> => {
    try {
      setLoading(true);
      setError(null);
      const analysis = await analyticsApi.performCorrelationAnalysis({
        flock_id: flockId,
        metric1,
        metric2,
        period_days: periodDays,
      });
      return analysis;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to perform correlation analysis';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  const value: AnalyticsContextType = {
    dashboards,
    currentDashboard,
    kpis,
    kpiCalculations,
    benchmarks,
    loading,
    error,
    setCurrentDashboard,
    fetchDashboards,
    fetchDashboard,
    fetchDashboardData,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    fetchKPIs,
    fetchKPI,
    calculateKPI,
    fetchKPICalculations,
    fetchBenchmarks,
    compareFlockToBenchmark,
    performTrendAnalysis,
    performCorrelationAnalysis,
  };

  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
};

