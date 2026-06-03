# ROADMAP.md — Sentinela
_last_updated: 2026-06-03 | branch: main_

## Concluído

### Núcleo operacional
- [x] Watchdog local com stream de logs via SSE
- [x] Controle remoto do runner com start, stop e restart
- [x] `AIProcessorWorker` como classificador oficial do pipeline
- [x] Triagem local com `ollama`
- [x] Fallback profundo com `FallbackLLM`
- [x] `NetworkMiner` com deduplicação por assinatura lexical
- [x] `Treasurer` com telemetria financeira
- [x] `researcher_agent` com atualização de heurísticas em `config/custom_rules.json`

### Escalabilidade e resiliência
- [x] Claim atômico da `fila_coleta`
- [x] Suporte a `SELECT FOR UPDATE SKIP LOCKED`
- [x] Release de locks expirados
- [x] Circuit breaker para IA
- [x] `db_circuit_breaker` para Supabase
- [x] buffer/checkpoint de scraping em estágio operacional

### UX e operação
- [x] `local_dashboard.html` com tabs de monitor e logs
- [x] frontend oficial em `frontend/`
- [x] dashboard financeiro com Recharts

---

## Em andamento

### Coleta e scraping
- [ ] checkpoint intermediário por post raspado
- [ ] rotação real de proxies no Playwright
- [ ] redução de ciclos com `no_comments_found`

### Inteligência
- [ ] saneamento da malha de providers em `config/fallback_providers.yaml`
- [ ] remover referências residuais a LiteRT do código e da operação
- [ ] calibrar reanálise de baixa confiança com menor ruído de fallback

### Administração e analytics
- [ ] tabelas tabulares de gasto por usuário e por perfil monitorado
- [ ] shadowban léxico
- [ ] exportação de dossiês em lote

---

## Futuro

### Fila distribuída
- [ ] avaliar PGMQ como alternativa futura de fila
- [ ] decidir se PGMQ agrega valor além da trava atômica já implantada

### Operação
- [ ] consolidar documentação viva por domínio
- [ ] reduzir artefatos históricos conflitantes no workspace

---

## Decisões registradas

- a fila atômica atual usa RPC + `SELECT FOR UPDATE SKIP LOCKED`
- PGMQ não é requisito atual de produção
- LiteRT não compõe mais o pipeline de processamento ativo
- `frontend/` é o frontend oficial
- `STATE.md` é a fonte de verdade operacional