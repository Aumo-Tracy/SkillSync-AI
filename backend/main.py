from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.utils.logger import get_logger
from app.db.qdrant_client import get_qdrant_client, ensure_collections
from app.db.redis_client import get_redis_client, close_redis_client
from app.db.supabase_client import get_supabase_client
from app.api.routes import auth, workflow, jobs, resume, feedback
import os
from app.core.config import settings

# LangSmith tracing
if settings.langchain_tracing_v2 and settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Resume Agent API in {settings.app_env} mode")

    try:
        qdrant = get_qdrant_client()
        ensure_collections(qdrant)
        logger.info("Qdrant connection verified")
    except Exception as e:
        logger.error(f"Qdrant connection failed: {e}")

    try:
        redis = await get_redis_client()
        await redis.ping()
        logger.info("Redis connection verified")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")

    try:
        supabase = get_supabase_client()
        supabase.table("profiles").select("id").limit(1).execute()
        logger.info("Supabase connection verified")
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")

    yield
    await close_redis_client()
    logger.info("Shutting down Resume Agent API")

app = FastAPI(title="Resume Agent API", version="0.1.0", lifespan=lifespan)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env}