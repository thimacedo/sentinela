# ROADMAP.md — Sentinela
_last_updated: 2026-06-12 | branch: main | version: v98.0_

## Concluído

### Extração Avançada e Anti-Detecção (v98.0)
- [x] **Benchmark de Scrapers**: Análise técnica de 11 repositórios (drawrowfly, MRISOON, instagram4j) para identificar gaps e melhores práticas de extração
- [x] **Fase 1 — Wait Strategy**: Substituido `asyncio.sleep` fixo por `wait_for_selector()` e `wait_for_response()` para eliminar race condition onde DOM era lido antes dos XHRs de comentários carregarem
- [x] **Fase 2 — API Interna com Paginação**: Implementado `_fetch_comments_via_api()` chamando `i.instagram.com/api/v1/media/{pk}/comments/` via `httpx` com loop `next_max_id`. CSRF/session capturados automaticamente pelo interceptador; pk resolvido via XHR cache e DOM
- [x] **Fase 3 — User-Agents Android**: Pool de UAs do app Instagram Android (Samsung, Pixel, Xiaomi, versões 275–281) integrado ao stealth profile. Peso 40% Android / 60% Web Desktop
- [x] **Sticky Proxy Binding**: `_get_next_session()` gera `sticky_proxy_id` SHA256 determinístico. `PROXY_URL_TEMPLATE` com `{SESSION_ID}` para proxies residenciais — cada sessão IG usa sempre o mesmo IP durante todo o `scrape_profile()`

### Núcleo operacional e SRE (v97.7)
- [x] Resiliência de DOM Scraper: correção e adaptação de extração de comentários baseada em links de perfil, contornando a exclusão de elementos h3 no Instagram Web (v97.7)
- [x] Diagnóstico Granular de Coleta Zero: detecção e classificação em logs/DB de causas de raspagem vazia (v97.6)
- [x] Sala de Controle e Coleta Direcionada no Dashboard local com triggerForceScrape e fila prioritária no Supabase (v97.5)
- [x] DOM Healing e Visão Computacional: regeneração de seletores CSS via Gemini 2.5 Flash e cache aprendido local (v97.2)
- [x] ScrapeAgent: Loop Cognitivo OODA, ferramentas de comportamento humano estocástico e priorização de alvos (v97.0)
- [x] Agente de SRE Autônomo: Watchdog v52.0 reativo com tool calling para autocura, restart automático por crash IPC (EPIPE) do Playwright (v96.2)
- [x] Resiliência de Inicialização: desvio Headless sem janelas para processos desanexados, bypass de setup_tray e conexão IPv6 local estabilizada (v96.2)

### Núcleo operacional antigo (v94.0 e anteriores)
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
- [x] Padronização semântica e de nomenclatura de todos os workers (`wk_`) e subagentes (`sa_`) em português brasileiro
- [x] Especialização da classe BaseSubAgent com offloading de CPU (processos) e I/O (threads)
- [x] Orquestração concorrente de subagentes analíticos efêmeros com lotes via `SELECT FOR UPDATE SKIP LOCKED`
- [x] Cascata de IA resiliente com circuit breaker local e detecção de drift analítico em SaAuditaClassificacoes
- [x] Parametrização imutável por ciclo operacional no WkColetaInstagram para mitigação de race conditions de SRE
- [x] Unificação e estabilização do watchdog_tray (Fase 5): instância única robusta (socket + boot file lock) e correção do menu Win32 travado
- [x] Otimização de IA e Fila Secundária (Fase 6): priorização do Ollama local com delay de 1s e criação do subagente SaRevisaoOnline (nuvem) para comentários suspeitos
- [x] Cobertura Total de Comandos na Bandeja do Watchdog (Fase 7): criação de entrypoints CLI de offloading para todos os subagentes/workers e menu bandeja categorizado
- [x] Otimização de Performance no Cadastro de Candidatos (Fase 8): processamento e escrita em lote (Bulk Upserts) de novos alvos e coletas no WkEscaneiaCandidatos
- [x] Refinação da Inteligência de Autocura (Fase 4): implementação real do DocFetcher (sincronização remota) e refatoração do AIAdvisor para cascata de IA resiliente
- [x] Segurança, Governança e Filtros Analíticos (Fase 10): implementação de RLS global, normalização de categorias MCA v2.2 e Shadowban Léxico no frontend
- [x] Saneamento Determinístico de Gênero e Cargo (PASA v94.0): eliminação de heurísticas nominais em prol de leitura direta por CSV e extensão da taxonomia.
- [x] Resiliência Anti-Sangria e Circuito Local (PASA v52.5): proteção financeira com fallback imediato para erro se Ollama falhar, evitando gastos não planejados na nuvem.
- [x] Refatoração Estrutural e Modularização do Frontend (Warroom): isolamento do estado (TargetCard, InvestigationModal, CommentCard) prevenindo UI freezing e re-renders sistêmicos.
- [x] Integração Nativa Voyant Tools (v92.0): Implementação da Trombone API para triagem fast-drop determinística e redução de burn rate de LLM.
- [x] Subagente Voyant (SaVoyant v92.3): Conversão da engine léxica em um Subagente autônomo com integração às bases de Linguística Forense.

- [x] Otimização de Boot e Pré-Aquecimento de Filas (v89.2): filas populadas antes do start dos workers
- [x] Otimização de Produção e Escalabilidade de IA (v90.0): implementação do Batch Processing concorrente, Escalonamento Horizontal de Workers (múltiplos classificadores) e Auto-renovação Preditiva de Sessões
- [x] Integração de IA e Estabilização de UX (v90.4): Atualização Maritaca Sabia-4, Integração Hugging Face MCP e eliminação total de popups de console no Windows via `CREATE_NO_WINDOW`.

### Coleta e scraping
- [x] Claim atômico da `fila_coleta`
- [x] Suporte a `SELECT FOR UPDATE SKIP LOCKED`
- [x] Release de locks expirados
- [x] Circuit breaker para IA
- [x] `db_circuit_breaker` para Supabase
- [x] buffer/checkpoint de scraping em estágio operacional
- [x] **Coleta Direcionada**: Interface de input para forçar coleta imediata de alvos (v97.5).

### UX e operação
- [x] local_dashboard.html refeito com UI Premium, Glassmorphism e responsividade absoluta (Mobile-first, com colunas flexíveis de `calc(100vh-290px)`, telemetria e alvos roláveis e auto-reload automático de 10s com trava de concorrência).
- [x] **Sala de Controle Granular**: UI para telemetria em tempo real baseada em banco de dados e controle de workers/subagentes modernos (v97.5).
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
- [x] checkpoint intermediário por post raspado
- [x] rotação real de proxies no Playwright
- [x] redução de ciclos com `no_comments_found`

### UI e Operação

### Otimização de Pipeline Reativo (Fase 9) - Concluído
- [x] Implementar `EventBus` centralizado para sinalização em memória (`AsyncLocalEventBus`).
- [x] Atualizar `InstagramScraperWorker` para disparar evento `NEW_DATA_AVAILABLE` após a coleta atômica.
- [x] Atualizar `AIProcessorWorker` (via `Orchestrator`) para usar `event.wait()` (Reatividade) em vez de polling constante, com timeout de segurança de 1200s.
- [x] Validar redução de latência entre coleta e classificação (reatividade comprovada: ~2.00ms de overhead real vs espera inativa).

### Resiliência de Workers (Fase 6 - SRE) - Concluído
- [x] Circuit Breakers v2 com estados finitos e backoff exponencial
- [x] Integração de resiliência profunda no `DatabaseClient` e `WkColetaInstagram`
- [x] Visualização de saúde de provedores em tempo real no Dashboard

### Inteligência
- [x] saneamento da malha de providers em `config/fallback_providers.yaml`
- [x] extração de bigramas e trigramas no `BehaviorEngine` (Fase 8)
- [x] detecção de slogans coordenados em campanhas de ataque
- [x] remover referências residuais a LiteRT do código e da operação
- [x] Caching de I/O e expurgo de modelos inoperantes (401/402/404) via `_handle_provider_error`
- [x] Estabelecer a Metodologia Vichi-Sentinela de análise linguística (POS filtering + Lematização + N-Gramas) como inegociável no projeto
- [ ] calibrar reanálise de baixa confiança com menor ruído de fallback

### Workers e orquestração
- [x] simplificar `workers/orchestrator/orchestrator.py`
- [x] unificar semântica de `no_tasks_available` entre workers ativos
- [x] reduzir duplicidade de logging, cooldown e fluxo entre ciclos
- [x] `WkPesquisaAlvos` migrado de `workers/ai/` para `workers/processors/wk_pesquisa_alvos.py` (Fase 9)

### Administração e analytics
- [x] tabelas tabulares de gasto por usuário e por perfil monitorado (Fase 7)
- [x] shadowban léxico (Fase 9.5)
- [x] exportação de dossiês em lote (integrado via API v1)

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
- [ ] **Contratar proxy residencial** (Webshare ou IPRoyal, ~$10–15/mês) e configurar `PROXY_URL_TEMPLATE` no `.env` para ativar o Sticky Proxy Binding implementado na v98.0

---

## Decisões registradas

- a fila atômica atual usa RPC + `SELECT FOR UPDATE SKIP LOCKED`
- PGMQ não é requisito atual de produção
- LiteRT não compõe mais o pipeline de processamento ativo
- `frontend/` é o frontend oficial
- `STATE.md` é a fonte de verdade operacional
- o runtime oficial de workers usa `workers/base/worker_base.py`
- entrypoints paralelos legados não devem ser reintroduzidos