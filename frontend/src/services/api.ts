import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API endpoints
export const overviewApi = {
  get: () => api.get('/overview'),
}

export const resourcesApi = {
  list: (params?: { region?: string; cluster?: string; project?: string }) =>
    api.get('/resources', { params }),
  get: (id: string) => api.get(`/resources/${id}`),
}

export const deploymentsApi = {
  list: (params?: { service?: string; project?: string }) =>
    api.get('/deployments', { params }),
  get: (id: string) => api.get(`/deployments/${id}`),
  getChain: (id: string) => api.get(`/deployments/${id}/chain`),
}

export const alertsApi = {
  list: (params?: { project?: string; severity?: string; status?: string }) =>
    api.get('/alerts', { params }),
  get: (id: string) => api.get(`/alerts/${id}`),
}

export const ticketsApi = {
  list: (params?: { assignee?: string; project?: string; status?: string }) =>
    api.get('/tickets', { params }),
  get: (id: string) => api.get(`/tickets/${id}`),
  create: (data: Partial<Ticket>) => api.post('/tickets', data),
  update: (id: string, data: Partial<Ticket>) => api.put(`/tickets/${id}`, data),
}

export const aiApi = {
  query: (q: string, context?: Record<string, unknown>) =>
    api.get('/ai/query', { params: { q, ...context } }),
  chat: (message: string, conversationId?: string) =>
    api.post('/ai/chat', { message, conversationId }),
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

// Type exports
import { Ticket } from '../types'
