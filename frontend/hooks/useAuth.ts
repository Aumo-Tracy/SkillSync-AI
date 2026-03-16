'use client'

import { useCallback, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/lib/api'

export function useAuth() {
  const store = useAuthStore()
  const router = useRouter()
  
  // Rehydrate auth state on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const userStr = localStorage.getItem('user')
    
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr)
        store.setUser(user, token)
      } catch {
        store.clearUser()
      }
    } else {
      store.setLoading(false)
    }
  }, [])
  
  const signin = useCallback(async (email: string, password: string) => {
    const data = await authApi.signin(email, password)
    store.setUser(data.user, data.access_token)
    router.push('/dashboard')
    return data
  }, [store, router])
  
  const signup = useCallback(async (
    email: string,
    password: string,
    full_name?: string
  ) => {
    const data = await authApi.signup(email, password, full_name)
    store.setUser(data.user, data.access_token)
    router.push('/dashboard')
    return data
  }, [store, router])
  
  const signout = useCallback(async () => {
    await authApi.signout()
    store.clearUser()
    router.push('/login')
  }, [store, router])
  
  return {
    user: store.user,
    token: store.token,
    isLoading: store.isLoading,
    isAuthenticated: store.isAuthenticated,
    signin,
    signup,
    signout
  }
}