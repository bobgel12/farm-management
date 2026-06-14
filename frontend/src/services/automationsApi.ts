import api from './api';

export interface AutomationWorkflow {
  id: number;
  slug: string;
  name: string;
  description: string;
  organization: string;
  farm_id: number | null;
  farm_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AutomationWorkflowInput {
  slug: string;
  name: string;
  description?: string;
  webhook_url: string;
  webhook_secret?: string;
  organization: string;
  farm?: number | null;
  is_active?: boolean;
}

export interface AutomationTriggerResult {
  status: 'success' | 'failed';
  message: string;
  execution_time: number;
  workflow_slug: string;
}

function unwrapResponse<T>(response: { data: T | { data: T } }): T {
  const payload = response.data as { data?: T };
  return payload?.data ?? (response.data as T);
}

/**
 * n8n automation workflow API service
 */
export const automationsApi = {
  async listWorkflows(params?: {
    organization_id?: string;
    farm_id?: number;
  }): Promise<AutomationWorkflow[]> {
    const response = await api.get('/automations/', { params });
    const data = unwrapResponse<{ results?: AutomationWorkflow[] } | AutomationWorkflow[]>(response);
    if (Array.isArray(data)) {
      return data;
    }
    return data.results ?? [];
  },

  async createWorkflow(data: AutomationWorkflowInput): Promise<AutomationWorkflow> {
    const response = await api.post('/automations/', data);
    return unwrapResponse<AutomationWorkflow>(response);
  },

  async updateWorkflow(
    id: number,
    data: Partial<AutomationWorkflowInput>
  ): Promise<AutomationWorkflow> {
    const response = await api.patch(`/automations/${id}/`, data);
    return unwrapResponse<AutomationWorkflow>(response);
  },

  async deleteWorkflow(id: number): Promise<void> {
    await api.delete(`/automations/${id}/`);
  },

  async triggerWorkflow(
    slug: string,
    options?: {
      organizationId?: string;
      farmId?: number;
      payload?: Record<string, unknown>;
    }
  ): Promise<AutomationTriggerResult> {
    const response = await api.post(`/automations/${slug}/trigger/`, {
      organization_id: options?.organizationId,
      farm_id: options?.farmId,
      payload: options?.payload ?? {},
    });
    return unwrapResponse<AutomationTriggerResult>(response);
  },

  async testWorkflow(
    slug: string,
    options?: {
      organizationId?: string;
      farmId?: number;
    }
  ): Promise<AutomationTriggerResult> {
    const response = await api.post(`/automations/${slug}/test/`, {
      organization_id: options?.organizationId,
      farm_id: options?.farmId,
    });
    return unwrapResponse<AutomationTriggerResult>(response);
  },
};
