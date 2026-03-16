'use client'

import { useState, useEffect } from 'react'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/lib/api'
import { 
  User, 
  Save, 
  Loader2, 
  Plus, 
  X,
  Zap,
  Brain
} from 'lucide-react'

export default function ProfilePage() {
  const { user, setUser, token } = useAuthStore()
  
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [targetRoles, setTargetRoles] = useState<string[]>(user?.target_roles || [])
  const [newRole, setNewRole] = useState('')
  const [priorityPreference, setPriorityPreference] = useState(user?.priority_preference || 'remote_international')
  const [preferredLlm, setPreferredLlm] = useState(user?.preferred_llm || 'openai')
  const [tonePreference, setTonePreference] = useState(user?.tone_preference || 'professional')
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '')
      setTargetRoles(user.target_roles || [])
      setPriorityPreference(user.priority_preference || 'remote_international')
      setPreferredLlm(user.preferred_llm || 'openai')
      setTonePreference(user.tone_preference || 'professional')
    }
  }, [user])

  const addRole = () => {
    if (newRole.trim() && !targetRoles.includes(newRole.trim())) {
      setTargetRoles([...targetRoles, newRole.trim()])
      setNewRole('')
    }
  }

  const removeRole = (role: string) => {
    setTargetRoles(targetRoles.filter(r => r !== role))
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError('')
    try {
      const updated = await authApi.updateProfile({
        full_name: fullName,
        target_roles: targetRoles,
        priority_preference: priorityPreference,
        preferred_llm: preferredLlm,
        tone_preference: tonePreference
      })
      if (token) setUser(updated, token)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save')
    } finally {
      setIsSaving(false)
    }
  }

  const sectionStyle = {
    padding: '24px',
    background: 'rgba(255,255,255,0.02)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '12px',
    marginBottom: '16px'
  }

  const labelStyle = {
    display: 'block',
    fontSize: '12px',
    color: '#64748b',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    marginBottom: '8px'
  }

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '8px',
    color: 'white',
    fontSize: '14px',
    outline: 'none',
    fontFamily: 'Inter, sans-serif'
  }

  const selectStyle = {
    ...inputStyle,
    cursor: 'pointer',
    appearance: 'none' as const
  }

  return (
    <div style={{ maxWidth: '680px' }}>

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontFamily: 'Sora, sans-serif', fontSize: '28px', fontWeight: 700, color: 'white', marginBottom: '8px' }}>
          Profile Settings
        </h1>
        <p style={{ color: '#64748b', fontSize: '14px' }}>
          Configure your job search preferences and agent behavior.
        </p>
      </div>

      {/* Personal Info */}
      <div style={sectionStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <User size={16} color="#00D4FF" />
          <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>
            Personal Information
          </p>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={labelStyle}>Full Name</label>
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Your full name"
            style={inputStyle}
          />
        </div>

        <div>
          <label style={labelStyle}>Email</label>
          <input
            value={user?.email || ''}
            disabled
            style={{ ...inputStyle, opacity: 0.4, cursor: 'not-allowed' }}
          />
        </div>
      </div>

      {/* Target Roles */}
      <div style={sectionStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <Zap size={16} color="#00D4FF" />
          <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>
            Target Roles
          </p>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
          {targetRoles.map((role) => (
            <div key={role} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '6px 12px', borderRadius: '6px',
              background: 'rgba(0, 212, 255, 0.08)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              color: '#00D4FF', fontSize: '13px'
            }}>
              {role}
              <button
                onClick={() => removeRole(role)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
              >
                <X size={12} color="#00D4FF" />
              </button>
            </div>
          ))}
          {targetRoles.length === 0 && (
            <p style={{ color: '#475569', fontSize: '13px' }}>No roles added yet</p>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addRole()}
            placeholder="e.g. AI Engineer, Python Developer"
            style={{ ...inputStyle, flex: 1 }}
          />
          <button
            onClick={addRole}
            style={{
              padding: '10px 16px', background: 'rgba(0, 212, 255, 0.1)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              borderRadius: '8px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '4px',
              color: '#00D4FF', fontSize: '13px'
            }}
          >
            <Plus size={14} />
            Add
          </button>
        </div>
      </div>

      {/* Agent Preferences */}
      <div style={sectionStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <Brain size={16} color="#00D4FF" />
          <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>
            Agent Preferences
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={labelStyle}>Job Priority</label>
            <select
              value={priorityPreference}
              onChange={(e) => setPriorityPreference(e.target.value as "remote_international" | "hybrid_local" | "fulltime_local")}
              style={selectStyle}
            >
              <option value="remote_international">Remote International First</option>
              <option value="hybrid_local">Hybrid Local First</option>
              <option value="fulltime_local">On-site Local First</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>AI Model</label>
            <select
              value={preferredLlm}
              onChange={(e) => setPreferredLlm(e.target.value)}
              style={selectStyle}
            >
              <option value="openai">OpenAI GPT-4o Mini</option>
              <option value="openai_large">OpenAI GPT-4o</option>
              <option value="gemini">Gemini 1.5 Flash</option>
              <option value="gemini_large">Gemini 1.5 Pro</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>Resume Tone</label>
            <select
              value={tonePreference}
              onChange={(e) => setTonePreference(e.target.value)}
              style={selectStyle}
            >
              <option value="professional">Professional</option>
              <option value="confident">Confident</option>
              <option value="technical">Technical</option>
              <option value="creative">Creative</option>
            </select>
          </div>
        </div>
      </div>

      {/* Token Usage */}
      <div style={sectionStyle}>
        <p style={{ color: '#64748b', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
          Monthly Token Usage
        </p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ color: 'white', fontSize: '24px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
            {user?.monthly_token_usage?.toLocaleString() || 0}
          </span>
          <span style={{ color: '#64748b', fontSize: '13px' }}>
            / 100,000 tokens
          </span>
        </div>
        <div style={{ height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px' }}>
          <div style={{
            height: '100%',
            width: `${Math.min(((user?.monthly_token_usage || 0) / 100000) * 100, 100)}%`,
            background: 'linear-gradient(90deg, #00D4FF, #a78bfa)',
            borderRadius: '2px'
          }} />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '12px 16px', marginBottom: '16px',
          background: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: '8px', color: '#f87171', fontSize: '13px'
        }}>
          {error}
        </div>
      )}

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={isSaving}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '12px 28px', borderRadius: '8px', border: 'none',
          background: saved ? 'rgba(16,185,129,0.15)' : '#00D4FF',
          color: saved ? '#10b981' : '#0A0F1E',
          fontWeight: 600, fontSize: '14px', cursor: 'pointer',
          transition: 'all 0.2s'
        }}
      >
        {isSaving ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <Save size={16} />
        )}
        {saved ? 'Saved!' : 'Save Changes'}
      </button>
    </div>
  )
}