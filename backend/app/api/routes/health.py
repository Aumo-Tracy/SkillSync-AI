"""
Health Check Endpoint
System health and status monitoring
"""
from fastapi import APIRouter
from datetime import datetime
from typing import Literal, Dict

router = APIRouter()


# Track server start time
_server_start_time = datetime.utcnow()


@router.get("/health")
async def health_check():
    """
    Check system health and component status
    
    Returns:
        dict: System health status
    """
    # Lazy imports to avoid circular dependencies
    try:
        from app.config import settings
    except:
        settings = None
    
    components = {}
    
    # Check OpenAI API key
    if settings:
        components["openai"] = bool(settings.OPENAI_API_KEY)
    else:
        components["openai"] = False
    
    # Check database
    try:
        from app.services.database import get_database
        db = get_database()
        db_status = db.health_check()
        components["database"] = db_status["status"] == "healthy"
    except Exception as e:
        components["database"] = False
    
    # Check vector store
    try:
        from app.services.rag.vector_store import get_vector_store
        vector_store = get_vector_store()
        components["vector_store"] = vector_store.is_initialized()
    except Exception as e:
        components["vector_store"] = False
    
    # Determine overall status
    all_healthy = all(components.values())
    
    if all_healthy:
        status = "healthy"
    elif any(components.values()):
        status = "degraded"
    else:
        status = "unhealthy"
    
    # Calculate uptime
    uptime_seconds = (datetime.utcnow() - _server_start_time).total_seconds()
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": components,
        "uptime_seconds": uptime_seconds
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ShopEase AI Support API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }