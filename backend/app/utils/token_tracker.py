from app.db.supabase_client import get_supabase_admin_client
from app.db.redis_client import get_redis_client
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def check_token_budget(user_id: str) -> dict:
    try:
        supabase = get_supabase_admin_client()
        result = supabase.table("profiles")\
            .select("monthly_token_usage")\
            .eq("id", user_id)\
            .single()\
            .execute()
        
        usage = result.data.get("monthly_token_usage", 0)
        budget = settings.monthly_token_budget
        remaining = budget - usage
        at_limit = remaining <= 0
        near_limit = remaining <= (budget * 0.2)
        
        return {
            "usage": usage,
            "budget": budget,
            "remaining": remaining,
            "at_limit": at_limit,
            "near_limit": near_limit,
            "percentage_used": round((usage / budget) * 100, 1)
        }
        
    except Exception as e:
        logger.error(f"Token budget check failed: {e}")
        return {"at_limit": False, "remaining": settings.monthly_token_budget}

async def cache_workflow_status(workflow_run_id: str, status: dict):
    try:
        redis = await get_redis_client()
        import json
        await redis.setex(
            f"workflow_status:{workflow_run_id}",
            3600,  # 1 hour TTL
            json.dumps(status)
        )
    except Exception as e:
        logger.error(f"Failed to cache workflow status: {e}")

async def get_workflow_status(workflow_run_id: str) -> dict:
    try:
        redis = await get_redis_client()
        import json
        data = await redis.get(f"workflow_status:{workflow_run_id}")
        return json.loads(data) if data else {}
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return {}