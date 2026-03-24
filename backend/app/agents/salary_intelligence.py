import json
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.llm import call_llm
from app.core.config import settings


class SalaryIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__("salary_intelligence")

    async def execute(self, state: WorkflowState) -> dict:
        approved_jobs = state.get("approved_jobs", [])
        resume_analyses = state.get("resume_analyses", [])
        user_profile = state.get("user_profile", {})
        provider = user_profile.get("preferred_llm") or settings.default_llm_provider

        if not approved_jobs:
            return {"salary_intelligence": [], "current_agent": "salary_intelligence"}

        analyses_by_title = {a.get("job_title"): a for a in resume_analyses}
        salary_data = []

        for job in approved_jobs:
            analysis = analyses_by_title.get(job.get("title"), {})
            data = await self._research_salary(
                job=job,
                analysis=analysis,
                user_profile=user_profile,
                provider=provider
            )
            salary_data.append(data)
            self.logger.info(f"Salary research complete | job={job.get('title')} | target={data.get('recommended_ask')}")

        return {
            "salary_intelligence": salary_data,
            "current_agent": "salary_intelligence"
        }

    async def _research_salary(self, job: dict, analysis: dict, user_profile: dict, provider: str) -> dict:
        match_score = analysis.get("match_score", 50)
        matching_skills = analysis.get("matching_skills", [])
        missing_skills = analysis.get("missing_skills", [])

        prompt = f"""
You are a compensation specialist and career coach with deep knowledge of global remote tech salaries.

Research and provide salary intelligence for this role and candidate.

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', 'Unknown')}
JOB DESCRIPTION EXCERPT: {job.get('description', '')[:1500]}

CANDIDATE PROFILE:
- Match score: {match_score}%
- Matching skills: {matching_skills}
- Missing skills: {missing_skills}
- Location: Remote (candidate based in Africa/Uganda)

Provide salary intelligence as a JSON object:
{{
    "job_title": "{job.get('title', '')}",
    "company": "{job.get('company', '')}",
    "market_range": {{
        "low": <integer USD annual>,
        "median": <integer USD annual>,
        "high": <integer USD annual>,
        "currency": "USD",
        "basis": "annual"
    }},
    "recommended_ask": <integer — personalized target based on match score and skills>,
    "minimum_acceptable": <integer — walk away if below this>,
    "confidence": "high|medium|low",
    "data_sources": ["<source used e.g. Glassdoor, Levels.fyi, RemoteOK listings>"],
    "location_note": "<important note about remote pay equity for international candidates>",
    "negotiation_scripts": {{
        "initial_ask": "<script for when they ask expected salary>",
        "counter_offer": "<script when offer comes in low>",
        "fixed_budget": "<script when they say budget is fixed>",
        "justify_ask": "<script for why you deserve this rate>"
    }},
    "red_flags": [
        "<warning sign in this job posting or company to watch for>"
    ],
    "equity_note": "<advice on standing firm on international pay equity>"
}}

IMPORTANT RULES:
- Base salary ranges on real market data for remote roles (not local Uganda rates)
- Remote work is location-agnostic — candidate deserves same pay as anyone else doing this job
- recommended_ask should be at or above median if match score > 65%, at median if 50-65%, slightly below if < 50%
- minimum_acceptable should be 15-20% below recommended_ask
- Be honest about data confidence level
- negotiation scripts must be professional, assertive, and specific to this role
- Return ONLY the JSON object, no other text
"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            temperature=0.3,
            max_tokens=2000
        )

        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse salary intelligence JSON")
            return {
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "error": "Salary research failed"
            }