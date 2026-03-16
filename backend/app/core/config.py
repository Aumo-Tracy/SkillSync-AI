from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # App
    app_env: Literal["development", "production"] = "development"
    app_secret_key: str

    # LLM
    openai_api_key: str
    gemini_api_key: str
    default_llm_provider: str = "gemini"
    default_llm_model: str = "gemini-2.0-pro"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_collection_resumes: str = "resumes"
    qdrant_collection_jobs: str = "jobs"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Job APIs
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    tavily_api_key: str = ""

    # Rate limiting
    max_workflows_per_hour: int = 10
    max_requests_per_minute: int = 50
    monthly_token_budget: int = 500000

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()