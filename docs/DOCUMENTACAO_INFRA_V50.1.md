# Documentacao Tecnica: Sentinela v50.1 (Infraestrutura Operacional)
_last_updated: 2026-05-21_

## Estado Atual

| Subsistema | Status |
|---|---|
| Coleta Zyte | Operacional (fallback headless ativo) |
| Coleta Headless | Operacional (150 comentarios/ciclo validados) |
| Persistencia | OK — upsert idempotente |
| Classificacao IA | OK — limitada a 10/ciclo |
| Fila de Coleta | OK — rotate_target idempotente |
| RewardEngine | Operacional — tier/score reais persistidos |
| Watchdog | Operacional — sem restarts em producao |
| simulated=False | Confirmado em producao |

## Contratos Tecnicos

### BaseWorker
- `setup()`, `run_cycle() -> CycleResult`, `teardown()`, `describe()` obrigatorios
- `run_cycle()` NUNCA lanca excecao — sempre retorna `CycleResult`
- `teardown()` sempre executado via `finally`

### CycleResult
Campos obrigatorios: `worker_id`, `cycle`
Campos operacionais: `target`, `source`, `extracted`, `inserted`, `duplicated`, `classified`, `failed`, `db_success`, `classifier_success`, `simulated`, `error`

### IGZyteWorker
1. `_build_session_cookie()` — slots sequenciais, blacklist, fallback storage_state
2. `fetch_comments_via_zyte()` — perfil → posts → `_fetch_comments_paginated()`
3. `_fetch_comments_paginated()` — loop next_min_id ate max_comments_per_post
4. `persist_comments()` — upsert id_externo, ignore_duplicates
5. `classify_comments()` — limite 10/ciclo, cascade IA
6. `run_cycle()` — finally: rotate_target

### IGHeadlessWorker
1. `InstagramHeadlessScraper.run()` — retorna lista de comentarios
2. Persistencia e classificacao inline no `run_cycle()`
3. `rotate_target` em `finally`

### QueueManager
- `claim_next_target(config, seen_queue_ids, seen_targets, active_targets)` — respeita active_targets do orquestrador
- `rotate_target(target)` — upsert com on_conflict=candidato_id,data_agendada + ignore_duplicates

### RewardEngine
- `calculate_score(result)` — float 0-100
- `resolve_tier(score, result)` — platinum/gold/silver/bronze/critical/db_failed/idle/dry_run
- `get_interval(tier)` — segundos: platinum=120, gold=180, silver=300, bronze=480, critical/db_failed=600
- `process_result(result)` — persiste e retorna `RewardSummary`

### MemoryStore
- `save_reward()` — persiste tier real (nao mais fixado em 'gold')
- `save_suggestion()` — status=pending_review, nunca auto-aplicado
- `save_metrics()` — metricas por ciclo

## Observabilidade

Log padrao por ciclo:
```
[worker_id] ciclo #N | target=@X | origem=Y | extraidos=A | inseridos=B |
duplicados=C | classificados=D | falhas=E | db=ok|falhou | ia=ok|nao |
score=X.X | tier=Y | simulado=False | erro=nenhum
```

AIAdvisor acionado apenas quando `score < 40` ou `tier in (critical, db_failed)`.

## Troubleshooting

| Sintoma | Causa Provavel | Acao |
|---|---|---|
| `Login Wall slot=X` | Sessao expirada | Renovar INSTAGRAM_SESSIONID_X ou rodar export_playwright_cookies.py |
| `no_target_available` | seen_targets esgotado | Normal — limpo a cada ciclo automaticamente |
| `duplicate key fila_coleta` | rotate_target chamado 2x | Corrigido — rotate em finally unico |
| `circuit_open zyte_api` | Muitas falhas consecutivas | Aguardar cooldown (10min) ou verificar ZYTE_API_KEY |
| `score=0 tier=dry_run` | simulated=True | Verificar se worker tem target e sessao valida |
| IA classificados=0 | Circuit breaker IA aberto | Verificar GROQ_API_KEY / MISTRAL_API_KEY / OPENROUTER_API_KEY |
