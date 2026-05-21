# Arquitetura Sentinela — PASA v50.1
_last_updated: 2026-05-21_

## 1. Visao Geral

Sentinela e uma plataforma de inteligencia politica para deteccao de discurso de odio e desinformacao no Instagram, focada nas eleicoes brasileiras de 2026. Opera sob o protocolo PASA (Protocolo de Analise Semantica e Ameacas) v50.1.

## 2. Topologia

```
[watchdog.py]
    └── [main_runner.py]
          └── SentinelaOrchestrator
                ├── _active_targets: set  (anti-duplicata entre workers)
                ├── _claim_lock: asyncio.Lock
                ├── IGZyteWorker          (Tier 3 — Zyte API)
                └── IGHeadlessWorker      (Tier 2 — Playwright)

[proposta_frontend/]  →  /api/*  →  [api/index.py FastAPI]  →  Supabase
[supabase/functions/mcp-proxy/]  →  ROUTES semanticas (SQL estatico)
```

## 3. Workers

### IGZyteWorker
- Extrai perfil via `GET /api/v1/users/web_profile_info/`
- Fallback para Browser Rendering (Zyte) se API JSON falhar
- Paginacao de comentarios via `next_min_id` (ate `max_comments_per_post=100`)
- Rotacao sequencial de slots `INSTAGRAM_SESSIONID*`
- Slots com login wall adicionados a `_blocked_slots` permanentemente no ciclo
- Fallback final: `sessionid` extraido de `configs/instagram_storage_state.json`
- Fallback de coleta: `InstagramHeadlessScraper` se Zyte retornar vazio

### IGHeadlessWorker
- Playwright headless com `IdentityManager` (rotacao de contas via `scraping_accounts`)
- Fallback de conta: `IG_USER`/`IG_PASS` do `.env`
- Coleta shortcodes via DOM, comentarios via `page.evaluate()`
- Retorna lista de comentarios para persistencia pelo worker

### Contrato BaseWorker
```python
async def setup() -> None       # inicializacao de recursos
async def run_cycle() -> CycleResult  # um ciclo completo
async def teardown() -> None    # sempre executado, mesmo apos excecao
def describe() -> str           # descricao legivel
```

## 4. Orquestrador

- `asyncio.gather()` executa todos os workers em paralelo
- `_active_targets` compartilhado: workers nao pegam o mesmo alvo no mesmo ciclo
- `rotate_target()` em `finally` — chamada unica garantida
- Apos cada ciclo: `RewardEngine.process_result()` → `AIAdvisor` (condicional)

## 5. Pipeline de Dados

```
Instagram
  └── Scrapers (Zyte / Playwright)
        └── comentarios (Supabase)
              ├── processado_ia=False  (recém inserido)
              └── AIService.classify_text()
                    ├── Groq (llama3-8b-8192)       — mais rapido
                    ├── Mistral (open-mistral-nemo)  — preciso em PT-BR
                    └── OpenRouter (llama-3.1-8b)    — fallback gratuito
                          └── comentarios.processado_ia=True
                                ├── categoria_ia, confianca_ia, is_hate
                                └── AlertManager → WhatsApp / Firebase
```

## 6. Sistema de Recompensas

```
CycleResult
  └── RewardEngine.calculate_score()   → float 0-100
  └── RewardEngine.resolve_tier()      → platinum/gold/silver/bronze/critical
  └── RewardEngine.resolve_badges()    → ["Persistencia OK", "IA OK", ...]
  └── RewardEngine.get_interval()      → segundos ate proximo ciclo
  └── MemoryStore.save_reward()        → worker_rewards (Supabase)
```

## 7. Fila de Coleta

Prioridade de claim:
1. `config["target"]` ou `TEST_TARGET_USERNAME` (manual)
2. `fila_coleta` (status=PENDENTE)
3. `candidatos` (status_monitoramento=Ativo, order by last_scraped_at ASC)

`rotate_target()`: delete + upsert com `on_conflict=candidato_id,data_agendada` + `ignore_duplicates=True`

## 8. Seguranca

- SQL arbitrario bloqueado na Edge Function (`mcp-proxy`): apenas `{ action }` aceito
- `SUPABASE_SERVICE_KEY` exclusivo do backend — nunca exposto ao frontend
- `configs/instagram_storage_state.json` no `.gitignore` e `.vercelignore`
- `.vercelignore` protege `workers/`, `core/`, `configs/`, `.env*`, sessoes
- AIAdvisor: nunca aplica patches — apenas salva sugestoes com `status=pending_review`

## 9. Frontend

- Localização: `proposta_frontend/` (deploy Vercel, `Root Directory=proposta_frontend`)
- Stack: Next.js 16 + React 19 + TypeScript + Tailwind v4 + shadcn/ui
- Comunicacao: `/api/*` endpoints FastAPI — sem SQL direto
- Tabs: War Room, Analise Forense, Alvos, Dossies, Alertas, Rede, Fila de Coleta

## 10. Decisoes Arquiteturais

| Decisao | Motivo |
|---|---|
| `ignore_duplicates=True` no upsert | Contagem real de duplicados vs inseridos |
| `active_targets` set compartilhado | Workers paralelos nao desperdicam trabalho no mesmo alvo |
| `rotate_target` em `finally` | Chamada unica garantida independente de sucesso/excecao |
| IA limitada a 10/ciclo | Evita circuit breaker por excesso de chamadas |
| AIAdvisor condicional | Evita ruido em ciclos saudaveis |
| Slots sequenciais (nao aleatorios) | Slots ruins sao bloqueados e nao voltam no ciclo |
