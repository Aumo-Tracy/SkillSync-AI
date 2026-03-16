export interface UserProfile {
  id: string
  email: string
  full_name: string | null
  target_roles: string[]
  priority_preference: 'remote_international' | 'hybrid_local' | 'fulltime_local'
  preferred_llm: string
  tone_preference: string
  monthly_token_usage: number
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface Resume {
  id: string
  user_id: string
  title: string
  raw_text: string
  is_base: boolean
  skills_extracted: string[]
  version: number
  created_at: string
}

export type LocationType = 
  | 'remote_international' 
  | 'hybrid_local' 
  | 'fulltime_local'

export interface Job {
  id?: string
  external_id: string
  title: string
  company: string
  location: string
  location_type: LocationType
  description: string
  required_skills: string[]
  source: string
  url: string
  salary_min: number | null
  salary_max: number | null
  priority_tier: number
}

export type WorkflowStatus = 
  | 'pending'
  | 'running' 
  | 'awaiting_hitl'
  | 'completed'
  | 'failed'

export type SSEEventType =
  | 'agent_started'
  | 'agent_completed'
  | 'hitl_required'
  | 'pipeline_complete'
  | 'pipeline_error'

export interface SSEEvent {
  event_type: SSEEventType
  message: string
  workflow_run_id: string
  data: {
    agent?: string
    jobs?: Job[]
    count?: number
    pause_point?: string
    analyses?: any[]
    resumes?: any[]
    research?: any[]
  }
}

export interface WorkflowRun {
  id: string
  user_id: string
  status: WorkflowStatus
  current_agent: string | null
  input_data: Record<string, any>
  output_data: Record<string, any>
  error_message: string | null
  started_at: string
  completed_at: string | null
}

export interface TailoredResume {
  job_title: string
  summary: string
  experience: {
    title: string
    company: string
    duration: string
    bullets: string[]
  }[]
  skills: {
    technical: string[]
    tools: string[]
    soft: string[]
  }
  education: {
    degree: string
    institution: string
    year: string
  }[]
  certifications: string[]
  ats_keywords_added: string[]
  changes_summary: string[]
  match_score: number
}

export interface Feedback {
  rating: number
  feedback_text?: string
  feedback_type: 'resume_quality' | 'job_match' | 'company_research' | 'overall'
  workflow_run_id?: string
  application_id?: string
}