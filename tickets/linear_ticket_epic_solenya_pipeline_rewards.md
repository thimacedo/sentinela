---
id: epic_solenya_pipeline_rewards
title: "[Epic] Otimização de Pipeline de Dados e Sistema de Recompensas"
status: Done
priority: High
order: 1
created: 2026-05-07
updated: 2026-05-21
links:
  - url: prd.md
    title: PRD Original
---

## Resultado

### Ticket 1 — Otimizacao de scrapers
- IGZyteWorker: paginacao via next_min_id, rotacao sequencial de slots, blacklist login wall, fallback storage_state
- IGHeadlessWorker: implementado com scraping real, persistencia e classificacao
- active_targets compartilhado: workers pegam alvos diferentes no mesmo ciclo

### Ticket 2 — Refinamento PASA
- Classificacao IA limitada a 10/ciclo para evitar circuit breaker
- Cascade Groq -> Mistral -> OpenRouter operacional
- rotate_target idempotente (23505 nao derruba worker)

### Ticket 3 — Sistema de Recompensas
- RewardEngine.calculate_score(): score 0-100 baseado em extracted/inserted/classified/failed
- RewardEngine.resolve_tier(): platinum/gold/silver/bronze/critical/db_failed/idle/dry_run
- RewardEngine.get_interval(): intervalo dinamico por tier (120s platinum -> 600s critical)
- RewardEngine.process_result(): retorna RewardSummary com score/tier/badges
- MemoryStore.save_reward(): tier real persistido (removido 'gold' fixo)
- Orchestrator: loga score/tier/badges por ciclo, AIAdvisor acionado apenas quando score<40 ou tier critical/db_failed
