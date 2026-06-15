import api from './api';

export interface FarmTransferResult {
  status: 'success';
  message: string;
  farm_id: number;
  previous_organization_id: string;
  organization_id: string;
  dashboards_updated: number;
  automation_workflows_updated: number;
}

function unwrapResponse<T>(response: { data: T | { data: T } }): T {
  const payload = response.data as { data?: T };
  return payload?.data ?? (response.data as T);
}

export function extractApiErrorMessage(err: unknown, fallback = 'Request failed'): string {
  const axiosErr = err as { response?: { data?: Record<string, unknown> } };
  const data = axiosErr.response?.data;
  if (!data) {
    return fallback;
  }

  const errorField = data.error;
  if (typeof errorField === 'string') {
    return errorField;
  }
  if (errorField && typeof errorField === 'object') {
    const nested = (errorField as { error?: string; message?: string }).error
      || (errorField as { message?: string }).message;
    if (nested) {
      return nested;
    }
  }

  if (typeof data.message === 'string') {
    return data.message;
  }

  return fallback;
}

export const farmsApi = {
  async transferFarm(
    farmId: number,
    targetOrganizationId: string
  ): Promise<FarmTransferResult> {
    const response = await api.post(`/farms/${farmId}/transfer/`, {
      target_organization_id: targetOrganizationId,
    });
    return unwrapResponse<FarmTransferResult>(response);
  },
};
