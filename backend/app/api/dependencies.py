"""
API Dependencies
Shared dependencies for FastAPI routes
"""
from typing import Optional
from fastapi import Header, HTTPException, status
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify API key (optional - for production)
    
    Args:
        x_api_key: API key from header
        
    Returns:
        bool: True if valid or not required
        
    Raises:
        HTTPException: If API key required but invalid
    """
    # In development, API key not required
    if settings.ENVIRONMENT == "development":
        return True
    
    # In production, check if API key is configured
    if not hasattr(settings, 'API_KEY') or not settings.API_KEY:
        return True  # API key not configured, allow access
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if x_api_key != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True


async def get_user_email(x_user_email: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract user email from header (optional)
    
    Args:
        x_user_email: User email from header
        
    Returns:
        Optional user email
    """
    return x_user_email


# Export
__all__ = ['verify_api_key', 'get_user_email']