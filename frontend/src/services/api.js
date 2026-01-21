// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('🔑 Token from localStorage:', token ? 'exists' : 'missing'); // Debug
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Added Authorization header'); // Debug
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.log('❌ 401 Unauthorized - clearing token');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

// Admin API endpoints
export const adminAPI = {
  // Teams
  getTeams: () => api.get('/admin/teams'),
  createTeam: (data) => api.post('/admin/teams', data),
  deleteTeam: (id) => api.delete(`/admin/teams/${id}`),

  // Boards
  getBoards: () => api.get('/admin/boards'),
  createBoard: (data) => api.post('/admin/boards', data),
  updateBoard: (id, data) => api.put(`/admin/boards/${id}`, data),
  deleteBoard: (id) => api.delete(`/admin/boards/${id}`),

  // Users
  getUsers: () => api.get('/admin/users'),
  updateUserRole: (id, role) => api.put(`/admin/users/${id}/role`, { role }),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
};

// Manager API endpoints
export const managerAPI = {
  // Tasks
  createTask: (data) => api.post('/manager/tasks', data),
  getBoardTasks: (boardId) => api.get(`/manager/boards/${boardId}/tasks`),
  updateTask: (id, data) => api.put(`/manager/tasks/${id}`, data),
  deleteTask: (id) => api.delete(`/manager/tasks/${id}`),
  assignTask: (taskId, userId) => api.put(`/manager/tasks/${taskId}/assign`, { user_id: userId }),
};

// Tasks API endpoints
export const tasksAPI = {
  getMyTasks: () => api.get('/tasks/my-tasks'),
  getBoardTasks: (boardId) => api.get(`/tasks/boards/${boardId}/tasks`),
  getTask: (id) => api.get(`/tasks/tasks/${id}`),
  updateTaskStatus: (id, status) => api.put(`/tasks/tasks/${id}/status`, { status }),
  getMyBoards: () => api.get('/tasks/my-boards'),
  getBoardDetails: (id) => api.get(`/tasks/boards/${id}`),
};

// Users API endpoints
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Chat API endpoints
export const chatAPI = {
  getOnlineUsers: (boardId) => api.get(`/chat/boards/${boardId}/online-users`),
  connectToBoard: (boardId, token) => {
    const protocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const host = API_BASE_URL.replace(/^https?:\/\//, '');
    const wsUrl = `${protocol}://${host}/chat/ws/${boardId}?token=${token}`;
    return new WebSocket(wsUrl);
  },
};

// Activity API endpoints
export const activityAPI = {
  getRecentActivity: () => api.get('/activity/'),
};

export default api;