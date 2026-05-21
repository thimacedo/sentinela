# Sentinela — Technology Stack

## Backend (Python)

### Runtime
- Python 3.12+ (`.python-version` at root)
- `asyncio` for all async I/O (workers, scrapers, AI calls)
- `from __future__ import annotations` used throughout for forward references

### Core Dependencies (`requirements.txt`)
```
scrapy>=2.11.0
twisted>=23.10.0
scrapy-playwright>=0.0.34
playwright>=1.40.0
zyte-api>=0.5.0
fastapi>=0.109.0
uvicorn>=0.27.0
python-dotenv>=1.0.0
itemadapter>=0.8.0
python-dateutil>=2.8.2
```

### Additional Backend Deps (inferred from code)
- `supabase` — Python Supabase client
- `openai` — AsyncOpenAI client (used for Groq, Mistral, OpenRouter via compatible API)
- `pydantic` — Data validation (schemas.py)
- `reportlab` or similar — PDF dossier generation

### AI Providers (cascade order)
1. Groq — `llama3-8b-8192` (fastest, lower RPM)
2. Mistral — `open-mistral-nemo` (accurate in PT-BR)
3. OpenRouter — `meta-llama/llama-3.1-8b-instruct:free` (free fallback)
- All accessed via `AsyncOpenAI` with custom `base_url`
- Circuit breaker per provider (`core/circuit_breaker.py`)

### Database
- Supabase (PostgreSQL) — primary data store
  - Tables: `candidatos`, `comentarios`, `threat_alerts`, `dossies`, `worker_sessions`, `worker_metrics`, `worker_rewards`
  - RLS (Row Level Security) enforced
  - Migrations versioned in `supabase/migrations/` (v44→v50.1) and `migrations/`
- Local SQLite (`proposta_frontend/db/custom.db`) — demo/seed data via Prisma

### Scraping Stack
- Scrapy 2.15.2 (vendored fork in `scrapy-tags-2.15.2/`)
- Playwright (headless Chromium) for Tier 2 scraping
- Zyte API for Tier 3 (anti-bot bypass)
- Three Scrapy projects: `sentinela_novo/`, `sentinela_scraper/`, `sentinela_scrapy/`

### Configuration
- All secrets via `.env` / environment variables
- `core/config.py` — `Settings` class (not Pydantic BaseSettings, plain class)
- Key env vars:
  - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`
  - `GROQ_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`
  - `ZYTE_API_KEY`
  - `INSTAGRAM_SESSIONID`
  - `WATCHDOG_ACTIVE` — changes log format when true
  - `IA_PROVIDER` — `hybrid` | `gemini` | `groq` | `ollama`

## Frontend (proposta_frontend — OFFICIAL)

### Runtime & Framework
- Next.js 16 (App Router)
- React 19
- TypeScript 5
- Bun (package manager + runtime for production server)

### UI Stack
- Tailwind CSS v4
- shadcn/ui component library
- Radix UI primitives (full suite)
- `framer-motion` v12 — animations
- `lucide-react` — icons
- `recharts` — data visualization charts
- `sonner` — toast notifications

### State & Data
- `zustand` v5 — client state management
- `@tanstack/react-query` v5 — server state / data fetching
- `@tanstack/react-table` v8 — data tables
- `react-hook-form` v7 + `zod` v4 — form validation
- `prisma` v6 + `@prisma/client` — local SQLite ORM (demo data)

### Auth
- `next-auth` v4 — authentication

### Dev Tools
- ESLint 9 with `eslint-config-next`
- TypeScript strict mode
- `postcss` with `@tailwindcss/postcss`

### Frontend Scripts
```bash
bun run dev      # Dev server on port 3000
bun run build    # Production build
bun run start    # Production server (standalone)
bun run lint     # ESLint
bun run db:push  # Prisma schema push
```

## Deployment

### Vercel (Frontend)
- Root Directory: `proposta_frontend`
- Framework: Next.js
- Config: `vercel.json` at root

### Render (Backend)
- Config: `render.yaml`
- Entry: `python main_runner.py`

### CI/CD (GitHub Actions — `.github/workflows/`)
- `daily_pipeline.yml` — scheduled data pipeline
- `pipeline.yml` — main CI pipeline
- `intelligence_worker.yml` — intelligence worker automation
- `deploy-data.yml` — data deployment
- `render_deploy.yml` — Render deployment trigger

## Development Commands

```bash
# Backend
python main_runner.py          # Start worker orchestrator
python watchdog.py             # Start watchdog supervisor

# Frontend
cd proposta_frontend
bun install
bun run dev

# Database migrations
python scripts/apply_local_migrations.py
python scripts/apply_migration.py

# Testing
pytest                         # Python tests
cd proposta_frontend && bun test  # Frontend tests
```
