from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models import ProfileResponse, FeedbackCreate, FeedbackResponse
from app.db.supabase_client import get_supabase_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    result = supabase.table("feedback").insert({
        "user_id": str(current_user.id),
        "application_id": str(payload.application_id) if payload.application_id else None,
        "workflow_run_id": str(payload.workflow_run_id) if payload.workflow_run_id else None,
        "rating": payload.rating,
        "feedback_text": payload.feedback_text,
        "feedback_type": payload.feedback_type,
        "agent_adjustments": payload.agent_adjustments
    }).execute()
    
    logger.info(
        f"Feedback submitted | "
        f"user={current_user.email} | "
        f"rating={payload.rating} | "
        f"type={payload.feedback_type}"
    )
    
    return FeedbackResponse(**result.data[0])

@router.get("/", response_model=list[FeedbackResponse])
async def get_feedback_history(
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    result = supabase.table("feedback")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("created_at", desc=True)\
        .execute()
    
    return [FeedbackResponse(**f) for f in result.data]