'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import Link from 'next/link'
import { Loader2, Zap } from 'lucide-react'

export default function SignupPage() {
  const { signup } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await signup(email, password, fullName)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="glass rounded-2xl p-8 space-y-8">
      <div className="space-y-2">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 rounded-lg bg-cyan-400 flex items-center justify-center">
            <Zap className="w-4 h-4 text-[#0A0F1E]" />
          </div>
          <span 
            className="text-lg font-semibold text-white"
            style={{ fontFamily: 'Sora, sans-serif' }}
          >
            SkillSync AI
          </span>
        </div>

        <h1 
          className="text-2xl font-bold text-white"
          style={{ fontFamily: 'Sora, sans-serif' }}
        >
          Create your account
        </h1>
        <p className="text-sm text-slate-400">
          Start your AI-powered job search
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label className="text-slate-300 text-xs uppercase tracking-wider">
            Full Name
          </Label>
          <Input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Aumo Tracy"
            className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 
                       focus:border-cyan-400 h-11"
          />
        </div>

        <div className="space-y-2">
          <Label className="text-slate-300 text-xs uppercase tracking-wider">
            Email
          </Label>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 
                       focus:border-cyan-400 h-11"
          />
        </div>

        <div className="space-y-2">
          <Label className="text-slate-300 text-xs uppercase tracking-wider">
            Password
          </Label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            className="bg-white/5 border-white/10 text-white placeholder:text-slate-500 
                       focus:border-cyan-400 h-11"
          />
        </div>

        {error && (
          <div className="text-red-400 text-sm bg-red-400/10 border border-red-400/20 
                          rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full h-11 bg-cyan-400 hover:bg-cyan-300 text-[#0A0F1E] 
                     font-semibold transition-all"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            'Create Account'
          )}
        </Button>
      </form>

      <p className="text-center text-sm text-slate-500">
        Already have an account?{' '}
        <Link 
          href="/login" 
          className="text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          Sign in
        </Link>
      </p>
    </div>
  )
}