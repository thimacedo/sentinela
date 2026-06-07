# STATE.md — Sentinela
_last_updated: 2026-06-05 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo com ritmo conservador (10 a 30 min de cooldown) focado em constância e prevenção de bloqueios |
| Inteligência | 🟢 Operacional | Fila de processamento cíclico cadenciada e rotativa Round-Robin baseada em chaves de IA cloud (.env) e ollama local |
| Analytics de Rede | 🟢 Operacional | Subagente `SaMineracaoRedes` ativo de forma reativa/sob demanda |
| Financeiro | 🟢 Operacional | Subagente `SaAuditoriaFinanceira` ativo de forma reativa/sob demanda, com telemetria e burn rate diário de IA |
| Watchdog Local | 🟢 Operacional | Porta 8001, SSE, controle remoto, dashboard local premium e monitor dinâmico de chaves de IA ativo |
| Frontend oficial | 🟢 Estável | `frontend/` é o frontend oficial, com integração de relatórios reais e CTAs conectados |

## Verdades operacionais auditadas

1. O backend é iniciado por `main_runner.py`.
2. O watchdog local supervisiona a execução, gerencia os status dinâmicos de IA e publica logs por SSE.
3. O classificador oficial em produção é `workers/processors/wk_classifica_comentarios.py`.
4. A trava de instância única no `main_runner.py` e `watchdog` impede a execução redundante de múltiplos processos usando caminhos de lock absoluto baseados em `PROJECT_ROOT`.
5. O `cleanup_orphans()` é executado preventivamente no boot do `main_runner.py`, no setup de cada worker (`WkColetaInstagram` e `WkPesquisaAlvos`), no `run_all()` do orquestrador e ciclicamente na sua autocura.
6. A cadência de ciclos de processamento de todos os workers e agentes é lenta e constante: **10 min** (gold), **20 min** (silver/idle) e **30 min** (bronze) para proteção de sessões e cotas.
7. LiteRT não compõe mais o pipeline ativo de processamento.
8. A fila distribuída real hoje usa travas atômicas com `SELECT FOR UPDATE SKIP LOCKED`.
9. PGMQ permanece como possibilidade futura, não como base atual do runtime.
10. `frontend/` é o frontend oficial.
11. `local_dashboard.html` é o painel operacional local do watchdog, contendo seção de "Serviços de IA" dinâmica que exibe bolinhas cinzas (`bg-slate-600`) para serviços Cloud não configurados (status `DESATIVADO`).

## Achados da auditoria documental

### Certo

- watchdog com start/stop/restart e SSE
- `ollama` ativo
- `WkClassificaComentarios` como classificador central
- `WkPesquisaAlvos` com ativação controlada por `RESEARCHER_MODE`
- `queue_manager` com claim atômico
- Stripe com fallback mock controlado por flag (`STRIPE_ALLOW_MOCK_PAYMENTS`)
- AdSense com retry defensivo para evitar race condition de carregamento
- página de relatórios ligada ao backend FastAPI (`/api/v1/dossiers`)

### Refatorações de workers já concluídas

- `ClassifierWorker` foi removido do runtime e sua lógica útil de padrão ouro foi absorvida por `core/ai_service.py`
- entrypoints legados paralelos foram expurgados:
  - `core/orquestrador.py`
  - `workers/core/base_worker.py`
  - `workers/processors/queue_manager.py`
  - `workers/processors/search_watcher.py`
  - `workers/processors/cleanup_worker.py`
  - `workers/analytics/report_worker.py`
  - `workers/official_solenya_daemon.py`
  - `workers/orchestrator_long_run.py`
  - `workers/schedule_long_scrape.py`
- `researcher-01` não sobe mais por padrão sem backlog real
- `scripts/work_session.py` e `scripts/night_watch_pipeline.sh` foram alinhados ao runtime moderno

### Errado nos documentos antigos

- LiteRT descrito como engine ativa
- PGMQ descrito como implantado
- `proposta_frontend/` como frontend oficial
- Gemini tratado como classificador principal de produção

### Risco atual

O principal risco operacional hoje é a expiração ou bloqueio de cookies da sessão do Instagram (gerando respostas de feeds vazios):
- Necessidade de renovação periódica das cookies via script interativo no terminal.
- A mitigação do risco de taxa foi aplicada aumentando os cooldowns de todos os ciclos para 10 a 30 minutos de descanso.

## Situação da IA

### Ativo

- **Fila Circular Unificada**: Local (Ollama) e Cloud (Mistral, Groq, etc.) dividem o mesmo loop com rotacionamento Round-Robin.
- **Parametrização Diferenciada (Método Vichi-Sentinela Inegociável)**:
  - **Cloud Providers**: Consomem o prompt completo enriquecido com `PADRONIZACAO_LINGUISTICA_ANALITICA.md` (PASA v16.3), `custom_rules.json` e o `classifier_gold_dataset.json`, aplicando rigorosamente a Metodologia Vichi-Sentinela (lematização de termos agressivos, POS filtering focado em verbos/substantivos/adjetivos ofensivos e contagem de N-Gramas para detecção de slogans coordenados).
  - **Local (Ollama)**: Utiliza uma versão **reduzida** e otimizada baseada nos pilares do método Vichi para triagem rápida, visando evitar o *context bloat*, garantir respostas em < 2s e marcar como `"SUSPEITO"` qualquer comentário com desvios léxicos e ofensas para revisão profunda na nuvem.
- **Termômetro de Alvos (PASA v88.2)**: Reativada a classificação automática de temperatura (Frio/Morno/Quente) no fluxo de coleta. O status do alvo agora é atualizado imediatamente após a extração, garantindo o posicionamento correto na fila de prioridade.
- **Restrição de Reanálise**: A re-análise de comentários de baixa confiança permanece ativa para garantir a qualidade analítica, porém ela foi **desacoplada** do status do alvo. O termômetro do candidato (Frio/Morno/Quente) agora é atualizado **exclusivamente** durante os ciclos de coleta (scrape), baseando-se no timing e volume de dados frescos.
- **Circuit Breaker & Poda**: Provedores com erro 401/403 (chave/cota) são removidos da malha ativa em tempo real; erros 429 (rate limit) geram suspensão temporária de 60s.
- **Cache de I/O**: Prompts e datasets locais são carregados na RAM no boot para zero overhead de leitura em disco.
- **SaConsultaBanco (Subagente de dados)**: Integrado para consultas SQL e buscas FTS5 via porta 8002.

### Saneado

- Referências residuais a LiteRT removidas do pipeline de processamento ativo.
- Malha de fallback reordenada e sem provedores indisponíveis.

## Situação da fila

### Ativo no código

- claim atômico
- release atômico
- stale lock release
- fallback compatível quando RPC não existe

### Implicação

A documentação deve tratar a fila atômica como realidade atual.
PGMQ deve aparecer apenas como hipótese futura.

## Situação da documentação

### Fonte de verdade

- `STATE.md`
- `ROADMAP.md`
- `docs/SYSTEM_CONTEXT.md`
- `docs/DOCUMENTATION_AUDIT.md`

### Contexto histórico

- `docs/archive/**`
- `docs/superpowers/**`
- arquitetura PASA antiga

## Auditoria Operacional e Transparência (v88.9 / v89.0 - 2026-06-05)

### Diagnóstico de Colapso (Coleta)
- **Status Real**: 🔴 **COLAPSO DE COLETA (Corrigido na v89.0)**. 
- **Causa Raiz 1 (Falso Positivo de Estabilidade)**: O sistema entrou em um "crash loop" silencioso devido à ausência da biblioteca `psutil` no ambiente virtual e a uma falha lógica no `core/process_cleaner.py`, que levava o `main_runner` a cometer "suicídio" (matar a si próprio) logo no boot. O Watchdog reiniciava o processo infinitamente, omitindo os logs para evitar poluição no terminal, o que gerou um falso reporte de "Operacional".
- **Causa Raiz 2 (Dashboard Vazio)**: O frontend (`local_dashboard.html`) utilizava caminhos relativos (`/api/metrics`) que quebravam silenciosamente por problemas de CORS/Origem quando o arquivo era aberto diretamente via protocolo `file://` no navegador.
- **Impacto**: O backlog de 13.8k comentários não estava recebendo novos dados. O AIAdvisor gerou **68 sugestões de autocura** pendentes, apontando falhas de extração.

### Status da Camada de IA
- **Status**: 🟡 **DEGRADADO (Corrigido na v90.1)**.
- **Observações**: Malha de IA enfrentava exaustão de cota massiva. **Maritaca (403)**, **DeepSeek (402)** e **Groq (429)** sob Circuit Breaker. A operação estava sendo sustentada pelo **Ollama local** e **Mistral**, resultando em menor throughput. O modelo **Gemini-1.5-flash** estava descontinuado e foi atualizado para **Gemini-2.5-flash** na v90.1, restaurando a comunicação com a API do Google.
- O modelo do Ollama (`llama3.2:1b`) não estava instalado, causando erros locais, mas já foi puxado e as classificações operam sem falhas locais.

### Melhorias de Resiliência e UX (v89.0)
- **Filtro de Ruído no Terminal**: Implementamos supressão inteligente no terminal do Watchdog. Erros previsíveis de rede (429, 403, 401) agora são omitidos do stdout para evitar a "enxurrada de erros", mas permanecem visíveis no Dashboard SSE.
- **Alertas Críticos no Dashboard**: Criamos um painel de alertas de alta visibilidade no `local_dashboard.html`. O sistema agora valida e exibe explicitamente o estado de "SESSÕES EXPIRADAS" e "MALHA DE IA DEGRADADA".
- **Resiliência do Frontend**: O Dashboard foi refatorado para detectar automaticamente o ambiente de execução (`file://` vs `http://`) e injetar o host `http://localhost:8001` em todas as chamadas de Fetch e Server-Sent Events, garantindo que os dados apareçam mesmo ao abrir o HTML direto no desktop.
- **Boot Seguro (ProcessCleaner)**: Corrigida a lógica de proteção de PIDs. O sistema agora limpa zumbis sem interromper a thread principal.

## Otimização de Produção e Cura da Malha de IA (v90.0 - 2026-06-05)

### 1. Escalonamento Horizontal de Classificadores
- Aumentada a capacidade de processamento com a instância simultânea de múltiplos classificadores de inteligência artificial (`ai-processor-01` e `ai-processor-02`), impulsionados pela variável de ambiente `NUM_AI_WORKERS=2`. Isso duplica o throughput de esvaziamento do backlog primário e suporta concorrência assíncrona nas requisições aos modelos locais e em nuvem.

### 2. Implementação Híbrida de Batching / Paralelismo Local
- O endpoint `run_batch_classification` agora processa tarefas concorrentemente com uso de semáforos (`asyncio.Semaphore(5)`), limitando a pressão sobre APIs pagas (e Ollama local) ao enviar *batches* paralelos. Isso aumenta drasticamente o limite operacional em comparação ao antigo loop linear síncrono. Fallback suave é mantido na conversão JSON.

### 3. Pipeline Reativo (Event-Driven) Consolidado
- Os workers e a malha de IA foram acoplados pelo `EventBus` (`core.event_bus`). A lógica implementa reatividade em tempo real: assim que a coleta salva um dado classificado como "SUSPEITO", a fila secundária de *Revisão Online* acorda do estado `Idle` sem a necessidade de esperar timeouts (polling) ociosos. 

### 4. Gestão Preditiva de Sessões de Coleta
- Implementado um check proativo no `health_check.py` que lê o banco de dados diretamente: se a proporção de contas `active` chegar a 0% (todas expiradas ou com login wall), o Sentinel engatilha automaticamente um script shell em background (`export_playwright_cookies.py`) para auto-renovação preditiva dos cookies sem travar o orchestrator.

## Integração BrowserAct MCP e Fallback CDP (v90.2)
- **Integração de Credenciais**: A chave da API de nuvem do BrowserAct foi recebida e fixada no ambiente como `BROWSERACT_API_KEY`.
- **Mitigação de Erros 401**: O sistema tentou conectar via WebSocket do Chrome DevTools Protocol (`connect_over_cdp`) nativamente, mas enfrentou erros *Unauthorized 401*. Foi diagnosticado que parâmetros como `?token=` devem ser substituídos por `?apiKey=` nas futuras versões do BrowserAct ou que seu plano requer autorização de IPs e Workflow explícito.
- **Configuração de Servidor MCP**: Em resposta ao problema, retrocedemos o Playwright para instância local no backend Python (`instagram_scraper_v2.py`) e acoplamos a plataforma **BrowserAct via MCP Server** no arquivo `.gemini/settings.json`. O Gemini CLI agora possui acesso nativo aos nós do BrowserAct (List Workflows, Create Tasks) via Model Context Protocol sem precisar abrir portas WebSocket manualmente no código local.

## Estabilização e Atualização de Provedores (v90.4 - 2026-06-05)

### 1. Atualização Maritaca AI (Sabia-4)
- **Nova Chave de API**: Integrada a nova credencial Maritaca via `.env`.
- **Capacidade Operacional**: Modelo configurado para `sabia-4` com suporte a 60 RPM (Requisições por Minuto). A malha de IA (`AIService`) agora utiliza este modelo como um dos provedores primários de auditoria.

### 2. Integração Hugging Face Hub (MCP)
- **Instalação**: Extensão `huggingface` instalada no Gemini CLI.
- **Autenticação**: Token de API configurado no `.env` como `HF_TOKEN` e injetado nos headers do servidor MCP no arquivo `.gemini/settings.json` via variável de ambiente. O agente agora possui acesso direto ao ecossistema Hugging Face (Modelos, Datasets e Spaces).

### 2. Correção de Foco e UX (Anti-Popup Windows)
- **CREATE_NO_WINDOW**: Aplicada a flag de sistema `0x08000000` em todas as chamadas de subprocessos no Windows, incluindo o orquestrador (`watchdog`), verificadores de saúde (`core.health_check`), limpadores de processos (`core.process_cleaner`) e até mesmo nos gatilhos manuais da bandeja gráfica (`watchdog/__main__.py`). Isso elimina definitivamente o problema de janelas pretas de terminal (cmd.exe) abrindo e roubando o foco do usuário durante a operação em background.
- **Headless Enforcement**: Reforçada a política de execução invisível para todos os workers de coleta, garantindo que o sistema opere de forma 100% silenciosa.

### 3. Estabilização de Runtime e Monitoramento (v90.5 - 2026-06-06)
- **Eliminação de Zumbis**: Identificada e corrigida uma condição de corrida que gerava instâncias duplicadas do `main_runner.py` durante o boot do Watchdog. O sistema agora utiliza o `GuardLocker` com maior rigor, garantindo um único orquestrador ativo.
- **Visibilidade de IA**: Ativado o nível de log `INFO` para `core.ai_service` e `worker.ai_processor`, permitindo o acompanhamento detalhado da vazão de classificação no terminal e dashboard.
- **Início do Ciclo de 24h**: Iniciado monitoramento contínuo de 24h para validação de estresse. Vazão inicial estabilizada em ~25 classificações/minuto com suporte total da malha Maritaca Sabia-4.

## Estabilização v90.7 e Gestão de IA (2026-06-06)

### 1. Robustez do GuardLocker (Anti-Shim)
- Refatoração profunda do `core/guard_locker.py` para utilizar `wmic` no Windows, permitindo a limpeza agressiva de "shim processes" (processos órfãos de interpretadores Python) que ficavam presos no boot.
- Implementação de `CREATE_NO_WINDOW` em todas as chamadas de subprocesso do locker para garantir operação 100% invisível.

### 2. Gestão de IA via Dashboard
- Implementada interface visual (`local_dashboard.html`) para gestão de chaves de API.
- Criados endpoints no Watchdog (`/api/ai/details` e `/api/ai/update_key`) que permitem atualizar o arquivo `.env` e testar a conectividade dos provedores em tempo real sem acesso direto ao terminal.
- Adicionado alerta de "Malha Degradada" no dashboard quando provedores cloud estão sob rate limit ou bloqueio.

### 3. Calibragem de Resiliência de IA
- Aumentado o backoff de erro 429 (Rate Limit) de 60s para **300s (5 minutos)** em `core/ai_service.py`. Isso evita a queima desnecessária de tokens de auditoria e respeita melhor os limites de provedores gratuitos/tiers básicos.

### 4. Manutenção de Banco de Dados
- Executada purga total da tabela `worker_suggestions` (1399 registros removidos). As sugestões acumuladas eram sintomas de colapsos de sessão anteriores e geravam ruído analítico desnecessário para o SRE.

### 5. Diagnóstico de Boot
- Adicionado log de emergência `boot_debug.log` no `main_runner.py` para capturar falhas silenciosas antes da inicialização completa do logger.

### 6. Correções em Ferramentas e Logging
- Corrigido `NameError` em `tools/refresh_session.py` (adicionado import faltante de `db_client`).
- Ativado log `INFO` para `core.autopilot` no `main_runner.py` para visibilidade do loop OODA.
- Validado boot limpo sem loops de reinicialização ou falhas de sintaxe.

### 7. Resiliência do Watchdog (v50.2)
- **Shield Auto-Clean**: O Watchdog agora tenta limpar automaticamente a porta de lock (**8009**) antes de iniciar, evitando conflitos de instâncias "zumbis".
- **Suavização de Restart**: Aumentada a tolerância para falhas rápidas de 3 para **5 tentativas**. O tempo de hibernação por erro de boot foi reduzido de 1h para **10 minutos**.
- **Gestão de Cotas IA**: Adicionado tratamento específico para erros **403/402** (Maritaca/OpenRouter) no Watchdog. O sistema agora entra em espera de 10 min nessas falhas em vez de tentar reinícios agressivos, preservando a saúde da malha de fallback.

### 8. Refatoração de Resiliência (v90.8)
- **Watchdog Adaptive Threshold**: Aumentada a janela de detecção de "falha rápida" para **120s** (configurável via `WATCHDOG_FAST_CRASH_THRESHOLD`). Reduzido tempo de hibernação para **10 minutos**.
- **Maritaca Async Recovery**: O erro 403 da Maritaca não trava mais o loop de reinício do Watchdog. A recuperação foi delegada ao `maritaca_resurrector_loop` com **backoff exponencial** (1m a 1h).
- **SQLite WAL Mode**: Implementado modo de escrita assíncrona (WAL) e retentativas em `scripts/export_to_sqlite.py`, eliminando conflitos de bloqueio com o Datasette.
- **Auditoria de Kills**: O `GuardLocker` agora registra o `cmdline` de processos zumbis antes de encerrá-los para rastreabilidade de SRE.
- **Proteção de Guardião**: O `process_cleaner.py` foi blindado para identificar e **proteger o PID do Watchdog** (avô do processo), impedindo o auto-encerramento acidental do sistema de supervisão.

### 9. Triagem Determinística Voyant (v92.3.1)
- **Estabilização do Protocolo**: Identificado que o parâmetro `input` era inválido na API Trombone, causando erro 500 no `DocumentExpander`. A correção definitiva utiliza o parâmetro `string` (multidocumento), conforme documentação oficial do Voyant.
- **Deduplicação e IDF**: O sistema agora envia cada comentário como um parâmetro `string` separado, criando um corpus com documentos reais. Isso permite que o Voyant calcule estatísticas de IDF precisas dentro do próprio lote, melhorando a qualidade da triagem.
- **Validação de Produção**: O script `scripts/validate_trombone.py` agora passa em 100% dos testes (5/5), detectando corretamente 30% de agressividade em lotes hostis e executando o Fast-Drop em lotes neutros.

### 10. Subagente Voyant (v92.5)
- **SaVoyant (Subagente Linguista)**: Elevado ao padrão de produção com processamento incremental via checkpoint de timestamp (`_last_processed_ts`), eliminando re-análise redundante.
- **Resiliência de Conexão**: Implementado monitoramento ativo com reconexão automática ao VoyantServer (porta 8888).
- **Extração de Bigramas**: Adicionada detecção local de slogans e padrões coordenados para enriquecer os insights periciais.
- **Otimização de Dados**: Queries SQL agora utilizam SELECT seletivo, reduzindo overhead de tráfego com o Supabase.
- **Reward Engine Sync**: Correção na atribuição de XP (+15.0 para insights relevantes) garantindo a progressão do agente.

## Próximos passos OBRIGATÓRIOS
1. **Rotação de Proxies**: Finalizar a integração real de proxies residenciais no Scraper V2 (AGENTS_SYNC.md).
2. **Checkpoint por Post**: Implementar persistência intermediária para evitar perda de progresso em coletas de perfis grandes.

## Últimas Operações (YOLO Test)

- **Teste de Operação Contínua (5 Minutos)**: Em 2026-06-04, um teste acelerado foi executado (`test_5min_operation.py`) para validar simultaneamente o pool de coleta (`WkColetaInstagram`) e o classificador da fila primária (`WkClassificaComentarios`).
- **Pipeline Reativo (Início da Fase 9)**: Em 2026-06-04, foi aprovada a otimização arquitetural para mover o sistema de um modelo "Polling-based" para "Event-Driven". O objetivo é conectar o Scraper diretamente ao AIProcessor via EventBus (sinalização em memória), zerando a latência de repouso do dado no banco.
- **Resultados e Auditoria**:
  - **Fila Atômica**: O mecanismo `queue_manager` funcionou perfeitamente realizando claims com `SKIP LOCKED` do Supabase.
  - **Coleta**: Scraper V2 autenticou, identificou postagens fixadas (FAST-SKIP) e avançou pelo grid alvo (`@dep.paulomagalhaes`) utilizando instâncias autônomas Headless do Playwright.
  - **Inteligência (Fallbacks Ativados)**: O Round-Robin com CircuitBreaker operou conforme esperado:
    - OLLAMA (Local) e MISTRAL (Cloud) operaram com sucesso contínuo.
    - MARITACA sofreu falha (403 Forbidden - Provável Chave Expirada/Sem Fundo) e sofreu **Poda Automática** via CircuitBreaker, sendo removido permanentemente da malha ativa, protegendo o runtime.
    - GROQ sofreu limitador de taxa (429 Too Many Requests) e foi temporariamente suspenso na rotação, direcionando a carga fluída para Ollama e Mistral sem interromper o serviço (graceful fallback).
  - **Conclusão**: O sistema operou de forma perfeitamente resiliente, sem quedas ou congelamentos (deadlocks), confirmando a robustez da arquitetura PASA e do roteamento adaptativo de LLM. O processo assíncrono finalizou corretamente.

## Auditoria de Inteligência (SaAuditaClassificacoes)

- **Falha de Persistência**: Em 2026-06-04, o `SaAuditaClassificacoes` detectou uma falha de schema ao tentar salvar dados de auditoria cruzada. O erro `PGRST204` confirmou a ausência da coluna `audit_data` na tabela `comentarios`.
- **Correção Aplicada**: Criada a migração `migrations/20260604_add_audit_data.sql` para adicionar a coluna `JSONB` necessária.
- **Detecção de Drift**: O agente reportou um **Drift de 26.7%** (4 divergências em 15 amostras) entre o classificador de produção e o auditor (Groq/Llama 3.3). O alerta de drift (> 20%) foi disparado, sugerindo necessidade de recalibragem dos prompts ou do threshold de confiança.
- **Relatórios de Rede**: O `SaMineracaoRedes` gerou novos relatórios em `frontend/public/reports/` identificando clusters de ataque coordenado com score de perigo máximo (100/100).

## Otimização de Subagentes (Fases 1, 2, 3 e 4)

- **Classe Abstrata BaseSubAgent (Fase 1)**: Criamos `workers/base/subagent_base.py` herdando de `BaseWorker` e fornecendo `ProcessPoolExecutor` para offloading assíncrono de tarefas CPU-bound.
- **Concorrência e Claims Horizontais (Fase 2)**: Criamos a tabela `lotes_analises` e a RPC `reivindicar_lote_analise` (corrigindo ambiguidades do compilador SQL) aplicando claims baseados em `SELECT FOR UPDATE SKIP LOCKED`. Refatoramos o `SaMineracaoRedes` para reivindicar lotes e persistir o status atômico de término do ciclo (`CONCLUIDO` / `ERRO`).
- **Resiliência e Drift em IA (Fase 3)**: Corrigimos a ausência da coluna `audit_data` na tabela `comentarios` do Supabase remoto. Refatoramos `SaAuditaClassificacoes` para herdar de `BaseSubAgent` e consumir a cascata de IA (Groq -> Mistral -> Ollama) integrada com o `ai_circuit_breaker` global. Adicionamos a lógica de criação de sugestões `drift_detected` de prioridade `HIGH` na tabela `worker_suggestions` se o drift superar 20%.
- **Parametrização por Ciclo (Fase 4)**: Implementamos a clonagem e congelamento de configurações no boot do ciclo operacional (`current_cycle_config`) do `WkColetaInstagram` para evitar race conditions contra as alterações automáticas do SRE via `WkAplicaSugestoes`.
- **Validação Integrada**: Rodamos os testes scratch de imports e de claims analíticos integrados com sucesso absoluto de processamento e persistência. Todas as fases foram commitadas e sincronizadas com a branch `main`.

## Estabilização e Resiliência do Watchdog (2026-06-05)

- **Loop do Guardião Responsivo**: Refatoramos a thread `guard` do Watchdog para ser totalmente interrompível. O loop de monitoramento do processo e os períodos de cooldown/hibernação agora respondem instantaneamente a comandos de Start/Stop/Restart via Dashboard ou menu da bandeja.
- **Detecção de Erros Refinada**: Implementamos uma lógica de classificação de erros baseada em tracebacks reais e tipos específicos de exceções Python (ex: `NameError`, `SyntaxError`). Removemos a captura genérica da palavra "exception" para evitar falsos positivos de logs informacionais, prevenindo paradas desnecessárias do sistema.
- **Autocura de Threads**: Adicionamos tratamento de exceções robusto com `traceback.print_exc()` e timeouts de `join` em threads de leitura de pipes para evitar o congelamento do guardião em casos de crashes anômalos.
- **Validação de Sucesso**: Toda a suíte de testes unitários (12/12) foi validada com 100% de sucesso, garantindo que as mudanças de resiliência não introduziram regressões.

## Otimização de Classificação de IA e Fila Secundária (Fase 6)

- **Prioridade e Triagem Rápida Local (Ollama)**: Configuramos o pipeline primário de classificação (`WkClassificaComentarios`) para utilizar exclusivamente o Ollama local na primeira perícia de triagem. Inserimos um delay rígido e obrigatório de **1 segundo** entre as chamadas ao Ollama para evitar sobrecargas de CPU/recursos na máquina do usuário.
- **Fila Secundária de Revisão Online (Cloud)**:
  - Comentários sinalizados com hostilidade ou potenciais ataques na triagem do Ollama local recebem a categoria `"SUSPEITO"` e são salvos com `processado_ia = True` (concluindo o ciclo do scraper e da fila primária sem gerar gargalos).
  - Criamos o subagente **`SaRevisaoOnline`** (`sa_revisao_online.py`) herdando do `BaseSubAgent`. Ele atua em ciclos assíncronos paralelos e independentes gerenciados pelo orquestrador no `main_runner.py`.
  - Este subagente executa a rotina `run_batch_online_review` buscando no banco apenas registros `"SUSPEITO"` e os revisa utilizando exclusivamente a malha de IA Cloud (Mistral, Groq, etc.), liberando totalmente o fluxo de coletas e a fila de triagem primária de interrupções e timeouts de rede externa.
- **Validação com Sucesso**: Implementamos e rodamos testes unitários de integração que confirmaram o redirecionamento e a perícia do Ollama para `"SUSPEITO"`, seguido pela classificação cloud no Mistral para a categoria correta (`DANO_A_IMAGEM`). Todos os patches foram commitados e sincronizados remotamente.
- **Atalhos e Disparo sob Demanda (Bandeja Gráfica)**:
  - Desenvolvemos scripts de entrypoint CLI individuais na pasta `scripts/` para rodar os subagentes sob demanda:
    - [run_mineracao_redes.py](file:///C:/Projetos/sentinela/scripts/run_mineracao_redes.py) para o `SaMineracaoRedes`.
    - [run_auditoria_financeira.py](file:///C:/Projetos/sentinela/scripts/run_auditoria_financeira.py) para o `SaAuditoriaFinanceira`.
    - [run_revisao_online.py](file:///C:/Projetos/sentinela/scripts/run_revisao_online.py) para o `SaRevisaoOnline`.
  - Acrescentamos comandos no menu da bandeja do Watchdog ([__main__.py](file:///C:/Projetos/sentinela/watchdog/__main__.py)) mapeando atalhos que abrem novas janelas dedicadas de console do Windows para disparar individualmente cada um dos subagentes (`SaAuditaClassificacoes`, `SaRevisaoOnline`, `SaMineracaoRedes`, `SaAuditoriaFinanceira`, `ScannerAgent`, `DossierAgent`).
  - Todos os scripts e patches de menu foram comitados e sincronizados remotamente.

## Cobertura Total de Comandos na Bandeja do Watchdog (Fase 7)

- **Novos Scripts de Entrada CLI Individuais**: Desenvolvemos e organizamos entrypoints individuais na pasta `scripts/` para os subagentes e workers restantes agirem de forma autônoma e assíncrona sob demanda em consoles dedicados:
  - [run_coleta_instagram.py](file:///C:/Projetos/sentinela/scripts/run_coleta_instagram.py) para o `WkColetaInstagram`.
  - [run_pesquisa_alvos.py](file:///C:/Projetos/sentinela/scripts/run_pesquisa_alvos.py) para o `WkPesquisaAlvos`.
  - [run_classifica_comentarios.py](file:///C:/Projetos/sentinela/scripts/run_classifica_comentarios.py) para o `WkClassificaComentarios`.
  - [run_analisa_tendencias.py](file:///C:/Projetos/sentinela/scripts/run_analisa_tendencias.py) para o `WkAnalisaTendencias`.
  - [run_aplica_sugestoes.py](file:///C:/Projetos/sentinela/scripts/run_aplica_sugestoes.py) para o `WkAplicaSugestoes`.
  - [run_gera_alertas.py](file:///C:/Projetos/sentinela/scripts/run_gera_alertas.py) para o `WkGeraAlertas`.
  - [run_consulta_banco.py](file:///C:/Projetos/sentinela/scripts/run_consulta_banco.py) para o `SaConsultaBanco`.
  - [run_diagnostica_sistemas.py](file:///C:/Projetos/sentinela/scripts/run_diagnostica_sistemas.py) para o `SaDiagnosticaSistemas`.
  - [run_doc_fetcher.py](file:///C:/Projetos/sentinela/scripts/run_doc_fetcher.py) para o `DocFetcher`.
- **Interface Organizada e Hierárquica**:
  - Reestruturamos o menu da bandeja do Watchdog em [__main__.py](file:///C:/Projetos/sentinela/watchdog/__main__.py) dividindo os disparadores explicitamente em dois blocos organizados por divisores visuais: `SUBAGENTES (SA)` e `WORKERS (WK)`.
  - Essa divisão traz total clareza operacional para o usuário e assegura compatibilidade absoluta e estabilidade de renderização no Windows, sem os riscos de falhas de reconstrução do Win32 comuns com submenus dinâmicos profundos.
- **Validação**: Testamos a compilação e sintaxe de todos os módulos com sucesso absoluto. Todos os arquivos foram preparados para o versionamento do Git.

## Otimização de Performance no Cadastro de Candidatos (Fase 8)

- **Processamento e Escrita em Lote (Bulk Upserts)**: Refatoramos o `WkEscaneiaCandidatos` ([wk_escaneia_candidatos.py](file:///C:/Projetos/sentinela/workers/processors/wk_escaneia_candidatos.py)) para acumular dados de novos alvos e agendamentos de coletas e gravá-los de uma única vez em lote ao fim do processamento do PDF de pesquisa.
  - O método `_handle_candidate` agora gera e retorna objetos contendo as instruções estruturadas de persistência em vez de fazer chamadas individuais diretas ao Supabase remoto para cada candidato.
  - A escrita no banco de dados agora executa um único Bulk Upsert na tabela `candidatos` e outro Bulk Upsert na tabela `fila_coleta`, reduzindo expressivamente o consumo de conexões simultâneas, o tráfego de rede e a latência global da aplicação.
- **Validação**: Verificada a compilação sem falhas de sintaxe e preparada a sincronização via Git.

## Reorganização Arquitetural de Domínio (Fase 9)

- **Migração do WkPesquisaAlvos**: Movemos o arquivo de curadoria de alvos `WkPesquisaAlvos` de `workers/ai/wk_pesquisa_alvos.py` para o domínio adequado de processadores operacionais em `workers/processors/wk_pesquisa_alvos.py`.
  - Esta alteração resolve a inconsistência semântica de manter um worker de prospecção/curadoria sob o domínio exclusivo de IA (`workers/ai/`), alinhando-o com o `WkEscaneiaCandidatos` e garantindo coerência de pastas no projeto.
- **Ajuste de Referências de Import**:
  - Atualizamos as referências de importação do `WkPesquisaAlvos` em [main_runner.py](file:///C:/Projetos/sentinela/main_runner.py), [scripts/add_target.py](file:///C:/Projetos/sentinela/scripts/add_target.py) e [scripts/run_pesquisa_alvos.py](file:///C:/Projetos/sentinela/scripts/run_pesquisa_alvos.py).
- **Validação**: Todos os módulos compilados e testados com sucesso total. Alterações registradas no repositório.

## Correções de Estabilidade do Stack de Desenvolvimento (2026-06-05 sessão 2)

- **Fix Crítico — Uvicorn CancelledError em Loop**: O script `api` no `package.json` usava `uvicorn --reload` sem exclusões. Qualquer arquivo gerado em `scratch/`, `.agents/`, `logs/` ou `runtime_state/` disparava um reload imediato do uvicorn, causando `asyncio.CancelledError` em cadeia e derrubando o backend constantemente. Adicionadas flags `--reload-exclude` para esses quatro diretórios.
- **Substituição de Alvo**: O alvo `pablomarcaloficial` foi desativado (`status_monitoramento = DESATIVADO`) no Supabase. O alvo canônico `pablomarcal1` permanece ATIVO e é o ponto de monitoramento oficial do candidato.
- **Ordenação de Serviços de IA no Dashboard**: Confirmado que a lógica de ordenação no `local_dashboard.html` já está correta (local → cloud, ambos asc). O problema de "dados não atualizando" era consequência do Watchdog offline por causa do CancelledError em loop — corrigido pelo item acima.

## Correções de Resiliência e Conformidade Jurídica (2026-06-05)

- **Conversão de Métodos Síncronos para Assíncronos**: Refatoramos métodos no cliente de banco de dados (`core/db.py`), no gerenciador de checkpoints (`core/checkpoint_manager.py`) e no gerenciador de filas (`core/queue_manager.py`) para utilizar `async/await`. Mapeamos as chamadas síncronas do Supabase (`execute()`) usando `asyncio.to_thread` para prevenir bloqueios indesejados no event loop do runner principal e dos workers.
- **Resolução de Syntax Errors**: Corrigimos duplicações de código que haviam gerado erros sintáticos em `core/queue_manager.py` e `core/db.py`.
- **Conformidade Jurídica de Nomenclatura**: Renomeamos `docs/METODOLOGIA_VICHI_FORENSE.md` para `docs/METODOLOGIA_VICHI_ANALITICA.md` e removemos menções aos termos proibidos ("forense", "evidência", "pericial") substituindo-os por termos permitidos ("indício", "analítica") em toda a documentação de IA, critérios de treinamento, e prompts em `core/ai_service.py` e `docs/`.
- **Validação de Testes Unitários**: Atualizamos a lógica dos testes de rebaixamento de temperatura para `no_comments_found` (PASA v88.4) no `tests/test_queue_manager.py` de modo a testar adequadamente as transições para "FRIO" (partindo de "MORNO" ou indefinido) e para "MORNO" (partindo de "QUENTE"). Todos os 12 testes unitários agora estão verdes e validados com 100% de sucesso.

## Sanitização de Gênero e Flexão de Cargos (PASA v94.0 - 2026-06-07)

- **Sanitização Determinística via CSV**: Refatoramos o [ground_truth.py](file:///c:/projetos/sentinela/core/ground_truth.py) para ler o sexo diretamente do arquivo [alvos_sanitizacao.csv](file:///c:/projetos/sentinela/alvos_sanitizacao.csv) (coluna `sexo`), extinguindo heurísticas falhas de sufixo no Python.
- **Flexão de Cargos**: Expandimos a `TAXONOMIA_CARGOS_VALIDOS` em [intelligence_service.py](file:///c:/projetos/sentinela/core/intelligence_service.py) para suportar versões femininas de cargos políticos (ex: `"Deputada Federal"`, `"Governadora"`, `"Ministra"`) e atualizamos o prompt da IA para obedecer à flexão de gênero correspondente.
- **Sincronização com o Banco**: O script [corrige_perfis_csv.py](file:///c:/projetos/sentinela/scripts/corrige_perfis_csv.py) foi adaptado para ler a nova coluna e atualizou com sucesso 373 registros da tabela `candidatos` do banco de dados remoto Supabase com gênero e cargos políticos flexionados corretos.

## Fallback Local e Gestão Resiliente do Ollama (PASA v52.5 - 2026-06-07)

- **Auto-Start e Processamento Singular**: Atualizamos o [ai_service.py](file:///c:/projetos/sentinela/core/ai_service.py) para injetar ativamente a inicialização do provedor local via `ensure_ollama_running()` ao detectar a necessidade. Integrado com `process_cleaner.py` para assegurar somente uma instância em execução.
- **Prevenção contra "Sangria de Nuvem"**: Refatorado o fallback de falha crítica na triagem: caso o servidor do Ollama colapse, a tarefa é marcada com `"categoria_ia": "ERRO"` em vez de repassá-la adiante como `"SUSPEITO"`. Isso garante contenção total de custos na malha Cloud (Mistral/Gemini).
- **Notificação Direta (Circuit Breaker)**: Inserida lógica no tratador de falhas de APIs (`_handle_provider_error`). Ao exceder os _retries_ toleráveis do modelo local (acionando o Circuit Breaker), um aviso é imediatamente encaminhado via `watchdog.send_whatsapp_alert` informando a necessidade de intervenção do operador para destravamento local.
- **Modelo Utilizado na Execução**: *Gemini 3.1 Pro (High)*, conforme protocolo de uso.

## Refatoração Estrutural do Warroom (2026-06-07)

- **Desacoplamento de UI Monolítica**: Os componentes pesados e integrados do painel (como as abas monolíticas de 300+ linhas) foram quebrados em subcomponentes puros e memoizados sob a estrutura diretorial em `frontend/components/warroom/`.
  - Pasta `targets/`: Criados `TargetCard` e `TargetFilters`, aliviando o excessivo estado da aba de prospecção.
  - Pasta `alerts/`: O `InvestigationModal` e o `UnlockOverlay` foram abstraídos, contendo logicamente seus próprios estados (ex: inputs textuais) limitando a carga de processamento de re-render da árvore inteira no *Feed*. O `AlertItem` garante a estabilidade de exibição em listas massivas.
  - Pasta `analise/`: Layout estético e marcação em Markdown concentrados em `CommentCard`, removendo bibliotecas desnecessárias de renderização (React Markdown + GFM) do contêiner principal da Aba.
- **Prevenção de Render Looping**: O travamento de UI ocorrido anteriormente, proveniente de digitação reativa que repintava a árvore HTML de todos os dados defasados e do feed em tempo real, foi sanado. Módulos reagem agora individualmente.
- **Modelo Utilizado na Execução**: *Gemini 3.5 Flash (High)*, perfil ideal para boilerplating/refatorações locais e greps complexos.

## Auditoria e Manutenção Semanal de Workspace (2026-06-07)

- **Higienização Geral**: Concluída a purga de arquivos temporários, logs antigos rotacionados e capturas obsoletas de erros acumulados em `logs/evidence/` para liberação de espaço em disco.
- **Saneamento de Assets**: Excluídas duplicatas de arquivos PNG e SVG que residiam na raiz do workspace, mantendo unicamente as instâncias válidas e centralizadas na pasta oficial do frontend (`frontend/public/`).
- **Remoção de Legados**: Eliminadas as pastas obsoletas de testes e scaffolds antigos (`frontend-bleeding-edge/` e `test_api/`) e scripts de testes locais soltos na raiz.
- **Otimização de Testes Unitários**: Ajustado o arquivo `pytest.ini` para isolar a varredura automática do pytest unicamente à pasta `tests/`. Isso preveniu a execução indevida e lenta (que demandava cerca de 4 minutos de requisições de rede) de scripts CLI manuais do operador, reduzindo o tempo de validação local para **0.06 segundos**.
- **Modelo Utilizado na Execução**: *Gemini 3.5 Flash (Medium)*, conforme protocolo de uso de IA para investigações locais e limpezas.

## Resolução da Condição de Corrida no AIService (Ollama - 2026-06-07)

- **Eliminação de Race Condition**: Sanamos uma falha crítica de concorrência assíncrona no [ai_service.py](file:///c:/projetos/sentinela/core/ai_service.py). O método de re-análise em lote (`run_batch_reanalysis`) removia fisicamente o `"ollama"` do array global compartilhado `self.providers` durante todo o seu ciclo (que pode levar dezenas de segundos), gerando falsos erros de triagem paralela em outros loops ativos de classificação.
- **Isolamento de Chamada**: Removemos a manipulação direta e mutável do catálogo global e passamos `force_cloud=True` no parâmetro de chamada `classify_text` no lote de re-análise. Isso mantém a lista global compartilhada estática e garante a integridade de todas as classificações paralelas concorrentes do sistema.
- **Modelo Utilizado na Execução**: *Gemini 3.5 Flash (Medium)*, ideal para diagnósticos de SRE, correções locais e testes rápidos.

## Estabilização do Voyant Tools (2026-06-07)

- **Correção no Subagente (`sa-voyant-01`)**: Corrigida a falha `'APIResponse' object is not callable` em [sa_voyant.py](file:///c:/projetos/sentinela/workers/ai/sa_voyant.py#L121) ao remover os parênteses extras do método `execute` do Supabase passado ao `asyncio.to_thread`. A função agora é delegada e executada corretamente em background.
- **Resiliência do VoyantService**: Ajustado o [voyant_service.py](file:///c:/projetos/sentinela/core/voyant_service.py) para utilizar gerenciadores de contexto `async with httpx.AsyncClient` locais a cada chamada de rede.
- **Resolução Definitiva de Erro de Transporte (Attempted to send a sync request...)**: Sanamos o bug `RuntimeError: Attempted to send a sync request with an AsyncClient instance` no [voyant_service.py](file:///c:/projetos/sentinela/core/voyant_service.py) e no [validate_trombone.py](file:///c:/projetos/sentinela/scripts/validate_trombone.py). O erro ocorria quando o HTTPX tentava gerar internamente streams síncronos (`SyncByteStream`) ao receber listas de tuplas ou dicionários no parâmetro `data` sob chamadas assíncronas concorrentes. A solução definitiva codifica manualmente o payload como form data plano (`urllib.parse.urlencode`) e o transmite usando o parâmetro `content` (com cabeçalho `application/x-www-form-urlencoded`), garantindo compatibilidade absoluta do cliente HTTPX assíncrono em memória.
- **Validação Integrada de Produção**: Executada a suite de testes oficiais integrada contra o `VoyantServer.jar` local em modo `headless=true`, obtendo 100% de sucesso (5/5 testes verdes no `validate_trombone.py` sem nenhuma falha de transporte ou AttributeError).
- **Modelo Utilizado na Execução**: *Claude Sonnet 4.6 (Thinking)* / *Gemini 3.5 Flash (Medium)*, ideal para diagnóstico de concorrência HTTP, testes e estabilização de workers.