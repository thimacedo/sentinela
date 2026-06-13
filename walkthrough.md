# Walkthrough — Estado Atual Auditável
_last_updated: 2026-06-12_

Este documento resume apenas o que continua válido após auditoria do código.

## 1. Pipeline ativo

- Watchdog supervisiona `main_runner.py`
- Orquestrador registra workers especializados:
  - `WkColetaInstagram` (coleta do Instagram)
  - `WkClassificaComentarios` (classificador oficial do pipeline via IA)
  - `SaRevisaoOnline` (revisão de comentários de baixa confiança na nuvem)
  - `SaFastDrop` (pré-triagem léxica local, zero Java, zero LLM)
- `WkPesquisaAlvos` (pesquisa de alvos) só entra no runtime se `RESEARCHER_MODE` estiver habilitado
- `AutopilotManager.pulse()` em background supervisiona a saúde do sistema e delega autocura ao `SREAgent`
- `WkAplicaSugestoes.start()` em background aplica automaticamente correções de configuração a cada 10 minutos
- `CloudListener.start()` fornece batimentos cardíacos (heartbeat) e aceita comandos remotos

## 2. IA ativa

Camadas observadas no código:

1. `ollama` para triagem local (opcional)
2. `maritaca` (Sabia-4) para auditoria e perícia cloud
3. `huggingface` via MCP para descoberta de modelos e datasets
4. `mistral`, `groq`, `openrouter` para refino e auditoria cruzada
5. `FallbackLLM` como recuperação de desastre

## 3. O que mudou na auditoria (v96.0)

- **Watchdog como Agente SRE Autônomo**: O `AutopilotManager` procedimental foi convertido em um **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`). O agente possui um registro de ferramentas de controle do sistema (**Tool Calling**) que executa ações como reiniciar workers específicos, reiniciar o main_runner inteiro, colocar alvos problemáticos em cooldown temporário no banco de dados, e rotacionar chaves de sessões.
- **Loop Cognitivo OODA Híbrido**: O agente resolve erros comuns localmente por regras (0 tokens) e consulta a malha de IA (Gemini/Mistral em JSON) de forma estritamente reativa sob degradação complexa (`DOM_CHANGE` ou `UNKNOWN`), garantindo burn rate mínimo de tokens.
- **Desativação Completa do VoyantServer (Java)**: O thread de inicialização de `VoyantServer.jar` (JVM) foi removido do watchdog, cortando de vez todo o vazamento de recursos no boot.
- **Validação de SRE**: Adicionado o script de teste de SRE ([test_sre_agent.py](file:///c:/Projetos/sentinela/scratch/test_sre_agent.py)) validado com 100% de sucesso.
- **Expurgo do Java VoyantServer**: O subagente `SaVoyant` foi removido e desativado. Substituído por completo pelo `SaFastDrop` (`workers/ai/sa_fast_drop.py`) que usa processamento de string puro local (`core/lexical_filter.py`), sem qualquer dependência de JVM/HTTP e com custo zero de tokens.
- **Advisor Determinístico (Zero Tokens)**: O `SaDiagnosticaSistemas` e a classe `Diagnostician` foram refatorados para analisar erros comuns por meio de regras determinísticas locais e dicionários de sugestões pré-fabricadas.
- **Autocura Acelerada**: O intervalo de execução do worker `WkAplicaSugestoes` foi reduzido de 30 minutos para 10 minutos.
- **Faxina Arquitetural de Arquivos Órfãos**: 8 arquivos obsoletos em `core/` sem qualquer importação ativa no runtime foram purgados definitivamente.
- **Correção de NameError**: Corrigida a importação em falta do `WkAplicaSugestoes` no boot do `main_runner.py`.

## 4. Consolidação do DOM Healing e Visão Computacional (v97.2)

- **Correção de Bugs e Indentação no Adaptador**: Corrigidos erros de sintaxe de merge e logging em `worker_adapter.py`.
- **Roteamento de Visão no Gemini Flash**: Mudança do nome do provedor de `"google_gemini"` para `"gemini-2.5-flash"` em `core/ai_service.py` para sincronizar perfeitamente com os nomes esperados pela API de Visão do Gemini.
- **Prevenção de Ciclo de Vida Vazio**: Adicionada a chamada `_ensure_clients()` no patch de visão (`core/ai_service_vision_patch.py`) para garantir que os providers estejam instanciados sob chamadas isoladas ao método `vision_completion`.
- **Testes de Integração Automatizados**: Criação do script de teste [test_dom_healing.py](file:///c:/Projetos/sentinela/scratch/test_dom_healing.py), que obteve sucesso na inferência de seletores HTML via visão com o modelo remoto Gemini Flash e salvou corretamente o resultado em `configs/learned_selectors.json`.

## 5. Estado da fila

O código atual já suporta:

- claim atômico
- release atômico
- desbloqueio de lock expirado
- fallback para fluxo legado quando a RPC não existe

## 5. Estado da reclassificação

O script `scripts/reclassify_low_confidence.py`:

- prioriza cloud
- pode permitir fallback local com `ollama`
- não deve mais ser descrito como fluxo LiteRT/Ollama

## 6. Estado da refatoração de workers

Já foi concluído:

- expurgo dos entrypoints e contratos legados que competiam com o runtime moderno
- absorção da lógica útil do antigo `ClassifierWorker` em `core/ai_service.py`
- atualização dos scripts operacionais auxiliares
- desativação padrão do `researcher-01`

## 7. Uso recomendado

Para iniciar trabalho novo:

1. leia `STATE.md`
2. leia `docs/SYSTEM_CONTEXT.md`
3. leia `ROADMAP.md`
4. valide no código

## 8. Frente 1 — Coleta Direcionada & Sala de Controle (v97.5)

- **Coleta Direcionada (Furar Fila)**:
  - Adicionado painel visual dinâmico com input e botão de ação instantânea no `local_dashboard.html`.
  - O botão de envio exibe feedback visual imediato (<100ms) ao operador usando spinners e ícones atualizados do Lucide.
  - Implementada a função AJAX `triggerForceScrape()` direcionada ao endpoint `/api/control/force_scrape` do Watchdog na porta `8001`.
  - Atualizado o método `add_target_to_queue()` no `core/queue_manager.py` para upsertar alvos prioritários na `fila_coleta` com prioridade `1` (fila prioritária).
  - Corrigido bug de coluna inexistente (`username`) no insert da tabela `fila_coleta` do Supabase.

- **Sala de Controle Granular (Telemetria Real)**:
  - Atualizada a lista de status de workers/subagentes no painel de Diagnóstico do `local_dashboard.html` para refletir a arquitetura moderna de microsserviços: `IG-V2` (Coleta), `AI-PROC` (IA), `SA-FAST` (Triage), `SA-REV` (Cloud) e `RESEARCHER` (Alvos).
  - Implementada a função `fetchWorkerStatus()` no frontend que consulta diretamente o histórico de batimentos na tabela `worker_metrics` do Supabase via cliente JS anônimo.
  - Integrada a telemetria ao loop do dashboard chamando `fetchWorkerStatus()` a cada pulso do dashboard (`fetchDashboard()`).
  - Removidas com segurança as referências obsoletas ao `voyant-status` no JavaScript para evitar erros fatais de `TypeError` (DOM ausente) no navegador.

- **Validação e Testes**:
  - Validada a sintaxe e compilação dos arquivos Python alterados (`core/queue_manager.py` e `watchdog/__init__.py`).
  - Executados com sucesso os testes unitários do `QueueManager` (`tests/test_queue_manager.py`).
  - Criado e executado script de integração `scratch/test_force_scrape.py` para testar ponta a ponta a inserção física de alvos com prioridade `1` no Supabase remoto e posterior limpeza de dados de teste.

## 9. Sincronização Geral de Documentação (v97.6)

- **Unificação na Mesma Etapa (v97.6)**:
  - Sincronizados e alinhados todos os arquivos `.md` do workspace à realidade atual do backend resiliente e autônomo.
  - Atualizados `README.md`, `ROADMAP.md`, `PROJECT.md` e `AGENTS_SYNC.md` na raiz para remover referências obsoletas.
  - Atualizados `docs/SYSTEM_CONTEXT.md` e `docs/ARCH_AUTOHEALING.md` para descrever o Agente SRE Autônomo, o DOM Healing via visão computacional do Gemini 2.5 Flash, o Diagnóstico Granular de Coleta Zero e o `SaFastDrop`.
- **Expurgo e Depreciação de Tecnologias Java**:
  - Marcados explicitamente como legados/depreciados os documentos `docs/workers/SA_VOYANT.md` e `docs/VOYANT_INTEGRATION.md`, registrando o expurgo da JVM Java em prol da pré-triagem Python pura.
- **Novas Documentações Criadas**:
  - Criado `docs/workers/SA_FAST_DROP.md` detalhando as responsabilidades da engine léxica local ativa.
  - Sincronizado o índice de documentação em `docs/index_documentacao.md` para unificar e direcionar as leituras de auditoria e desenvolvimento.
- **Validação de Conformidade**:
  - Verificada a coerência textual e a terminologia em pt-BR em todos os arquivos Markdown.

## 10. Resiliência do DOM Scraper (v97.7)

- **Engenharia Reversa e Correção de Seletores**:
  - Identificada mudança no DOM do Instagram Web que removeu tags `h3` nos comentários, quebrando o fallback do scraper e retornando 0 comentários.
  - Criado script de inspeção `scratch/inspect_dom.py` para mapear o HTML real do post autenticado.
  - Refatorada a função `_extract_from_dom` em `core/instagram_scraper_v2.py` para ler os usernames via links de perfil (`a[href*="/"]`) e spans com `dir="auto"`.
- **Validação e Testes**:
  - Criado o script `scratch/test_coleta_direta.py` que validou com sucesso a extração em tempo real de 10 comentários de posts ativos no perfil da `@janjalula`.

## 11. Benchmark de Scrapers + 4 Camadas Anti-Detecção (v98.0)

- **Benchmark Técnico (11 repositórios)**:
  - Analisados drawrowfly/instagram-scraper, MRISOON/no-cookie-scraper, instagram4j, postaddictme/php-scraper, houzz-scraper e outros.
  - Causa raiz principal dos 0 comentários: **ausência de paginação** (só 1 tela de comentários) + **race condition** (DOM lido antes do XHR de comentários carregar).

- **Fase 1 — Wait Strategy**:
  - Substituído `asyncio.sleep` fixo por `wait_for_selector('article time, ...')` com timeout 12s antes de ler a data do post.
  - Aguarda XHR de comentários com `wait_for_response()` (timeout 8s) antes de extrair — elimina race condition.

- **Fase 2 — API Interna com Paginação**:
  - `_handle_response()` agora captura proativamente CSRF token e session_id de todos os requests ao Instagram.
  - `_try_extract_pk_from_data()` extrai pares shortcode→pk dos XHRs interceptados e salva em `_pk_cache`.
  - `_resolve_pk_from_dom()` resolve pk via `window.__additionalDataLoaded` e scripts JSON inline.
  - `_fetch_comments_via_api()` chama `i.instagram.com/api/v1/media/{pk}/comments/` via `httpx` com loop de paginação por `next_max_id`. Extrai todos os comentários, não apenas os da primeira tela.
  - Fallback completo para pipeline DOM/XHR legacy se a API retornar vazio ou erro.

- **Fase 3 — User-Agents Android**:
  - Pool de UAs do app Instagram Android (Samsung S21/S23, Pixel 8, Xiaomi) com versões reais (275.0/278.0/281.0).
  - Peso 40% Android / 60% Web Desktop — o IG reconhece UAs Android como clientes legítimos.
  - Headers condicionais: `Sec-Ch-Ua-Mobile: ?1` e campos `x-ig-app-id` para perfis mobile.

- **Sticky Proxy Binding (análise externa validada)**:
  - `_get_next_session()` gera `sticky_proxy_id` SHA256(label)[:10] determinístico por sessão.
  - Nova variável `PROXY_URL_TEMPLATE` com `{SESSION_ID}` para proxies residenciais (Webshare/IPRoyal ~$10–15/mês).
  - `SESSION_1` → sempre IP A, `SESSION_2` → sempre IP B durante todo `scrape_profile()`.
  - Troca de sessão IG = troca de IP — sem fragmentação mid-session que sinaliza bot.
  - Retrocompatível: `PROXY_LIST` e `PROXY_URL` continuam funcionando normalmente.

## 12. Resiliência de Cache do DOM Healing (v98.1)

- **Causa Raiz do Travamento**:
  - Em casos de falha do modelo de visão (Gemini) em encontrar seletores (ex: comentários vazios devido a bloqueios de rede ou alteração no layout), a resposta da IA trazia mensagens textuais explicativas em português ("Não é possível identificar...").
  - A heurística de validação de seletores aceitava qualquer string com espaços, fazendo com que a mensagem textual fosse salva como seletor CSS no arquivo persistido `configs/learned_selectors.json`.
  - A leitura subsequente no scraper causava um `SyntaxError` de QuerySelector no Playwright, derrubando o worker e travando o runner. O Watchdog reiniciava o main_runner em loop infinito sem sucesso, pois o cache corrompido continuava persistido.

- **Mitigações Implementadas**:
  - **Validação de Sintaxe Restrita**: Criada validação regex que bloqueia caracteres acentuados ou fora do padrão ASCII de seletores CSS em `validate_css_selector`.
  - **Autocura Automática de Cache**: Se o scraper detectar que o seletor carregado de `configs/learned_selectors.json` possui um padrão inválido (acentos ou mais de 5 palavras), o arquivo de cache é deletado do disco na hora e o scraper volta aos seletores padrão.
  - **Try/Catch no Browser**: Adicionado tratamento de erro no runtime do Playwright para que seletores inválidos não quebrem a execução do script no evaluate do browser.

- **Validação**:
  - Executados testes via [test_dom_healing.py](file:///c:/Projetos/sentinela/scratch/test_dom_healing.py), demonstrando o salvamento e validação de seletores válidos com sucesso.
  - O arquivo `configs/learned_selectors.json` foi limpo e restabelecido com uma chave válida.