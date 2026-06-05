# ROADMAP.md — Sentinela
_last_updated: 2026-06-05 | branch: main_

## Concluído

### Núcleo operacional
- [x] Watchdog local com stream de logs via SSE
- [x] Controle remoto do runner com start, stop e restart
- [x] `AIProcessorWorker` como classificador oficial do pipeline
- [x] Triagem local com `ollama`
- [x] Fallback profundo com `FallbackLLM`
- [x] AuditWorker refatorado para AuditAgent (subagente analítico sob demanda)
- [x] `NetworkMinerWorker` refatorado para `NetworkMinerAgent` (subagente relacional sob demanda)
- [x] `TreasurerWorker` refatorado para `TreasurerAgent` (subagente financeiro sob demanda)
- [x] `TargetResearchWorker` com ativação controlada por `RESEARCHER_MODE`
- [x] Expurgo dos entrypoints e contratos legados paralelos ao runtime oficial
- [x] Absorção do padrão ouro legado em `core/ai_service.py`
- [x] Atualização dos scripts operacionais para o runtime moderno

### Escalabilidade e resiliência
- [x] Claim atômico da `fila_coleta`
- [x] Suporte a `SELECT FOR UPDATE SKIP LOCKED`
- [x] Release de locks expirados
- [x] Circuit breaker para IA
- [x] `db_circuit_breaker` para Supabase
- [x] buffer/checkpoint de scraping em estágio operacional

### UX e operação
- [x] local_dashboard.html refeito com UI Premium, Glassmorphism e responsividade absoluta (Mobile-first, com colunas flexíveis de `calc(100vh-290px)`, telemetria e alvos roláveis e auto-reload automático de 10s com trava de concorrência).
- [x] frontend oficial em `frontend/`
- [x] dashboard financeiro com Recharts
- [x] robustez do carregamento AdSense com retry até script estar pronto
- [x] integração de checkout e planos com base URL centralizada
- [x] conclusão da página `frontend/app/relatorios/page.tsx` com backend real
- [x] ativação de CTAs e botões sem ação em páginas principais
- [x] melhorias visuais focadas na home e navegação (sem animações excessivas e com alvos de clique maiores)
- [x] remoção de item administrativo exposto no menu público
- [x] remoção da rota de relatórios obsoleta do Next.js (FastAPI como fonte única de dossiês)
- [x] padronização e versionamento das variáveis de ambiente de produção para Stripe e frontend (`STRIPE_*`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`)

---

## Em andamento

### Coleta e scraping
- [ ] checkpoint intermediário por post raspado
- [x] rotação real de proxies no Playwright
- [x] redução de ciclos com `no_comments_found`

### Otimização de Pipeline Reativo (Fase 9) - Concluído
- [x] Implementar `EventBus` centralizado para sinalização em memória (`AsyncLocalEventBus`).
- [x] Atualizar `InstagramScraperWorker` para disparar evento `NEW_DATA_AVAILABLE` após a coleta atômica.
- [x] Atualizar `AIProcessorWorker` (via `Orchestrator`) para usar `event.wait()` (Reatividade) em vez de polling constante, com timeout de segurança de 1200s.
- [x] Validar redução de latência entre coleta e classificação (reatividade comprovada: ~2.00ms de overhead real vs espera inativa).

### Inteligência
- [x] saneamento da malha de providers em `config/fallback_providers.yaml`
- [x] remover referências residuais a LiteRT do código e da operação
- [x] Caching de I/O e expurgo de modelos inoperantes (401/402/404) via `_handle_provider_error`
- [ ] calibrar reanálise de baixa confiança com menor ruído de fallback

### Workers e orquestração
- [x] simplificar `workers/orchestrator/orchestrator.py`
- [x] unificar semântica de `no_tasks_available` entre workers ativos
- [x] reduzir duplicidade de logging, cooldown e fluxo entre ciclos
- [x] padronizar nomenclatura de todos os workers e subagentes em português (prefixos `wk_` e `sa_`)
- [ ] revisar se `WkPesquisaAlvos` deve permanecer em `workers/ai/` ou migrar para domínio próprio

### Administração e analytics
- [ ] tabelas tabulares de gasto por usuário e por perfil monitorado
- [ ] shadowban léxico
- [ ] exportação de dossiês em lote

### Monetização e relatórios
- [x] executar validação final de lint/testes do frontend (build estático verificado com sucesso)

---

## Futuro

### Fila distribuída
- [ ] avaliar PGMQ como alternativa futura de fila
- [ ] decidir se PGMQ agrega valor além da trava atômica já implantada

### Operação
- [ ] consolidar documentação viva por domínio
- [x] reduzir artefatos históricos conflitantes no workspace (limpeza de drift e termos restritos concluída)

---

## Decisões registradas

- a fila atômica atual usa RPC + `SELECT FOR UPDATE SKIP LOCKED`
- PGMQ não é requisito atual de produção
- LiteRT não compõe mais o pipeline de processamento ativo
- `frontend/` é o frontend oficial
- `STATE.md` é a fonte de verdade operacional
- o runtime oficial de workers usa `workers/base/worker_base.py`
- entrypoints paralelos legados não devem ser reintroduzidos