# SkillSync AI — Multi-Agent Resume Tailoring System

An intelligent job search assistant that discovers remote opportunities, analyzes your resume against each role, and generates tailored resumes using a multi-agent AI pipeline with human-in-the-loop control.

---

## 🧠 System Architecture

```
User Upload Resume
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                   LangGraph Pipeline                     │
│                                                         │
│  job_discovery → [HITL: User Approves Jobs]             │
│       → resume_analysis → resume_tailoring              │
│       → company_research → memory_agent                 │
└─────────────────────────────────────────────────────────┘
        │
        ▼
  Tailored Resumes + Company Intel saved to Supabase
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| AI Orchestration | LangGraph (stateful multi-agent) |
| LLM Abstraction | LiteLLM (OpenAI / Gemini) |
| Frontend | Next.js 14 + TypeScript |
| Auth + Database | Supabase (PostgreSQL + Auth) |
| Vector Store | Qdrant Cloud |
| Cache / State | Upstash Redis |
| Job APIs | Adzuna, Remotive, RemoteOK, Arbeitnow |
| Web Search | Tavily |

---

## 🤖 Agent Pipeline

### 1. Job Discovery Agent
- Searches 4 remote job sources: Adzuna, Remotive, RemoteOK, Arbeitnow
- Filters out senior roles, onsite jobs, location-restricted postings (EU-only, US-only, etc.)
- Relevance filter ensures only software/AI/backend roles are returned
- Ranks jobs by relevance score (junior-friendly keywords, source quality, location)
- Supports manual job entry with URL auto-fetch via Tavily

### 2. Human-in-the-Loop (HITL)
- Pipeline pauses after job discovery via LangGraph interrupt
- User reviews and selects which jobs to proceed with
- Manually added jobs are auto-approved and always included
- Pipeline resumes with only approved jobs

### 3. Resume Analysis Agent
- Performs skill gap analysis for each approved job
- Validated match scoring — prevents LLM from hallucinating high scores on poor matches
- Score is cross-checked against missing/matching skill counts
- Returns: matching skills, missing skills, experience gaps, ATS keywords, recommended changes

### 4. Resume Tailoring Agent
- Rewrites resume for each job using analysis guidance
- Anti-fabrication rules: never invents job titles, companies, or experience
- Incorporates user tailoring instructions (e.g. "emphasize LangChain projects")
- Missing skills noted as "currently learning" rather than fabricated
- Returns structured JSON with summary, experience, skills, education, ATS keywords added

### 5. Company Research Agent
- Uses Tavily to gather company intelligence for each approved job
- Returns recent news, company culture, tech stack, interview tips

### 6. Memory Agent
- Persists all results to Supabase `workflow_runs` table
- Saves tailored resumes, analyses, company research to `applications` table
- Enables Applications page to show full history

---

## 🗂️ Project Structure

```
resume-agent/
├── backend/
│   ├── main.py                          # FastAPI entry point
│   ├── requirements.txt
│   ├── app/
│   │   ├── agents/
│   │   │   ├── state.py                 # LangGraph WorkflowState
│   │   │   ├── graph.py                 # LangGraph pipeline definition
│   │   │   ├── job_discovery.py         # 4-source job search + filtering
│   │   │   ├── resume_analysis.py       # Skill gap analysis + score validation
│   │   │   ├── resume_tailoring.py      # LLM resume rewriting
│   │   │   ├── company_research.py      # Tavily company intel
│   │   │   └── memory_agent.py          # Supabase persistence
│   │   ├── api/routes/
│   │   │   ├── auth.py                  # signup, signin, signout, me, update
│   │   │   ├── workflow.py              # start (SSE), approve (SSE), history, feedback
│   │   │   └── resume.py                # upload, list, base resume
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic settings
│   │   │   ├── llm.py                   # LiteLLM abstraction
│   │   │   └── security.py              # JWT auth
│   │   ├── db/
│   │   │   ├── supabase_client.py
│   │   │   ├── qdrant_client.py
│   │   │   └── redis_client.py
│   │   └── services/
│   │       └── workflow_service.py      # SSE streaming + LangGraph execution
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/login/               # Login page
│   │   ├── (auth)/signup/              # Signup page
│   │   └── (dashboard)/
│   │       ├── dashboard/              # Stats + quick actions
│   │       ├── workflow/               # Main pipeline UI
│   │       ├── applications/           # Saved tailored resumes
│   │       └── profile/                # User preferences + LLM selection
│   ├── components/
│   │   ├── ResumeEditor.tsx            # Edit + PDF download
│   │   └── FeedbackModal.tsx           # 3-dimension star rating
│   ├── hooks/useWorkflow.ts            # SSE streaming hook
│   ├── store/
│   │   ├── auth.ts                     # Zustand auth store
│   │   └── workflow.ts                 # Zustand workflow store (no persist)
│   └── lib/api.ts                      # Axios + fetch API client
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase project
- Qdrant Cloud cluster
- Upstash Redis instance
- OpenAI or Gemini API key
- Adzuna API credentials
- Tavily API key

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

Create `backend/.env`:
```env
APP_SECRET_KEY=your_64_char_hex_secret
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
QDRANT_HOST=your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_key
REDIS_URL=rediss://default:password@host.upstash.io:6379
ADZUNA_APP_ID=your_app_id
ADZUNA_API_KEY=your_api_key
TAVILY_API_KEY=your_tavily_key
```

Run the backend:
```bash
uvicorn main:app --reload --reload-dir app --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the frontend:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## 🗄️ Database Setup

Run these in your Supabase SQL editor:

```sql
-- Resume feedback table
create table if not exists resume_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  workflow_run_id text not null,
  job_title text not null,
  rating int check (rating between 1 and 5),
  resume_quality int check (resume_quality between 1 and 5),
  job_relevance int check (job_relevance between 1 and 5),
  comment text,
  created_at timestamptz default now()
);
alter table resume_feedback enable row level security;
create policy "Users manage own feedback" on resume_feedback for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
```

---

## ✨ Key Features

- **Multi-agent pipeline** — LangGraph orchestrates 5 specialized AI agents
- **Human-in-the-loop** — User reviews and approves jobs before resume tailoring
- **Anti-fabrication** — LLM never invents experience; missing skills noted as "currently learning"
- **Validated scoring** — Match scores cross-checked against actual skill data
- **Manual job entry** — Add jobs from LinkedIn/Wellfound with URL auto-fetch
- **Tailoring instructions** — Tell the AI exactly how to customize your resumes
- **Accessibility filter** — Removes onsite, EU-only, US-only jobs automatically
- **Feedback system** — Rate resume quality, job relevance, overall satisfaction
- **PDF export** — Edit and download tailored resumes as PDF
- **LLM flexibility** — Switch between OpenAI and Gemini per user preference

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/signin` | Sign in |
| GET | `/api/auth/me` | Current user |
| POST | `/api/resume/upload` | Upload resume |
| POST | `/api/workflow/start` | Start pipeline (SSE) |
| POST | `/api/workflow/{id}/approve` | Approve jobs (SSE) |
| GET | `/api/workflow/history` | Workflow history |
| POST | `/api/workflow/fetch-job` | Fetch job from URL |
| POST | `/api/workflow/feedback` | Submit resume feedback |

---

## 👤 Author

**Tracy Aumotrac**  
Turing College — AI Engineering Program  
[GitHub](https://github.com/Aumo-Tracy)