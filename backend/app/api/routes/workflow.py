import httpx
import re
from app.core.config import settings
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import get_current_user
from app.models import ProfileResponse, JobSearchParams
from app.services.workflow_service import (
    create_workflow_run,
    stream_workflow,
    resume_workflow_after_approval,
    get_workflow_status,
    update_workflow_run
)
from app.db.supabase_client import get_supabase_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class StartWorkflowRequest(BaseModel):
    resume_id: str
    search_params: Optional[dict] = None
    user_feedback: Optional[str] = None

class ApprovalRequest(BaseModel):
    approved_job_ids: list[str]

@router.post("/start")
async def start_workflow(
    payload: StartWorkflowRequest,
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    
    # Fetch the user's resume
    try:
        resume_result = supabase.table("resumes")\
            .select("*")\
            .eq("id", payload.resume_id)\
            .eq("user_id", str(current_user.id))\
            .single()\
            .execute()
        
        if not resume_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Default search params from user profile
    search_params = payload.search_params or {
        "roles": current_user.target_roles or [
            "AI engineer",
            "Python developer",
            "backend developer"
        ],
        "max_results": 20
    }

    # Extract manual jobs before passing search_params to agents
    manual_jobs = search_params.pop("manual_jobs", [])

    # Create workflow run record
    workflow_run_id = await create_workflow_run(
        user_id=str(current_user.id),
        input_data={
            "resume_id": payload.resume_id,
            "search_params": search_params
        }
    )

    # Build initial LangGraph state
    initial_state = {
        "workflow_run_id": workflow_run_id,
        "user_id": str(current_user.id),
        "user_profile": current_user.model_dump(mode="json"),
        "base_resume": resume_result.data,
        "search_params": search_params,
        "discovered_jobs": manual_jobs,
        "user_feedback": payload.user_feedback,
        "messages": []
    }
    logger.info(
        f"Workflow started | "
        f"user={current_user.email} | "
        f"workflow={workflow_run_id}"
    )
    
    # Return SSE stream
    return StreamingResponse(
        stream_workflow(
            user_id=str(current_user.id),
            workflow_run_id=workflow_run_id,
            initial_state=initial_state
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Workflow-ID": workflow_run_id
        }
    )

@router.post("/{workflow_run_id}/approve")
async def approve_jobs(
    workflow_run_id: str,
    payload: ApprovalRequest,
    current_user: ProfileResponse = Depends(get_current_user)
):
    # Verify this workflow belongs to the current user
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("workflow_runs")\
            .select("*")\
            .eq("id", workflow_run_id)\
            .eq("user_id", str(current_user.id))\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        if result.data["status"] != "awaiting_hitl":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is not awaiting approval"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    logger.info(
        f"Jobs approved | "
        f"workflow={workflow_run_id} | "
        f"approved={len(payload.approved_job_ids)}"
    )
    
    # Resume pipeline with approved jobs as SSE stream
    return StreamingResponse(
        resume_workflow_after_approval(
            workflow_run_id=workflow_run_id,
            user_id=str(current_user.id),
            approved_job_ids=payload.approved_job_ids
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Workflow-ID": workflow_run_id
        }
    )

@router.get("/{workflow_run_id}/status")
async def get_status(
    workflow_run_id: str,
    current_user: ProfileResponse = Depends(get_current_user)
):
    # Check Redis cache first
    cached = await get_workflow_status(workflow_run_id)
    if cached:
        return cached
    
    # Fall back to database
    supabase = get_supabase_client()
    result = supabase.table("workflow_runs")\
        .select("*")\
        .eq("id", workflow_run_id)\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    return result.data

@router.get("/history")
async def get_workflow_history(
    current_user: ProfileResponse = Depends(get_current_user)
):
    supabase = get_supabase_client()
    result = supabase.table("workflow_runs")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("started_at", desc=True)\
        .limit(20)\
        .execute()
    return result.data or []
    
@router.post("/fetch-job")
async def fetch_job_from_url(
    payload: dict,
    current_user: ProfileResponse = Depends(get_current_user)
):
    """
    Fetch job details from a URL using Tavily.
    Returns extracted title, company, and description.
    """
    import re
    import httpx

    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    if not settings.tavily_api_key:
        raise HTTPException(status_code=400, detail="Tavily API key not configured")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": f"job description {url}",
                    "search_depth": "advanced",
                    "max_results": 1,
                    "include_raw_content": True,
                    "urls": [url]
                }
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    result = results[0]
                    raw = result.get("raw_content", "") or result.get("content", "")
                    title = result.get("title", "")
                    clean = re.sub(r'\n{3,}', '\n\n', raw)
                    clean = clean[:5000]

                    return {
                        "success": True,
                        "title": title,
                        "description": clean,
                        "url": url
                    }

        return {
            "success": False,
            "error": "Could not extract job details from this URL"
        }

    except Exception as e:
        logger.error(f"Job URL fetch failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")   
    
    return result.data

# Add this to backend/app/api/routes/workflow.py

from pydantic import BaseModel
from typing import Optional

class FeedbackPayload(BaseModel):
    application_id: Optional[str] = None
    workflow_run_id: str
    job_title: str
    rating: int  # 1-5
    comment: Optional[str] = None
    resume_quality: Optional[int] = None   # 1-5 specifically on resume output
    job_relevance: Optional[int] = None    # 1-5 on job match relevance

@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackPayload,
    current_user: ProfileResponse = Depends(get_current_user)
):
    try:
        from app.db.supabase_client import get_supabase_admin_client
        supabase = get_supabase_admin_client()
        
        supabase.table("resume_feedback").insert({
            "user_id": str(current_user.id),
            "workflow_run_id": payload.workflow_run_id,
            "job_title": payload.job_title,
            "rating": payload.rating,
            "comment": payload.comment,
            "resume_quality": payload.resume_quality,
            "job_relevance": payload.job_relevance,
        }).execute()
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))