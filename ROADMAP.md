# ROADMAP.md — Sentinela Democratica
_last_updated: 2026-06-02 | branch: main_

## Concluido

### Inteligência e Coleta Industrial (v65 - v86.0)
- [x] **Stealth Mode**: Rotação dinâmica de User-Agents, Viewports e injeção anti-fingerprint (v85.10).
- [x] **Triagem Local (Ollama)**: Integração com IA local para redução de custos em 50% (v85.11).
- [x] **Dossiês Analíticos Reais**: Motor PDF v85.9 com assinatura SHA-256 e selo de integridade.
- [x] **Network Miner**: Detecção de clusters coordenados e contas multi-target (v85.13).
- [x] **Otimização de Ociosidade**: Smart Wait e Background Utility Tasks para re-análise automática (v85.12).
- [x] **Frontend v86**: Grid 2-colunas, filtros dinâmicos de UF/Partido e transparência de IA (Parecer Técnico).
- [x] **Governança Financeira e CI (Fase 7.1)**: Tesoureiro (Auditoria e DRE Automático) e Catraca no Supabase via proxy de CI.

### Infraestrutura e Monetização (Legado v48 - v64.0)
- [x] **Motor Scraper V2**: Playwright independente sem Zyte.
- [x] **Integridade Analítica**: Validação biográfica via IA (v64.0).
- [x] **Frontend Next.js 16**: App Router + Tailwind v4 + Stripe E2E.
- [x] **Fila Inteligente**: Prioridade Dinâmica (Termômetro) e Hibernação de alvos ociosos.
- [x] **Resiliencia de Dados**: Buffer de emergência Zero-Loss e fallback de schema mismatch.

---

## Em Andamento (Fase 7.2: Dashboard e Analytics Web)

### Painel Administrativo de CIs
- [x] Interface gráfica de faturamento e consumo de CIs (`/admin/financeiro`) — DRE Recharts integrado.
- [x] Integração com Recharts para DRE diário (Inflow vs Outflow) — entregue na v86.7.
- [ ] Tabelas tabulares para rastrear origem do gasto por usuário e perfil monitorado.

### Expansão Analítica
- [ ] Análise de "Shadowban" léxico: detectar quando a plataforma oculta termos específicos.
- [ ] Exportação de Dossiês em lote para contas de agências.
- [ ] Dashboard Financeiro Admin para monitoramento de custos por alvo.

---

## Próxima Fase (Fase 8: Escalabilidade, Desacoplamento e Resiliência)

### 8.1 — Desacoplamento Scraping / IA
- [x] Transformar `IGWorkerV2` em `InstagramScraperWorker` (somente coleta).
- [x] Criar `AIClassificationWorker` independente para processar o backlog.
- [x] Liberar o contexto Playwright imediatamente após a coleta, reduzindo uso de memória.

### 8.2 — Paralelismo Assíncrono
- [x] Implementar `asyncio.Semaphore(3)` no loop de processamento de alvos do Orchestrator (Auditado: superado pelo design multi-worker de produção).
- [x] Multiplicar a taxa de ingestão sem aumentar a carga no Supabase.

### 8.3 — Fila Distribuída (PGMQ)
- [ ] Integrar PGMQ (`pgmq_setup.sql` já disponível) para travas atômicas no `claim_next_target`.
- [ ] Habilitar execução multi-servidor (Cluster de Sentinelas) sem colisões de fila.

### 8.4 — Rotação de Proxies
- [c] Acoplar provedor de proxy (Bright Data / Oxylabs / ProxyRack) ao `new_context` do Playwright (Parcial: proxy estático via `.env` integrado).
- [ ] Elevar resiliência anti-Shadowban de “Médio” para “Extremo” (implementar lista de proxies rotativos).

### 8.5 — Graceful Shutdown com Checkpoint
- [c] Implementar checkpoint de comentários processados no `local_buffer` (SQLite) a cada lote (Parcial: buffer SQLite ativo no final do ciclo).
- [ ] Garantir que reinicializações do servidor não percam dados parcialmente coletados (implementar checkpoint intermediário a cada post raspado).

### 8.6 — Circuit Breaker Global
- [x] Expandir `core/circuit_breaker.py` para cobrir o Supabase e o Scraping (além da IA) (Auditado: `db_circuit_breaker` ativo).
- [x] Proteção total contra instabilidade externa em toda a infraestrutura.

---

## Próximas Ações Imediatas

1. Executar `scripts/reclassify_low_confidence.py` em produção e acompanhar taxa de acerto pós-reclassificação.
2. Refatorar `Orchestrator` com `asyncio.Semaphore(3)` para paralelismo de alvos (Fase 8.2).
3. Integrar PGMQ na `fila_coleta` com `SELECT FOR UPDATE SKIP LOCKED` para escala horizontal (Fase 8.3).

## Registro da Rodada 31/05/2026
- **Data/Hora:** 31/05/2026 13:37 (GMT‑3)
- **Objetivo:** Documentar a sessão de hoje conforme solicitado.
- **Ações realizadas:**
  - Criação de artefato de documentação da rodada.
  - Atualização de STATUS e ROADMAP com referência à rodada.
- **Próximos passos sugeridos:**
  - Incorporar métricas de desempenho no dashboard.
  - Revisar persistência técnica de logs.

## Registro da Rodada 03/06/2026
- **Data/Hora:** 03/06/2026 09:40 (GMT-3)
- **Objetivo:** Auditar a implementação do Watchdog local, verificar frentes implementadas e lacunas, e implementar terminal de logs e controle remoto no dashboard.
- **Ações realizadas:**
  - Auditamos frentes da Fase 8: confirmamos que o desacoplamento de Scraping/IA (8.1) e o Circuit Breaker global (8.6) estão totalmente operacionais. Rotação de proxies (8.4) e Zero-Loss Buffer (8.5) estão parcialmente em vigor.
  - Implementamos abas de navegação no painel central do `local_dashboard.html` ("Monitor de Discurso" e "Console de Logs") e conectamos via EventSource ao SSE `/api/stream` do Watchdog, transmitindo logs técnicos do `main_runner.py` em tempo real.
  - Adicionamos botões de controle de execução no Header do dashboard local (Play, Stop, Restart) e gatilho de inicialização manual de Ollama/LiteRT quando inativos.
- **Próximos passos sugeridos:**
  - Implementar checkpoints intermediários intra-cycle (a cada post raspado) no loop do `InstagramScraperWorker` para salvar o estado antes do final do perfil completo (Fase 8.5).
  - Implementar suporte para travas atômicas na `fila_coleta` via `SELECT FOR UPDATE SKIP LOCKED` ou com fila PGMQ no Supabase para suportar clusters horizontais de múltiplos servidores (Fase 8.3).
