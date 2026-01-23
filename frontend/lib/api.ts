/**
 * API client for EpiSphere AI backend
 */

import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token')
      if (typeof window !== 'undefined') {
        window.location.href = '/auth/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  register: async (userData: any) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Cases endpoints
export const casesApi = {
  list: async (params?: any) => {
    const response = await api.get('/cases', { params })
    return response.data
  },
  create: async (caseData: any) => {
    const response = await api.post('/cases', caseData)
    return response.data
  },
  upload: async (file: File, countryId: number, diseaseId: number) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('country_id', countryId.toString())
    formData.append('disease_id', diseaseId.toString())
    const response = await api.post('/cases/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  getStats: async (params?: any) => {
    const response = await api.get('/cases/stats', { params })
    return response.data
  },
}

// Alerts endpoints
export const alertsApi = {
  list: async (params?: any) => {
    const response = await api.get('/alerts', { params })
    return response.data
  },
  get: async (alertId: number) => {
    const response = await api.get(`/alerts/${alertId}`)
    return response.data
  },
  resolve: async (alertId: number, data: any) => {
    const response = await api.post(`/alerts/${alertId}/resolve`, data)
    return response.data
  },
}

// Dashboard endpoints
export const dashboardApi = {
  getGlobal: async (params?: any) => {
    const response = await api.get('/dashboard/global', { params })
    return response.data
  },
  getCountry: async (countryId: number, params?: any) => {
    const response = await api.get(`/dashboard/country/${countryId}`, { params })
    return response.data
  },
}

// Forecast endpoints
export const forecastApi = {
  generate: async (data: any) => {
    const response = await api.post('/forecast/generate', data)
    return response.data
  },
  list: async (params?: any) => {
    const response = await api.get('/forecast', { params })
    return response.data
  },
}

// Countries and diseases
export const countriesApi = {
  list: async () => {
    const response = await api.get('/countries')
    return response.data
  },
  get: async (countryId: number) => {
    const response = await api.get(`/countries/${countryId}`)
    return response.data
  },
}

export const diseasesApi = {
  list: async (activeOnly: boolean = true) => {
    const response = await api.get('/diseases', { params: { active_only: activeOnly } })
    return response.data
  },
  get: async (diseaseId: number) => {
    const response = await api.get(`/diseases/${diseaseId}`)
    return response.data
  },
}

export const facilitiesApi = {
  list: async () => {
    const response = await api.get('/facilities')
    return response.data
  },
  create: async (data: any) => {
    const response = await api.post('/facilities', data)
    return response.data
  }
}

export const clinicalApi = {
  getPatients: async () => {
    const response = await api.get('/clinical/patients')
    return response.data
  },
  createPatient: async (data: any) => {
    const response = await api.post('/clinical/patients', data)
    return response.data
  },
  createEncounter: async (data: any) => {
    const response = await api.post('/clinical/encounters', data)
    return response.data
  }
}

export const pharmacyApi = {
  getPending: async () => {
    const response = await api.get('/pharmacy/prescriptions')
    return response.data
  },
  dispense: async (data: any) => {
    const response = await api.post('/pharmacy/dispense', data)
    return response.data
  }
}

export const surveillanceApi = {
  getSyndromicTrends: async (days: number = 7) => {
    const response = await api.get('/surveillance/syndromes/trends', { params: { days } })
    return response.data
  },
  getHeatmap: async () => {
    const response = await api.get('/surveillance/heatmap')
    return response.data
  }
}

export const interopApi = {
  getLogs: async () => {
    const response = await api.get('/interop/logs')
    return response.data
  },
  syncDHIS2: async (dataset: string, payload: any) => {
    const response = await api.post('/interop/dhis2/sync', { dataset, payload })
    return response.data
  }
}

export const publicApi = {
  getStats: async () => {
    const response = await api.get('/public/stats')
    return response.data
  },
  getMap: async () => {
    const response = await api.get('/public/map')
    return response.data
  },
  getAlerts: async () => {
    const response = await api.get('/public/alerts')
    return response.data
  }
}

export const facilitySettingsApi = {
  updateConsent: async (facilityId: number, visible: boolean) => {
    const response = await api.put(`/facilities/${facilityId}/consent`, null, { params: { public_visible: visible } })
    return response.data
  }
}

export default api
