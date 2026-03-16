from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    target_roles: list[str] = []
    priority_preference: str = "remote_international"
    preferred_llm: str = "openai"
    tone_preference: str = "professional"

class ProfileCreate(ProfileBase):
    email: EmailStr
    full_name: Optional[str] = None

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    target_roles: Optional[list[str]] = None
    priority_preference: Optional[str] = None
    preferred_llm: Optional[str] = None
    tone_preference: Optional[str] = None

class ProfileResponse(ProfileBase):
    id: UUID
    email: str
    monthly_token_usage: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Auth-specific models
class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ProfileResponse