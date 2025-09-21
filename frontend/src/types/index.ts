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

export interface Farm {
  id: number;
  name: string;
  location: string;
  contact_email: string;
  contact_phone: string;
  created_at: string;
  updated_at: string;
  owner: number;
}

export interface House {
  id: number;
  name: string;
  capacity: number;
  current_population: number;
  farm: number;
  created_at: string;
  updated_at: string;
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
