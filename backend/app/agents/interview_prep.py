import json
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.llm import call_llm
from app.core.config import settings


class InterviewPrepAgent(BaseAgent):
    def __init__(self):
        super().__init__("interview_prep")

    async def execute(self, state: WorkflowState) -> dict:
        base_resume = state.get("base_resume", {})
        tailored_resumes = state.get("tailored_resumes", [])
        resume_analyses = state.get("resume_analyses", [])
        approved_jobs = state.get("approved_jobs", [])
        user_profile = state.get("user_profile", {})
        provider = user_profile.get("preferred_llm") or settings.default_llm_provider

        if not tailored_resumes:
            return {"interview_prep": [], "current_agent": "interview_prep"}

        # Build a lookup of analyses by job_id
        analyses_by_job = {
            a.get("job_id"): a for a in resume_analyses
        }

        # Build a lookup of jobs by external_id
        jobs_by_id = {
            j.get("external_id"): j for j in approved_jobs
        }

        interview_preps = []

        for resume in tailored_resumes:
            job_id = resume.get("base_resume_id") or ""

            # Find matching job and analysis
            analysis = analyses_by_job.get(job_id, {})
            job = None
            for j in approved_jobs:
                if j.get("title") == resume.get("job_title"):
                    job = j
                    break

            if not job:
                continue

            prep = await self._generate_interview_prep(
                resume=base_resume,
                tailored_resume=resume,
                job=job,
                analysis=analysis,
                provider=provider
            )
            interview_preps.append(prep)
            self.logger.info(
                f"Interview prep generated | job={resume.get('job_title')} | "
                f"questions={len(prep.get('questions', []))}"
            )

        return {
            "interview_prep": interview_preps,
            "current_agent": "interview_prep"
        }

    async def _generate_interview_prep(
        self,
        resume: dict,
        tailored_resume: dict,
        job: dict,
        analysis: dict,
        provider: str
    ) -> dict:

        prompt = f"""
You are an expert technical interviewer and career coach.

Generate a comprehensive interview preparation guide for this candidate applying to this role.

CANDIDATE RESUME:
{resume.get('raw_text', '')}

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', 'the company')}
JOB DESCRIPTION:
{job.get('description', '')[:3000]}

CANDIDATE STRENGTHS: {analysis.get('strengths', [])}
CANDIDATE GAPS: {analysis.get('missing_skills', [])}

Generate ONLY a valid JSON object with this structure:
{{
    "job_title": "{job.get('title', '')}",
    "company": "{job.get('company', '')}",
    "questions": [
        {{
            "type": "technical|behavioral|situational|culture",
            "question": "<interview question>",
            "why_asked": "<why interviewers ask this>",
            "suggested_answer": "<personalized answer based on candidate's actual experience>",
            "key_points": ["<point to emphasize>", "<point to emphasize>"]
        }}
    ],
    "red_flags": [
        "<question or topic to watch out for and how to handle it>"
    ],
    "talking_points": [
        "<key strength or experience to proactively mention>"
    ],
    "questions_to_ask_interviewer": [
        "<smart question candidate should ask the interviewer>"
    ]
}}

Rules:
- Generate exactly 8 questions: 3 technical, 3 behavioral, 1 situational, 1 culture fit
- Suggested answers MUST be based on the candidate's ACTUAL experience in the resume
- Never fabricate experience — if they lack something, suggest honest framing
- Red flags should address the candidate's specific gaps
- Talking points should highlight their genuine strengths
- Questions to ask should show genuine interest in the role
- Return ONLY the JSON object, no other text
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
            result["job_title"] = job.get("title", "")
            result["company"] = job.get("company", "")
            return result
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse interview prep JSON")
            return {
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                "questions": [],
                "error": "Interview prep generation failed"
            }