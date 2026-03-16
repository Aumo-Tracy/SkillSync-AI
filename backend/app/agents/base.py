import time
from abc import ABC, abstractmethod
from app.agents.state import WorkflowState
from app.db.supabase_client import get_supabase_admin_client
from app.utils.logger import get_logger

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"agent.{name}")
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> dict:
        """Each agent implements this — receives state, returns state updates"""
        pass
    
    async def run(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        self.logger.info(f"Agent started | workflow={state['workflow_run_id']}")
        
        try:
            # Execute the agent's core logic
            updates = await self.execute(state)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log execution to database
            await self._log_execution(
                workflow_run_id=state["workflow_run_id"],
                input_data={"current_state_keys": list(state.keys())},
                output_data=updates,
                tokens_used=updates.get("total_tokens_used", 0),
                duration_ms=duration_ms,
                status="success"
            )
            
            self.logger.info(
                f"Agent completed | "
                f"workflow={state['workflow_run_id']} | "
                f"duration={duration_ms}ms"
            )
            
            return updates
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(
                f"Agent failed | "
                f"workflow={state['workflow_run_id']} | "
                f"error={e}"
            )
            
            await self._log_execution(
                workflow_run_id=state["workflow_run_id"],
                input_data={},
                output_data={},
                tokens_used=0,
                duration_ms=duration_ms,
                status="failed",
                error_message=str(e)
            )
            
            return {"error": str(e), "current_agent": self.name}
    
    async def _log_execution(
        self,
        workflow_run_id: str,
        input_data: dict,
        output_data: dict,
        tokens_used: int,
        duration_ms: int,
        status: str,
        error_message: str = None
    ):
        try:
            supabase = get_supabase_admin_client()
            supabase.table("agent_logs").insert({
                "workflow_run_id": workflow_run_id,
                "agent_name": self.name,
                "input_data": input_data,
                "output_data": output_data,
                "tokens_used": tokens_used,
                "duration_ms": duration_ms,
                "status": status,
                "error_message": error_message
            }).execute()
        except Exception as e:
            self.logger.error(f"Failed to log execution: {e}")