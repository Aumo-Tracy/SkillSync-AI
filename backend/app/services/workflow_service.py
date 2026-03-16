import asyncio
import json
import uuid
from typing import AsyncGenerator
from app.agents.graph import workflow_graph
from app.agents.state import WorkflowState
from app.db.supabase_client import get_supabase_admin_client
from app.models import WorkflowStatus
from app.utils.token_tracker import (
    check_token_budget,
    cache_workflow_status,
    get_workflow_status
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def create_workflow_run(user_id: str, input_data: dict) -> str:
    supabase = get_supabase_admin_client()
    
    result = supabase.table("workflow_runs").insert({
        "user_id": user_id,
        "status": "pending",
        "input_data": input_data
    }).execute()
    
    return result.data[0]["id"]

async def update_workflow_run(workflow_run_id: str, updates: dict):
    try:
        supabase = get_supabase_admin_client()
        supabase.table("workflow_runs")\
            .update(updates)\
            .eq("id", workflow_run_id)\
            .execute()
    except Exception as e:
        logger.error(f"Failed to update workflow run: {e}")

async def stream_workflow(
    user_id: str,
    workflow_run_id: str,
    initial_state: dict
) -> AsyncGenerator[str, None]:
    
    def make_event(event_type: str, message: str, data: dict = None) -> str:
        payload = {
            "event_type": event_type,
            "message": message,
            "workflow_run_id": workflow_run_id,
            "data": data or {}
        }
        return f"data: {json.dumps(payload)}\n\n"
    
    try:
        # Check token budget before starting
        budget = await check_token_budget(user_id)
        if budget["at_limit"]:
            yield make_event(
                "pipeline_error",
                "Monthly token budget exceeded. Please wait until next month.",
            )
            return
        
        if budget["near_limit"]:
            yield make_event(
                "agent_started",
                f"Warning: {budget['percentage_used']}% of monthly token budget used.",
            )
        
        # Update workflow status to running
        await update_workflow_run(workflow_run_id, {
            "status": WorkflowStatus.running,
            "current_agent": "job_discovery"
        })
        
        yield make_event(
            "agent_started",
            "Job discovery started — searching remote and local opportunities...",
            {"agent": "job_discovery"}
        )
        
        # LangGraph thread config for state persistence
        config = {"configurable": {"thread_id": workflow_run_id}}
        
        # Run graph until first interrupt (HITL job approval)
        async for event in workflow_graph.astream(
            initial_state,
            config=config
        ):
            node_name = list(event.keys())[0] if event else None
            
            if not node_name or node_name == "__end__":
                continue
            
            node_output = event.get(node_name, {})
            
            # Handle errors
            if node_output.get("error"):
                yield make_event(
                    "pipeline_error",
                    f"Error in {node_name}: {node_output['error']}"
                )
                await update_workflow_run(workflow_run_id, {
                    "status": WorkflowStatus.failed,
                    "error_message": node_output["error"]
                })
                return
            
            # Emit progress event for each completed node
            if node_name == "job_discovery":
                jobs = node_output.get("discovered_jobs", [])
                yield make_event(
                    "agent_completed",
                    f"Found {len(jobs)} job listings — review and approve to continue.",
                    {
                        "agent": "job_discovery",
                        "jobs": jobs,
                        "count": len(jobs)
                    }
                )
                
                # Pause for HITL
                await update_workflow_run(workflow_run_id, {
                    "status": WorkflowStatus.awaiting_hitl,
                    "current_agent": "hitl_job_approval"
                })
                
                yield make_event(
                    "hitl_required",
                    "Please review and approve jobs to proceed.",
                    {
                        "pause_point": "job_approval",
                        "jobs": jobs
                    }
                )
                
                # Cache status so frontend can poll if SSE disconnects
                await cache_workflow_status(workflow_run_id, {
                    "status": "awaiting_hitl",
                    "pause_point": "job_approval",
                    "jobs": jobs
                })
                
                return  # Stream ends here — resumes after user approval
            
            elif node_name == "resume_analysis":
                analyses = node_output.get("resume_analyses", [])
                yield make_event(
                    "agent_completed",
                    f"Resume analyzed against {len(analyses)} jobs.",
                    {"agent": "resume_analysis", "analyses": analyses}
                )
            
            elif node_name == "resume_tailoring":
                resumes = node_output.get("tailored_resumes", [])
                yield make_event(
                    "agent_completed",
                    f"Tailored {len(resumes)} resume versions.",
                    {"agent": "resume_tailoring", "resumes": resumes}
                )
            
            elif node_name == "company_research":
                research = node_output.get("company_research", [])
                yield make_event(
                    "agent_completed",
                    f"Researched {len(research)} companies.",
                    {"agent": "company_research", "research": research}
                )
            
            elif node_name == "memory_agent":
                yield make_event(
                    "agent_completed",
                    "Results saved to your profile.",
                    {"agent": "memory_agent"}
                )
        
        # Pipeline complete
        await update_workflow_run(workflow_run_id, {
            "status": WorkflowStatus.completed,
            "current_agent": None
        })
        
        yield make_event(
            "pipeline_complete",
            "Workflow complete — your tailored resumes are ready.",
        )
        
    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled | workflow={workflow_run_id}")
    except Exception as e:
        logger.error(f"Stream error | workflow={workflow_run_id} | {e}")
        yield make_event("pipeline_error", f"Unexpected error: {str(e)}")
        await update_workflow_run(workflow_run_id, {
            "status": WorkflowStatus.failed,
            "error_message": str(e)
        })

async def resume_workflow_after_approval(
    workflow_run_id: str,
    user_id: str,
    approved_job_ids: list[str]
) -> AsyncGenerator[str, None]:
    
    def make_event(event_type: str, message: str, data: dict = None) -> str:
        payload = {
            "event_type": event_type,
            "message": message,
            "workflow_run_id": workflow_run_id,
            "data": data or {}
        }
        return f"data: {json.dumps(payload)}\n\n"
    
    try:
        config = {"configurable": {"thread_id": workflow_run_id}}
        
        # Get current graph state and inject approved jobs
        current_state = workflow_graph.get_state(config)
        
        # Find approved jobs from the discovered list
        discovered = current_state.values.get("discovered_jobs", [])

        # Manual jobs are always auto-approved
        manual_jobs = [j for j in discovered if j.get("source") == "manual"]

        # User-selected jobs from discovered list
        selected_jobs = [
            j for j in discovered
            if j.get("external_id") in approved_job_ids
            and j.get("source") != "manual"
     ]

        approved_jobs = manual_jobs + selected_jobs
        # Update state with approved jobs
        workflow_graph.update_state(
            config,
            {"approved_jobs": approved_jobs}
        )
        
        await update_workflow_run(workflow_run_id, {
            "status": WorkflowStatus.running,
            "current_agent": "resume_analysis"
        })
        
        yield make_event(
            "agent_started",
            f"Resuming pipeline with {len(approved_jobs)} approved jobs...",
            {"agent": "resume_analysis"}
        )
        
        # Continue graph from where it paused
        async for event in workflow_graph.astream(None, config=config):
            node_name = list(event.keys())[0] if event else None
            
            if not node_name or node_name == "__end__":
                continue
            
            node_output = event.get(node_name, {})
            
            if node_output.get("error"):
                yield make_event(
                    "pipeline_error",
                    f"Error in {node_name}: {node_output['error']}"
                )
                return
            
            if node_name == "resume_analysis":
                analyses = node_output.get("resume_analyses", [])
                yield make_event(
                    "agent_completed",
                    f"Resume analyzed against {len(analyses)} roles.",
                    {"agent": "resume_analysis"}
                )
            
            elif node_name == "resume_tailoring":
                resumes = node_output.get("tailored_resumes", [])
                yield make_event(
                    "agent_completed",
                    f"Generated {len(resumes)} tailored resume versions.",
                    {"agent": "resume_tailoring", "resumes": resumes}
                )
            
            elif node_name == "company_research":
                research = node_output.get("company_research", [])
                yield make_event(
                    "agent_completed",
                    f"Researched {len(research)} companies.",
                    {"agent": "company_research"}
                )
            
            elif node_name == "memory_agent":
                yield make_event(
                    "agent_completed",
                    "All results saved successfully.",
                    {"agent": "memory_agent"}
                )
        
        await update_workflow_run(workflow_run_id, {
            "status": WorkflowStatus.completed
        })
        
        yield make_event(
            "pipeline_complete",
            "Your tailored resumes are ready to download.",
        )
        
    except Exception as e:
        logger.error(f"Resume workflow error: {e}")
        yield make_event("pipeline_error", str(e))