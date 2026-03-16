from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.db.supabase_client import get_supabase_admin_client
from app.db.redis_client import get_redis_client
import json

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("memory_agent")
    
    async def execute(self, state: WorkflowState) -> dict:
        user_id = state.get("user_id")
        workflow_run_id = state.get("workflow_run_id")
        
        await self._save_applications(state)
        await self._update_workflow_output(state)
        await self._update_token_usage(state)
        await self._cache_preferences(state)
        
        self.logger.info(
            f"Memory persisted | "
            f"user={user_id} | workflow={workflow_run_id}"
        )
        
        return {
            "current_agent": "memory_agent",
            "completed": True
        }
    
    async def _update_workflow_output(self, state: WorkflowState):
        """Save output data directly to workflow_runs table for frontend display"""
        try:
            supabase = get_supabase_admin_client()
            supabase.table("workflow_runs").update({
                "output_data": {
                    "tailored_resumes": state.get("tailored_resumes", []),
                    "company_research": state.get("company_research", []),
                    "approved_jobs": state.get("approved_jobs", []),
                    "resume_analyses": state.get("resume_analyses", [])
                },
                "status": "completed",
                "current_agent": None
            }).eq("id", state["workflow_run_id"]).execute()
        except Exception as e:
            self.logger.error(f"Failed to update workflow output: {e}")

    async def _save_applications(self, state: WorkflowState):
        supabase = get_supabase_admin_client()
        tailored_resumes = state.get("tailored_resumes", [])
        approved_jobs = state.get("approved_jobs", [])
        research_map = {
            r["job_id"]: r 
            for r in state.get("company_research", [])
            if "job_id" in r
        }
        
        for resume in tailored_resumes:
            job = next((
                j for j in approved_jobs 
                if j.get("title") == resume.get("job_title")
            ), {})
            
            try:
                supabase.table("applications").insert({
                    "user_id": state["user_id"],
                    "workflow_run_id": state["workflow_run_id"],
                    "status": "ready",
                    "skill_gap_analysis": resume,
                    "company_research": research_map.get(
                        job.get("external_id"), {}
                    )
                }).execute()
            except Exception as e:
                self.logger.error(f"Failed to save application: {e}")
    
    async def _update_token_usage(self, state: WorkflowState):
        supabase = get_supabase_admin_client()
        tokens = state.get("total_tokens_used", 0)
        
        if tokens > 0:
            try:
                supabase.rpc("increment_token_usage", {
                    "user_id": state["user_id"],
                    "tokens": tokens
                }).execute()
            except Exception as e:
                self.logger.error(f"Failed to update token usage: {e}")
    
    async def _cache_preferences(self, state: WorkflowState):
        try:
            redis = await get_redis_client()
            prefs_key = f"user_prefs:{state['user_id']}"
            prefs = {
                "preferred_llm": state.get(
                    "user_profile", {}
                ).get("preferred_llm", "openai"),
                "tone_preference": state.get(
                    "user_profile", {}
                ).get("tone_preference", "professional"),
            }
            await redis.setex(
                prefs_key,
                86400,
                json.dumps(prefs)
            )
        except Exception as e:
            self.logger.error(f"Failed to cache preferences: {e}")