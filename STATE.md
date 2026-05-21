# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-21 | branch: feat/autonomous-workers_

## Status Operacional

| Subsistema | Status | Observacao |
|---|---|---|
| Coleta Zyte (IGZyteWorker) | Operacional | Login wall em slot=2; fallback headless ativo |
| Coleta Headless (IGHeadlessWorker) | Operacional | 150 comentarios/ciclo validados em producao |
| Persistencia Supabase | OK | upsert id_externo, ignore_duplicates, duplicados contados corretamente |
| Classificacao IA | OK (limitada) | 10/ciclo, cascade Groq->Mistral->OpenRouter |
| Fila de Coleta | OK | rotate_target idempotente, 23505 tratado |
| RewardEngine | Operacional | score/tier/badges persistidos, get_interval() por tier |
| AIAdvisor | Condicional | Acionado apenas score<40 ou tier critical/db_failed |
| Watchdog | Operacional | Sem restarts em producao |
| Frontend (proposta_frontend) | Deployado | Vercel, Next.js 16, /api/* FastAPI |
| Edge Function (mcp-proxy) | Operacional | SQL arbitrario bloqueado, ROUTES semanticas |

## Arquitetura Atual (v50.1)

```
watchdog.py
  └── main_runner.py
        └── SentinelaOrchestrator
              ├── _active_targets: set  (compartilhado entre workers)
              ├── IGZyteWorker (ig-zyte-01)
              │     ├── _build_session_cookie()  → slots sequenciais + blacklist + storage_state
              │     ├── fetch_comments_via_zyte() → perfil → posts → _fetch_comments_paginated()
              │     ├── persist_comments()        → upsert id_externo
              │     └── classify_comments()       → limite 10/ciclo
              └── IGHeadlessWorker (ig-headless-01)
                    ├── InstagramHeadlessScraper  → Playwright + IdentityManager
                    ├── persist_comments()        → upsert id_externo
                    └── classify_comments()       → limite 10/ciclo

CycleResult → RewardEngine.process_result() → RewardSummary (score, tier, badges)
           → MemoryStore.save_reward()       → worker_rewards (Supabase)
           → AIAdvisor (condicional)         → worker_suggestions (Supabase)
```

## Fluxo de Dados

```
Instagram
  └── Zyte API / Playwright
        └── comentarios (Supabase)
              └── AIService.classify_text()  [Groq → Mistral → OpenRouter]
                    └── comentarios.processado_ia = True
                          └── AlertManager → WhatsApp / Firebase
                          └── DossierWorker → PDF
```

## Sessoes e Autenticacao

- `INSTAGRAM_SESSIONID*` — slots sequenciais, slots com login wall adicionados a `_blocked_slots`
- `INSTAGRAM_COOKIE_FULL` — prioridade maxima se presente
- `configs/instagram_storage_state.json` — fallback Playwright (validado via `scripts/probe_t3_2_storage.py`)
- Validacao do storage_state: abre perfil real do Supabase, checa URL + HTML (sem seletores frageis)

## Fila de Coleta

- Fonte primaria: `fila_coleta` (status=PENDENTE)
- Fallback: `candidatos` (status_monitoramento=Ativo, order by last_scraped_at ASC)
- `rotate_target()`: upsert com on_conflict=candidato_id,data_agendada + ignore_duplicates
- `active_targets`: set compartilhado via orquestrador — workers pegam alvos diferentes no mesmo ciclo

## Sistema de Recompensas

| Tier | Score | Intervalo |
|---|---|---|
| platinum | >= 85 | 120s |
| gold | >= 70 | 180s |
| silver | >= 50 | 300s |
| bronze | >= 25 | 480s |
| critical | < 25 | 600s |
| db_failed | — | 600s |

Score calculado por: extracted (+1.0/item, max 15) + inserted (+2.0/item, max 25) + classified (+1.5/item, max 15) + duplicated (+0.3/item, max 5) - failed (-5.0/item, max -35) + bonus perfeicao (+10 se success_rate>=95 e failed==0)

## Variaveis de Ambiente Necessarias

```
# Supabase
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY   # backend only, nunca frontend

# Instagram
ZYTE_API_KEY
INSTAGRAM_SESSIONID    # slot principal
INSTAGRAM_SESSIONID_2  # slot adicional (opcional)
INSTAGRAM_COOKIE_FULL  # cookie completo (opcional, prioridade maxima)

# IA
GROQ_API_KEY
MISTRAL_API_KEY
OPENROUTER_API_KEY

# Seguranca
DASHBOARD_PIN
SENTINELA_ADMIN_TOTP_SECRET
WATCHDOG_ACTIVE        # true = formato de log compacto
```

## Regras Criticas

1. Nunca enviar SQL bruto pelo frontend
2. `SUPABASE_SERVICE_KEY` apenas no backend
3. Nunca importar de `archive_v17_2026/` ou `.legacy_frontend/`
4. `configs/instagram_storage_state.json` nunca commitar (protegido no .gitignore)
5. AIAdvisor nunca aplica patches automaticamente — apenas salva sugestoes com status=pending_review

## Comandos Operacionais

```bash
# Backend
python main_runner.py          # orquestrador principal
python watchdog.py             # supervisor com auto-restart

# Validacao de sessao
python scripts/probe_t3_2_storage.py

# Frontend
cd proposta_frontend && bun run dev
cd proposta_frontend && bun run build

# Migrations
python scripts/apply_migration.py
```
