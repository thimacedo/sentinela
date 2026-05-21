# Sentinela — Development Guidelines

## Code Quality Standards

### Python Style
- Always include `from __future__ import annotations` at the top of every Python module
- Use `@dataclass` and `@dataclass(field=...)` for data contracts — never plain dicts for structured results
- Type hints on all function signatures; use `Optional[T]` for nullable fields
- `TYPE_CHECKING` guard for circular import prevention:
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from workers.base.reward_engine import RewardEngine
  ```
- Module-level logger per file: `logger = logging.getLogger("module_name")`
- Worker loggers use namespaced format: `logging.getLogger(f"worker.{worker_id}")`

### Naming Conventions
- Classes: PascalCase (`IGZyteWorker`, `CycleResult`, `RewardEngine`)
- Functions/methods: snake_case (`run_cycle`, `claim_next_target`, `persist_comments`)
- Constants: UPPER_SNAKE_CASE (`SYSTEM_PROMPT`, `WATCHDOG_ACTIVE`)
- Private methods: leading underscore (`_zyte_request`, `_extract_json_from_html`, `_parse_json_response`)
- Worker IDs: kebab-case strings (`"ig-zyte-01"`, `"ig-headless-01"`)

### Logging Pattern
Use structured log messages with emoji prefixes for operational clarity:
```python
logger.info("✅ Persistência concluída | @%s | inseridos=%s", username, count)
logger.warning("⚠️ [Zyte] Rate Limited (429). Aguardando backoff...")
logger.error("❌ Falha na persistência: %s", e)
logger.info("🎯 Ciclo %s | Alvo: @%s", cycle, username)
logger.info("🧠 Iniciando classificação MCA v2.2 para %s comentários...", count)
logger.info("🚀 [Zyte] Coletando perfil real: @%s", username)
```
- Use `%s` formatting in logger calls (not f-strings) for lazy evaluation
- Prefix log messages with `[module_name]` or `[WorkerID]` for traceability

## Architectural Patterns

### Worker Contract (BaseWorker ABC)
All workers MUST implement:
```python
class MyWorker(BaseWorker):
    async def setup(self) -> None: ...       # Resource initialization
    async def run_cycle(self) -> CycleResult: ...  # One collection cycle
    async def teardown(self) -> None: ...    # Always runs, even after exception
    def describe(self) -> str: ...           # Human-readable description
```
- `run_cycle()` MUST return `CycleResult` even on partial failure — never raise
- `teardown()` must always release resources regardless of exceptions
- Never override `start()` — it's the managed loop

### CycleResult Contract
Always return a fully populated `CycleResult` from `run_cycle()`:
```python
return CycleResult(
    worker_id=self.worker_id,
    cycle=self.cycle,
    target=target.username,
    target_id=target.candidato_id,
    source="zyte",           # fila_coleta | fallback | manual | dry_run
    extracted=len(comments),
    inserted=persist.inserted,
    duplicated=persist.duplicated,
    classified=classify.classified,
    failed=persist.failed + classify.failed,
    db_success=persist.success,
    classifier_success=classify.success,
    simulated=False
)
```
- Use `simulated=True` only for dry runs or when no real data was collected
- `error` field: truncate to 200 chars (`str(exc)[:200]`)

### Singleton Services
Core services use singleton pattern with lazy initialization:
```python
class SupabaseService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance
```
- `core/supabase_service.py` — `get_supabase_client()` convenience function
- `core/ai_service.py` — `ai_service = AIService()` module-level singleton
- `core/config.py` — `settings = Settings()` module-level singleton

### Circuit Breaker Pattern
All external API calls (AI providers, Zyte) go through circuit breakers:
```python
if not circuit_breaker.can_execute("provider_name"):
    continue  # skip this provider
try:
    result = await call_api()
    circuit_breaker.record_success("provider_name")
except APIStatusError as e:
    circuit_breaker.record_failure("provider_name", e.status_code)
```

### AI Provider Cascade
Always use the cascade order — never call a single provider directly:
1. Groq (`llama3-8b-8192`) — fastest
2. Mistral (`open-mistral-nemo`) — accurate in PT-BR
3. OpenRouter (`meta-llama/llama-3.1-8b-instruct:free`) — free fallback

### Retry / Backoff Pattern
```python
max_retries = 2
for attempt in range(max_retries + 1):
    if response.status_code == 429:
        await asyncio.sleep(10 * (attempt + 1))
        continue
    if response.status_code == 503:
        delay = 5 * (2 ** attempt)  # exponential backoff
        await asyncio.sleep(delay)
        continue
```

### Supabase Operations
Use `upsert` with `on_conflict` for idempotent writes:
```python
db.table('comentarios').upsert(
    comments_data,
    on_conflict="id_externo"
).execute()
```
- Always wrap DB calls in try/except and return a stats dataclass
- Use `.single().execute()` for single-row fetches
- Chain `.select().eq().order().limit().execute()` for queries

## Data Structures

### Intermediate Stats Dataclasses
Use dedicated dataclasses for operation results (not raw dicts):
```python
@dataclass
class PersistStats:
    inserted: int = 0
    duplicated: int = 0
    failed: int = 0
    inserted_ids: list[str] = field(default_factory=list)
    success: bool = False

@dataclass
class ClassifyStats:
    classified: int = 0
    failed: int = 0
    success: bool = False
```

### Comment Schema (Supabase `comentarios` table)
```python
{
    "id_externo": f"ig_{pk}",          # unique conflict key
    "texto_bruto": text,
    "autor_username": username,
    "data_publicacao": iso_timestamp,
    "data_coleta": iso_timestamp,
    "post_shortcode": shortcode,
    "plataforma": "INSTAGRAM",
    "rede_social": "INSTAGRAM",
    "candidato_id": uuid,
    "processado_ia": False,
    "mined": True
}
```

## Frontend Patterns (proposta_frontend)

### Component Structure
- All page components are `'use client'` with `useState`/`useEffect`/`useCallback`
- Data loading via `fetch('/api/...')` with error handling and `toast.error()`
- `useCallback` wraps all async handlers to prevent re-render loops
- `AnimatePresence` + `motion.div` for tab transitions (framer-motion)

### UI Conventions
- Dark theme: background `#020817`, surface `#0a0f1e`, borders `slate-800`
- Primary accent: `cyan-400` / `cyan-900/30`
- Status indicators: `emerald-400` (online), `red-500` (alert)
- Font: `font-mono` for technical data, default sans for labels
- Responsive: `hidden sm:inline` pattern for mobile-first text hiding

### API Calls
```typescript
const res = await fetch('/api/dashboard');
if (!res.ok) throw new Error('Failed to load');
const json = await res.json();
```
- Always check `res.ok` before parsing
- Use `toast.error()` / `toast.success()` from `sonner` for user feedback
- Loading states with `useState<boolean>` + conditional render

## Security Rules (Critical)
1. Never send raw SQL from frontend — all DB access through backend API
2. `SUPABASE_SERVICE_KEY` must never be exposed to frontend or committed
3. Never import from `archive_v17_2026/`, `app/` (legacy), or `core/` (legacy paths)
4. All secrets via environment variables — no hardcoded credentials
5. `DASHBOARD_PIN` and `ADMIN_TOTP_SECRET` required for admin access

## Environment Variable Conventions
- Check for presence before using: `key = os.getenv("KEY")` then `if key:`
- Log a warning (not error) when optional keys are missing:
  ```python
  if not zyte_key:
      logger.warning("[main_runner] ZYTE_API_KEY ausente; IGZyteWorker não registrado.")
  ```
- Raise `RuntimeError` only for truly required keys in `setup()`

## Testing
- `pytest.ini` at root for Python tests
- Mock Supabase client in `tests/mocks/mock_supabase_service.py`
- Playwright E2E specs in `tests/` (`*.spec.ts`)
- Test scripts in `test_scripts/` for connectivity and env validation
