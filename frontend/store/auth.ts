import { create } from 'zustand'
import { UserProfile } from '@/types'

interface AuthState {
  user: UserProfile | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  setUser: (user: UserProfile, token: string) => void
  clearUser: () => void
  setLoading: (loading: boolean) => void
  rehydrate: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user, token) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('user', JSON.stringify(user))
    // Store token creation time
    localStorage.setItem('token_created_at', Date.now().toString())
    set({ user, token, isAuthenticated: true, isLoading: false })
  },

  clearUser: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    localStorage.removeItem('token_created_at')
    set({ user: null, token: null, isAuthenticated: false, isLoading: false })
  },

  setLoading: (loading) => set({ isLoading: loading }),

  rehydrate: () => {
    try {
      const token = localStorage.getItem('access_token')
      const userStr = localStorage.getItem('user')
      const tokenCreatedAt = localStorage.getItem('token_created_at')

      if (!token || !userStr) {
        set({ isLoading: false })
        return
      }

      // Check if token is older than 23 hours — expire proactively before backend rejects it
      if (tokenCreatedAt) {
        const age = Date.now() - parseInt(tokenCreatedAt)
        const twentyThreeHours = 23 * 60 * 60 * 1000
        if (age > twentyThreeHours) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          localStorage.removeItem('token_created_at')
          set({ user: null, token: null, isAuthenticated: false, isLoading: false })
          return
        }
      }

      const user = JSON.parse(userStr)
      set({ user, token, isAuthenticated: true, isLoading: false })
    } catch {
      set({ isLoading: false })
    }
  }
}))