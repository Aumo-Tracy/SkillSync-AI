'use client'

import { useState, useEffect } from 'react'
import { workflowApi } from '@/lib/api'
import { WorkflowRun } from '@/types'
import { useAuthStore } from '@/store/auth'
import ResumeEditor from '@/components/ResumeEditor'
import {
  Briefcase,
  CheckCircle,
  Clock,
  XCircle,
  ChevronDown,
  ChevronUp,
  Zap,
  Building,
  FileText,
  Globe,
  Download
} from 'lucide-react'

const STATUS_CONFIG: Record<string, { color: string; bg: string; border: string; icon: any }> = {
  completed: { color: '#10b981', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.2)', icon: CheckCircle },
  running: { color: '#00D4FF', bg: 'rgba(0,212,255,0.1)', border: 'rgba(0,212,255,0.2)', icon: Zap },
  awaiting_hitl: { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)', border: 'rgba(251,191,36,0.2)', icon: Clock },
  failed: { color: '#f87171', bg: 'rgba(248,113,113,0.1)', border: 'rgba(248,113,113,0.2)', icon: XCircle },
  pending: { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', border: 'rgba(148,163,184,0.2)', icon: Clock },
}

export default function ApplicationsPage() {
  const { user } = useAuthStore()
  const [workflows, setWorkflows] = useState<WorkflowRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [editingResume, setEditingResume] = useState<any | null>(null)

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const data = await workflowApi.getHistory()
        setWorkflows(data || [])
      } catch (err) {
        console.error('Failed to fetch workflows', err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchWorkflows()
  }, [])

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id)
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#64748b' }}>
        <Zap size={16} className="animate-spin" />
        <span style={{ fontSize: '14px' }}>Loading applications...</span>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '860px' }}>

      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontFamily: 'Sora, sans-serif', fontSize: '28px', fontWeight: 700, color: 'white', marginBottom: '8px' }}>
          Applications
        </h1>
        <p style={{ color: '#64748b', fontSize: '14px' }}>
          Your workflow history and tailored resume results.
        </p>
      </div>

      {workflows.length === 0 ? (
        <div style={{
          padding: '48px', textAlign: 'center',
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: '12px'
        }}>
          <Briefcase size={32} color="#334155" style={{ margin: '0 auto 16px' }} />
          <p style={{ color: '#64748b', fontSize: '14px' }}>
            No workflows yet. Run your first job search from the Workflow page.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {workflows.map((workflow) => {
            const config = STATUS_CONFIG[workflow.status] || STATUS_CONFIG.pending
            const StatusIcon = config.icon
            const isExpanded = expandedId === workflow.id
            const outputData = workflow.output_data || {}
            const tailoredResumes = outputData.tailored_resumes || []
            const companyResearch = outputData.company_research || []

            return (
              <div key={workflow.id} style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '12px',
                overflow: 'hidden',
                transition: 'all 0.2s'
              }}>
                {/* Workflow header row */}
                <div
                  onClick={() => toggleExpand(workflow.id)}
                  style={{
                    padding: '16px 20px',
                    display: 'flex', alignItems: 'center', gap: '12px',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '8px',
                    background: config.bg, border: `1px solid ${config.border}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <StatusIcon size={16} color={config.color} />
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <p style={{ color: 'white', fontSize: '14px', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
                        {workflow.id.slice(0, 12)}...
                      </p>
                      <span style={{
                        fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                        background: config.bg, color: config.color,
                        border: `1px solid ${config.border}`,
                        fontFamily: 'JetBrains Mono, monospace'
                      }}>
                        {workflow.status}
                      </span>
                    </div>
                    <p style={{ color: '#64748b', fontSize: '12px' }}>
                      {new Date(workflow.started_at).toLocaleDateString('en-US', {
                        year: 'numeric', month: 'short', day: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                      })}
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    {tailoredResumes.length > 0 && (
                      <span style={{ color: '#64748b', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <FileText size={12} />
                        {tailoredResumes.length} resume{tailoredResumes.length > 1 ? 's' : ''}
                      </span>
                    )}
                    {isExpanded ? (
                      <ChevronUp size={16} color="#64748b" />
                    ) : (
                      <ChevronDown size={16} color="#64748b" />
                    )}
                  </div>
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', padding: '20px' }}>

                    {/* Tailored Resumes */}
                    {tailoredResumes.length > 0 && (
                      <div style={{ marginBottom: '20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                          <FileText size={14} color="#00D4FF" />
                          <p style={{ color: '#00D4FF', fontSize: '13px', fontWeight: 600 }}>
                            Tailored Resumes
                          </p>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {tailoredResumes.map((resume: any, i: number) => (
                            <div key={i} style={{
                              padding: '16px',
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid rgba(255,255,255,0.06)',
                              borderRadius: '10px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                                <p style={{ color: 'white', fontSize: '14px', fontWeight: 600 }}>
                                  {resume.job_title}
                                </p>
                                <span style={{
                                  fontSize: '12px', fontFamily: 'JetBrains Mono, monospace',
                                  color: resume.match_score >= 70 ? '#10b981' : '#fbbf24',
                                  background: resume.match_score >= 70 ? 'rgba(16,185,129,0.1)' : 'rgba(251,191,36,0.1)',
                                  padding: '3px 8px', borderRadius: '4px'
                                }}>
                                  {resume.match_score?.toFixed(0)}% match
                                </span>
                              </div>

                              {resume.changes_summary?.length > 0 && (
                                <div style={{ marginBottom: '10px' }}>
                                  <p style={{ color: '#475569', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                                    Changes
                                  </p>
                                  {resume.changes_summary.slice(0, 3).map((c: string, j: number) => (
                                    <p key={j} style={{ color: '#94a3b8', fontSize: '12px', display: 'flex', gap: '6px', marginBottom: '3px' }}>
                                      <span style={{ color: '#00D4FF' }}>›</span>{c}
                                    </p>
                                  ))}
                                </div>
                              )}

                              {resume.ats_keywords_added?.length > 0 && (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '12px' }}>
                                  {resume.ats_keywords_added.slice(0, 6).map((kw: string, j: number) => (
                                    <span key={j} style={{
                                      fontSize: '11px', padding: '2px 6px', borderRadius: '4px',
                                      background: 'rgba(0,212,255,0.06)', color: '#00D4FF',
                                      border: '1px solid rgba(0,212,255,0.15)',
                                      fontFamily: 'JetBrains Mono, monospace'
                                    }}>
                                      {kw}
                                    </span>
                                  ))}
                                </div>
                              )}

                              {/* Learning Roadmap */}
{(resume as any).learning_roadmap?.length > 0 && (
  <div style={{ marginTop: '12px' }}>
    <p style={{ color: '#64748b', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
      Skills to Learn
    </p>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {(resume as any).learning_roadmap.slice(0, 3).map((item: any, j: number) => (
        <div key={j} style={{
          padding: '10px 14px',
          background: 'rgba(167, 139, 250, 0.06)',
          border: '1px solid rgba(167, 139, 250, 0.15)',
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
            <p style={{ color: '#a78bfa', fontSize: '13px', fontWeight: 600 }}>{item.skill}</p>
            <span style={{
              fontSize: '10px', padding: '2px 8px', borderRadius: '4px',
              background: item.priority === 'high' ? 'rgba(239,68,68,0.1)' : item.priority === 'medium' ? 'rgba(251,191,36,0.1)' : 'rgba(16,185,129,0.1)',
              color: item.priority === 'high' ? '#f87171' : item.priority === 'medium' ? '#fbbf24' : '#10b981',
              fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase'
            }}>
              {item.priority} · {item.estimated_time}
            </span>
          </div>
          <p style={{ color: '#64748b', fontSize: '12px' }}>⚡ {item.quick_win}</p>
        </div>
      ))}
    </div>
  </div>
)}

                              {/* Edit & Download button */}
                              <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setEditingResume({
                                      full_name: user?.full_name || '',
                                      email: user?.email || '',
                                      job_title: resume.job_title || '',
                                      summary: resume.summary || '',
                                      experience: resume.experience || [],
                                      skills: resume.skills || { technical: [], tools: [], soft: [] },
                                      education: resume.education || [],
                                      certifications: resume.certifications || [],
                                      ats_keywords_added: resume.ats_keywords_added || []
                                    })
                                  }}
                                  style={{
                                    display: 'flex', alignItems: 'center', gap: '8px',
                                    padding: '8px 18px', borderRadius: '8px',
                                    background: 'rgba(0, 212, 255, 0.08)',
                                    border: '1px solid rgba(0, 212, 255, 0.2)',
                                    color: '#00D4FF', fontSize: '13px',
                                    cursor: 'pointer', fontWeight: 600,
                                    transition: 'all 0.2s'
                                  }}
                                >
                                  <Download size={14} />
                                  Edit & Download
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Company Research */}
                    {companyResearch.length > 0 && (
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                          <Globe size={14} color="#a78bfa" />
                          <p style={{ color: '#a78bfa', fontSize: '13px', fontWeight: 600 }}>
                            Company Research
                          </p>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {companyResearch.map((research: any, i: number) => (
                            <div key={i} style={{
                              padding: '16px',
                              background: 'rgba(255,255,255,0.02)',
                              border: '1px solid rgba(255,255,255,0.06)',
                              borderRadius: '10px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                <Building size={14} color="#a78bfa" />
                                <p style={{ color: 'white', fontSize: '14px', fontWeight: 600 }}>
                                  {research.company}
                                </p>
                              </div>
                              {research.overview && (
                                <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px', lineHeight: '1.5' }}>
                                  {research.overview}
                                </p>
                              )}
                              {research.tech_stack?.length > 0 && (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                  {research.tech_stack.slice(0, 6).map((tech: string, j: number) => (
                                    <span key={j} style={{
                                      fontSize: '11px', padding: '2px 6px', borderRadius: '4px',
                                      background: 'rgba(167,139,250,0.08)', color: '#a78bfa',
                                      border: '1px solid rgba(167,139,250,0.15)',
                                      fontFamily: 'JetBrains Mono, monospace'
                                    }}>
                                      {tech}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Empty state */}
                    {workflow.status === 'completed' && tailoredResumes.length === 0 && companyResearch.length === 0 && (
                      <p style={{ color: '#475569', fontSize: '13px' }}>
                        No output data available for this workflow.
                      </p>
                    )}

                    {/* Error message */}
                    {workflow.error_message && (
                      <div style={{
                        padding: '12px 16px',
                        background: 'rgba(239,68,68,0.08)',
                        border: '1px solid rgba(239,68,68,0.2)',
                        borderRadius: '8px', color: '#f87171', fontSize: '13px'
                      }}>
                        {workflow.error_message}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Resume Editor Modal */}
      {editingResume && (
        <ResumeEditor
          initialData={editingResume}
          onClose={() => setEditingResume(null)}
        />
      )}
    </div>
  )
}