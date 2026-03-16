from typing import Optional, Annotated
from uuid import UUID
import operator
from langgraph.graph import MessagesState

class WorkflowState(MessagesState):
    # Identity
    workflow_run_id: str
    user_id: str
    
    # User context
    user_profile: dict = {}
    base_resume: dict = {}
    search_params: dict = {}
    
    # Pipeline data — accumulates as agents complete
    discovered_jobs: Annotated[list[dict], operator.add] = []
    approved_jobs: list[dict] = []
    resume_analyses: Annotated[list[dict], operator.add] = []
    tailored_resumes: Annotated[list[dict], operator.add] = []
    company_research: Annotated[list[dict], operator.add] = []
    
    # Control flow
    current_agent: str = ""
    hitl_pause_point: Optional[str] = None
    user_feedback: Optional[str] = None
    error: Optional[str] = None
    completed: bool = False
    
    # Token tracking
    total_tokens_used: int = 0