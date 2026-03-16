import { create } from 'zustand'
import { Job, SSEEvent, WorkflowStatus, TailoredResume } from '@/types'

interface WorkflowState {
  workflowRunId: string | null
  status: WorkflowStatus | null
  events: SSEEvent[]
  discoveredJobs: Job[]
  approvedJobs: Job[]
  tailoredResumes: TailoredResume[]
  companyResearch: any[]
  isStreaming: boolean
  currentAgent: string | null
  error: string | null
  setWorkflowRunId: (id: string) => void
  setStatus: (status: WorkflowStatus) => void
  addEvent: (event: SSEEvent) => void
  setDiscoveredJobs: (jobs: Job[]) => void
  setApprovedJobs: (jobs: Job[]) => void
  setTailoredResumes: (resumes: TailoredResume[]) => void
  setCompanyResearch: (research: any[]) => void
  setStreaming: (streaming: boolean) => void
  setCurrentAgent: (agent: string | null) => void
  setError: (error: string | null) => void
  reset: () => void
}

const initialState = {
  workflowRunId: null,
  status: null,
  events: [],
  discoveredJobs: [],
  approvedJobs: [],
  tailoredResumes: [],
  companyResearch: [],
  isStreaming: false,
  currentAgent: null,
  error: null,
}

export const useWorkflowStore = create<WorkflowState>()((set) => ({
  ...initialState,
  setWorkflowRunId: (id) => set({ workflowRunId: id }),
  setStatus: (status) => set({ status }),
  addEvent: (event) => set((state) => ({ events: [...state.events, event] })),
  setDiscoveredJobs: (jobs) => set({ discoveredJobs: jobs }),
  setApprovedJobs: (jobs) => set({ approvedJobs: jobs }),
  setTailoredResumes: (resumes) => set({ tailoredResumes: resumes }),
  setCompanyResearch: (research) => set({ companyResearch: research }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setCurrentAgent: (agent) => set({ currentAgent: agent }),
  setError: (error) => set({ error }),
  reset: () => set(initialState)
}))