import api from './api';
import {
  Organization,
  OrganizationUser,
  OrganizationMembership,
  PaginatedResponse
} from '../types';

/**
 * Organizations API service
 */
export const organizationsApi = {
  /**
   * Get all organizations for the current user
   */
  async getMyOrganizations(): Promise<OrganizationMembership[]> {
    const response = await api.get('/organizations/my-organizations/');
    return response.data;
  },

  /**
   * Get all organizations (admin only)
   */
  async getOrganizations(params?: {
    organization_id?: string;
    is_active?: boolean;
  }): Promise<Organization[]> {
    const response = await api.get('/organizations/', { params });
    return response.data;
  },

  /**
   * Get organization by ID
   */
  async getOrganization(id: string): Promise<Organization> {
    const response = await api.get(`/organizations/${id}/`);
    return response.data;
  },

  /**
   * Create a new organization
   */
  async createOrganization(data: Partial<Organization>): Promise<Organization> {
    const response = await api.post('/organizations/', data);
    return response.data;
  },

  /**
   * Update an organization
   */
  async updateOrganization(id: string, data: Partial<Organization>): Promise<Organization> {
    const response = await api.patch(`/organizations/${id}/`, data);
    return response.data;
  },

  /**
   * Delete an organization
   */
  async deleteOrganization(id: string): Promise<void> {
    await api.delete(`/organizations/${id}/`);
  },

  /**
   * Get organization members
   */
  async getOrganizationMembers(organizationId: string): Promise<OrganizationUser[]> {
    const response = await api.get(`/organizations/${organizationId}/members/`);
    return response.data;
  },

  /**
   * Add a member to an organization
   */
  async addMember(organizationId: string, data: {
    user_id: number;
    role?: 'owner' | 'admin' | 'manager' | 'worker' | 'viewer';
    can_manage_farms?: boolean;
    can_manage_users?: boolean;
    can_view_reports?: boolean;
    can_export_data?: boolean;
  }): Promise<OrganizationUser> {
    const response = await api.post(`/organizations/${organizationId}/add_member/`, data);
    return response.data;
  },

  /**
   * Remove a member from an organization
   */
  async removeMember(organizationId: string, userId: number): Promise<void> {
    await api.delete(`/organizations/${organizationId}/remove_member/`, {
      data: { user_id: userId }
    });
  },

  /**
   * Get organization user by ID
   */
  async getOrganizationUser(id: number): Promise<OrganizationUser> {
    const response = await api.get(`/organization-users/${id}/`);
    return response.data;
  },

  /**
   * Update organization user
   */
  async updateOrganizationUser(id: number, data: Partial<OrganizationUser>): Promise<OrganizationUser> {
    const response = await api.patch(`/organization-users/${id}/`, data);
    return response.data;
  },

  /**
   * Delete organization user
   */
  async deleteOrganizationUser(id: number): Promise<void> {
    await api.delete(`/organization-users/${id}/`);
  },
};

