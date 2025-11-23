import api from './api';
import {
  ReportTemplate,
  ScheduledReport,
  ReportExecution,
  ReportBuilderQuery,
  PaginatedResponse
} from '../types';

/**
 * Reporting API service
 */
export const reportingApi = {
  // ==================== Report Templates ====================

  /**
   * Get all report templates
   */
  async getReportTemplates(params?: {
    organization_id?: string;
    report_type?: string;
    is_active?: boolean;
  }): Promise<ReportTemplate[]> {
    const response = await api.get('/report-templates/', { params });
    return response.data;
  },

  /**
   * Get report template by ID
   */
  async getReportTemplate(id: number): Promise<ReportTemplate> {
    const response = await api.get(`/report-templates/${id}/`);
    return response.data;
  },

  /**
   * Create a new report template
   */
  async createReportTemplate(data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    const response = await api.post('/report-templates/', data);
    return response.data;
  },

  /**
   * Update a report template
   */
  async updateReportTemplate(id: number, data: Partial<ReportTemplate>): Promise<ReportTemplate> {
    const response = await api.patch(`/report-templates/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a report template
   */
  async deleteReportTemplate(id: number): Promise<void> {
    await api.delete(`/report-templates/${id}/`);
  },

  // ==================== Scheduled Reports ====================

  /**
   * Get all scheduled reports
   */
  async getScheduledReports(params?: {
    organization_id?: string;
    status?: string;
  }): Promise<ScheduledReport[]> {
    const response = await api.get('/scheduled-reports/', { params });
    return response.data;
  },

  /**
   * Get scheduled report by ID
   */
  async getScheduledReport(id: number): Promise<ScheduledReport> {
    const response = await api.get(`/scheduled-reports/${id}/`);
    return response.data;
  },

  /**
   * Create a new scheduled report
   */
  async createScheduledReport(data: Partial<ScheduledReport>): Promise<ScheduledReport> {
    const response = await api.post('/scheduled-reports/', data);
    return response.data;
  },

  /**
   * Update a scheduled report
   */
  async updateScheduledReport(id: number, data: Partial<ScheduledReport>): Promise<ScheduledReport> {
    const response = await api.patch(`/scheduled-reports/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a scheduled report
   */
  async deleteScheduledReport(id: number): Promise<void> {
    await api.delete(`/scheduled-reports/${id}/`);
  },

  /**
   * Trigger scheduled report to run immediately
   */
  async runScheduledReportNow(id: number): Promise<void> {
    await api.post(`/scheduled-reports/${id}/run_now/`);
  },

  // ==================== Report Executions ====================

  /**
   * Get all report executions
   */
  async getReportExecutions(params?: {
    organization_id?: string;
    scheduled_report_id?: number;
    status?: string;
  }): Promise<ReportExecution[]> {
    const response = await api.get('/report-executions/', { params });
    return response.data;
  },

  /**
   * Get report execution by ID
   */
  async getReportExecution(id: number): Promise<ReportExecution> {
    const response = await api.get(`/report-executions/${id}/`);
    return response.data;
  },

  /**
   * Download report file
   */
  async downloadReportFile(id: number): Promise<Blob> {
    const response = await api.get(`/report-executions/${id}/download/`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // ==================== Report Builder Queries ====================

  /**
   * Get all report builder queries
   */
  async getReportQueries(params?: {
    organization_id?: string;
  }): Promise<ReportBuilderQuery[]> {
    const response = await api.get('/report-queries/', { params });
    return response.data;
  },

  /**
   * Get report query by ID
   */
  async getReportQuery(id: number): Promise<ReportBuilderQuery> {
    const response = await api.get(`/report-queries/${id}/`);
    return response.data;
  },

  /**
   * Create a new report query
   */
  async createReportQuery(data: Partial<ReportBuilderQuery>): Promise<ReportBuilderQuery> {
    const response = await api.post('/report-queries/', data);
    return response.data;
  },

  /**
   * Update a report query
   */
  async updateReportQuery(id: number, data: Partial<ReportBuilderQuery>): Promise<ReportBuilderQuery> {
    const response = await api.patch(`/report-queries/${id}/`, data);
    return response.data;
  },

  /**
   * Delete a report query
   */
  async deleteReportQuery(id: number): Promise<void> {
    await api.delete(`/report-queries/${id}/`);
  },

  // ==================== Report Generation ====================

  /**
   * Generate a report from template
   */
  async generateReport(templateId: number, parameters?: Record<string, any>, exportFormat?: string): Promise<ReportExecution> {
    const response = await api.post(`/report-templates/${templateId}/generate/`, {
      parameters,
      export_format: exportFormat
    });
    return response.data;
  },
};

