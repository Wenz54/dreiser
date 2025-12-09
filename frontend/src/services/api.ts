import axios from 'axios'
import { toast } from 'react-toastify'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// V1 API (legacy)
export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// V2 API (arbitrage bot)
export const apiV2 = axios.create({
  baseURL: `${API_URL}/api/v2`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - добавляем JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - обработка ошибок
const errorInterceptor = (error: any) => {
  if (error.response?.status === 401) {
    // Unauthorized - redirect to login
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    window.location.href = '/login'
  }
  
  const message = error.response?.data?.detail || 'An error occurred'
  toast.error(message)
  
  return Promise.reject(error)
}

api.interceptors.response.use((response) => response, errorInterceptor)
apiV2.interceptors.response.use((response) => response, errorInterceptor)

// V2 API request interceptor
apiV2.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// V2 API endpoints
export const engineAPI = {
  getStatus: () => apiV2.get('/engine/status'),
  getConfig: () => apiV2.get('/engine/config'),
  start: () => apiV2.post('/engine/start'),
  stop: () => apiV2.post('/engine/stop'),
  restart: () => apiV2.post('/engine/restart'),
  saveConfig: (config: any) => apiV2.post('/engine/config', config),
}

export const arbitrageAPI = {
  getStats: () => apiV2.get('/arbitrage/stats'),
  getProfitHistory: () => apiV2.get('/arbitrage/profit-history'),
  getHistory: (params: any) => apiV2.get('/arbitrage/history', { params }),
  exportHistory: () => apiV2.get('/arbitrage/history/export', { responseType: 'blob' }),
}

export const operationsAPI = {
  getLatest: (limit: number = 50) => apiV2.get('/operations/latest', { params: { limit } }),
  getStats: () => apiV2.get('/operations/stats'),
}

export default api











