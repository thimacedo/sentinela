# Worker Ledger System — Sentinela v50.1
_last_updated: 2026-05-21_

## Visao Geral

O sistema de recompensas avalia a performance de cada worker por ciclo, atribui score/tier/badges e persiste no Supabase (`worker_rewards`). Intervalos entre ciclos sao dinamicos baseados no tier.

## Calculo de Score (0-100)

```
Base: 40 pontos (ciclo real com target e db_success)

Bonus:
  + min(extracted * 1.0, 15)    # volume coletado
  + min(inserted  * 2.0, 25)    # persistencia nova
  + min(classified * 1.5, 15)   # classificacao IA
  + min(duplicated * 0.3, 5)    # upsert saudavel
  + 10 (se success_rate >= 95% e failed == 0)

Penalidade:
  - min(failed * 5.0, 35)       # falhas

Casos especiais:
  0.0  — simulated=True
  5.0  — sem target
  10.0 — erro ou db_success=False
  15.0 — extracted=0
  20.0 — inserted+duplicated=0
```

## Tiers e Intervalos

| Tier | Score | Intervalo | Significado |
|---|---|---|---|
| platinum | >= 85 | 120s | Performance maxima |
| gold | >= 70 | 180s | Alta performance |
| silver | >= 50 | 300s | Performance normal |
| bronze | >= 25 | 480s | Performance baixa |
| critical | < 25 | 600s | Degradado |
| db_failed | — | 600s | Falha de persistencia |
| idle | — | 300s | Sem target disponivel |
| dry_run | — | 300s | Ciclo simulado |

## Badges

| Badge | Criterio |
|---|---|
| Persistencia OK | failed=0 e inserted>0 |
| IA OK | classifier_success=True e classified>=inserted |
| Alta performance | score>=85 |
| Upsert saudavel | duplicated>0 e inserted>0 |

## AIAdvisor

Acionado apenas quando `score < 40` ou `tier in (critical, db_failed)`.
Salva sugestao em `worker_suggestions` com `status=pending_review`.
**Nunca aplica patches automaticamente.**

## Tabelas Supabase

### worker_rewards
```sql
worker_id    text
cycle        integer
score        float
tier         text
delta        float
badges       jsonb
recommendation text
timestamp    timestamptz
```

### worker_suggestions
```sql
worker_id    text
cycle        integer
suggestion   text
status       text  -- pending_review | approved | rejected
timestamp    timestamptz
```

### worker_metrics
```sql
worker_id        text
cycle            integer
items_collected  integer
items_failed     integer
duration_seconds float
errors           jsonb
timestamp        timestamptz
```

## Auditoria

```bash
# Ver rewards recentes
# Supabase: SELECT * FROM worker_rewards ORDER BY timestamp DESC LIMIT 20;

# Ver sugestoes pendentes
# Supabase: SELECT * FROM worker_suggestions WHERE status = 'pending_review';

# Ledger local
cat metrics/performance_ledger.json
```
