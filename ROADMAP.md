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
- [ ] Transformar `IGWorkerV2` em `InstagramScraperWorker` (somente coleta).
- [ ] Criar `AIClassificationWorker` independente para processar o backlog.
- [ ] Liberar o contexto Playwright imediatamente após a coleta, reduzindo uso de memória.

### 8.2 — Paralelismo Assíncrono
- [ ] Implementar `asyncio.Semaphore(3)` no loop de processamento de alvos do Orchestrator.
- [ ] Multiplicar a taxa de ingestão sem aumentar a carga no Supabase.

### 8.3 — Fila Distribuída (PGMQ)
- [ ] Integrar PGMQ (`pgmq_setup.sql` já disponível) para travas atômicas no `claim_next_target`.
- [ ] Habilitar execução multi-servidor (Cluster de Sentinelas) sem colisões de fila.

### 8.4 — Rotação de Proxies
- [ ] Acoplar provedor de proxy (Bright Data / Oxylabs / ProxyRack) ao `new_context` do Playwright.
- [ ] Elevar resiliência anti-Shadowban de “Médio” para “Extremo”.

### 8.5 — Graceful Shutdown com Checkpoint
- [ ] Implementar checkpoint de comentários processados no `local_buffer` (SQLite) a cada lote.
- [ ] Garantir que reinicializções do servidor não percam dados parcialmente coletados.

### 8.6 — Circuit Breaker Global
- [ ] Expandir `core/circuit_breaker.py` para cobrir o Supabase e o Scraping (além da IA).
- [ ] Proteção total contra instabilidade externa em toda a infraestrutura.

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

## Registro da Rodada 02/06/2026
- **Data/Hora:** 02/06/2026 14:47 (GMT‑3)
- **Objetivo:** Documentação oficial pós-entrega dos sub-agentes de reclassificação e pesquisa de critérios.
- **Ações realizadas:**
  - `reclassify_agent` e `researcher_agent` definidos e validados.
  - Fallback local (Ollama/LiteRT) adicionado ao reclassificador.
  - Backoff de 5s implementado para proteção das cotas de API.
  - Documentação sincronizada em todos os arquivos oficiais.
- **Próximos passos sugeridos:**
  - Iniciar Fase 8 com desacoplamento Scraping/IA e paralelismo no Orchestrator.
