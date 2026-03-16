import axios from 'axios'
import { AuthResponse, Resume, WorkflowRun, Feedback } from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' }
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// Handle 401 responses — clear session and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        // Clear stale session
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        localStorage.removeItem('token_created_at')
        // Redirect to login if not already there
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const authApi = {
  signup: async (email: string, password: string, full_name?: string) => {
    const res = await api.post<AuthResponse>('/api/auth/signup', {
      email, password, full_name
    })
    return res.data
  },

  signin: async (email: string, password: string) => {
    const res = await api.post<AuthResponse>('/api/auth/signin', {
      email, password
    })
    return res.data
  },

  signout: async () => {
    try {
      await api.post('/api/auth/signout')
    } catch {
      // Even if signout fails, clear local session
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_created_at')
    }
  },

  getMe: async () => {
    const res = await api.get('/api/auth/me')
    return res.data
  },

  updateProfile: async (data: Partial<{
    full_name: string
    target_roles: string[]
    priority_preference: string
    preferred_llm: string
    tone_preference: string
  }>) => {
    const res = await api.patch('/api/auth/me', data)
    return res.data
  }
}

// Resumes
export const resumeApi = {
  upload: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await api.post<Resume>('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  getAll: async () => {
    const res = await api.get<Resume[]>('/api/resume/')
    return res.data
  },

  getBase: async () => {
    const res = await api.get<Resume>('/api/resume/base')
    return res.data
  }
}

// Workflow
export const workflowApi = {
  start: async (resume_id: string, search_params?: any) => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`${BASE_URL}/api/workflow/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ resume_id, search_params })
    })
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_created_at')
      window.location.href = '/login'
    }
    return response
  },

  approveJobs: async (workflow_run_id: string, approved_job_ids: string[]) => {
    const token = localStorage.getItem('access_token')
    const response = await fetch(
      `${BASE_URL}/api/workflow/${workflow_run_id}/approve`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ approved_job_ids })
      }
    )
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      localStorage.removeItem('token_created_at')
      window.location.href = '/login'
    }
    return response
  },

  getStatus: async (workflow_run_id: string) => {
    const res = await api.get<WorkflowRun>(
      `/api/workflow/${workflow_run_id}/status`
    )
    return res.data
  },

  getHistory: async () => {
    const res = await api.get<WorkflowRun[]>('/api/workflow/history')
    return res.data
  }
}

// Feedback
export const feedbackApi = {
  submit: async (feedback: Feedback) => {
    const res = await api.post('/api/feedback/', feedback)
    return res.data
  },

  getHistory: async () => {
    const res = await api.get('/api/feedback/')
    return res.data
  }
}

export default api