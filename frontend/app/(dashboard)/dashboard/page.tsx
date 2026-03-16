'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import { resumeApi, workflowApi } from '@/lib/api'
import { Zap, FileText, Briefcase, ChevronRight, Upload, RotateCcw, CheckCircle, Clock } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const router = useRouter()
  const [resumeCount, setResumeCount] = useState<number>(0)
  const [workflowCount, setWorkflowCount] = useState<number>(0)
  const [recentWorkflows, setRecentWorkflows] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [resumes, workflows] = await Promise.all([
          resumeApi.list().catch(() => []),
          workflowApi.history().catch(() => [])
        ])
        setResumeCount(resumes?.length || 0)
        const wf = workflows || []
        setWorkflowCount(wf.length)
        setRecentWorkflows(wf.slice(0, 3))
      } catch {
        // silently fail
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [])

  const firstName = user?.full_name?.split(' ')[0] || 'there'

  const card = (content: React.ReactNode) => (
    <div style={{
      padding: '24px',
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: '16px',
    }}>
      {content}
    </div>
  )

  return (
    <div style={{ maxWidth: '860px' }}>

      {/* Welcome */}
      <div style={{ marginBottom: '36px' }}>
        <h1 style={{ fontFamily: 'Sora, sans-serif', fontSize: '28px', fontWeight: 700, color: 'white', marginBottom: '8px' }}>
          Hey, {firstName} 👋
        </h1>
        <p style={{ color: '#64748b', fontSize: '14px' }}>
          {user?.target_roles?.length
            ? `Targeting: ${user.target_roles.join(', ')}`
            : 'Set your target roles in Profile to get better job matches.'}
        </p>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '28px' }}>
        {[
          { label: 'Resumes Uploaded', value: isLoading ? '—' : resumeCount, icon: FileText, color: '#00D4FF' },
          { label: 'Workflows Run', value: isLoading ? '—' : workflowCount, icon: Zap, color: '#a78bfa' },
          { label: 'Applications', value: isLoading ? '—' : workflowCount, icon: Briefcase, color: '#10b981' },
        ].map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} style={{
              padding: '20px 24px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <div style={{
                  width: '32px', height: '32px', borderRadius: '8px',
                  background: `${stat.color}15`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  <Icon size={16} color={stat.color} />
                </div>
                <span style={{ color: '#64748b', fontSize: '13px' }}>{stat.label}</span>
              </div>
              <p style={{ fontFamily: 'Sora, sans-serif', fontSize: '32px', fontWeight: 700, color: 'white' }}>
                {stat.value}
              </p>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: '28px' }}>
        <p style={{ color: '#64748b', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
          Quick Actions
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <button
            onClick={() => router.push('/workflow')}
            style={{
              padding: '18px 20px', borderRadius: '12px',
              background: 'rgba(0, 212, 255, 0.08)',
              border: '1px solid rgba(0, 212, 255, 0.2)',
              cursor: 'pointer', textAlign: 'left',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Zap size={18} color="#00D4FF" />
              <div>
                <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>Start New Workflow</p>
                <p style={{ color: '#64748b', fontSize: '12px', marginTop: '2px' }}>Upload resume & find jobs</p>
              </div>
            </div>
            <ChevronRight size={16} color="#00D4FF" />
          </button>

          <button
            onClick={() => router.push('/applications')}
            style={{
              padding: '18px 20px', borderRadius: '12px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              cursor: 'pointer', textAlign: 'left',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Briefcase size={18} color="#a78bfa" />
              <div>
                <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>View Applications</p>
                <p style={{ color: '#64748b', fontSize: '12px', marginTop: '2px' }}>See tailored resumes</p>
              </div>
            </div>
            <ChevronRight size={16} color="#64748b" />
          </button>
        </div>
      </div>

      {/* Recent Workflows */}
      {card(
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <p style={{ color: 'white', fontSize: '15px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>Recent Workflows</p>
            <button onClick={() => router.push('/applications')} style={{ background: 'none', border: 'none', color: '#00D4FF', fontSize: '13px', cursor: 'pointer' }}>
              View all
            </button>
          </div>
          {isLoading ? (
            <p style={{ color: '#64748b', fontSize: '13px' }}>Loading...</p>
          ) : recentWorkflows.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0' }}>
              <Upload size={32} color="#334155" style={{ margin: '0 auto 12px' }} />
              <p style={{ color: '#475569', fontSize: '14px', marginBottom: '16px' }}>No workflows yet — run your first one</p>
              <button
                onClick={() => router.push('/workflow')}
                style={{
                  padding: '8px 20px', borderRadius: '8px',
                  background: '#00D4FF', color: '#0A0F1E',
                  border: 'none', cursor: 'pointer',
                  fontSize: '13px', fontWeight: 600,
                  display: 'inline-flex', alignItems: 'center', gap: '6px'
                }}
              >
                <Zap size={14} /> Start Workflow
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {recentWorkflows.map((wf, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '12px 16px', borderRadius: '10px',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.04)'
                }}>
                  <div style={{
                    width: '32px', height: '32px', borderRadius: '8px',
                    background: wf.status === 'completed' ? 'rgba(16,185,129,0.1)' : 'rgba(251,191,36,0.1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    {wf.status === 'completed'
                      ? <CheckCircle size={16} color="#10b981" />
                      : <Clock size={16} color="#fbbf24" />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ color: 'white', fontSize: '13px', fontWeight: 500 }}>
                      Workflow {wf.workflow_run_id?.slice(0, 8) || `#${i + 1}`}
                    </p>
                    <p style={{ color: '#64748b', fontSize: '12px' }}>
                      {wf.created_at ? new Date(wf.created_at).toLocaleDateString() : 'Recent'}
                    </p>
                  </div>
                  <span style={{
                    fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                    fontFamily: 'JetBrains Mono, monospace',
                    background: wf.status === 'completed' ? 'rgba(16,185,129,0.1)' : 'rgba(251,191,36,0.1)',
                    color: wf.status === 'completed' ? '#10b981' : '#fbbf24'
                  }}>
                    {wf.status?.toUpperCase() || 'DONE'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

    </div>
  )
}