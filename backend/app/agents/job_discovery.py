import httpx
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState
from app.core.config import settings
from app.utils.circuit_breaker import CircuitBreaker

circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

NON_TECH_BLOCKLIST = [
    "electrical engineer", "mechanical engineer", "civil engineer",
    "hardware engineer", "network engineer", "security engineer",
    "business analyst", "business manager", "business development",
    "sales", "account executive", "account manager",
    "office assistant", "office manager", "administrative",
    "receptionist", "secretary", "clerk",
    "recruiter", "talent acquisition", "hr ", "human resources",
    "people operations",
    "marketing", "copywriter", "content writer", "social media",
    "customer support", "customer success", "customer service",
    "support specialist", "help desk",
    "pharmacist", "pharmacy", "nurse", "medical", "healthcare",
    "attorney", "lawyer", "paralegal", "legal ",
    "financial analyst", "accountant", "bookkeeper", "cfo",
    "graphic designer", "ui designer", "ux designer",
    "data labeling", "data annotation", "ai rater", "internet rater",
    "quality rater", "search evaluator",
    "red team", "penetration tester", "threat intelligence",
    "crypto market", "forex trader",
    "virtual assistant", "data entry",
    "fleet management", "edge systems",
]

TECH_TITLE_KEYWORDS = [
    "python", "backend", "back-end", "back end",
    "frontend", "front-end",
    "full stack", "fullstack", "full-stack",
    "software developer", "software engineer",
    "web developer", "web engineer",
    "data scientist", "data engineer", "data analyst",
    "ml engineer", "ai engineer", "machine learning",
    "llm", "langchain", "prompt engineer",
    "cloud engineer", "platform engineer",
    "devops engineer", "site reliability",
    "automation engineer", "qa engineer",
    "api developer", "integration developer",
    "mobile developer", "android developer", "ios developer",
    "node.js", "react developer", "django", "fastapi",
    " ai ", "artificial intelligence",
]

MANAGEMENT_BLOCKLIST = [
    "engineering manager", "team lead", "head of", "vp ",
    "vice president", "director", "cto", "chief",
]

SOFT_SENIOR = ["senior", "sr.", "lead", "principal", "staff", "architect"]

JUNIOR_KEYWORDS = [
    "junior", "entry level", "entry-level", "graduate",
    "new grad", "associate", "intern", "trainee",
    "0-2 years", "1-2 years", "no experience"
]

AI_KEYWORDS = [
    "llm", "langchain", "openai", "gpt", "ai engineer",
    "prompt engineer", "machine learning", "deep learning"
]

ADZUNA_TERMS = [
    "junior python developer",
    "junior backend developer",
    "junior AI engineer",
    "machine learning engineer",
    "junior software engineer remote",
]

REMOTIVE_CATEGORIES = ["software-dev", "dev-ops", "data"]

REMOTIVE_TERMS = [
    "python developer",
    "AI engineer",
    "machine learning",
    "backend developer",
    "LLM developer",
]

ARBEITNOW_TERMS = [
    "python developer",
    "AI engineer",
    "machine learning engineer",
    "backend developer",
    "LLM engineer",
]

LOCATION_BLOCK = [
    "must be based in", "must reside in", "must live in",
    "relocation required", "must relocate",
    "no remote", "not remote",
    "visa sponsorship not available", "no visa",
    "authorized to work in", "right to work in",
]


class JobDiscoveryAgent(BaseAgent):
    def __init__(self):
        super().__init__("job_discovery")

    async def execute(self, state: WorkflowState) -> dict:
        all_jobs = []

        adzuna_jobs = await self._fetch_adzuna()
        all_jobs.extend(adzuna_jobs)
        self.logger.info(f"After Adzuna: {len(all_jobs)} total")

        remotive_jobs = await self._fetch_remotive()
        all_jobs.extend(remotive_jobs)
        self.logger.info(f"After Remotive: {len(all_jobs)} total")

        remoteok_jobs = await self._fetch_remoteok()
        all_jobs.extend(remoteok_jobs)
        self.logger.info(f"After RemoteOK: {len(all_jobs)} total")

        arbeitnow_jobs = await self._fetch_arbeitnow()
        all_jobs.extend(arbeitnow_jobs)
        self.logger.info(f"After Arbeitnow: {len(all_jobs)} total")

        step1 = self._filter_non_tech(all_jobs)
        self.logger.info(f"After non-tech filter: {len(step1)}")

        step2 = self._filter_management(step1)
        self.logger.info(f"After management filter: {len(step2)}")

        step3 = self._filter_remote_only(step2)
        self.logger.info(f"After remote filter: {len(step3)}")

        unique = self._deduplicate(step3)
        self.logger.info(f"After dedup: {len(unique)}")

        ranked = self._rank(unique)
        self.logger.info(f"Final: {len(ranked)} jobs returning to user")

        return {
            "discovered_jobs": ranked[:30],
            "current_agent": "job_discovery",
            "hitl_pause_point": "job_approval"
        }

    def _filter_non_tech(self, jobs):
        result = []
        for job in jobs:
            title = job.get("title", "").lower()
            if any(bad in title for bad in NON_TECH_BLOCKLIST):
                self.logger.debug(f"Blocked non-tech: {job.get('title')}")
                continue
            if any(good in title for good in TECH_TITLE_KEYWORDS):
                result.append(job)
            else:
                self.logger.debug(f"No tech keyword: {job.get('title')}")
        return result

    def _filter_management(self, jobs):
        result = []
        for job in jobs:
            title = job.get("title", "").lower()
            if any(m in title for m in MANAGEMENT_BLOCKLIST):
                self.logger.debug(f"Blocked management: {job.get('title')}")
                continue
            result.append(job)
        return result

    def _filter_remote_only(self, jobs):
        result = []
        for job in jobs:
            if job.get("location_type") != "remote_international":
                continue
            desc = (job.get("description", "") or "").lower()
            loc = (job.get("location", "") or "").lower()
            if any(bad in desc + " " + loc for bad in LOCATION_BLOCK):
                continue
            result.append(job)
        return result

    def _deduplicate(self, jobs):
        seen = set()
        unique = []
        for job in jobs:
            key = f"{job.get('title','').lower()}|{job.get('company','').lower()}"
            if key not in seen:
                seen.add(key)
                unique.append(job)
        return unique

    def _rank(self, jobs):
        def score(job):
            s = 0
            text = (job.get("title", "") + " " + job.get("description", "")).lower()
            title = job.get("title", "").lower()
            for kw in JUNIOR_KEYWORDS:
                if kw in text:
                    s += 20
            for kw in AI_KEYWORDS:
                if kw in text:
                    s += 15
            if "python" in text:
                s += 10
            if "backend" in text or "back-end" in text:
                s += 10
            if job.get("salary_min"):
                s += 5
            if any(sk in title for sk in SOFT_SENIOR):
                s -= 30
            return s

        for job in jobs:
            job["relevance_score"] = score(job)
        return sorted(jobs, key=lambda x: x["relevance_score"], reverse=True)

    # ─── Adzuna ───────────────────────────────────────────────────────────────

    async def _fetch_adzuna(self):
        if not (settings.adzuna_app_id and settings.adzuna_api_key):
            self.logger.warning("Adzuna not configured")
            return []
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for country in ["us", "gb"]:
                for term in ADZUNA_TERMS[:3]:
                    try:
                        resp = await client.get(
                            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                            params={
                                "app_id": settings.adzuna_app_id,
                                "app_key": settings.adzuna_api_key,
                                "what": term,
                                "where": "remote",
                                "results_per_page": 10,
                            }
                        )
                        if resp.status_code == 200:
                            for j in resp.json().get("results", []):
                                desc = j.get("description", "").lower()
                                loc_type = "remote_international" if "remote" in desc else "fulltime_local"
                                jobs.append({
                                    "external_id": str(j.get("id", "")),
                                    "title": j.get("title", ""),
                                    "company": j.get("company", {}).get("display_name", ""),
                                    "location": j.get("location", {}).get("display_name", ""),
                                    "location_type": loc_type,
                                    "description": j.get("description", ""),
                                    "url": j.get("redirect_url", ""),
                                    "salary_min": j.get("salary_min"),
                                    "salary_max": j.get("salary_max"),
                                    "source": "adzuna",
                                    "required_skills": []
                                })
                    except Exception as e:
                        self.logger.error(f"Adzuna error [{country}][{term}]: {e}")
        self.logger.info(f"Adzuna returned {len(jobs)} raw jobs")
        return jobs

    # ─── Remotive ─────────────────────────────────────────────────────────────

    async def _fetch_remotive(self):
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for cat in REMOTIVE_CATEGORIES:
                try:
                    resp = await client.get(
                        "https://remotive.com/api/remote-jobs",
                        params={"category": cat, "limit": 20}
                    )
                    if resp.status_code == 200:
                        for j in resp.json().get("jobs", []):
                            jobs.append({
                                "external_id": str(j.get("id", "")),
                                "title": j.get("title", ""),
                                "company": j.get("company_name", ""),
                                "location": j.get("candidate_required_location", "Worldwide"),
                                "location_type": "remote_international",
                                "description": j.get("description", ""),
                                "url": j.get("url", ""),
                                "salary_min": None,
                                "salary_max": None,
                                "source": "remotive",
                                "required_skills": j.get("tags", [])
                            })
                except Exception as e:
                    self.logger.error(f"Remotive [{cat}] error: {e}")

            for term in REMOTIVE_TERMS:
                try:
                    resp = await client.get(
                        "https://remotive.com/api/remote-jobs",
                        params={"search": term, "limit": 10}
                    )
                    if resp.status_code == 200:
                        for j in resp.json().get("jobs", []):
                            jobs.append({
                                "external_id": str(j.get("id", "")),
                                "title": j.get("title", ""),
                                "company": j.get("company_name", ""),
                                "location": j.get("candidate_required_location", "Worldwide"),
                                "location_type": "remote_international",
                                "description": j.get("description", ""),
                                "url": j.get("url", ""),
                                "salary_min": None,
                                "salary_max": None,
                                "source": "remotive",
                                "required_skills": j.get("tags", [])
                            })
                except Exception as e:
                    self.logger.error(f"Remotive search [{term}] error: {e}")

        self.logger.info(f"Remotive returned {len(jobs)} raw jobs")
        return jobs

    # ─── RemoteOK ─────────────────────────────────────────────────────────────

    async def _fetch_remoteok(self):
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://remoteok.com/api",
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
                )
                if resp.status_code == 200:
                    for j in resp.json()[1:]:
                        if not isinstance(j, dict):
                            continue
                        title = j.get("position", "")
                        if not title:
                            continue
                        jobs.append({
                            "external_id": f"remoteok_{j.get('id', '')}",
                            "title": title,
                            "company": j.get("company", ""),
                            "location": "Remote (Worldwide)",
                            "location_type": "remote_international",
                            "description": (j.get("description", "") or "")[:2000],
                            "url": j.get("url", ""),
                            "salary_min": j.get("salary_min") or None,
                            "salary_max": j.get("salary_max") or None,
                            "source": "remoteok",
                            "required_skills": j.get("tags", [])
                        })
                        if len(jobs) >= 30:
                            break
        except Exception as e:
            self.logger.error(f"RemoteOK error: {e}")
        self.logger.info(f"RemoteOK returned {len(jobs)} raw jobs")
        return jobs

    # ─── Arbeitnow ────────────────────────────────────────────────────────────

    async def _fetch_arbeitnow(self):
        jobs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for term in ARBEITNOW_TERMS:
                try:
                    resp = await client.get(
                        "https://www.arbeitnow.com/api/job-board-api",
                        params={"search": term, "remote": "true", "page": 1, "language": "en"}
                    )
                    if resp.status_code == 200:
                        for j in resp.json().get("data", [])[:10]:
                            if not j.get("remote"):
                                continue
                            jobs.append({
                                "external_id": f"arbeitnow_{j.get('slug', '')}",
                                "title": j.get("title", ""),
                                "company": j.get("company_name", ""),
                                "location": j.get("location", "Remote"),
                                "location_type": "remote_international",
                                "description": (j.get("description", "") or "")[:2000],
                                "url": j.get("url", ""),
                                "salary_min": None,
                                "salary_max": None,
                                "source": "arbeitnow",
                                "required_skills": j.get("tags", [])
                            })
                except Exception as e:
                    self.logger.error(f"Arbeitnow [{term}] error: {e}")
        self.logger.info(f"Arbeitnow returned {len(jobs)} raw jobs")
        return jobs