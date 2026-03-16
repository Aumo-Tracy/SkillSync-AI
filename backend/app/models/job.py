from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class LocationType(str, Enum):
    remote_international = "remote_international"
    hybrid_local = "hybrid_local"
    fulltime_local = "fulltime_local"

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    location_type: LocationType
    description: Optional[str] = None
    required_skills: list[str] = []
    source: Optional[str] = None
    url: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

class JobCreate(JobBase):
    external_id: Optional[str] = None
    priority_tier: int = 3

class JobResponse(JobBase):
    id: UUID
    priority_tier: int
    fetched_at: datetime

    class Config:
        from_attributes = True

class JobSearchParams(BaseModel):
    # What the user sends when initiating job discovery
    roles: list[str] = ["AI engineer", "Python developer", "backend developer"]
    location_types: list[LocationType] = [
        LocationType.remote_international,
        LocationType.hybrid_local,
        LocationType.fulltime_local
    ]
    max_results: int = 20
    keywords: Optional[list[str]] = None

class JobShortlist(BaseModel):
    # What the orchestrator returns at the HITL approval gate
    jobs: list[JobResponse]
    total_found: int
    search_params_used: JobSearchParams
    requires_approval: bool = True

class JobApprovalRequest(BaseModel):
    # What the user sends back after reviewing the shortlist
    approved_job_ids: list[UUID]
    rejected_job_ids: list[UUID] = []