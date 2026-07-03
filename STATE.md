# STATE.md — Sentinela
_last_updated: 2026-07-03 | branch: main | version: v98.9_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Instagram funcional e validado. Twitter sob erro 402 (saldo Xquik zerado, esperado). Demais scrapers secundários desativados. |
| Inteligência | 🟢 Operacional | Malha de IA resiliente + SaFastDrop local + Adaptações de Failover ativos. |
| Dashboard | 🟢 Operacional | Painel "Decision Room" com telemetria real via DB e Coleta Direcionada. |
| SRE / Autocura | 🟢 Operacional | Agente de SRE Autônomo (`sre_agent.py`) verificado e 100% funcional. |

## Histórico Recente de Correções (v98.9)
1. **Auditoria Geral e Correções Críticas de Persistência (Concluído)**:
   - **Correção de Chaves no Upsert:** Ajustadas as chamadas de `.upsert()` em [local_buffer.py](file:///c:/projetos/sentinela/core/local_buffer.py), [wk_coleta_instagram.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_instagram.py), [wk_coleta_twitter.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_twitter.py) e [cloud_scrape_cycle.py](file:///c:/projetos/sentinela/scripts/cloud_scrape_cycle.py) para utilizar `on_conflict="id_externo"`, respeitando a restrição única correta do Supabase remoto e evitando falhas de chave primária duplicada.
   - **Remoção de Campos Órfãos no Sync:** Removido o campo inexistente `is_spam` do mapeamento de dados do Instagram. Atualizada a lógica de autocura/fallback em [local_buffer.py](file:///c:/projetos/sentinela/core/local_buffer.py) para remover os campos `is_spam` e `sentimento` antes da persistência, resolvendo o erro `PGRST204` de Schema mismatch.
   - **Ajuste de Timeout de Auditoria:** Ampliado o timeout do ciclo do Instagram no script de auditoria rápida [audit_scrapers.py](file:///c:/projetos/sentinela/scratch/audit_scrapers.py) para 120s, permitindo o tempo de inicialização do Playwright e carregamento de rede.
   - **Verificação Geral de Agentes:** Validados os ciclos OODA e integrações de [ScrapeAgent](file:///c:/projetos/sentinela/core/agent_scraper/agent.py) e [SREAgent](file:///c:/projetos/sentinela/core/autopilot/sre_agent.py) via scripts unitários e de integração, com 100% de sucesso.
   - **Envio de Ciclos via Ntfy & Correção Unicode:** Criado o script controlado [monitor_ciclo_coleta.py](file:///c:/projetos/sentinela/scratch/monitor_ciclo_coleta.py) para rodar a extração e classificação de forma atômica e enviar os resultados ao canal `sentinela` no `ntfy.sh`. Identificado e corrigido bug de codificação `'latin-1'` no [ntfy_client.py](file:///c:/projetos/sentinela/core/ntfy_client.py) usando codificação de MIME Header no `Title` e `Tags` para suportar emojis e caracteres acentuados sem estourar o HTTP requests.
   - **Patches de Autocura e Falha de Extração:** Criada a exceção customizada [ExtractionFailure](file:///c:/projetos/sentinela/core/exceptions.py) e integrada ao final de `_scrape_post` em [instagram_scraper_v2.py](file:///c:/projetos/sentinela/core/instagram_scraper_v2.py) para notificar falhas estruturais de forma não-silenciosa. Aplicada a liberação atômica `_release_atomic` em `rotate_target` no [queue_manager.py](file:///c:/projetos/sentinela/core/queue_manager.py) e configurado o retorno com chaves de sucesso/contagens no `scrape_profile`, resolvendo todos os comportamentos de alvos presos na fila. Adicionada detecção ativa e autocura de login walls silenciosos no DOM (identificando campos de login) quando o Instagram impede o carregamento dos posts sem redirecionar a URL.

## Histórico Recente de Correções (v98.8)
1. **Eliminação de Módulos de Baixa Relevância (Concluído)**:
   - **Remoção de Arquivos:** Excluídos permanentemente os arquivos de workers de coleta secundários: [wk_coleta_bluesky.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_bluesky.py), [wk_coleta_reddit.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_reddit.py) e [wk_coleta_telegram.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_telegram.py).
   - **Limpeza do Orquestrador:** Modificado o orquestrador principal [main_runner.py](file:///c:/projetos/sentinela/main_runner.py) para omitir os imports, registros de execução e loggers correspondentes a essas 3 plataformas, reduzindo overhead de inicialização e dependências órfãs.
   - **Limpeza de Scripts Auxiliares:** Atualizado o script de auditoria rápida [audit_scrapers.py](file:///c:/projetos/sentinela/scratch/audit_scrapers.py) para monitorar apenas as coletas ativas (Twitter e Instagram).


## Histórico Recente de Correções (v98.7)
1. **Auditoria e Diagnóstico Completo de Scrapers (Concluído)**:
   - **Script de Diagnóstico Rápido:** Criado o script [audit_scrapers.py](file:///c:/projetos/sentinela/scratch/audit_scrapers.py) para auditar concorrentemente e com timeouts seguros os setups e ciclos de todas as plataformas de coleta (Instagram, Bluesky, Reddit, Telegram, Twitter/X).
   - **Identificação de Problemas:**
     - *Twitter/X (Xquik):* Identificado erro **402 Payment Required** (Credits = 0) na conta cadastrada no `.env`.
     - *Bluesky, Reddit, Telegram:* Identificada falha de `auth_missing` causada por variáveis de ambiente ausentes no `.env` (`BSKY_PASS`, `REDDIT_CLIENT_ID`/`SECRET`, `TG_API_ID`/`HASH`).
     - *Instagram:* Identificada latência e expirações de sessão no Playwright Web.
   - **Validação de Playwright:** Criado o script [test_playwright.py](file:///c:/projetos/sentinela/scratch/test_playwright.py) que confirmou o pleno funcionamento do navegador Chromium headless local.
   - **Relatório Forense:** Gerado o relatório de coleta em [analise_coleta_sentinela.md](file:///C:/Users/THIAGO/.gemini/antigravity/brain/cf932e9c-ddda-4639-b3fc-d8e478b1ea52/analise_coleta_sentinela.md).


## Histórico Recente de Correções (v98.6)
1. **Integração do Stanford NLP (Stanza, DSPy e GloVe) (Concluído)**:
   - **Stanza Engine:** Implementada a classe `StanzaNLPEngine` (`core/stanza_nlp.py`) para processamento linguístico em CPU (`use_gpu=False`). Realiza lematização e extração de POS tags do Método Vichi-Sentinela. Os metadados são persistidos em tempo real na nova coluna `analise_linguistica` (JSONB) no Supabase remoto.
   - **Geração de N-Gramas:** A contagem pericial de bigramas e trigramas agora respeita estritamente os limites de sentenças delimitados pela rede neural do Stanza.
   - **DSPy Integration:** Estruturada a assinatura `ClassificarComentarioPASA` (`core/dspy_integration.py`) baseada no protocolo MCA v2.3. Um adaptador de LM customizado (`SentinelaLM`) mapeia as chamadas estruturadas do DSPy para a cascata interna de provedores do `ai_service`, preservando circuit breakers, retry e redundâncias.
   - **DataMiner & GloVe:** Refatorada a clusterização temática do `DataMiner` (`processing/data_miner.py`) para operar sobre os lemmas unificados. Adicionado suporte em memória a embeddings densos locais do GloVe, com fallback automático a TF-IDF lematizado.
   - **Migration DDL:** Aplicada com sucesso a coluna `analise_linguistica` no Supabase remoto via injeção benigna na RPC `exec_sql`.

## Histórico Recente de Correções (v98.5)
1. **Integração do Twitter/X Scraper - Xquik (Concluído)**:
   - **Novo Worker:** Desenvolvida a classe `WkColetaTwitter` (`workers/scrapers/wk_coleta_twitter.py`) para coleta de publicações de candidatos via API Xquik. O worker suporta autenticação via chave `XQUIK_API_KEY` do `.env`.
   - **Resiliência e Circuit Breaker:** Integrado o status do worker do Twitter ao `scraper_circuit_breaker` de rede e ao fluxo do `QueueManager` (locks atômicos de concorrência e release/rotate automáticos).
   - **Padrão de Coleta:** Mapeados os tweets coletados para o schema `comentarios` do banco Supabase sob a plataforma `TWITTER` com limpeza de caracteres nulos, filtragem léxica e detecção de bots coordenada via `behavior_engine`.
   - **Registro Principal:** Registrada a classe `WkColetaTwitter` de forma ativa nas instâncias do orquestrador em `main_runner.py`.
2. **Correção de Concorrência Crítica de Locks na Fila (Concluído)**:
   - **Problema:** O método `pre_warm_queues()` do `QueueManager` limpava **todos** os locks de coleta da fila atômica (`timeout_minutes=0`) indiscriminadamente. Como ele era chamado periodicamente a cada 10 ciclos de autocura do orquestrador principal (`_perform_self_healing`), ele derrubava locks legítimos e ativos de scrapers em andamento, causando colisões de coleta.
   - **Correção:** Refatorado `pre_warm_queues()` para aceitar o argumento `force_release`. No boot inicial do orquestrador, ele limpa tudo (`force_release=True`/`timeout_minutes=0`). Nas limpezas periódicas subsequentes do orquestrador, ele limpa apenas locks expirados por inatividade há mais de 30 minutos (`force_release=False`/`timeout_minutes=30`).

## Histórico Recente de Correções (v98.4)
1. **Resiliência e Correção de Bugs do ScrapeAgent Stealth (Concluído)**:
   - **Correção 1:** Corrigido bug de `UnboundLocalError: cannot access local variable 'time'` no login do Instagram Stealth (`instagram_scraper/scrape_stealth.py`) causado pelo sombreamento de escopo local da variável `time` por causa de um import local redundante no bloco except de debug.
   - **Correção 2:** Adicionado método `publish` compatível e tolerante no barramento local (`core/event_bus.py` - `AsyncLocalEventBus`) para evitar quebras por `AttributeError` sob chamadas de controle ou sinalizações in-memory (como as emitidas pelo SRE Agent e Watchdog).
   - **Correção 3:** Atualizada a chamada de reatividade em `workers/ai/sa_instagram_stealth.py` para invocar diretamente `local_bus.signal_new_data()` em vez de chamar `.publish` in-memory.
   - **Correção 4:** Corrigidas as inserções de eventos de telemetria de mudança de estado do circuit breaker na tabela `system_events` (`core/circuit_breaker.py`), removendo as colunas inexistentes `status` e `source_module`, adequando os campos ao schema real da tabela (`source`, `severity`, `description`, `metadata`).

## Histórico Recente de Correções (v98.3)
1. **Auditoria Crítica do ScrapeAgent (Concluído)**:
   - **Correção 1:** Adicionado o import de `Any` em `wk_coleta_instagram.py` para prevenir `NameError` no worker.
   - **Correção 2:** Ajustada a atribuição incorreta de `session.blocked` para `session.blocked_until` em `instagram_scraper_v2.py` ao detectar muros de login, garantindo o cooldown efetivo da sessão no pool.
   - **Correção 3:** Inserido o campo `tier_used` na montagem do dict `safe_c`, prevenindo `KeyError` no fallback SQLite.
   - **Correção 4:** O `shutdown_event` agora é propagado corretamente no método `setup()` do worker para o scraper instanciado.
   - **Correção 5:** O parser de credenciais de proxy agora utiliza `rsplit("@", 1)` e `split(":", 1)`, impedindo crashes com proxies cujas credenciais contêm `:` ou URLs com múltiplos `@`.
   - **Correção 6:** O cálculo de horário noturno agora utiliza `zoneinfo.ZoneInfo("America/Fortaleza")`, prevenindo bloqueios prematuros motivados pelo timezone UTC do servidor host.
   - **Correção 7:** Aplicado fallback em `texto_bruto` garantindo a persistência do texto caso ele venha derivado das extrações DOM (`texto`).

## Histórico Recente de Correções (v98.2)
1. **Refatoração Tipo-Segura (Type-Safe) de Exceções e Sinais de Controle (Concluído)**:
   - **Exceções customizadas**: Criados arquivos de exceções customizadas em `core/exceptions.py`, substituindo *string matching* de erros no orquestrador por tipos específicos (`DOMHealerRestartSignal`, `SessionExpiredError`, `ChallengeRequiredError`, etc.).
   - **Cura funcional de DOM**: Refatorado o `dom_healing.py` e o seletor de cura para instanciar e utilizar o `SelectorValidator` (`core/selector_validator.py`), testando os seletores gerados pela IA no DOM vivo da página e retornando erros caso falhem em visibilidade/conteúdo.
   - **Evitando Falsos Bloqueios (Circuit Breaker)**: O Worker (`wk_coleta_instagram.py`) e o Adaptador (`worker_adapter.py`) foram atualizados para interceptar sinais de controle como `DOMHealerRestartSignal` e classificá-los semântica e imediatamente como status `PENDENTE` em vez de falhas de scraping, impedindo que o auto-healing acione falsos-positivos no circuit breaker de rede.
   - **Métricas e Monitoramento**: Desenvolvidas as classes `MetricsCollector` em `core/scrape_metrics.py` e `HealingAttemptTracker` em `core/healing_attempt_tracker.py` para limitar tentativas de healing consecutivas e salvar relatórios detalhados em disco JSON.
   - **Login Wall e Precedência**: Criado o `LoginWallDetector` (`core/login_wall_detector.py`) com regex robustas de URL, títulos e conteúdo, corrigindo bugs latentes de precedência de operadores lógicos (`and`/`or` no check antigo).
   - **Validação**: Todos os testes unitários e de integração básicos (`test_dom_healing.py` e `test_scrape_agent.py`) foram executados e passaram com 100% de sucesso.

## Histórico Recente de Correções (v98.1)
1. **Resiliência de Cache do DOM Healing (Concluído)**:
   - **Causa Raiz**: O modelo de visão Gemini Flash, ao não identificar o container de comentários, retornava mensagens textuais em português (ex: *"Não é possível identificar o container CSS de 'comment"*). Devido a uma falha na heurística de validação de seletores (que aceitava espaços), a mensagem era salva como um seletor CSS no arquivo `configs/learned_selectors.json`.
   - **Envenenamento de Cache**: O scraper varia o seletor aprendido do cache e tentava executá-lo no Playwright. Isso causava um `SyntaxError` Javascript fatal que derrubava o worker. O watchdog então reiniciava o main_runner em loop infinito (pois o cache em disco continuava corrompido).
   - **Correção 1 — Validação Estrita**: Refatorada a função `validate_css_selector` no `core/agent_scraper/dom_healing.py` para proibir qualquer caractere fora da tabela ASCII padrão de CSS (bloqueando acentuação) e limitar a no máximo 5 tokens com espaço.
   - **Correção 2 — Autocura de Cache**: Atualizado o `scroll_comment_column` no `core/instagram_scraper_v2.py` para validar o seletor lido do arquivo no Python. Se for detectado um formato inválido, ele limpa o arquivo no disco de forma proativa.
   - **Correção 3 — Tratamento de Exceções**: Adicionado bloco `try/catch` no Javascript do `page.evaluate` para impedir que seletores incorretos causem uma quebra catastrófica de processamento no Playwright.
   - **Validação**: Executado com sucesso o script `scratch/test_dom_healing.py` provando o funcionamento correto e salvamento de seletor válido.
2. **Tratamento do Fluxo de Exceção do DOM Healing (Concluído)**:
   - **Causa Raiz**: Ao curar o DOM com sucesso ou ignorar o HITL em background/YOLO mode, o scraper disparava `RuntimeError("hitl_intervention_completed_restarting")`. Essa exceção propagava e era capturada como falha comum de rede/bloqueio, consumindo tentativas de retry do scraper e marcando o alvo como falho.
   - **Correção**: Adicionado tratamento específico para a exceção `"hitl_intervention_completed_restarting"` no loop principal do scraper em [instagram_scraper_v2.py](file:///c:/Projetos/sentinela/core/instagram_scraper_v2.py#L570-L574). Agora a tentativa é reiniciada imediatamente sem penalidades no contador de retries ou backoffs exponenciais longos.
   - **Validação**: Validada a execução e resiliência da raspagem através do script [test_coleta_direta.py](file:///c:/Projetos/sentinela/scratch/test_coleta_direta.py), confirmando extração correta sob sessões ativas sem disparar loops ou crashes.

## Histórico Recente de Correções (v98.0)
1. **Benchmark de Scrapers + 4 Camadas Anti-Detecção (Concluído)**:
   - Realizado benchmark técnico de 11 repositórios de scraping do Instagram (drawrowfly, MRISOON, instagram4j e outros).
   - **Fase 1 — Wait Strategy**: Substituído `asyncio.sleep` fixo por `page.wait_for_selector()` e `page.wait_for_response()` no `_scrape_post()`, eliminando race conditions onde o DOM era lido antes dos comentários XHR carregarem.
   - **Fase 2 — API Interna com Paginação**: Implementado `_fetch_comments_via_api()` que chama `i.instagram.com/api/v1/media/{pk}/comments/` via `httpx` com loop de paginação por `next_max_id`. CSRF token e session_id são capturados automaticamente pelo `_handle_response()`. Resolve `pk` do post via cache XHR ou extração DOM (`_resolve_pk_from_dom()`). Fallback para DOM/XHR legacy se a API retornar 0.
   - **Fase 3 — User-Agents Android**: Adicionado pool de User-Agents do app Android do Instagram ao `_generate_stealth_profile()` (Samsung Galaxy, Pixel 8, Xiaomi). Peso 40% Android / 60% Web Desktop. Headers Mobile (`x-ig-app-id`, `Sec-Ch-Ua-Mobile`) ajustados por tipo de perfil.
   - **Sticky Proxy Binding**: `_get_next_session()` agora deriva um `sticky_proxy_id` SHA256 determinístico por sessão. Suporte ao `PROXY_URL_TEMPLATE` com `{SESSION_ID}` para proxies residenciais (Webshare/IPRoyal). Cada sessão IG sempre usa o mesmo IP residencial durante todo o `scrape_profile()`, eliminando fragmentação de IP que sinaliza bot.

## Histórico Recente de Correções (v97.7)
1. **Resiliência do DOM Scraper (Instagram Web v97.7) (Concluído)**:
   - Identificada a causa raiz de falsos-positivos de 0 comentários na coleta: o Instagram Web removeu o uso de tags `h3` na representação de usernames dos autores dos comentários.
   - A indisponibilidade da API do Gemini 2.5 Flash de visão (erro HTTP 503 por sobrecarga) impediu a auto-recuperação visual via DOM Healing, ativando HITL fallbacks repetitivos.
   - Refatorada a função `_extract_from_dom` no `core/instagram_scraper_v2.py` substituindo seletores baseados em `h3` por um algoritmo robusto de detecção de links de usernames de perfis (`a[href*="/"]`) e spans com `dir="auto"`.
   - Validada a extração bem-sucedida em tempo real via script `scratch/test_coleta_direta.py` coletando posts ativos do perfil `@janjalula` sem erros e sem custos extras.

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
