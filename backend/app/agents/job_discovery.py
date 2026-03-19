import httpx
import re
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.config import settings
from app.utils.circuit_breaker import CircuitBreaker

circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

SENIOR_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "head of",
    "director", "vp ", "vice president", "staff engineer",
    "engineering manager", "cto", "chief", "architect",
    "manager", "team lead"
]

JUNIOR_FRIENDLY_KEYWORDS = [
    "junior", "entry level", "entry-level", "graduate", "intern",
    "early career", "new grad", "bootcamp", "self-taught",
    "no experience required", "0-2 years", "1-2 years", "1+ year",
    "2+ years", "2 years", "associate"
]

INACCESSIBLE_LOCATION_KEYWORDS = [
    "must be based in", "must reside in", "must live in",
    "on-site only", "onsite only", "in-office only",
    "relocation required", "must relocate",
    "germany only", "austria only", "switzerland only",
    "eu only", "europe only", "european union only",
    "uk only", "united kingdom only",
    "us only", "usa only", "united states only",
    "canada only", "australia only",
    "no remote", "not remote",
    "visa sponsorship not", "no visa",
    "authorized to work in", "right to work in",
    "work permit required",
]

# Job titles/keywords that are clearly NOT software/AI roles
IRRELEVANT_TITLE_KEYWORDS = [
    "office assistant", "office manager", "executive assistant", "administrative",
    "receptionist", "secretary", "clerk",
    "recruiter", "recruiting", "talent acquisition", "hr ", "human resources",
    "people operations", "people partner", "engagement partner",
    "sales", "account executive", "account manager", "business development",
    "account representative", "sales representative", "sdr", "bdr",
    "marketing", "copywriter", "content writer", "content creator",
    "seo specialist", "social media", "community manager",
    "customer success", "customer support", "customer service",
    "support specialist", "support agent", "help desk", "helpdesk",
    "pharmacist", "pharmacy", "nurse", "medical", "healthcare",
    "clinical", "therapist", "dental", "physician",
    "legal", "attorney", "lawyer", "paralegal", "compliance officer",
    "finance", "accounting", "bookkeeper", "cfo", "controller",
    "financial analyst", "tax",
    "graphic design", "graphic designer", "ui designer", "ux designer",
    "visual designer", "motion designer",
    "data labeling", "data annotation", "ai trainer", "ai training",
    "ai rater", "internet rater", "search evaluator", "quality rater",
    "transcription", "translation", "freelance writer",
    "operations manager", "scrum master", "agile coach",
    "project coordinator", "program coordinator",
    "red team", "penetration tester", "threat intelligence",
    "offensive security", "malware analyst",
    "crypto trader", "crypto market", "forex", "trading specialist",
    "virtual assistant", "data entry", "research assistant",
]

# At least one of these must appear in title OR description for the job to pass
REQUIRED_TECH_TITLE_KEYWORDS = [
    "developer", "engineer", "programmer",
    "python", "backend", "back-end", "back end",
    "frontend", "front-end", "full stack", "fullstack", "full-stack",
    "software", "devops", "sre ",
    "data scientist", "data engineer", "ml engineer", "ai engineer",
    "machine learning", "llm", "langchain", "nlp engineer",
    "cloud engineer", "platform engineer", "infrastructure engineer",
    "automation engineer", "qa engineer", "test engineer",
    "api developer", "integration developer", "prompt engineer",
]

ADZUNA_SEARCH_TERMS = [
    "junior python developer",
    "junior backend developer",
    "junior developer remote",
    "python developer entry level",
]

REMOTIVE_SEARCH_TERMS = [
    "junior python",
    "junior developer",
    "junior backend",
    "entry level developer",
    "python developer",
]

# Remotive category slugs for software engineering only
REMOTIVE_CATEGORIES = [
    "software-dev",
    "dev-ops",
    "data",
]

ARBEITNOW_SEARCH_TERMS = [
    "AI engineer",
    "LLM developer",
    "python developer",
    "backend developer",
    "AI automation",
]


class JobDiscoveryAgent(BaseAgent):
    def __init__(self):
        super().__init__("job_discovery")

    async def execute(self, state: WorkflowState) -> dict:
        user_profile = state.get("user_profile", {})
        profile_roles = user_profile.get("target_roles", [])

        if profile_roles:
            adzuna_terms = [f"junior {r}" for r in profile_roles[:3]] + ADZUNA_SEARCH_TERMS[:2]
        else:
            adzuna_terms = ADZUNA_SEARCH_TERMS

        all_jobs = []

        adzuna_jobs = await self._fetch_adzuna(adzuna_terms)
        all_jobs.extend(adzuna_jobs)

        remotive_jobs = await self._fetch_remotive(REMOTIVE_SEARCH_TERMS)
        all_jobs.extend(remotive_jobs)

        remoteok_jobs = await self._fetch_remoteok()
        all_jobs.extend(remoteok_jobs)

        arbeitnow_jobs = await self._fetch_arbeitnow(ARBEITNOW_SEARCH_TERMS)
        all_jobs.extend(arbeitnow_jobs)

        # Filter pipeline
        filtered_jobs = self._filter_by_seniority(all_jobs)
        filtered_jobs = self._filter_by_relevance(filtered_jobs, profile_roles)
        filtered_jobs = self._filter_by_accessibility(filtered_jobs)

        # Deduplicate
        seen_urls = set()
        seen_titles_companies = set()
        unique_jobs = []
        for job in filtered_jobs:
            url = job.get("url", "")
            title_company = f"{job.get('title', '').lower().strip()}|{job.get('company', '').lower().strip()}"
            if url and url not in seen_urls and title_company not in seen_titles_companies:
                seen_urls.add(url)
                seen_titles_companies.add(title_company)
                unique_jobs.append(job)

        ranked_jobs = self._rank_jobs(unique_jobs)

        self.logger.info(
            f"Job discovery complete | "
            f"total={len(all_jobs)} | after_filter={len(filtered_jobs)} | "
            f"unique={len(unique_jobs)} unique jobs"
        )

        return {
            "discovered_jobs": ranked_jobs,
            "current_agent": "job_discovery",
            "hitl_pause_point": "job_approval"
        }

    def _filter_by_seniority(self, jobs: list[dict]) -> list[dict]:
        filtered = []
        for job in jobs:
            title = job.get("title", "").lower()
            is_senior = any(kw in title for kw in SENIOR_TITLE_KEYWORDS)
            if not is_senior:
                filtered.append(job)
            else:
                self.logger.debug(f"Filtered senior role: {job.get('title')}")
        return filtered

    def _filter_by_relevance(self, jobs: list[dict], profile_roles: list[str]) -> list[dict]:
        extra_title_keywords = [r.lower() for r in profile_roles] if profile_roles else []
        all_required = REQUIRED_TECH_TITLE_KEYWORDS + extra_title_keywords
        filtered = []
        for job in jobs:
            title = job.get("title", "").lower()
            is_irrelevant = any(kw in title for kw in IRRELEVANT_TITLE_KEYWORDS)
            if is_irrelevant:
                self.logger.debug(f"Relevance filter [irrelevant]: {job.get('title')}")
                continue
            has_tech_title = any(kw in title for kw in all_required)
            if not has_tech_title:
                self.logger.debug(f"Relevance filter [no tech keyword]: {job.get('title')}")
                continue
            filtered.append(job)
        self.logger.info(f"Relevance filter: {len(jobs)} -> {len(filtered)} jobs")
        return filtered

    def _filter_by_accessibility(self, jobs: list[dict]) -> list[dict]:
        filtered = []
        for job in jobs:
            location_type = job.get("location_type", "")

            if location_type != "remote_international":
                self.logger.debug(f"Filtered non-remote job: {job.get('title')} [{location_type}]")
                continue

            description = (job.get("description", "") or "").lower()
            location = (job.get("location", "") or "").lower()
            combined = description + " " + location

            is_restricted = any(kw in combined for kw in INACCESSIBLE_LOCATION_KEYWORDS)
            if is_restricted:
                self.logger.debug(f"Filtered location-restricted job: {job.get('title')} @ {job.get('company')}")
                continue

            filtered.append(job)

        self.logger.info(f"Accessibility filter: {len(jobs)} → {len(filtered)} jobs")
        return filtered

    def _score_job(self, job: dict) -> int:
        score = 0
        title = job.get("title", "").lower()
        description = (job.get("description", "") or "").lower()
        combined = title + " " + description

        for kw in JUNIOR_FRIENDLY_KEYWORDS:
            if kw in combined:
                score += 10

        score += 15  # all remaining jobs are remote_international

        if job.get("source") in ["remotive", "remoteok", "arbeitnow"]:
            score += 10

        if job.get("salary_min"):
            score += 5

        location = (job.get("location", "") or "").lower()
        if any(kw in location for kw in ["worldwide", "global", "anywhere", "international"]):
            score += 10

        # Boost AI/LLM specific roles
        if any(kw in combined for kw in ["llm", "langchain", "ai engineer", "prompt", "openai", "gpt"]):
            score += 15

        return score

    def _rank_jobs(self, jobs: list[dict]) -> list[dict]:
        for job in jobs:
            job["relevance_score"] = self._score_job(job)
        return sorted(jobs, key=lambda x: x.get("relevance_score", 0), reverse=True)

    # ─── Adzuna ───────────────────────────────────────────────────────────────

    async def _fetch_adzuna(self, search_terms: list[str]) -> list[dict]:
        if not settings.adzuna_app_id or not settings.adzuna_api_key:
            self.logger.warning("Adzuna credentials not configured, skipping")
            return []

        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for country in ["us", "gb"]:
                for term in search_terms[:3]:
                    try:
                        response = await client.get(
                            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                            params={
                                "app_id": settings.adzuna_app_id,
                                "app_key": settings.adzuna_api_key,
                                "what": term,
                                "where": "remote",
                                "content-type": "application/json",
                                "results_per_page": 10,
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            for job in data.get("results", []):
                                normalized = self._normalize_adzuna_job(job)
                                if normalized["location_type"] == "remote_international":
                                    jobs.append(normalized)
                        else:
                            self.logger.warning(f"Adzuna [{country}] returned {response.status_code} for term: {term}")
                    except Exception as e:
                        self.logger.error(f"Adzuna [{country}] fetch failed for term '{term}': {e}")
                        continue

        self.logger.info(f"Adzuna returned {len(jobs)} remote jobs")
        return jobs

    def _normalize_adzuna_job(self, job: dict) -> dict:
        description = job.get("description", "").lower()
        location_type = "fulltime_local"
        if "remote" in description:
            location_type = "remote_international"
        elif "hybrid" in description:
            location_type = "hybrid_local"

        return {
            "external_id": job.get("id"),
            "title": job.get("title", ""),
            "company": job.get("company", {}).get("display_name", ""),
            "location": job.get("location", {}).get("display_name", ""),
            "location_type": location_type,
            "description": job.get("description", ""),
            "url": job.get("redirect_url", ""),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "source": "adzuna",
            "required_skills": []
        }

    # ─── Remotive ─────────────────────────────────────────────────────────────

    async def _fetch_remotive(self, search_terms: list[str]) -> list[dict]:
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Fetch by category first — software-dev, devops, data only
            for category in REMOTIVE_CATEGORIES:
                try:
                    response = await client.get(
                        "https://remotive.com/api/remote-jobs",
                        params={"category": category, "limit": 15}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for job in data.get("jobs", []):
                            jobs.append(self._normalize_remotive_job(job))
                    else:
                        self.logger.warning(f"Remotive category [{category}] returned {response.status_code}")
                except Exception as e:
                    self.logger.error(f"Remotive category [{category}] failed: {e}")
                    continue

            # Also search by terms for more targeted results
            for term in search_terms[:3]:
                try:
                    response = await client.get(
                        "https://remotive.com/api/remote-jobs",
                        params={"search": term, "limit": 8}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for job in data.get("jobs", []):
                            jobs.append(self._normalize_remotive_job(job))
                except Exception as e:
                    self.logger.error(f"Remotive search [{term}] failed: {e}")
                    continue

        self.logger.info(f"Remotive returned {len(jobs)} raw jobs")
        return jobs

    def _normalize_remotive_job(self, job: dict) -> dict:
        return {
            "external_id": str(job.get("id")),
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("candidate_required_location", "Worldwide"),
            "location_type": "remote_international",
            "description": job.get("description", ""),
            "url": job.get("url", ""),
            "salary_min": None,
            "salary_max": None,
            "source": "remotive",
            "required_skills": job.get("tags", [])
        }

    # ─── RemoteOK ─────────────────────────────────────────────────────────────

    async def _fetch_remoteok(self) -> list[dict]:
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://remoteok.com/api",
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)",
                        "Accept": "application/json"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    for job in data[1:]:
                        if not isinstance(job, dict):
                            continue
                        normalized = self._normalize_remoteok_job(job)
                        if normalized:
                            jobs.append(normalized)
                        if len(jobs) >= 20:
                            break
                else:
                    self.logger.warning(f"RemoteOK returned {response.status_code}")
        except Exception as e:
            self.logger.error(f"RemoteOK fetch failed: {e}")

        self.logger.info(f"RemoteOK returned {len(jobs)} jobs")
        return jobs

    def _normalize_remoteok_job(self, job: dict) -> dict:
        title = job.get("position", "")
        if not title:
            return None
        return {
            "external_id": f"remoteok_{job.get('id', '')}",
            "title": title,
            "company": job.get("company", ""),
            "location": "Remote (Worldwide)",
            "location_type": "remote_international",
            "description": job.get("description", "")[:2000],
            "url": job.get("url", ""),
            "salary_min": job.get("salary_min") or None,
            "salary_max": job.get("salary_max") or None,
            "source": "remoteok",
            "required_skills": job.get("tags", [])
        }

    # ─── Arbeitnow ────────────────────────────────────────────────────────────

    async def _fetch_arbeitnow(self, roles: list[str]) -> list[dict]:
        jobs = []
        search_terms = roles[:3] if roles else ["python developer", "AI engineer", "backend developer"]

        async with httpx.AsyncClient(timeout=15.0) as client:
            for term in search_terms:
                try:
                    response = await client.get(
                        "https://www.arbeitnow.com/api/job-board-api",
                        params={
                            "search": term,
                            "remote": "true",
                            "page": 1,
                            "language": "en"
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for job in data.get("data", [])[:10]:
                            if job.get("remote"):
                                jobs.append(self._normalize_arbeitnow_job(job))
                    else:
                        self.logger.warning(f"Arbeitnow returned {response.status_code} for term: {term}")
                except Exception as e:
                    self.logger.error(f"Arbeitnow fetch failed for term '{term}': {e}")
                    continue

        self.logger.info(f"Arbeitnow returned {len(jobs)} remote jobs")
        return jobs

    def _normalize_arbeitnow_job(self, job: dict) -> dict:
        return {
            "external_id": f"arbeitnow_{job.get('slug', '')}",
            "title": job.get("title", ""),
            "company": job.get("company_name", ""),
            "location": job.get("location", "Remote"),
            "location_type": "remote_international" if job.get("remote") else "fulltime_local",
            "description": job.get("description", "")[:2000],
            "url": job.get("url", ""),
            "salary_min": None,
            "salary_max": None,
            "source": "arbeitnow",
            "required_skills": job.get("tags", [])
        }
