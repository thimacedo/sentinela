# ROADMAP.md — Sentinela Democratica
_last_updated: 2026-05-21 | branch: feat/autonomous-workers_

## Concluido

### Fundacao e Core (v17 - v24)
- [x] Arquitetura BaseWorker com contrato abstrato (setup/run_cycle/teardown/describe)
- [x] Circuit Breaker para IA (Groq/Mistral/OpenRouter) e Zyte
- [x] Supabase singleton com lazy loading e fallback SERVICE_KEY -> KEY -> ANON_KEY

### Fortaleza Instagram e Fila (v25 - v34)
- [x] Fila inteligente com cooldown e rotacao de alvos
- [x] QueueManager com claim_next_target (fila -> candidatos fallback)
- [x] rotate_target idempotente (upsert + ignore_duplicates + tratamento 23505)

### Inteligencia e Convergencia (v35 - v44)
- [x] Watchdog com auto-restart e health check
- [x] MCA v2.2 — classificacao PASA com 7 categorias
- [x] Cascade IA: Groq -> Mistral -> OpenRouter com circuit breaker por provider

### Governanca e Otimizacao (v45 - v47)
- [x] Sistema de metricas de workers (worker_metrics, worker_rewards, worker_suggestions)
- [x] Backend FastAPI compativel com Vercel Serverless
- [x] Rotacao de contas de scraping via IdentityManager

### Coleta Real e Workers Autonomos (v48 - v50.1)
- [x] IGZyteWorker: extracao real com paginacao next_min_id (max 100 comentarios/post)
- [x] IGZyteWorker: rotacao sequencial de slots, blacklist login wall, fallback storage_state
- [x] IGHeadlessWorker: implementado com scraping real (150 comentarios/ciclo validados)
- [x] active_targets compartilhado: workers pegam alvos diferentes no mesmo ciclo
- [x] CycleResult: contrato completo com inserted/duplicated/classified/failed
- [x] RewardEngine: score 0-100, tiers, badges, get_interval() dinamico
- [x] MemoryStore: tier real persistido (removido 'gold' fixo)
- [x] Orchestrator: loga score/tier/badges, AIAdvisor condicional
- [x] probe_t3_2_storage.py: validacao com alvo dinamico do Supabase
- [x] Edge Function mcp-proxy: SQL arbitrario bloqueado, ROUTES semanticas
- [x] Frontend proposta_frontend: sem SQL bruto, /api/* FastAPI
- [x] .gitignore e .vercelignore: reescritos UTF-8, dados de runtime protegidos
- [x] simulated=False confirmado em producao

---

## Pendente

### Sessao Zyte
- [ ] Renovar INSTAGRAM_SESSIONID slot=2 (login wall detectado em producao)
- [ ] Implementar renovacao automatica de sessao via export_playwright_cookies.py

### Expansao de Coleta
- [ ] Ativar paginacao de posts (atualmente max_posts=3)
- [ ] Mapeamento de shadowbans: detectar quando alvo oculta comentarios
- [ ] Analise de engajamento: correlacionar likes com severidade do discurso

### Refinamento de IA
- [ ] Few-shot dinamico baseado em audit_gold_standards
- [ ] Aumentar limite de classificacao por ciclo conforme estabilidade dos circuit breakers
- [ ] Fine-tuning de modelo local (Ollama) para reducao de dependencia de API

### Relatorios
- [ ] Exportacao de dossies PDF automatica pos-ciclo
- [ ] Grafos de redes coordenadas no frontend

### Infraestrutura
- [ ] Merge feat/autonomous-workers -> main
- [ ] Deploy Render com main_runner.py em modo persistente
- [ ] Monitoramento de RewardEngine via dashboard frontend

---

## Proximas Acoes Imediatas

1. Renovar sessao Instagram (slot=2 bloqueado)
2. Rodar `python watchdog.py` com novo slot e validar ciclo completo com IA classificando
3. Merge para main apos validacao
