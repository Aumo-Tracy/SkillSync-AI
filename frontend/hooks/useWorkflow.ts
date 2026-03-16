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
        if (event.data.jobs) store.setDiscoveredJobs(event.data.jobs)
        // Capture workflow ID at the HITL pause point
        if (event.workflow_run_id) {
          store.setWorkflowRunId(event.workflow_run_id)
        }
        break
        
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
    
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: SSEEvent = JSON.parse(line.slice(6))
              store.addEvent(event)
              handleEvent(event)
            } catch {
              // Skip malformed events
            }
          }
        }
      }
    } finally {
      store.setStreaming(false)
      reader.releaseLock()
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
      await parseSSEStream(response)
    } catch (error: any) {
      store.setError(error.message)
      store.setStatus('failed')
    }
  }, [parseSSEStream, store])
  
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