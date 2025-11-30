import axios from 'axios';
import { Issue, IssueListItem, IssueCreate, IssuePhoto, IssueComment, IssueStatus, IssueCategory, IssuePriority } from '../types';

// Use the same pattern as api.ts - REACT_APP_API_URL already includes /api
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  return 'http://localhost:8002/api';
};

const API_BASE_URL = getApiUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export interface IssueFilters {
  house_id?: number;
  farm_id?: number;
  status?: IssueStatus | 'open'; // 'open' includes open and in_progress
  category?: IssueCategory;
  priority?: IssuePriority;
  my_issues?: boolean;
}

export const issuesApi = {
  // Get issues with optional filters
  getIssues: async (filters: IssueFilters = {}): Promise<IssueListItem[]> => {
    const params = new URLSearchParams();
    if (filters.house_id) params.append('house_id', filters.house_id.toString());
    if (filters.farm_id) params.append('farm_id', filters.farm_id.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.category) params.append('category', filters.category);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.my_issues) params.append('my_issues', 'true');
    
    const response = await api.get(`/issues/?${params.toString()}`);
    // Handle paginated response
    if (response.data && Array.isArray(response.data.results)) {
      return response.data.results;
    }
    // Handle non-paginated response (direct array)
    if (Array.isArray(response.data)) {
      return response.data;
    }
    // Fallback to empty array
    return [];
  },

  // Get a single issue with full details
  getIssue: async (id: number): Promise<Issue> => {
    const response = await api.get(`/issues/${id}/`);
    return response.data;
  },

  // Create a new issue
  createIssue: async (data: IssueCreate): Promise<Issue> => {
    const response = await api.post('/issues/', data);
    return response.data;
  },

  // Update an issue
  updateIssue: async (id: number, data: Partial<IssueCreate & { status?: IssueStatus; assigned_to?: number }>): Promise<Issue> => {
    const response = await api.patch(`/issues/${id}/`, data);
    return response.data;
  },

  // Delete an issue
  deleteIssue: async (id: number): Promise<void> => {
    await api.delete(`/issues/${id}/`);
  },

  // Add photos to an issue
  addPhotos: async (issueId: number, photos: Array<{ image: string; caption?: string }>): Promise<{ photos: IssuePhoto[] }> => {
    const response = await api.post(`/issues/${issueId}/photos/`, { photos });
    return response.data;
  },

  // Add a single photo
  addPhoto: async (issueId: number, image: string, caption?: string): Promise<{ photos: IssuePhoto[] }> => {
    const response = await api.post(`/issues/${issueId}/photos/`, { image, caption });
    return response.data;
  },

  // Delete a photo
  deletePhoto: async (issueId: number, photoId: number): Promise<void> => {
    await api.delete(`/issues/${issueId}/photos/${photoId}/`);
  },

  // Resolve an issue
  resolveIssue: async (id: number, resolutionNotes?: string): Promise<Issue> => {
    const response = await api.post(`/issues/${id}/resolve/`, { resolution_notes: resolutionNotes });
    return response.data;
  },

  // Reopen an issue
  reopenIssue: async (id: number): Promise<Issue> => {
    const response = await api.post(`/issues/${id}/reopen/`);
    return response.data;
  },

  // Create a task from an issue
  createTask: async (issueId: number, data: {
    title?: string;
    worker_id?: number;
    due_date?: string;
    priority?: 'low' | 'medium' | 'high';
  }): Promise<{ task_id: number; task_title: string; message: string }> => {
    const response = await api.post(`/issues/${issueId}/create-task/`, data);
    return response.data;
  },

  // Get comments for an issue
  getComments: async (issueId: number): Promise<IssueComment[]> => {
    const response = await api.get(`/issues/${issueId}/comments/`);
    return response.data;
  },

  // Add a comment to an issue
  addComment: async (issueId: number, content: string): Promise<IssueComment> => {
    const response = await api.post(`/issues/${issueId}/comments/`, { content });
    return response.data;
  },
};

export default issuesApi;

