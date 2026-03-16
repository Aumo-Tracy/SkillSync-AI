from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ResumeSection(BaseModel):
    # Structured representation of parsed resume sections
    summary: Optional[str] = None
    experience: list[dict] = []
    education: list[dict] = []
    skills: list[str] = []
    projects: list[dict] = []
    certifications: list[str] = []

class ResumeBase(BaseModel):
    title: str
    raw_text: str
    is_base: bool = False

class ResumeCreate(ResumeBase):
    user_id: UUID

class ResumeResponse(ResumeBase):
    id: UUID
    user_id: UUID
    parsed_sections: ResumeSection = ResumeSection()
    skills_extracted: list[str] = []
    version: int = 1
    created_at: datetime

    class Config:
        from_attributes = True

class TailoredResumeRequest(BaseModel):
    base_resume_id: UUID
    job_listing_id: UUID
    user_feedback: Optional[str] = None
    tone_override: Optional[str] = None

class TailoredResumeResponse(BaseModel):
    original_resume_id: UUID
    job_listing_id: UUID
    tailored_content: ResumeSection
    changes_summary: list[str] = []
    match_score: float = 0.0
    ats_keywords_added: list[str] = []
    skill_gaps_identified: list[str] = []