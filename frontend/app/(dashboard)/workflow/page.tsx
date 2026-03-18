'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuthStore } from '@/store/auth'
import { useWorkflow } from '@/hooks/useWorkflow'
import { useWorkflowStore } from '@/store/workflow'
import { resumeApi } from '@/lib/api'
import { TailoredResume } from '@/types'
import ResumeEditor from '@/components/ResumeEditor'
import FeedbackModal from '@/components/FeedbackModal'
import {
  Upload, Zap, CheckCircle, Loader2, ExternalLink,
  Building, Globe, ChevronRight, FileText,
  Search, Brain, PenTool, Database, AlertCircle,
  Download, Plus, X, Briefcase, Link, RotateCcw,
  Star, ThumbsUp, MessageSquare
} from 'lucide-react'

const AGENT_STEPS = [
  { id: 'job_discovery', label: 'Job Discovery', icon: Search, description: 'Searching remote and local opportunities' },
  { id: 'hitl_job_approval', label: 'Your Approval', icon: CheckCircle, description: 'Review and approve job listings' },
  { id: 'resume_analysis', label: 'Resume Analysis', icon: Brain, description: 'Analyzing skill gaps and match scores' },
  { id: 'resume_tailoring', label: 'Resume Tailoring', icon: PenTool, description: 'Rewriting resume for each role' },
  { id: 'company_research', label: 'Company Research', icon: Globe, description: 'Gathering company intelligence' },
  { id: 'memory_agent', label: 'Saving Results', icon: Database, description: 'Persisting your applications' },
]

const LOCATION_LABELS: Record<string, string> = {
  remote_international: 'Remote',
  hybrid_local: 'Hybrid',
  fulltime_local: 'On-site',
}

const LOCATION_COLORS: Record<string, string> = {
  remote_international: '#00D4FF',
  hybrid_local: '#a78bfa',
  fulltime_local: '#94a3b8',
}

interface ManualJob {
  id: string
  title: string
  company: string
  url: string
  description: string
  location_type: string
}

function SectionLabel({ number, label, done }: { number: number; label: string; done?: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
      <div style={{
        width: '24px', height: '24px', borderRadius: '50%',
        background: done ? 'rgba(16,185,129,0.15)' : 'rgba(0, 212, 255, 0.1)',
        border: done ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(0, 212, 255, 0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '11px', fontWeight: 700,
        color: done ? '#10b981' : '#00D4FF',
        fontFamily: 'JetBrains Mono, monospace', flexShrink: 0
      }}>
        {done ? '✓' : number}
      </div>
      <p style={{ fontFamily: 'Sora, sans-serif', fontSize: '15px', fontWeight: 600, color: 'white' }}>
        {label}
      </p>
    </div>
  )
}

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '8px',
  color: 'white',
  fontSize: '13px',
  outline: 'none',
  fontFamily: 'Inter, sans-serif',
  boxSizing: 'border-box' as const
}

const FEEDBACK_SUGGESTIONS = [
  'Emphasize my AI/LLM projects',
  'Keep it to 1 page',
  'Focus on Python and backend skills',
  'Highlight self-taught and bootcamp experience',
  'Make the summary more impactful',
]

export default function WorkflowPage() {
  const { user } = useAuthStore()
  const store = useWorkflowStore()
  const {
    status, events, discoveredJobs, tailoredResumes,
    isStreaming, currentAgent, error, workflowRunId,
    startWorkflow, approveJobs
  } = useWorkflow()

  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [resumeId, setResumeId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [selectedJobs, setSelectedJobs] = useState<Set<string>>(new Set())
  const [isDragging, setIsDragging] = useState(false)
  const [editingResume, setEditingResume] = useState<any | null>(null)
  const [feedbackTarget, setFeedbackTarget] = useState<{ jobTitle: string } | null>(null)
  const [submittedFeedback, setSubmittedFeedback] = useState<Set<string>>(new Set())
  const fileInputRef = useRef<HTMLInputElement>(null)
  const eventsEndRef = useRef<HTMLDivElement>(null)

  const [manualJobs, setManualJobs] = useState<ManualJob[]>([])
  const [showManualForm, setShowManualForm] = useState(false)
  const [manualForm, setManualForm] = useState({
    title: '', company: '', url: '', description: '', location_type: 'remote_international'
  })
  const [manualFormError, setManualFormError] = useState('')
  const [isFetchingUrl, setIsFetchingUrl] = useState(false)
  const [fetchUrlError, setFetchUrlError] = useState('')

  // User tailoring instructions
  const [tailoringInstructions, setTailoringInstructions] = useState('')

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (status === 'completed' || status === 'failed') {
      store.reset()
    }
  }, [])

  const handleReset = () => {
    store.reset()
    setResumeId(null)
    setUploadedFile(null)
    setSelectedJobs(new Set())
    setManualJobs([])
    setShowManualForm(false)
    setUploadError('')
    setManualFormError('')
    setFetchUrlError('')
    setSubmittedFeedback(new Set())
    setFeedbackTarget(null)
    setTailoringInstructions('')
  }

  const handleFetchFromUrl = async () => {
    if (!manualForm.url.trim()) { setFetchUrlError('Enter a URL first'); return }
    setIsFetchingUrl(true)
    setFetchUrlError('')
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`${BASE_URL}/api/workflow/fetch-job`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ url: manualForm.url.trim() })
      })
      const data = await res.json()
      if (data.success) {
        setManualForm(prev => ({ ...prev, title: prev.title || data.title || '', description: data.description || '' }))
      } else {
        setFetchUrlError(data.error || 'Could not extract job details — paste the description manually')
      }
    } catch {
      setFetchUrlError('Fetch failed — paste the description manually')
    } finally {
      setIsFetchingUrl(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setUploadError('')
    try {
      const resume = await resumeApi.upload(file)
      setResumeId(resume.id)
      setUploadedFile(file)
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileUpload(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFileUpload(file)
  }

  const addManualJob = () => {
    setManualFormError('')
    if (!manualForm.title.trim()) { setManualFormError('Job title is required'); return }
    if (!manualForm.company.trim()) { setManualFormError('Company name is required'); return }
    if (!manualForm.description.trim()) { setManualFormError('Job description is required — paste it or fetch from URL'); return }
    const newJob: ManualJob = {
      id: `manual_${Date.now()}`,
      title: manualForm.title.trim(), company: manualForm.company.trim(),
      url: manualForm.url.trim(), description: manualForm.description.trim(),
      location_type: manualForm.location_type
    }
    setManualJobs(prev => [...prev, newJob])
    setManualForm({ title: '', company: '', url: '', description: '', location_type: 'remote_international' })
    setShowManualForm(false)
    setFetchUrlError('')
  }

  const removeManualJob = (id: string) => setManualJobs(prev => prev.filter(j => j.id !== id))

  const handleStartWorkflow = async () => {
    if (!resumeId) return
    const manualJobsFormatted = manualJobs.map(j => ({
      external_id: j.id, title: j.title, company: j.company, url: j.url,
      description: j.description,
      location: j.location_type === 'remote_international' ? 'Remote (Worldwide)' : 'On-site',
      location_type: j.location_type, source: 'manual',
      required_skills: [], salary_min: null, salary_max: null
    }))
    await startWorkflow(resumeId, {
      roles: user?.target_roles?.length ? user.target_roles : ['AI engineer', 'Python developer', 'backend developer'],
      max_results: 20,
      manual_jobs: manualJobsFormatted,
      user_feedback: tailoringInstructions.trim() || null,
    })
  }

  const toggleJob = (jobId: string) => {
    setSelectedJobs(prev => {
      const next = new Set(prev)
      if (next.has(jobId)) next.delete(jobId); else next.add(jobId)
      return next
    })
  }

  const handleApproveJobs = async () => {
    if (!workflowRunId || selectedJobs.size === 0) return
    await approveJobs(workflowRunId, Array.from(selectedJobs))
  }

  const openEditor = (resume: TailoredResume) => {
    console.log('Resume data:', JSON.stringify(resume, null, 2))
    setEditingResume({
      full_name: user?.full_name || '',
      email: user?.email || '',
      job_title: resume.job_title || '',
      summary: (resume as any).summary || '',
      experience: (resume as any).experience || [],
      skills: (resume as any).skills || { technical: [], tools: [], soft: [] },
      education: (resume as any).education || [],
      certifications: (resume as any).certifications || [],
      ats_keywords_added: resume.ats_keywords_added || []
    })
  }

  const getCurrentStepIndex = () => {
    if (!currentAgent) return -1
    return AGENT_STEPS.findIndex(s => s.id === currentAgent)
  }

  const progressPercent = status === 'completed'
    ? 100 : Math.max(0, (getCurrentStepIndex() / AGENT_STEPS.length) * 100)

  const allJobsForApproval = discoveredJobs

  return (
    <div style={{ maxWidth: '900px' }}>

      {/* Header */}
      <div style={{ marginBottom: '32px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontFamily: 'Sora, sans-serif', fontSize: '28px', fontWeight: 700, color: 'white', marginBottom: '8px' }}>
            Job Search Workflow
          </h1>
          <p style={{ color: '#64748b', fontSize: '14px' }}>
            Upload your resume, add jobs manually or let the agent discover them, then get tailored resumes.
          </p>
        </div>
        {status && (
          <button onClick={handleReset} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 14px', borderRadius: '8px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#64748b', fontSize: '13px', cursor: 'pointer'
          }}>
            <RotateCcw size={13} />New Workflow
          </button>
        )}
      </div>

      {/* Step 1 — Resume Upload */}
      <div style={{ marginBottom: '24px' }}>
        <SectionLabel number={1} label="Upload Your Resume" done={!!resumeId} />
        {!resumeId ? (
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${isDragging ? '#00D4FF' : 'rgba(255,255,255,0.1)'}`,
              borderRadius: '12px', padding: '48px', textAlign: 'center',
              cursor: 'pointer',
              background: isDragging ? 'rgba(0, 212, 255, 0.03)' : 'rgba(255,255,255,0.02)',
              transition: 'all 0.2s'
            }}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,.txt,.doc,.docx" onChange={handleFileChange} style={{ display: 'none' }} />
            {isUploading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <Loader2 size={32} color="#00D4FF" className="animate-spin" />
                <p style={{ color: '#94a3b8', fontSize: '14px' }}>Uploading and extracting text...</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <Upload size={32} color="#64748b" />
                <div>
                  <p style={{ color: 'white', fontSize: '15px', marginBottom: '4px' }}>Drop your resume here or click to browse</p>
                  <p style={{ color: '#64748b', fontSize: '13px' }}>PDF, DOC, DOCX or TXT — max 10MB</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 20px',
            background: 'rgba(0, 212, 255, 0.05)', border: '1px solid rgba(0, 212, 255, 0.2)', borderRadius: '12px'
          }}>
            <FileText size={20} color="#00D4FF" />
            <div style={{ flex: 1 }}>
              <p style={{ color: 'white', fontSize: '14px', fontWeight: 500 }}>{uploadedFile?.name || 'Resume uploaded'}</p>
              <p style={{ color: '#64748b', fontSize: '12px' }}>Ready for analysis</p>
            </div>
            <CheckCircle size={18} color="#00D4FF" />
          </div>
        )}
        {uploadError && (
          <div style={{ marginTop: '8px', padding: '10px 14px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', color: '#f87171', fontSize: '13px' }}>
            {uploadError}
          </div>
        )}
      </div>

      {/* Step 2 — Manual Job Entry */}
      {resumeId && !status && (
        <div style={{ marginBottom: '24px' }}>
          <SectionLabel number={2} label="Add Jobs Manually (Optional)" />
          <div style={{ padding: '20px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '16px' }}>
              Found a role on LinkedIn, Wellfound, or anywhere else? Paste the URL to auto-fetch details, or fill in manually.
            </p>
            {manualJobs.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {manualJobs.map(job => (
                  <div key={job.id} style={{
                    display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
                    background: 'rgba(0, 212, 255, 0.04)', border: '1px solid rgba(0, 212, 255, 0.15)', borderRadius: '8px'
                  }}>
                    <Briefcase size={14} color="#00D4FF" />
                    <div style={{ flex: 1 }}>
                      <p style={{ color: 'white', fontSize: '13px', fontWeight: 600 }}>{job.title}</p>
                      <p style={{ color: '#64748b', fontSize: '12px' }}>{job.company}</p>
                    </div>
                    <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(167, 139, 250, 0.1)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.2)', fontFamily: 'JetBrains Mono, monospace' }}>MANUAL</span>
                    <button onClick={() => removeManualJob(job.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}>
                      <X size={14} color="#64748b" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {showManualForm ? (
              <div style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                    Job URL — paste to auto-fetch description
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      value={manualForm.url}
                      onChange={e => setManualForm(p => ({ ...p, url: e.target.value }))}
                      placeholder="https://linkedin.com/jobs/view/..."
                      style={{ ...inputStyle, flex: 1 }}
                    />
                    <button
                      onClick={handleFetchFromUrl}
                      disabled={isFetchingUrl || !manualForm.url.trim()}
                      style={{
                        padding: '10px 16px', borderRadius: '8px',
                        background: manualForm.url.trim() ? 'rgba(0, 212, 255, 0.1)' : 'rgba(255,255,255,0.04)',
                        border: '1px solid rgba(0, 212, 255, 0.2)',
                        color: manualForm.url.trim() ? '#00D4FF' : '#475569',
                        fontSize: '13px', cursor: manualForm.url.trim() ? 'pointer' : 'not-allowed',
                        display: 'flex', alignItems: 'center', gap: '6px',
                        whiteSpace: 'nowrap' as const, fontWeight: 600
                      }}
                    >
                      {isFetchingUrl ? <Loader2 size={13} className="animate-spin" /> : <Link size={13} />}
                      {isFetchingUrl ? 'Fetching...' : 'Fetch Details'}
                    </button>
                  </div>
                  {fetchUrlError && <p style={{ color: '#f87171', fontSize: '12px', marginTop: '6px' }}>{fetchUrlError}</p>}
                  {manualForm.description && !fetchUrlError && (
                    <p style={{ color: '#10b981', fontSize: '12px', marginTop: '6px' }}>✓ Description fetched — review and edit below if needed</p>
                  )}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Job Title *</label>
                    <input value={manualForm.title} onChange={e => setManualForm(p => ({ ...p, title: e.target.value }))} placeholder="e.g. Junior AI Engineer" style={inputStyle} />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Company *</label>
                    <input value={manualForm.company} onChange={e => setManualForm(p => ({ ...p, company: e.target.value }))} placeholder="e.g. Anthropic" style={inputStyle} />
                  </div>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Work Type</label>
                  <select value={manualForm.location_type} onChange={e => setManualForm(p => ({ ...p, location_type: e.target.value }))} style={{ ...inputStyle, cursor: 'pointer' }}>
                    <option value="remote_international">Remote (International)</option>
                    <option value="hybrid_local">Hybrid</option>
                    <option value="fulltime_local">On-site</option>
                  </select>
                </div>
                <div style={{ marginBottom: '12px' }}>
                  <label style={{ display: 'block', fontSize: '11px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                    Job Description * — fetched automatically or paste manually
                  </label>
                  <textarea
                    value={manualForm.description}
                    onChange={e => setManualForm(p => ({ ...p, description: e.target.value }))}
                    placeholder="Paste the full job description here, or click Fetch Details above to auto-populate."
                    rows={6}
                    style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.5' }}
                  />
                </div>
                {manualFormError && <p style={{ color: '#f87171', fontSize: '12px', marginBottom: '12px' }}>{manualFormError}</p>}
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button onClick={addManualJob} style={{ padding: '8px 18px', borderRadius: '8px', background: '#00D4FF', color: '#0A0F1E', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Plus size={14} />Add Job
                  </button>
                  <button onClick={() => { setShowManualForm(false); setManualFormError(''); setFetchUrlError('') }} style={{ padding: '8px 18px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.08)', cursor: 'pointer', fontSize: '13px' }}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowManualForm(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', borderRadius: '8px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#94a3b8', fontSize: '13px', cursor: 'pointer', transition: 'all 0.2s' }}>
                <Plus size={14} />
                Add a job from LinkedIn / Wellfound / anywhere
              </button>
            )}
          </div>
        </div>
      )}

      {/* Step 3 — Launch */}
      {resumeId && !status && (
        <div style={{ marginBottom: '24px' }}>
          <SectionLabel number={3} label="Launch Agent Pipeline" />
          <div style={{ padding: '24px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}>
            <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '16px' }}>
              Agent will search for{' '}
              <strong style={{ color: 'white' }}>
                {user?.target_roles?.join(', ') || 'AI engineer, Python developer, backend developer'}
              </strong>{' '}roles across Remotive, We Work Remotely, Adzuna, and Arbeitnow.
            </p>
            {manualJobs.length > 0 && (
              <p style={{ color: '#a78bfa', fontSize: '13px', marginBottom: '16px' }}>
                + {manualJobs.length} manually added job{manualJobs.length > 1 ? 's' : ''} will be included.
              </p>
            )}

            {/* Tailoring Instructions */}
            <div style={{ marginBottom: '20px', padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <MessageSquare size={14} color="#a78bfa" />
                <label style={{ fontSize: '13px', color: '#a78bfa', fontWeight: 600 }}>
                  Tailoring Instructions — optional
                </label>
              </div>
              <p style={{ color: '#475569', fontSize: '12px', marginBottom: '10px' }}>
                Tell the AI how to customize your resumes. Be specific — this applies to every resume generated.
              </p>
              <textarea
                value={tailoringInstructions}
                onChange={e => setTailoringInstructions(e.target.value)}
                placeholder="e.g. Emphasize my LangChain and FastAPI projects. Keep it concise, max 1 page. Highlight that I'm self-taught with real project experience."
                rows={3}
                style={{ ...inputStyle, resize: 'vertical', lineHeight: '1.6', marginBottom: '10px' }}
              />
              {/* Quick suggestion chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {FEEDBACK_SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => setTailoringInstructions(prev =>
                      prev ? `${prev}. ${suggestion}` : suggestion
                    )}
                    style={{
                      fontSize: '11px', padding: '4px 10px', borderRadius: '20px',
                      background: 'rgba(167,139,250,0.06)',
                      border: '1px solid rgba(167,139,250,0.15)',
                      color: '#94a3b8', cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    + {suggestion}
                  </button>
                ))}
              </div>
              {tailoringInstructions && (
                <p style={{ color: '#10b981', fontSize: '12px', marginTop: '8px' }}>
                  ✓ Instructions will be applied to all tailored resumes
                </p>
              )}
            </div>

            <button onClick={handleStartWorkflow} style={{ background: '#00D4FF', color: '#0A0F1E', fontWeight: 600, padding: '10px 24px', borderRadius: '8px', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
              <Zap size={16} />Launch Agent Pipeline
            </button>
          </div>
        </div>
      )}

      {/* Step 4 — Pipeline Progress */}
      {status && status !== 'completed' && (
        <div style={{ marginBottom: '24px' }}>
          <SectionLabel number={4} label="Agent Pipeline" />
          <div style={{ marginBottom: '20px' }}>
            <div style={{ height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${progressPercent}%`, background: 'linear-gradient(90deg, #00D4FF, #a78bfa)', borderRadius: '2px', transition: 'width 0.5s ease' }} />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {AGENT_STEPS.map((step, index) => {
              const Icon = step.icon
              const stepIndex = getCurrentStepIndex()
              const isDone = index < stepIndex
              const isActive = step.id === currentAgent
              const isPending = index > stepIndex
              return (
                <div key={step.id} style={{
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '10px',
                  background: isActive ? 'rgba(0, 212, 255, 0.06)' : isDone ? 'rgba(255,255,255,0.02)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 212, 255, 0.15)' : '1px solid transparent', transition: 'all 0.3s'
                }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: isDone ? 'rgba(16, 185, 129, 0.15)' : isActive ? 'rgba(0, 212, 255, 0.15)' : 'rgba(255,255,255,0.04)', flexShrink: 0 }}>
                    {isDone ? <CheckCircle size={16} color="#10b981" /> : isActive ? <Loader2 size={16} color="#00D4FF" className="animate-spin" /> : <Icon size={16} color={isPending ? '#334155' : '#64748b'} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '13px', fontWeight: 500, color: isDone ? '#10b981' : isActive ? '#00D4FF' : isPending ? '#334155' : '#94a3b8' }}>{step.label}</p>
                    {isActive && <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{step.description}</p>}
                  </div>
                  {isActive && <div style={{ fontSize: '11px', color: '#00D4FF', fontFamily: 'JetBrains Mono, monospace', background: 'rgba(0, 212, 255, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>RUNNING</div>}
                </div>
              )
            })}
          </div>
          {events.length > 0 && (
            <div style={{ marginTop: '16px', padding: '16px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.04)', maxHeight: '160px', overflowY: 'auto', fontFamily: 'JetBrains Mono, monospace' }}>
              {events.map((event, i) => (
                <div key={i} style={{ fontSize: '12px', color: event.event_type === 'pipeline_error' ? '#f87171' : event.event_type === 'pipeline_complete' ? '#10b981' : '#64748b', marginBottom: '4px', display: 'flex', gap: '8px' }}>
                  <span style={{ color: '#334155' }}>›</span>{event.message}
                </div>
              ))}
              <div ref={eventsEndRef} />
            </div>
          )}
          {error && (
            <div style={{ marginTop: '12px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={16} color="#f87171" />
              <p style={{ color: '#f87171', fontSize: '13px' }}>{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Step 5 — HITL Job Approval */}
      {status === 'awaiting_hitl' && allJobsForApproval.length > 0 && (
        <div style={{ marginBottom: '24px', position: 'relative', zIndex: 20 }}>
          <SectionLabel number={5} label="Review and Approve Jobs" />
          <div style={{ padding: '16px 20px', background: 'rgba(251, 191, 36, 0.06)', border: '1px solid rgba(251, 191, 36, 0.2)', borderRadius: '10px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={16} color="#fbbf24" />
            <p style={{ color: '#fbbf24', fontSize: '13px' }}>Select the jobs you want tailored resumes for, then click Proceed.</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
            {allJobsForApproval.map((job) => {
              const isSelected = selectedJobs.has(job.external_id)
              const isManual = job.source === 'manual'
              return (
                <div key={job.external_id} onClick={() => toggleJob(job.external_id)} style={{
                  padding: '16px 20px', borderRadius: '12px',
                  border: isSelected ? '1px solid rgba(0, 212, 255, 0.3)' : '1px solid rgba(255,255,255,0.06)',
                  background: isSelected ? 'rgba(0, 212, 255, 0.05)' : 'rgba(255,255,255,0.02)',
                  cursor: 'pointer', transition: 'all 0.2s'
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ width: '18px', height: '18px', borderRadius: '4px', border: isSelected ? '2px solid #00D4FF' : '2px solid rgba(255,255,255,0.2)', background: isSelected ? '#00D4FF' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: '2px' }}>
                      {isSelected && <CheckCircle size={12} color="#0A0F1E" />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                        <p style={{ color: 'white', fontSize: '14px', fontWeight: 600 }}>{job.title}</p>
                        <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: `${LOCATION_COLORS[job.location_type]}15`, color: LOCATION_COLORS[job.location_type], border: `1px solid ${LOCATION_COLORS[job.location_type]}30`, fontFamily: 'JetBrains Mono, monospace' }}>
                          {LOCATION_LABELS[job.location_type]}
                        </span>
                        {isManual && (
                          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(167, 139, 250, 0.1)', color: '#a78bfa', border: '1px solid rgba(167,139,250,0.2)', fontFamily: 'JetBrains Mono, monospace' }}>MANUAL</span>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#64748b', fontSize: '13px' }}><Building size={12} />{job.company}</span>
                        {job.url && (
                          <a href={job.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#00D4FF', fontSize: '12px', textDecoration: 'none' }}>
                            View <ExternalLink size={10} />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={handleApproveJobs}
              disabled={selectedJobs.size === 0 || isStreaming}
              style={{
                background: selectedJobs.size > 0 ? '#00D4FF' : 'rgba(255,255,255,0.06)',
                color: selectedJobs.size > 0 ? '#0A0F1E' : '#64748b',
                fontWeight: 600, padding: '10px 24px', borderRadius: '8px', border: 'none',
                cursor: selectedJobs.size > 0 ? 'pointer' : 'not-allowed',
                display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', transition: 'all 0.2s'
              }}
            >
              {isStreaming ? <Loader2 size={16} className="animate-spin" /> : <ChevronRight size={16} />}
              Proceed with {selectedJobs.size} selected
            </button>
            <p style={{ color: '#475569', fontSize: '13px' }}>{allJobsForApproval.length} total listings found</p>
          </div>
        </div>
      )}

      {/* Step 6 — Results */}
      {status === 'completed' && tailoredResumes.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <SectionLabel number={6} label="Your Tailored Resumes" done />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {tailoredResumes.map((resume: TailoredResume, i: number) => (
              <div key={i} style={{ padding: '20px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <p style={{ color: 'white', fontSize: '15px', fontWeight: 600, fontFamily: 'Sora, sans-serif' }}>{resume.job_title}</p>
                  <span style={{ fontSize: '13px', fontFamily: 'JetBrains Mono, monospace', color: resume.match_score >= 70 ? '#10b981' : '#fbbf24', background: resume.match_score >= 70 ? 'rgba(16,185,129,0.1)' : 'rgba(251,191,36,0.1)', padding: '4px 10px', borderRadius: '6px' }}>
                    {resume.match_score?.toFixed(0)}% match
                  </span>
                </div>
                {resume.changes_summary?.length > 0 && (
                  <div>
                    <p style={{ color: '#64748b', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Changes Made</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {resume.changes_summary.slice(0, 3).map((change: string, j: number) => (
                        <p key={j} style={{ color: '#94a3b8', fontSize: '13px', display: 'flex', gap: '8px' }}><span style={{ color: '#00D4FF' }}>›</span>{change}</p>
                      ))}
                    </div>
                  </div>
                )}
                {resume.ats_keywords_added?.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <p style={{ color: '#64748b', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Keywords Added</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {resume.ats_keywords_added.slice(0, 8).map((kw: string, j: number) => (
                        <span key={j} style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', background: 'rgba(0, 212, 255, 0.08)', color: '#00D4FF', border: '1px solid rgba(0, 212, 255, 0.15)', fontFamily: 'JetBrains Mono, monospace' }}>{kw}</span>
                      ))}
                    </div>
                  </div>
                )}
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <button onClick={() => openEditor(resume)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 18px', borderRadius: '8px', background: 'rgba(0, 212, 255, 0.08)', border: '1px solid rgba(0, 212, 255, 0.2)', color: '#00D4FF', fontSize: '13px', cursor: 'pointer', fontWeight: 600, transition: 'all 0.2s' }}>
                    <Download size={14} />Edit & Download
                  </button>
                  {submittedFeedback.has(resume.job_title) ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '13px' }}>
                      <ThumbsUp size={14} /> Feedback submitted
                    </span>
                  ) : (
                    <button
                      onClick={() => setFeedbackTarget({ jobTitle: resume.job_title })}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', borderRadius: '8px', background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.15)', color: '#fbbf24', fontSize: '13px', cursor: 'pointer' }}
                    >
                      <Star size={14} /> Rate this resume
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Completion banner */}
      {status === 'completed' && (
        <div style={{ marginTop: '8px', padding: '20px', background: 'rgba(16, 185, 129, 0.06)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <CheckCircle size={20} color="#10b981" />
          <div style={{ flex: 1 }}>
            <p style={{ color: '#10b981', fontSize: '14px', fontWeight: 600 }}>Workflow Complete</p>
            <p style={{ color: '#64748b', fontSize: '13px', marginTop: '2px' }}>Your tailored resumes and company research are saved to Applications.</p>
          </div>
        </div>
      )}

      {/* Modals */}
      {editingResume && <ResumeEditor initialData={editingResume} onClose={() => setEditingResume(null)} />}
      {feedbackTarget && workflowRunId && (
        <FeedbackModal
          jobTitle={feedbackTarget.jobTitle}
          workflowRunId={workflowRunId}
          onClose={() => setFeedbackTarget(null)}
          onSubmitted={() => {
            setSubmittedFeedback(prev => new Set(prev).add(feedbackTarget.jobTitle))
            setFeedbackTarget(null)
          }}
        />
      )}
    </div>
  )
}