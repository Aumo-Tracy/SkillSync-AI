"""
Chat API Endpoints
Main chat interface for the AI support agent
"""
import uuid
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

router = APIRouter()


# Define request/response models inline to avoid import issues
class ChatRequest(BaseModel):
    """Chat request from frontend"""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_email: Optional[EmailStr] = None
    include_sources: bool = True


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint - process user messages
    
    Args:
        request: ChatRequest with message and optional metadata
        
    Returns:
        ChatResponse: AI response with sources and metadata
        
    Raises:
        ValidationException: If input validation fails
        HTTPException: If processing fails
    """
    # Lazy imports to avoid circular dependencies
    from app.core.logging import get_logger
    from app.core.security import validate_chat_request
    from app.core.errors import ValidationException
    from app.services.langchain.agent import get_support_agent
    
    logger = get_logger(__name__)
    
    # Validate request
    is_valid, error_message = validate_chat_request(
        message=request.message,
        email=request.user_email
    )
    
    if not is_valid:
        logger.warning(
            "Chat request validation failed",
            extra={"error": error_message}
        )
        raise ValidationException(error_message)
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:16]}"
    
    logger.info(
        "Chat request received",
        extra={
            "session_id": session_id,
            "has_email": bool(request.user_email),
            "message_length": len(request.message)
        }
    )
    
    try:
        # Get agent and process
        agent = get_support_agent()
        
        response = await agent.chat(
            message=request.message,
            session_id=session_id,
            user_email=request.user_email,
            include_sources=request.include_sources
        )
        
        logger.info(
            "Chat response generated",
            extra={
                "session_id": session_id,
                "response_length": len(response.response),
                "sources_count": len(response.sources) if response.sources else 0,
                "tools_used": len(response.tool_calls) if response.tool_calls else 0
            }
        )
        
        # Convert to dict for response
        return {
            "response": response.response,
            "session_id": response.session_id,
            "sources": [s.model_dump() for s in response.sources] if response.sources else None,
            "tool_calls": [t.model_dump() for t in response.tool_calls] if response.tool_calls else None,
            "token_usage": response.token_usage.model_dump() if response.token_usage else None,
            "response_time_ms": response.response_time_ms,
            "timestamp": response.timestamp.isoformat()
        }
    
    except ValidationException:
        raise
    except Exception as e:
        logger.error(
            f"Chat processing failed: {e}",
            extra={"session_id": session_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process your message. Please try again."
        )


@router.post("/chat/clear-session")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    from app.core.logging import get_logger
    from app.services.langchain.agent import get_support_agent
    
    logger = get_logger(__name__)
    
    try:
        agent = get_support_agent()
        agent.clear_session(session_id)
        
        logger.info(f"Session cleared: {session_id}")
        
        return {
            "success": True,
            "message": f"Session {session_id} cleared successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear session"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of messages in the session
    """
    from app.core.logging import get_logger
    from app.services.langchain.agent import get_support_agent
    
    logger = get_logger(__name__)
    
    try:
        agent = get_support_agent()
        history = agent.get_session_history(session_id)
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "messages": [msg.model_dump() for msg in history]
        }
    
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )