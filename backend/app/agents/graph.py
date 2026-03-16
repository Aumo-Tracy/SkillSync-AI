from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import WorkflowState
from app.agents.job_discovery import JobDiscoveryAgent
from app.agents.resume_analysis import ResumeAnalysisAgent
from app.agents.resume_tailoring import ResumeTailoringAgent
from app.agents.company_research import CompanyResearchAgent
from app.agents.memory_agent import MemoryAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instantiate agents once
job_discovery = JobDiscoveryAgent()
resume_analysis = ResumeAnalysisAgent()
resume_tailoring = ResumeTailoringAgent()
company_research = CompanyResearchAgent()
memory_agent = MemoryAgent()

# Node wrapper functions
async def run_job_discovery(state: WorkflowState) -> WorkflowState:
    return await job_discovery.run(state)

async def run_resume_analysis(state: WorkflowState) -> WorkflowState:
    return await resume_analysis.run(state)

async def run_resume_tailoring(state: WorkflowState) -> WorkflowState:
    return await resume_tailoring.run(state)

async def run_company_research(state: WorkflowState) -> WorkflowState:
    return await company_research.run(state)

async def run_memory_agent(state: WorkflowState) -> WorkflowState:
    return await memory_agent.run(state)

# HITL pause node — graph stops here and waits for user input
async def hitl_job_approval(state: WorkflowState) -> WorkflowState:
    logger.info(
        f"Pipeline paused for job approval | "
        f"workflow={state['workflow_run_id']}"
    )
    return {
        "hitl_pause_point": "job_approval",
        "current_agent": "hitl_job_approval"
    }

# Conditional edge — determines what runs after job discovery
def should_pause_for_approval(state: WorkflowState) -> str:
    if state.get("error"):
        return "end"
    if state.get("hitl_pause_point") == "job_approval":
        return "hitl_approval"
    return "resume_analysis"

# Conditional edge — determines what runs after HITL
def after_approval(state: WorkflowState) -> str:
    approved = state.get("approved_jobs", [])
    if not approved:
        return "end"
    return "resume_analysis"

# Conditional edge — check for errors throughout
def check_error(state: WorkflowState) -> str:
    if state.get("error"):
        return "end"
    if state.get("completed"):
        return "end"
    return "continue"

def create_workflow_graph():
    graph = StateGraph(WorkflowState)
    
    # Register all nodes
    graph.add_node("job_discovery", run_job_discovery)
    graph.add_node("hitl_job_approval", hitl_job_approval)
    graph.add_node("resume_analysis", run_resume_analysis)
    graph.add_node("resume_tailoring", run_resume_tailoring)
    graph.add_node("company_research", run_company_research)
    graph.add_node("memory_agent", run_memory_agent)
    
    # Entry point
    graph.set_entry_point("job_discovery")
    
    # Edges
    graph.add_conditional_edges(
        "job_discovery",
        should_pause_for_approval,
        {
            "hitl_approval": "hitl_job_approval",
            "resume_analysis": "resume_analysis",
            "end": END
        }
    )
    
    graph.add_conditional_edges(
        "hitl_job_approval",
        after_approval,
        {
            "resume_analysis": "resume_analysis",
            "end": END
        }
    )
    
    # After analysis, run tailoring and research in sequence
    graph.add_edge("resume_analysis", "resume_tailoring")
    graph.add_edge("resume_tailoring", "company_research")
    graph.add_edge("company_research", "memory_agent")
    graph.add_edge("memory_agent", END)
    
    # Compile with memory checkpointer for state persistence
    checkpointer = MemorySaver()
    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_job_approval"]
    )
    
    logger.info("Workflow graph compiled successfully")
    return compiled

# Singleton graph instance
workflow_graph = create_workflow_graph()