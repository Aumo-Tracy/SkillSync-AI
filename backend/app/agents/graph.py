from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.state import WorkflowState
from app.agents.job_discovery import JobDiscoveryAgent
from app.agents.resume_analysis import ResumeAnalysisAgent
from app.agents.resume_tailoring import ResumeTailoringAgent
from app.agents.company_research import CompanyResearchAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.interview_prep import InterviewPrepAgent
from app.agents.salary_intelligence import SalaryIntelligenceAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Instantiate agents once
job_discovery = JobDiscoveryAgent()
resume_analysis = ResumeAnalysisAgent()
resume_tailoring = ResumeTailoringAgent()
company_research = CompanyResearchAgent()
memory_agent = MemoryAgent()
interview_prep_agent = InterviewPrepAgent()
salary_agent = SalaryIntelligenceAgent()

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

async def run_interview_prep(state: WorkflowState) -> WorkflowState:
    return await interview_prep_agent.run(state)

async def run_salary_intelligence(state: WorkflowState) -> WorkflowState:
    return await salary_agent.run(state)

# HITL pause node
async def hitl_job_approval(state: WorkflowState) -> WorkflowState:
    logger.info(f"Pipeline paused for job approval | workflow={state['workflow_run_id']}")
    return {
        "hitl_pause_point": "job_approval",
        "current_agent": "hitl_job_approval"
    }

# Conditional edges
def should_pause_for_approval(state: WorkflowState) -> str:
    if state.get("error"):
        return "end"
    if state.get("hitl_pause_point") == "job_approval":
        return "hitl_approval"
    return "resume_analysis_node"

def after_approval(state: WorkflowState) -> str:
    approved = state.get("approved_jobs", [])
    if not approved:
        return "end"
    return "resume_analysis_node"

def create_workflow_graph():
    graph = StateGraph(WorkflowState)

    # Register all nodes
    # NOTE: node names must not match WorkflowState field names.
    # Conflicting state keys: company_research, interview_prep, salary_intelligence
    # All nodes suffixed with _node to avoid ALL potential conflicts.
    graph.add_node("job_discovery_node",       run_job_discovery)
    graph.add_node("hitl_job_approval_node",   hitl_job_approval)
    graph.add_node("resume_analysis_node",     run_resume_analysis)
    graph.add_node("resume_tailoring_node",    run_resume_tailoring)
    graph.add_node("interview_prep_node",      run_interview_prep)
    graph.add_node("salary_intelligence_node", run_salary_intelligence)
    graph.add_node("company_research_node",    run_company_research)
    graph.add_node("memory_agent_node",        run_memory_agent)

    # Entry point
    graph.set_entry_point("job_discovery_node")

    # Conditional edges
    graph.add_conditional_edges(
        "job_discovery_node",
        should_pause_for_approval,
        {
            "hitl_approval":      "hitl_job_approval_node",
            "resume_analysis_node": "resume_analysis_node",
            "end": END
        }
    )

    graph.add_conditional_edges(
        "hitl_job_approval_node",
        after_approval,
        {
            "resume_analysis_node": "resume_analysis_node",
            "end": END
        }
    )

    # Sequential edges
    graph.add_edge("resume_analysis_node",     "resume_tailoring_node")
    graph.add_edge("resume_tailoring_node",    "interview_prep_node")
    graph.add_edge("interview_prep_node",      "salary_intelligence_node")
    graph.add_edge("salary_intelligence_node", "company_research_node")
    graph.add_edge("company_research_node",    "memory_agent_node")
    graph.add_edge("memory_agent_node",        END)

    # Compile with memory checkpointer
    checkpointer = MemorySaver()
    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["hitl_job_approval_node"]
    )

    logger.info("Workflow graph compiled successfully")
    return compiled

# Singleton graph instance
workflow_graph = create_workflow_graph()