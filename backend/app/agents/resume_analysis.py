import json
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.llm import call_llm
from app.core.config import settings


class ResumeAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("resume_analysis")

    async def execute(self, state: WorkflowState) -> dict:
        base_resume = state.get("base_resume", {})
        approved_jobs = state.get("approved_jobs", [])
        user_profile = state.get("user_profile", {})

        if not base_resume:
            return {"error": "No base resume found in state"}

        if not approved_jobs:
            return {"error": "No approved jobs to analyze against"}

        analyses = []

        for job in approved_jobs:
            analysis = await self._analyze_for_job(
                resume=base_resume,
                job=job,
                provider=user_profile.get("preferred_llm") or settings.default_llm_provider
            )
            analyses.append(analysis)
            self.logger.info(
                f"Analysis complete | job={job.get('title')} | "
                f"match_score={analysis.get('match_score')}"
            )

        return {
            "resume_analyses": analyses,
            "current_agent": "resume_analysis"
        }

    async def _analyze_for_job(
        self,
        resume: dict,
        job: dict,
        provider: str
    ) -> dict:

        prompt = f"""
You are a strict, honest resume analyst and ATS specialist.
Analyze this resume against the job description and return a JSON object only.

RESUME:
{resume.get('raw_text', '')}

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', '')}
JOB DESCRIPTION:
{job.get('description', '')[:4000]}

SCORING RULES — follow these strictly:
- Start at 50 (baseline for any relevant application)
- Add up to +30 for matching required skills (3 points per skill match, max 30)
- Add up to +10 for relevant experience level match
- Add up to +10 for matching tech stack or domain
- Subtract 5 for each critical missing skill (skills marked required/must have)
- Subtract 3 for each significant experience gap
- A candidate with 5+ missing required skills should NOT score above 60
- A candidate with no relevant experience should NOT score above 45
- Only score above 80 if the resume is a genuinely strong match
- Never return a score above 95 or below 10

Return ONLY a valid JSON object with this exact structure:
{{
    "job_id": "{job.get('external_id', '')}",
    "job_title": "{job.get('title', '')}",
    "match_score": <float 0-100, calculated strictly per the rules above>,
    "score_reasoning": "<1-2 sentences explaining why this score was given>",
    "matching_skills": [<skills present in BOTH resume and job description>],
    "missing_skills": [<skills required by job but NOT found in resume>],
    "experience_gaps": [<specific experience areas the candidate lacks>],
    "strengths": [<genuine strong matching points — be honest, not flattering>],
    "recommended_changes": [<specific actionable changes to improve this resume for this job>],
    "ats_keywords": [<important keywords from job description to include in resume>]
}}
"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            temperature=0.2,
            max_tokens=1500
        )

        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()

        try:
            result = json.loads(clean)
            result["match_score"] = self._validate_score(
                score=result.get("match_score", 0),
                missing_skills=result.get("missing_skills", []),
                matching_skills=result.get("matching_skills", [])
            )
            # Generate learning roadmap for missing skills
            if result.get("missing_skills") or result.get("experience_gaps"):
                roadmap = await self._generate_learning_roadmap(
                    missing_skills=result.get("missing_skills", []),
                    experience_gaps=result.get("experience_gaps", []),
                    job_title=result.get("job_title", ""),
                    provider=provider
                )
                result["learning_roadmap"] = roadmap
            return result
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse analysis JSON: {clean[:200]}")
            return {
                "job_id": job.get("external_id", ""),
                "job_title": job.get("title", ""),
                "match_score": 0,
                "error": "Analysis parsing failed",
                "raw_response": clean
            }

    def _validate_score(
        self,
        score: any,
        missing_skills: list,
        matching_skills: list
    ) -> float:
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 50.0

        score = max(10.0, min(95.0, score))

        missing_count = len(missing_skills)
        matching_count = len(matching_skills)

        if missing_count >= 8:
            score = min(score, 45.0)
        elif missing_count >= 5:
            score = min(score, 58.0)
        elif missing_count >= 3:
            score = min(score, 72.0)

        if matching_count == 0:
            score = min(score, 35.0)
        elif matching_count <= 2:
            score = min(score, 50.0)

        if matching_count >= 6 and missing_count <= 2:
            score = max(score, 72.0)

        return round(score, 1)

    async def _generate_learning_roadmap(
        self,
        missing_skills: list,
        experience_gaps: list,
        job_title: str,
        provider: str
    ) -> list:
        if not missing_skills and not experience_gaps:
            return []

        prompt = f"""
You are a career development coach specializing in tech roles.

A candidate is missing these skills for a {job_title} role:
Missing skills: {missing_skills}
Experience gaps: {experience_gaps}

Generate a practical learning roadmap. Return a JSON array:
[
    {{
        "skill": "<skill name>",
        "priority": "high|medium|low",
        "estimated_time": "<e.g. 2 weeks, 1 month>",
        "resources": [
            {{
                "type": "course|project|documentation|practice",
                "title": "<resource name>",
                "url": "<url if known, else null>",
                "description": "<one line on what to do>"
            }}
        ],
        "quick_win": "<one specific thing they can do THIS WEEK to start>"
    }}
]

Rules:
- Max 5 skills in the roadmap, prioritize the most critical ones
- Resources must be real and free or cheap (freeCodeCamp, fast.ai, official docs, GitHub)
- quick_win must be actionable in 1-3 days
- Return ONLY the JSON array, no other text
"""

        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            temperature=0.3,
            max_tokens=1500
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
            self.logger.error("Failed to parse learning roadmap JSON")
            return []