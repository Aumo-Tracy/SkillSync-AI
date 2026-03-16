'use client'

import { useState } from 'react'
import { generateResumePDF } from '@/lib/pdfGenerator'
import { X, Plus, Trash2, Download, ChevronDown, ChevronUp } from 'lucide-react'

interface Experience {
  title: string
  company: string
  duration: string
  bullets: string[]
}

interface Education {
  degree: string
  institution: string
  year: string
}

interface ResumeEditorProps {
  initialData: {
    full_name: string
    email: string
    job_title: string
    summary: string
    experience: Experience[]
    skills: { technical: string[]; tools: string[]; soft: string[] }
    education: Education[]
    certifications: string[]
    ats_keywords_added: string[]
  }
  onClose: () => void
}

const inputStyle = {
  width: '100%',
  padding: '8px 12px',
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '6px',
  color: 'white',
  fontSize: '13px',
  outline: 'none',
  fontFamily: 'Inter, sans-serif',
  boxSizing: 'border-box' as const
}

const textareaStyle = {
  ...inputStyle,
  resize: 'vertical' as const,
  minHeight: '80px',
  lineHeight: '1.5'
}

const sectionTitleStyle = {
  fontFamily: 'Sora, sans-serif',
  fontSize: '13px',
  fontWeight: 600,
  color: '#00D4FF',
  marginBottom: '12px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between' as const
}

const labelStyle = {
  fontSize: '11px',
  color: '#64748b',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.05em',
  marginBottom: '4px',
  display: 'block'
}

export default function ResumeEditor({ initialData, onClose }: ResumeEditorProps) {
  const [data, setData] = useState(initialData)
  const [expandedExp, setExpandedExp] = useState<number | null>(0)

  const updateField = (field: string, value: any) => {
    setData(prev => ({ ...prev, [field]: value }))
  }

  const updateExperience = (index: number, field: keyof Experience, value: any) => {
    const updated = [...data.experience]
    updated[index] = { ...updated[index], [field]: value }
    setData(prev => ({ ...prev, experience: updated }))
  }

  const updateExpBullet = (expIndex: number, bulletIndex: number, value: string) => {
    const updated = [...data.experience]
    const bullets = [...updated[expIndex].bullets]
    bullets[bulletIndex] = value
    updated[expIndex] = { ...updated[expIndex], bullets }
    setData(prev => ({ ...prev, experience: updated }))
  }

  const addExpBullet = (expIndex: number) => {
    const updated = [...data.experience]
    updated[expIndex] = { ...updated[expIndex], bullets: [...updated[expIndex].bullets, ''] }
    setData(prev => ({ ...prev, experience: updated }))
  }

  const removeExpBullet = (expIndex: number, bulletIndex: number) => {
    const updated = [...data.experience]
    updated[expIndex].bullets = updated[expIndex].bullets.filter((_, i) => i !== bulletIndex)
    setData(prev => ({ ...prev, experience: updated }))
  }

  const addExperience = () => {
    setData(prev => ({
      ...prev,
      experience: [...prev.experience, { title: '', company: '', duration: '', bullets: [''] }]
    }))
    setExpandedExp(data.experience.length)
  }

  const removeExperience = (index: number) => {
    setData(prev => ({ ...prev, experience: prev.experience.filter((_, i) => i !== index) }))
  }

  const updateEducation = (index: number, field: keyof Education, value: string) => {
    const updated = [...data.education]
    updated[index] = { ...updated[index], [field]: value }
    setData(prev => ({ ...prev, education: updated }))
  }

  const addEducation = () => {
    setData(prev => ({ ...prev, education: [...prev.education, { degree: '', institution: '', year: '' }] }))
  }

  const removeEducation = (index: number) => {
    setData(prev => ({ ...prev, education: prev.education.filter((_, i) => i !== index) }))
  }

  const updateSkills = (type: 'technical' | 'tools' | 'soft', value: string) => {
    setData(prev => ({
      ...prev,
      skills: { ...prev.skills, [type]: value.split(',').map(s => s.trim()).filter(Boolean) }
    }))
  }

  const handleDownload = () => {
    generateResumePDF(data)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      padding: '20px', overflowY: 'auto'
    }}>
      <div style={{
        width: '100%', maxWidth: '720px',
        background: '#0f172a',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: '16px',
        padding: '28px',
        position: 'relative',
        marginBottom: '20px'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontFamily: 'Sora, sans-serif', fontSize: '18px', fontWeight: 700, color: 'white', marginBottom: '4px' }}>
              Edit Resume
            </h2>
            <p style={{ color: '#64748b', fontSize: '13px' }}>
              Make changes before downloading your PDF
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
            <X size={20} color="#64748b" />
          </button>
        </div>

        {/* Personal Info */}
        <div style={{ marginBottom: '24px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>Personal Info</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={labelStyle}>Full Name</label>
              <input value={data.full_name} onChange={e => updateField('full_name', e.target.value)} style={inputStyle} placeholder="Your full name" />
            </div>
            <div>
              <label style={labelStyle}>Email</label>
              <input value={data.email} onChange={e => updateField('email', e.target.value)} style={inputStyle} placeholder="your@email.com" />
            </div>
          </div>
          <div>
            <label style={labelStyle}>Job Title</label>
            <input value={data.job_title} onChange={e => updateField('job_title', e.target.value)} style={inputStyle} placeholder="e.g. Junior Python Developer" />
          </div>
        </div>

        {/* Summary */}
        <div style={{ marginBottom: '24px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>Professional Summary</p>
          <textarea
            value={data.summary}
            onChange={e => updateField('summary', e.target.value)}
            style={textareaStyle}
            placeholder="Write a concise summary of your skills and goals..."
          />
        </div>

        {/* Experience */}
        <div style={{ marginBottom: '24px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>
            Experience
            <button onClick={addExperience} style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '6px', padding: '4px 10px', color: '#00D4FF', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Plus size={12} /> Add
            </button>
          </p>

          {data.experience.map((exp, i) => (
            <div key={i} style={{ marginBottom: '12px', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px', overflow: 'hidden' }}>
              {/* Exp header */}
              <div
                onClick={() => setExpandedExp(expandedExp === i ? null : i)}
                style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.02)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
              >
                <p style={{ color: exp.title ? 'white' : '#475569', fontSize: '13px', fontWeight: 500 }}>
                  {exp.title || 'Untitled Role'} {exp.company ? `@ ${exp.company}` : ''}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button onClick={(e) => { e.stopPropagation(); removeExperience(i) }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px' }}>
                    <Trash2 size={13} color="#f87171" />
                  </button>
                  {expandedExp === i ? <ChevronUp size={14} color="#64748b" /> : <ChevronDown size={14} color="#64748b" />}
                </div>
              </div>

              {expandedExp === i && (
                <div style={{ padding: '16px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                    <div>
                      <label style={labelStyle}>Job Title</label>
                      <input value={exp.title} onChange={e => updateExperience(i, 'title', e.target.value)} style={inputStyle} placeholder="e.g. Python Developer" />
                    </div>
                    <div>
                      <label style={labelStyle}>Company</label>
                      <input value={exp.company} onChange={e => updateExperience(i, 'company', e.target.value)} style={inputStyle} placeholder="Company name" />
                    </div>
                  </div>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={labelStyle}>Duration</label>
                    <input value={exp.duration} onChange={e => updateExperience(i, 'duration', e.target.value)} style={inputStyle} placeholder="e.g. Jan 2024 - Present" />
                  </div>
                  <label style={labelStyle}>Bullet Points</label>
                  {exp.bullets.map((bullet, j) => (
                    <div key={j} style={{ display: 'flex', gap: '8px', marginBottom: '6px' }}>
                      <input value={bullet} onChange={e => updateExpBullet(i, j, e.target.value)} style={{ ...inputStyle, flex: 1 }} placeholder="Describe what you did and the impact..." />
                      <button onClick={() => removeExpBullet(i, j)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', flexShrink: 0 }}>
                        <Trash2 size={13} color="#f87171" />
                      </button>
                    </div>
                  ))}
                  <button onClick={() => addExpBullet(i)} style={{ background: 'none', border: '1px dashed rgba(255,255,255,0.1)', borderRadius: '6px', padding: '6px 12px', color: '#64748b', fontSize: '12px', cursor: 'pointer', width: '100%', marginTop: '4px' }}>
                    + Add bullet point
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Skills */}
        <div style={{ marginBottom: '24px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>Skills</p>
          <p style={{ color: '#475569', fontSize: '12px', marginBottom: '12px' }}>Separate each skill with a comma</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <label style={labelStyle}>Technical Skills</label>
              <input value={data.skills.technical.join(', ')} onChange={e => updateSkills('technical', e.target.value)} style={inputStyle} placeholder="Python, FastAPI, LangChain, REST APIs..." />
            </div>
            <div>
              <label style={labelStyle}>Tools</label>
              <input value={data.skills.tools.join(', ')} onChange={e => updateSkills('tools', e.target.value)} style={inputStyle} placeholder="Git, VS Code, Docker, Supabase..." />
            </div>
          </div>
        </div>

        {/* Education */}
        <div style={{ marginBottom: '24px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>
            Education
            <button onClick={addEducation} style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: '6px', padding: '4px 10px', color: '#00D4FF', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Plus size={12} /> Add
            </button>
          </p>
          {data.education.map((edu, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 120px auto', gap: '10px', marginBottom: '10px', alignItems: 'end' }}>
              <div>
                <label style={labelStyle}>Degree / Program</label>
                <input value={edu.degree} onChange={e => updateEducation(i, 'degree', e.target.value)} style={inputStyle} placeholder="e.g. Certificate in Python" />
              </div>
              <div>
                <label style={labelStyle}>Institution</label>
                <input value={edu.institution} onChange={e => updateEducation(i, 'institution', e.target.value)} style={inputStyle} placeholder="School name" />
              </div>
              <div>
                <label style={labelStyle}>Year</label>
                <input value={edu.year} onChange={e => updateEducation(i, 'year', e.target.value)} style={inputStyle} placeholder="2025" />
              </div>
              <button onClick={() => removeEducation(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '8px', marginBottom: '2px' }}>
                <Trash2 size={13} color="#f87171" />
              </button>
            </div>
          ))}
        </div>

        {/* Certifications */}
        <div style={{ marginBottom: '28px', padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p style={sectionTitleStyle}>Certifications</p>
          <p style={{ color: '#475569', fontSize: '12px', marginBottom: '12px' }}>One per line</p>
          <textarea
            value={data.certifications.join('\n')}
            onChange={e => updateField('certifications', e.target.value.split('\n').filter(Boolean))}
            style={{ ...textareaStyle, minHeight: '60px' }}
            placeholder="e.g. AWS Cloud Practitioner&#10;Google Python Certificate"
          />
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{ padding: '10px 20px', borderRadius: '8px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', fontSize: '13px', cursor: 'pointer' }}
          >
            Cancel
          </button>
          <button
            onClick={handleDownload}
            style={{ padding: '10px 24px', borderRadius: '8px', background: '#00D4FF', border: 'none', color: '#0A0F1E', fontSize: '13px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Download size={14} />
            Download PDF
          </button>
        </div>
      </div>
    </div>
  )
}