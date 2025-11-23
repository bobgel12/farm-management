import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { reportingApi } from '../services/reportingApi';
import {
  ReportTemplate,
  ScheduledReport,
  ReportExecution,
  ReportBuilderQuery,
} from '../types';

interface ReportingContextType {
  templates: ReportTemplate[];
  scheduledReports: ScheduledReport[];
  executions: ReportExecution[];
  queries: ReportBuilderQuery[];
  currentTemplate: ReportTemplate | null;
  currentScheduledReport: ScheduledReport | null;
  loading: boolean;
  error: string | null;
  setCurrentTemplate: (template: ReportTemplate | null) => void;
  setCurrentScheduledReport: (report: ScheduledReport | null) => void;
  fetchTemplates: () => Promise<void>;
  fetchTemplate: (id: number) => Promise<ReportTemplate>;
  fetchScheduledReports: () => Promise<void>;
  fetchScheduledReport: (id: number) => Promise<ScheduledReport>;
  fetchExecutions: (params?: { scheduled_report_id?: number; status?: string }) => Promise<void>;
  fetchQueries: () => Promise<void>;
  createTemplate: (data: Partial<ReportTemplate>) => Promise<ReportTemplate>;
  updateTemplate: (id: number, data: Partial<ReportTemplate>) => Promise<ReportTemplate>;
  deleteTemplate: (id: number) => Promise<void>;
  createScheduledReport: (data: Partial<ScheduledReport>) => Promise<ScheduledReport>;
  updateScheduledReport: (id: number, data: Partial<ScheduledReport>) => Promise<ScheduledReport>;
  deleteScheduledReport: (id: number) => Promise<void>;
  runScheduledReportNow: (id: number) => Promise<void>;
  generateReport: (templateId: number, parameters?: Record<string, any>, exportFormat?: string) => Promise<ReportExecution>;
  downloadReportFile: (executionId: number) => Promise<void>;
  createQuery: (data: Partial<ReportBuilderQuery>) => Promise<ReportBuilderQuery>;
  updateQuery: (id: number, data: Partial<ReportBuilderQuery>) => Promise<ReportBuilderQuery>;
  deleteQuery: (id: number) => Promise<void>;
}

const ReportingContext = createContext<ReportingContextType | undefined>(undefined);

export const useReporting = () => {
  const context = useContext(ReportingContext);
  if (context === undefined) {
    throw new Error('useReporting must be used within a ReportingProvider');
  }
  return context;
};

interface ReportingProviderProps {
  children: ReactNode;
}

export const ReportingProvider: React.FC<ReportingProviderProps> = ({ children }) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>([]);
  const [executions, setExecutions] = useState<ReportExecution[]>([]);
  const [queries, setQueries] = useState<ReportBuilderQuery[]>([]);
  const [currentTemplate, setCurrentTemplate] = useState<ReportTemplate | null>(null);
  const [currentScheduledReport, setCurrentScheduledReport] = useState<ScheduledReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await reportingApi.getReportTemplates();
      setTemplates(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch report templates');
      console.error('Error fetching report templates:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTemplate = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const template = await reportingApi.getReportTemplate(id);
      setCurrentTemplate(template);
      return template;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch report template');
      console.error('Error fetching report template:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchScheduledReports = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await reportingApi.getScheduledReports();
      setScheduledReports(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch scheduled reports');
      console.error('Error fetching scheduled reports:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchScheduledReport = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      const report = await reportingApi.getScheduledReport(id);
      setCurrentScheduledReport(report);
      return report;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch scheduled report');
      console.error('Error fetching scheduled report:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchExecutions = useCallback(async (params?: { scheduled_report_id?: number; status?: string }) => {
    try {
      setLoading(true);
      setError(null);
      const data = await reportingApi.getReportExecutions(params);
      setExecutions(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch report executions');
      console.error('Error fetching report executions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchQueries = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await reportingApi.getReportQueries();
      setQueries(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch report queries');
      console.error('Error fetching report queries:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createTemplate = useCallback(async (data: Partial<ReportTemplate>): Promise<ReportTemplate> => {
    try {
      setLoading(true);
      setError(null);
      const template = await reportingApi.createReportTemplate(data);
      await fetchTemplates();
      return template;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create report template';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates]);

  const updateTemplate = useCallback(async (id: number, data: Partial<ReportTemplate>): Promise<ReportTemplate> => {
    try {
      setLoading(true);
      setError(null);
      const template = await reportingApi.updateReportTemplate(id, data);
      await fetchTemplates();
      if (currentTemplate?.id === id) {
        setCurrentTemplate(template);
      }
      return template;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update report template';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates, currentTemplate]);

  const deleteTemplate = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await reportingApi.deleteReportTemplate(id);
      await fetchTemplates();
      if (currentTemplate?.id === id) {
        setCurrentTemplate(null);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete report template';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchTemplates, currentTemplate]);

  const createScheduledReport = useCallback(async (data: Partial<ScheduledReport>): Promise<ScheduledReport> => {
    try {
      setLoading(true);
      setError(null);
      const report = await reportingApi.createScheduledReport(data);
      await fetchScheduledReports();
      return report;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create scheduled report';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchScheduledReports]);

  const updateScheduledReport = useCallback(async (id: number, data: Partial<ScheduledReport>): Promise<ScheduledReport> => {
    try {
      setLoading(true);
      setError(null);
      const report = await reportingApi.updateScheduledReport(id, data);
      await fetchScheduledReports();
      if (currentScheduledReport?.id === id) {
        setCurrentScheduledReport(report);
      }
      return report;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update scheduled report';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchScheduledReports, currentScheduledReport]);

  const deleteScheduledReport = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await reportingApi.deleteScheduledReport(id);
      await fetchScheduledReports();
      if (currentScheduledReport?.id === id) {
        setCurrentScheduledReport(null);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete scheduled report';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchScheduledReports, currentScheduledReport]);

  const runScheduledReportNow = useCallback(async (id: number) => {
    try {
      setError(null);
      await reportingApi.runScheduledReportNow(id);
      await fetchScheduledReports();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to run scheduled report';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchScheduledReports]);

  const generateReport = useCallback(async (
    templateId: number,
    parameters?: Record<string, any>,
    exportFormat?: string
  ): Promise<ReportExecution> => {
    try {
      setLoading(true);
      setError(null);
      const execution = await reportingApi.generateReport(templateId, parameters, exportFormat);
      await fetchExecutions();
      return execution;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to generate report';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchExecutions]);

  const downloadReportFile = useCallback(async (executionId: number) => {
    try {
      setError(null);
      const blob = await reportingApi.downloadReportFile(executionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${executionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to download report';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, []);

  const createQuery = useCallback(async (data: Partial<ReportBuilderQuery>): Promise<ReportBuilderQuery> => {
    try {
      setLoading(true);
      setError(null);
      const query = await reportingApi.createReportQuery(data);
      await fetchQueries();
      return query;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create report query';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchQueries]);

  const updateQuery = useCallback(async (id: number, data: Partial<ReportBuilderQuery>): Promise<ReportBuilderQuery> => {
    try {
      setLoading(true);
      setError(null);
      const query = await reportingApi.updateReportQuery(id, data);
      await fetchQueries();
      return query;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update report query';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchQueries]);

  const deleteQuery = useCallback(async (id: number) => {
    try {
      setLoading(true);
      setError(null);
      await reportingApi.deleteReportQuery(id);
      await fetchQueries();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete report query';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchQueries]);

  const value: ReportingContextType = {
    templates,
    scheduledReports,
    executions,
    queries,
    currentTemplate,
    currentScheduledReport,
    loading,
    error,
    setCurrentTemplate,
    setCurrentScheduledReport,
    fetchTemplates,
    fetchTemplate,
    fetchScheduledReports,
    fetchScheduledReport,
    fetchExecutions,
    fetchQueries,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    createScheduledReport,
    updateScheduledReport,
    deleteScheduledReport,
    runScheduledReportNow,
    generateReport,
    downloadReportFile,
    createQuery,
    updateQuery,
    deleteQuery,
  };

  return (
    <ReportingContext.Provider value={value}>
      {children}
    </ReportingContext.Provider>
  );
};

