from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class FeedbackType(str, Enum):
    resume_quality = "resume_quality"
    job_match = "job_match"
    company_research = "company_research"
    overall = "overall"

class FeedbackCreate(BaseModel):
    application_id: Optional[UUID] = None
    workflow_run_id: Optional[UUID] = None
    rating: int
    feedback_text: Optional[str] = None
    feedback_type: FeedbackType
    agent_adjustments: dict = {}

class FeedbackResponse(FeedbackCreate):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class AgentLogCreate(BaseModel):
    workflow_run_id: UUID
    agent_name: str
    input_data: dict = {}
    output_data: dict = {}
    tokens_used: int = 0
    duration_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None

class AgentLogResponse(AgentLogCreate):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True