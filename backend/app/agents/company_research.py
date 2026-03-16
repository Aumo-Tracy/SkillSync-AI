import httpx
import json
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.config import settings
from app.core.llm import call_llm

class CompanyResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("company_research")

    async def execute(self, state: WorkflowState) -> dict:
        approved_jobs = state.get("approved_jobs", [])
        user_profile = state.get("user_profile", {})
        provider = user_profile.get("preferred_llm", "gemini")

        research_results = []

        for job in approved_jobs:
            company = job.get("company", "")
            if not company:
                continue

            research = await self._research_company(
                company=company,
                job_title=job.get("title", ""),
                job_id=job.get("external_id", ""),
                provider=provider
            )
            research_results.append(research)
            self.logger.info(f"Research complete | company={company}")

        return {
            "company_research": research_results,
            "current_agent": "company_research"
        }

    async def _research_company(
        self,
        company: str,
        job_title: str,
        job_id: str,
        provider: str = "gemini"
    ) -> dict:

        raw_research = await self._tavily_search(company, job_title)

        if not raw_research:
            return {
                "job_id": job_id,
                "company": company,
                "status": "research_unavailable",
                "summary": "Company research could not be completed at this time."
            }

        summary = await self._summarize_research(
            company=company,
            job_title=job_title,
            raw_content=raw_research,
            provider=provider
        )

        return {
            "job_id": job_id,
            "company": company,
            "status": "completed",
            **summary
        }

    async def _tavily_search(self, company: str, job_title: str) -> str:
        if not settings.tavily_api_key:
            self.logger.warning("Tavily API key not configured")
            return ""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.tavily_api_key,
                        "query": f"{company} company culture tech stack remote work engineering hiring",
                        "search_depth": "basic",
                        "max_results": 5
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    return "\n\n".join([r.get("content", "") for r in results])

        except Exception as e:
            self.logger.error(f"Tavily search failed: {e}")

        return ""

    async def _summarize_research(
        self,
        company: str,
        job_title: str,
        raw_content: str,
        provider: str = "gemini"
    ) -> dict:

        prompt = f"""
You are helping a junior developer from Uganda who is applying for remote work.
Summarize this research about {company} for someone applying for a {job_title} position.

Focus on:
- Whether they hire internationally/remotely
- What the company actually does
- Their tech stack
- Culture and what it's like to work there
- Any red flags or green flags for a junior developer

RESEARCH CONTENT:
{raw_content[:4000]}

Return ONLY a valid JSON object:
{{
    "overview": "<2-3 sentence company overview>",
    "tech_stack": ["<technology>", ...],
    "culture_notes": "<brief culture and work environment notes>",
    "remote_policy": "<remote/hybrid/onsite policy and whether they hire internationally>",
    "junior_friendliness": "<assessment of how junior-friendly this company appears>",
    "interview_tips": "<any relevant interview or application tips>",
    "red_flags": "<any concerns worth noting, or null>"
}}
"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            temperature=0.3,
            max_tokens=800
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
            return {"overview": raw_content[:500], "error": "Summary parsing failed"}