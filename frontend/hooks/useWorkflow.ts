'use client'

import { useCallback } from 'react'
import { useWorkflowStore } from '@/store/workflow'
import { workflowApi } from '@/lib/api'
import { SSEEvent } from '@/types'

export function useWorkflow() {
  const store = useWorkflowStore()
  
  const handleEvent = useCallback((event: SSEEvent) => {
    // Always capture workflow_run_id from every event
    if (event.workflow_run_id && !useWorkflowStore.getState().workflowRunId) {
      useWorkflowStore.getState().setWorkflowRunId(event.workflow_run_id)
    }

    switch (event.event_type) {
      case 'agent_started':
        store.setCurrentAgent(event.data.agent || null)
        break
        
      case 'agent_completed':
        if (event.data.jobs) store.setDiscoveredJobs(event.data.jobs)
        if (event.data.resumes) store.setTailoredResumes(event.data.resumes)
        if (event.data.research) store.setCompanyResearch(event.data.research)
        break
        
      case 'hitl_required':
        store.setStatus('awaiting_hitl')
        if (event.data.jobs && event.data.jobs.length > 0) {
          store.setDiscoveredJobs(event.data.jobs)
        } else if (store.discoveredJobs.length === 0) {
          // jobs were set in agent_completed, status just needs updating
        }
        store.setCurrentAgent('hitl_job_approval')
        break  // ✅ FIXED: prevent fall-through
        
      case 'pipeline_complete':
        store.setStatus('completed')
        store.setCurrentAgent(null)
        break
        
      case 'pipeline_error':
        store.setStatus('failed')
        store.setError(event.message)
        break
    }
  }, [store])

  const parseSSEStream = useCallback(async (response: Response) => {
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  
  if (!reader) return
  
  store.setStreaming(true)
  let buffer = ''
  
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // Process complete lines only
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // keep incomplete last line in buffer
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const event: SSEEvent = JSON.parse(line.slice(6))
            console.log('SSE EVENT:', event.event_type, event.data?.jobs?.length)
            store.addEvent(event)
            handleEvent(event)
          } catch {
            // Skip malformed events
          }
        }
      }
    }
    // Process any remaining buffer
    if (buffer.startsWith('data: ')) {
      try {
        const event: SSEEvent = JSON.parse(buffer.slice(6))
        store.addEvent(event)
        handleEvent(event)
      } catch {}
    }
  } finally {
    store.setStreaming(false)
    reader.releaseLock()
    // Safety net
    const state = useWorkflowStore.getState()
    if (state.discoveredJobs.length > 0 && state.status === 'running') {
      store.setStatus('awaiting_hitl')
    }
  }
}, [store, handleEvent])
  
  const startWorkflow = useCallback(async (
    resumeId: string,
    searchParams?: any
  ) => {
    store.reset()
    store.setStatus('running')
    
    try {
      const response = await workflowApi.start(resumeId, searchParams)
      console.log('Response status:', response.status, 'ok:', response.ok)
      await parseSSEStream(response)

      // If stream ended but we have jobs, ensure HITL status is set
      const state = useWorkflowStore.getState()
      if (state.discoveredJobs.length > 0 && state.status === 'running') {
        store.setStatus('awaiting_hitl')
      }
    } catch (error: any) {
      store.setError(error.message)
      store.setStatus('failed')
    }
  }, [parseSSEStream, store]) // ✅ FIXED: closed function properly
  
  const approveJobs = useCallback(async (
    workflowRunId: string,
    approvedJobIds: string[]
  ) => {
    store.setApprovedJobs(
      store.discoveredJobs.filter(j => 
        approvedJobIds.includes(j.external_id)
      )
    )
    store.setStatus('running')
    
    try {
      const response = await workflowApi.approveJobs(
        workflowRunId,
        approvedJobIds
      )
      await parseSSEStream(response)
    } catch (error: any) {
      store.setError(error.message)
      store.setStatus('failed')
    }
  }, [parseSSEStream, store])
  
  return {
    ...store,
    startWorkflow,
    approveJobs
  }
}