'use client'

import { useState } from 'react'
import { X, Star, Send, Loader2 } from 'lucide-react'

interface FeedbackModalProps {
  jobTitle: string
  workflowRunId: string
  onClose: () => void
  onSubmitted: () => void
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function StarRow({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  const [hovered, setHovered] = useState(0)
  return (
    <div style={{ marginBottom: '16px' }}>
      <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>{label}</p>
      <div style={{ display: 'flex', gap: '6px' }}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => onChange(star)}
            onMouseEnter={() => setHovered(star)}
            onMouseLeave={() => setHovered(0)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px' }}
          >
            <Star
              size={24}
              fill={(hovered || value) >= star ? '#fbbf24' : 'none'}
              color={(hovered || value) >= star ? '#fbbf24' : '#334155'}
            />
          </button>
        ))}
        <span style={{ color: '#64748b', fontSize: '12px', marginLeft: '8px', alignSelf: 'center' }}>
          {(hovered || value) === 1 && 'Poor'}
          {(hovered || value) === 2 && 'Fair'}
          {(hovered || value) === 3 && 'Good'}
          {(hovered || value) === 4 && 'Great'}
          {(hovered || value) === 5 && 'Excellent'}
        </span>
      </div>
    </div>
  )
}

export default function FeedbackModal({ jobTitle, workflowRunId, onClose, onSubmitted }: FeedbackModalProps) {
  const [overallRating, setOverallRating] = useState(0)
  const [resumeQuality, setResumeQuality] = useState(0)
  const [jobRelevance, setJobRelevance] = useState(0)
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!overallRating) { setError('Please give an overall rating'); return }
    setIsSubmitting(true)
    setError('')
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`${BASE_URL}/api/workflow/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          workflow_run_id: workflowRunId,
          job_title: jobTitle,
          rating: overallRating,
          resume_quality: resumeQuality || null,
          job_relevance: jobRelevance || null,
          comment: comment.trim() || null
        })
      })
      const data = await res.json()
      if (data.success) {
        onSubmitted()
      } else {
        setError('Failed to submit feedback')
      }
    } catch {
      setError('Network error — try again')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        width: '100%', maxWidth: '480px',
        background: '#0F1629',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '16px', padding: '28px',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontFamily: 'Sora, sans-serif', fontSize: '18px', fontWeight: 700, color: 'white', marginBottom: '4px' }}>
              Rate this Resume
            </h3>
            <p style={{ color: '#64748b', fontSize: '13px' }}>{jobTitle}</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
            <X size={18} color="#64748b" />
          </button>
        </div>

        {/* Ratings */}
        <StarRow label="Overall — how useful was this tailored resume?" value={overallRating} onChange={setOverallRating} />
        <StarRow label="Resume Quality — how well was it rewritten?" value={resumeQuality} onChange={setResumeQuality} />
        <StarRow label="Job Relevance — how well did this job match your profile?" value={jobRelevance} onChange={setJobRelevance} />

        {/* Comment */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>
            Comments — what could be improved? (optional)
          </p>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="e.g. The summary was too generic, keywords were good but bullets needed more impact..."
            rows={3}
            style={{
              width: '100%', padding: '10px 14px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '8px', color: 'white', fontSize: '13px',
              outline: 'none', resize: 'vertical',
              fontFamily: 'Inter, sans-serif', boxSizing: 'border-box'
            }}
          />
        </div>

        {error && (
          <p style={{ color: '#f87171', fontSize: '13px', marginBottom: '12px' }}>{error}</p>
        )}

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !overallRating}
            style={{
              flex: 1, padding: '10px', borderRadius: '8px',
              background: overallRating ? '#00D4FF' : 'rgba(255,255,255,0.06)',
              color: overallRating ? '#0A0F1E' : '#64748b',
              border: 'none', cursor: overallRating ? 'pointer' : 'not-allowed',
              fontSize: '14px', fontWeight: 600,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
            }}
          >
            {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            Submit Feedback
          </button>
          <button
            onClick={onClose}
            style={{
              padding: '10px 18px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#94a3b8', fontSize: '14px', cursor: 'pointer'
            }}
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  )
}
