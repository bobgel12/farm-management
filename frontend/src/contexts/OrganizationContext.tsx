import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { organizationsApi } from '../services/organizationsApi';
import {
  Organization,
  OrganizationMembership,
  OrganizationUser,
  OrganizationInvite,
} from '../types';

interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: OrganizationMembership[];
  members: OrganizationUser[];
  pendingInvites: OrganizationInvite[];
  loading: boolean;
  error: string | null;
  setCurrentOrganization: (org: Organization | null) => void;
  fetchMyOrganizations: () => Promise<void>;
  fetchOrganization: (id: string) => Promise<void>;
  fetchMembers: (organizationId: string) => Promise<void>;
  fetchPendingInvites: (organizationId: string) => Promise<void>;
  createOrganization: (data: Partial<Organization>) => Promise<Organization>;
  updateOrganization: (id: string, data: Partial<Organization>) => Promise<Organization>;
  deleteOrganization: (id: string) => Promise<void>;
  addMember: (organizationId: string, userId: number, role?: string) => Promise<void>;
  removeMember: (organizationId: string, userId: number) => Promise<void>;
  updateMember: (memberId: number, data: Partial<OrganizationUser>) => Promise<void>;
  sendInvite: (organizationId: string, email: string, role?: string, permissions?: {
    can_manage_farms?: boolean;
    can_manage_users?: boolean;
    can_view_reports?: boolean;
    can_export_data?: boolean;
  }) => Promise<OrganizationInvite>;
  resendInvite: (organizationId: string, inviteId: string) => Promise<void>;
  cancelInvite: (organizationId: string, inviteId: string) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  isOwner: boolean;
  isAdmin: boolean;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
};

interface OrganizationProviderProps {
  children: ReactNode;
}

export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [members, setMembers] = useState<OrganizationUser[]>([]);
  const [pendingInvites, setPendingInvites] = useState<OrganizationInvite[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load organizations on mount (but not on login page)
  useEffect(() => {
    const isLoginPage = window.location.pathname === '/login' || 
                       window.location.pathname === '/forgot-password' ||
                       window.location.pathname === '/reset-password' ||
                       window.location.pathname.startsWith('/accept-invite');
    
    if (!isLoginPage) {
      fetchMyOrganizations();
    }
  }, []);

  // Load current organization members when organization changes
  useEffect(() => {
    if (currentOrganization) {
      fetchMembers(currentOrganization.id);
    } else {
      setMembers([]);
      setPendingInvites([]);
    }
  }, [currentOrganization]);

  const fetchMyOrganizations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await organizationsApi.getMyOrganizations();
      setOrganizations(data);
      
      // Set first organization as current if none is selected
      if (!currentOrganization && data.length > 0) {
        setCurrentOrganization(data[0].organization);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch organizations');
      console.error('Error fetching organizations:', err);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization]);

  const fetchOrganization = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const org = await organizationsApi.getOrganization(id);
      setCurrentOrganization(org);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch organization');
      console.error('Error fetching organization:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMembers = useCallback(async (organizationId: string) => {
    try {
      setError(null);
      const data = await organizationsApi.getOrganizationMembers(organizationId);
      setMembers(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch members');
      console.error('Error fetching members:', err);
    }
  }, []);

  const createOrganization = useCallback(async (data: Partial<Organization>): Promise<Organization> => {
    try {
      setLoading(true);
      setError(null);
      const org = await organizationsApi.createOrganization(data);
      await fetchMyOrganizations();
      setCurrentOrganization(org);
      return org;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create organization';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [fetchMyOrganizations]);

  const updateOrganization = useCallback(async (id: string, data: Partial<Organization>): Promise<Organization> => {
    try {
      setLoading(true);
      setError(null);
      const org = await organizationsApi.updateOrganization(id, data);
      if (currentOrganization?.id === id) {
        setCurrentOrganization(org);
      }
      await fetchMyOrganizations();
      return org;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update organization';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization, fetchMyOrganizations]);

  const addMember = useCallback(async (organizationId: string, userId: number, role: string = 'worker') => {
    try {
      setError(null);
      await organizationsApi.addMember(organizationId, { user_id: userId, role: role as any });
      await fetchMembers(organizationId);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add member';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchMembers]);

  const removeMember = useCallback(async (organizationId: string, userId: number) => {
    try {
      setError(null);
      await organizationsApi.removeMember(organizationId, userId);
      await fetchMembers(organizationId);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to remove member';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchMembers]);

  const updateMember = useCallback(async (memberId: number, data: Partial<OrganizationUser>) => {
    try {
      setError(null);
      await organizationsApi.updateOrganizationUser(memberId, data);
      if (currentOrganization) {
        await fetchMembers(currentOrganization.id);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || 'Failed to update member';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [currentOrganization, fetchMembers]);

  const deleteOrganization = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      await organizationsApi.deleteOrganization(id);
      await fetchMyOrganizations();
      if (currentOrganization?.id === id) {
        setCurrentOrganization(null);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete organization';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [currentOrganization, fetchMyOrganizations]);

  const fetchPendingInvites = useCallback(async (organizationId: string) => {
    try {
      setError(null);
      const data = await organizationsApi.getPendingInvites(organizationId);
      setPendingInvites(data);
    } catch (err: any) {
      // Don't set error for 403, just means user can't view invites
      if (err.response?.status !== 403) {
        setError(err.response?.data?.detail || 'Failed to fetch invites');
      }
      setPendingInvites([]);
    }
  }, []);

  const sendInvite = useCallback(async (
    organizationId: string, 
    email: string, 
    role: string = 'worker',
    permissions?: {
      can_manage_farms?: boolean;
      can_manage_users?: boolean;
      can_view_reports?: boolean;
      can_export_data?: boolean;
    }
  ): Promise<OrganizationInvite> => {
    try {
      setError(null);
      const result = await organizationsApi.sendInvite(organizationId, {
        email,
        role: role as any,
        ...permissions
      });
      await fetchPendingInvites(organizationId);
      return result.invite;
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Failed to send invite';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchPendingInvites]);

  const resendInvite = useCallback(async (organizationId: string, inviteId: string) => {
    try {
      setError(null);
      await organizationsApi.resendInvite(organizationId, inviteId);
      await fetchPendingInvites(organizationId);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Failed to resend invite';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchPendingInvites]);

  const cancelInvite = useCallback(async (organizationId: string, inviteId: string) => {
    try {
      setError(null);
      await organizationsApi.cancelInvite(organizationId, inviteId);
      await fetchPendingInvites(organizationId);
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || 'Failed to cancel invite';
      setError(errorMsg);
      throw new Error(errorMsg);
    }
  }, [fetchPendingInvites]);

  // Get current user's membership in current organization
  const currentMembership = organizations.find(
    (m) => m.organization.id === currentOrganization?.id
  );

  const hasPermission = useCallback((permission: string): boolean => {
    if (!currentMembership) return false;
    
    if (currentMembership.is_owner || currentMembership.is_admin) return true;
    
    switch (permission) {
      case 'manage_farms':
        return currentMembership.can_manage_farms;
      case 'manage_users':
        return currentMembership.can_manage_users;
      case 'view_reports':
        return currentMembership.can_view_reports;
      case 'export_data':
        return currentMembership.can_export_data;
      default:
        return false;
    }
  }, [currentMembership]);

  const isOwner = currentMembership?.is_owner || false;
  const isAdmin = currentMembership?.is_admin || false;

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    members,
    pendingInvites,
    loading,
    error,
    setCurrentOrganization,
    fetchMyOrganizations,
    fetchOrganization,
    fetchMembers,
    fetchPendingInvites,
    createOrganization,
    updateOrganization,
    deleteOrganization,
    addMember,
    removeMember,
    updateMember,
    sendInvite,
    resendInvite,
    cancelInvite,
    hasPermission,
    isOwner,
    isAdmin,
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
};

