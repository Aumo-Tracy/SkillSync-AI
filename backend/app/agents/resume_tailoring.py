import json
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.llm import call_llm
from app.core.config import settings
class ResumeTailoringAgent(BaseAgent):
    def __init__(self):
        super().__init__("resume_tailoring")
    
    async def execute(self, state: WorkflowState) -> dict:
        base_resume = state.get("base_resume", {})
        analyses = state.get("resume_analyses", [])
        user_profile = state.get("user_profile", {})
        user_feedback = state.get("user_feedback")
        
        if not analyses:
            return {"error": "No resume analyses found"}
        
        tailored_resumes = []
        
        for analysis in analyses:
            tailored = await self._tailor_resume(
                resume=base_resume,
                analysis=analysis,
                tone=user_profile.get("tone_preference", "professional"),
                feedback=user_feedback,
                provider=user_profile.get("preferred_llm") or settings.default_llm_provider
            )
            tailored_resumes.append(tailored)
            self.logger.info(
                f"Resume tailored | job={analysis.get('job_title')} | "
                f"keywords_added={len(tailored.get('ats_keywords_added', []))}"
            )
        
        return {
            "tailored_resumes": tailored_resumes,
            "current_agent": "resume_tailoring"
        }
    
    async def _tailor_resume(
        self,
        resume: dict,
        analysis: dict,
        tone: str,
        feedback: str,
        provider: str
    ) -> dict:
        
        feedback_section = f"\nUSER FEEDBACK TO INCORPORATE:\n{feedback}" if feedback else ""
        
        prompt = f"""
You are an expert resume writer specializing in AI engineering and tech roles.

Rewrite this resume tailored specifically for the job described below.
Tone: {tone}
{feedback_section}

ORIGINAL RESUME:
{resume.get('raw_text', '')}

JOB TITLE: {analysis.get('job_title', '')}

ANALYSIS GUIDANCE:
- Add these missing skills where truthfully applicable: {analysis.get('missing_skills', [])}
- Emphasize these strengths: {analysis.get('strengths', [])}
- Include these ATS keywords naturally: {analysis.get('ats_keywords', [])}
- Address these gaps: {analysis.get('experience_gaps', [])}
CRITICAL RULES:
- NEVER invent job titles, companies, or employment history that don't exist in the original resume
- ONLY reframe and strengthen what is already there
- Projects can be elevated but must be based on real work described in the resume
- If a skill is missing, note it as "currently learning" rather than claiming experience
- Apply these specific changes: {analysis.get('recommended_changes', [])}

Return ONLY a valid JSON object with this structure:
{{
    "job_title": "{analysis.get('job_title', '')}",
    "summary": "<rewritten professional summary>",
    "experience": [
        {{
            "title": "<job title>",
            "company": "<company>",
            "duration": "<dates>",
            "bullets": ["<achievement bullet>", ...]
        }}
    ],
    "skills": {{
        "technical": ["<skill>", ...],
        "tools": ["<tool>", ...],
        "soft": ["<skill>", ...]
    }},
    "education": [
        {{
            "degree": "<degree>",
            "institution": "<school>",
            "year": "<year>"
        }}
    ],
    "certifications": ["<cert>", ...],
    "ats_keywords_added": ["<keyword>", ...],
    "changes_summary": ["<description of change made>", ...]
}}
"""
        
        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            temperature=0.4,
            max_tokens=3000
        )
        
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip()
        
        try:
            result = json.loads(clean)
            result["base_resume_id"] = resume.get("id")
            result["match_score"] = analysis.get("match_score", 0)
            return result
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse tailored resume JSON")
            return {
                "job_title": analysis.get("job_title", ""),
                "error": "Tailoring parsing failed",
                "raw_response": clean
            }