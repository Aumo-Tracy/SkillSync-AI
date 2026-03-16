from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class WorkflowStatus(str, Enum):
    pending = "pending"
    running = "running"
    awaiting_hitl = "awaiting_hitl"
    completed = "completed"
    failed = "failed"

class AgentName(str, Enum):
    orchestrator = "orchestrator"
    job_discovery = "job_discovery"
    resume_analysis = "resume_analysis"
    resume_tailoring = "resume_tailoring"
    company_research = "company_research"
    memory_agent = "memory_agent"

class WorkflowRunCreate(BaseModel):
    user_id: UUID
    input_data: dict = {}

class WorkflowRunResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: WorkflowStatus
    current_agent: Optional[str] = None
    input_data: dict = {}
    output_data: dict = {}
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# SSE event models — these are what stream to your frontend in real time
class SSEEventType(str, Enum):
    agent_started = "agent_started"
    agent_completed = "agent_completed"
    hitl_required = "hitl_required"
    pipeline_complete = "pipeline_complete"
    pipeline_error = "pipeline_error"

class SSEEvent(BaseModel):
    event_type: SSEEventType
    agent_name: Optional[AgentName] = None
    message: str
    data: Optional[dict] = None
    workflow_run_id: UUID

# LangGraph state — this is the typed object that flows through your entire agent graph
class AgentState(BaseModel):
    workflow_run_id: UUID
    user_id: UUID
    user_profile: Optional[dict] = None
    base_resume: Optional[dict] = None
    search_params: Optional[dict] = None
    discovered_jobs: list[dict] = []
    approved_jobs: list[dict] = []
    resume_analyses: list[dict] = []
    tailored_resumes: list[dict] = []
    company_research: list[dict] = []
    current_agent: Optional[str] = None
    hitl_pause_point: Optional[str] = None
    error: Optional[str] = None
    completed: bool = False