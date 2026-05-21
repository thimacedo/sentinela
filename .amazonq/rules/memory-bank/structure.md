# Sentinela — Project Structure

## Root Entry Points
- `main_runner.py` — Primary backend entry point; builds orchestrator, registers workers, runs async loop
- `watchdog.py` — Operational supervisor process
- `vercel.json` — Vercel deployment config (routes API to Python backend)
- `render.yaml` — Render.com deployment config

## Directory Map

```
sentinela/
├── core/                    # Shared backend services (singleton pattern)
│   ├── ai_service.py        # LLM cascade classifier (Groq→Mistral→OpenRouter)
│   ├── circuit_breaker.py   # Per-provider circuit breaker for AI APIs
│   ├── config.py            # Settings class (env-based, singleton `settings`)
│   ├── supabase_service.py  # Supabase client singleton + CRUD helpers
│   ├── forensics_service.py # Forensic analysis pipeline
│   ├── alert_manager.py     # Threat alert orchestration
│   ├── whatsapp_alerter.py  # WhatsApp notification delivery
│   ├── firebase_alerter.py  # Firebase push notification delivery
│   ├── session_manager.py   # Instagram session lifecycle
│   ├── pasa_auditor.py      # PASA protocol audit logging
│   ├── behavior_engine.py   # Behavioral pattern detection
│   ├── predictive_service.py# Predictive threat scoring
│   ├── normalizer.py        # Text normalization utilities
│   └── schemas.py           # Pydantic data schemas
│
├── workers/                 # Async worker system
│   ├── base/
│   │   ├── worker_base.py   # BaseWorker ABC + WorkerMetrics dataclass
│   │   ├── cycle_result.py  # CycleResult contract dataclass
│   │   ├── reward_engine.py # Scores cycles, assigns tiers, sets intervals
│   │   └── memory_store.py  # In-memory state store for workers
│   ├── orchestrator/
│   │   └── orchestrator.py  # SentinelaOrchestrator: registers/runs workers
│   ├── scrapers/
│   │   ├── ig_zyte.py       # IGZyteWorker — Zyte API scraper (Tier 3)
│   │   └── ig_headless.py   # IGHeadlessWorker — Playwright scraper (Tier 2)
│   ├── processors/
│   │   ├── classifier_worker.py  # Batch AI classification worker
│   │   ├── alert_worker.py       # Alert generation worker
│   │   ├── dossier_worker.py     # Dossier PDF generation worker
│   │   ├── candidate_scanner.py  # New candidate discovery
│   │   ├── cleanup_worker.py     # Data hygiene worker
│   │   └── queue_manager.py      # Scraping queue management
│   ├── ai/
│   │   ├── ai_advisor.py    # Analyzes degraded workers, suggests fixes
│   │   └── doc_fetcher.py   # Fetches API docs for AI context
│   └── config/
│       └── settings.py      # Worker-specific configuration
│
├── processing/              # Data processing pipeline modules
│   ├── text_processor.py    # NLP text processing
│   ├── dossie_service.py    # Dossier assembly
│   ├── report_generator.py  # PDF report generation
│   ├── ad_processor.py      # Meta Ads processing
│   ├── data_miner.py        # Data mining utilities
│   ├── monetization_engine.py # Monetization tracking
│   ├── visual_engine.py     # Chart/visualization generation
│   └── workers_metrics.py   # Worker performance metrics
│
├── proposta_frontend/       # OFFICIAL frontend (Vercel deployment)
│   ├── src/app/             # Next.js App Router pages
│   │   └── page.tsx         # Main dashboard (War Room tabs)
│   ├── src/components/sentinela/  # Domain UI components
│   │   ├── WarRoom.tsx
│   │   ├── ForensicAnalysis.tsx
│   │   ├── TargetManagement.tsx
│   │   ├── DossierManager.tsx
│   │   ├── AlertsPanel.tsx
│   │   ├── CollectionQueue.tsx
│   │   └── NetworkAnalysis.tsx
│   ├── src/lib/             # API client, utilities
│   ├── src/types/           # TypeScript type definitions
│   ├── prisma/schema.prisma # Local SQLite schema (demo data)
│   └── package.json         # Next.js 16, React 19, Tailwind v4
│
├── api/                     # Vercel serverless Python API
│   ├── index.py             # FastAPI app entry
│   ├── routes/              # Route modules (audit, monitor, sessions)
│   └── requirements.txt     # API-specific dependencies
│
├── supabase/
│   ├── migrations/          # Versioned SQL migrations (v44→v50.1)
│   └── functions/           # Edge functions (mcp-proxy)
│
├── scripts/                 # Operational one-off scripts
├── tools/                   # Admin/maintenance tools
├── migrations/              # Additional SQL migration files
├── data/                    # Local data files, reports, KPI snapshots
├── docs/                    # Architecture docs, manuals, plans
├── tests/                   # Test suite (Python + JS/TS)
├── sentinela_novo/          # Scrapy project (active)
├── sentinela_scraper/       # Scrapy project (Instagram spider)
├── sentinela_scrapy/        # Scrapy project (API + DOM spiders)
├── scrapy-tags-2.15.2/      # Vendored Scrapy fork with custom tags
├── archive_v17_2026/        # LEGACY — do not import
└── .legacy_frontend/        # LEGACY — do not use
```

## Core Architectural Patterns

### Worker Lifecycle
```
main_runner.py
  └── SentinelaOrchestrator
        ├── register(IGZyteWorker)
        ├── register(IGHeadlessWorker)
        └── run_all() → asyncio.gather(run_cycle_with_validation per worker)
              └── CycleResult → RewardEngine.process_result() → AIAdvisor.analyze_and_suggest()
```

### Data Flow
```
Instagram → Scrapers (Zyte/Playwright) → Supabase (comentarios table)
                                              ↓
                                    AIService.classify_text()
                                    (Groq → Mistral → OpenRouter)
                                              ↓
                                    comentarios.processado_ia = True
                                    + categoria_ia, confianca_ia, evidencia_lexical
                                              ↓
                                    AlertManager → WhatsApp/Firebase
                                    DossierWorker → PDF reports
```

### Frontend ↔ Backend
- Frontend calls `/api/*` endpoints (Next.js API routes proxy to Supabase via Prisma or direct fetch)
- No raw SQL from frontend — all DB access through backend API layer
- `SUPABASE_SERVICE_KEY` never exposed to frontend

## Key Constraints (from README)
1. No raw SQL from frontend
2. `SUPABASE_SERVICE_KEY` stays backend-only
3. No imports from `archive_v17_2026/` or old `app/`/`core/` legacy paths
