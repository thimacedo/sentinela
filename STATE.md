# STATE.md — Sentinela
_last_updated: 2026-06-12 | branch: main | version: v97.6_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | ScrapeAgent (OODA loop, DOM Healing e Priorização Cognitiva) ativo. |
| Inteligência | 🟢 Operacional | Malha de IA resiliente + SaFastDrop local. |
| Dashboard | 🟢 Operacional | Painel "Decision Room" com auto-start, telemetria real via DB e Coleta Direcionada. |
| SRE / Autocura | 🟢 Operacional | Agente de SRE Autônomo (`sre_agent.py`) ativo em background com desvio headless. |

## Histórico Recente de Correções (v97.6)
1. **Coleta Monitorada e Resiliência de SRE (Concluído)**:
   - Criado o script utilitário `scratch/monitor_coleta.py` para disparar e monitorar a coleta de candidatos através de SSE (Server-Sent Events) no Watchdog.
   - Forçada a coleta do candidato prioritário `@benmendes` com prioridade 0 para furar a fila do orquestrador.
   - Validada a atuação em tempo real do SRE Agent do Watchdog, que aplicou com sucesso a autocura (restart do runner principal) ao detectar erro desconhecido e crash de IPC do Playwright (EPIPE).
   - Validada a auto-recuperação de seletores DOM (DOM Healing) via visão computacional do Gemini 2.5 Flash, seguido de cache hit para evitar gastos desnecessários de tokens.
   - Implementado o **Diagnóstico Granular de Coleta Zero**: O worker `WkColetaInstagram` agora analisa as estatísticas de raspagem e Playwright para classificar coletas vazias de forma detalhada (`no_posts_found`, `no_comments_in_posts`, `playwright_error`, `junk_detected`). O `SentinelaOrchestrator` mapeia esses erros para sugestões de autocura específicas e determinísticas salvas no banco.

## Histórico Recente de Correções (v97.5)
1. **Coleta Direcionada e Sala de Controle (Concluído)**:
   - Adicionado painel visual dinâmico com input e botão de ação instantânea no `local_dashboard.html`.
   - O botão de envio exibe feedback visual imediato (<100ms) ao operador usando spinners e ícones atualizados do Lucide.
   - Implementada a função AJAX `triggerForceScrape()` direcionada ao endpoint `/api/control/force_scrape` do Watchdog na porta `8001`.
   - Atualizado o método `add_target_to_queue()` no `core/queue_manager.py` para upsertar alvos prioritários na `fila_coleta` com prioridade `1` (fila prioritária).
   - Corrigido bug de coluna inexistente (`username`) no insert da tabela `fila_coleta` do Supabase.
   - Atualizada a lista de status de workers/subagentes no painel de Diagnóstico do `local_dashboard.html` para refletir a arquitetura moderna de microsserviços: `IG-V2` (Coleta), `AI-PROC` (IA), `SA-FAST` (Triage), `SA-REV` (Cloud) e `RESEARCHER` (Alvos).
   - Implementada a função `fetchWorkerStatus()` no frontend que consulta diretamente o histórico de batimentos na tabela `worker_metrics` do Supabase via cliente JS anônimo.
   - Integrada a telemetria ao loop do dashboard chamando `fetchWorkerStatus()` a cada pulso do dashboard (`fetchDashboard()`).
   - Removidas com segurança as referências obsoletas ao `voyant-status` no JavaScript para evitar erros fatais de `TypeError` (DOM ausente) no navegador.

## Histórico Recente de Correções (v97.2)
1. **Consolidação do DOM Healing e Visão Computacional (Concluído)**:
   - Sincronizado o nome do provedor de visão no `core/ai_service.py` de `"google_gemini"` para `"gemini-2.5-flash"` para compatibilidade com o roteador em `core/ai_service_vision_patch.py`.
   - Implementada a inicialização tardia com `_ensure_clients()` na chamada de `vision_completion` para evitar que a lista de provedores seja vazia sob chamadas diretas ou isoladas.
   - Corrigidos erros de compilação e sintaxe no `worker_adapter.py`.
   - Adicionado script de teste de integração `scratch/test_dom_healing.py`, validando com sucesso a comunicação com o Gemini Flash e o salvamento em `configs/learned_selectors.json`.

## Histórico Recente de Correções (v97.0)
1. **ScrapeAgent — Agente Cognitivo de Scraping (Concluído)**:
   - Implementação da arquitetura isolada `core/agent_scraper/` com Loop Cognitivo OODA (`agent.py`) e registro modular de 8 ferramentas (`tools.py`).
   - Lógica de auto-recuperação de seletores DOM via Visão Computacional do Gemini Flash (`dom_healing.py` e patch `core/ai_service_vision_patch.py`), preservando a chamada ao HITL legado como fallback.
   - Motor de comportamento humano estocástico com níveis `disabled`, `minimal` e `full` (`persona_mode.py`) para burlar proteções de bots no Instagram.
   - Priorização cognitiva de alvos baseada em queries de engajamento e de proporção de ódio no Supabase remoto (`cognitive_prioritizer.py`).
   - Integração completa através do adaptador de worker (`worker_adapter.py`) no worker de scraping principal `workers/scrapers/wk_coleta_instagram.py` e motor `core/instagram_scraper_v2.py`.
   - Adicionado script de validação de integração (`scratch/test_scrape_agent.py`) confirmando a execução perfeita dos ciclos OODA e consultas Supabase.

## Histórico Recente de Correções (v96.2)
1. **Agente de SRE Autônomo (Watchdog v52.0) (Concluído)**:
   - Transformação do `AutopilotManager` procedimental em um **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`).
   - Implementação de registro de ferramentas (**Tool Calling**) para autocura: `restart_worker`, `restart_main_runner`, `rotate_session` (via `SessionHealer`), `cooldown_target` (no Supabase) e `adjust_concurrency_and_jitter`.
   - Loop cognitivo OODA reativo: processa erros comuns deterministicamente a custo zero (0 tokens), e recorre a IA sob demanda (Gemini/Mistral in JSON estruturado) somente para erros de `DOM_CHANGE` ou `UNKNOWN`.
   - Expurgo completo do thread de inicialização do `VoyantServer.jar` (JVM) do watchdog, economizando recursos de CPU e RAM no boot.
   - Criado script de validação de SRE ([test_sre_agent.py](file:///c:/Projetos/sentinela/scratch/test_sre_agent.py)).
2. **Gatilho de Auto-Ativação e Estabilização de Rede (Watchdog v52.2) (Concluído)**:
   - Implementação da lógica de auto-ativação no `local_dashboard.html` quando o motor estiver com o status inoperante (`PARADO` ou `HIBERNANDO`).
   - Introdução da flag `autoStartAttempted` para evitar disparos em loop infinito de ativação caso o operador decida parar a execução intencionalmente.
   - **Correção de Conectividade IPv6 (Windows)**: Modificadas as referências críticas de `localhost:8001` para `127.0.0.1:8001` no dashboard, logs e requisições de restart internas do Watchdog, contornando a recusa de conexões em máquinas onde `localhost` resolve para o IPv6 `[::1]`.
   - **Correção de Crash Headless/Background**: Adicionado desvio no boot de `watchdog/__main__.py` para pular a criação da bandeja do sistema (`setup_tray`) se o processo for desanexado do terminal (`--background` / `--detached`), eliminando o crash silencioso de DLLs de GUI do Windows em processos sem console.
3. **Refactoring Estratégico v51.0 (Concluído)**:
   - Expurgo do Java VoyantServer e do `SaVoyant`. Substituído pelo `SaFastDrop` (léxico local em Python puro) sem dependências externas.
   - Refatoração do `SaDiagnosticaSistemas` e do `Diagnostician` para utilizar regras determinísticas locais em falhas comuns.
   - WkAplicaSugestoes: Intervalo de autocura reduzido de 30 para 10 minutos.
   - Faxina arquitetural: Remoção de 8 arquivos órfãos em `core/`.
   - Resolvido o NameError de import do `WkAplicaSugestoes` no `main_runner.py`.
