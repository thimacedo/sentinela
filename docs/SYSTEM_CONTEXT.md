# Sentinela — Contexto do Sistema
_last_updated: 2026-06-12 | versão: v98.0_

## 1. Missão

O Sentinela é uma plataforma de monitoramento político com foco em:

- coleta automatizada de conteúdo público (Instagram)
- classificação de hostilidade e risco informacional (PASA)
- mineração de redes e sinais coordenados
- produção de relatórios e dossiês
- operação supervisionada por watchdog local e autocura autônoma via SRE Agent

## 2. Topologia atual

```text
[Watchdog Local] (Porta 8001 + logs SSE)
  ├── Agente de SRE Autônomo (core/autopilot/sre_agent.py - OODA e Autocura)
  └── main_runner.py (Orquestrador v97.6)
        ├── WkColetaInstagram (InstagramScraperV2 + API Interna + DOM Healing + Diagnóstico Zero + Sticky Proxy)
        ├── WkClassificaComentarios (Cascata: Ollama local -> Sabia-4 -> Cloud)
        ├── SaRevisaoOnline (Fila secundária / Nuvem)
        ├── SaFastDrop (Linguística Forense / Triagem local fast-drop sem JVM)
        └── WkPesquisaAlvos (Curadoria opcional por RESEARCHER_MODE)

[Subagentes Analíticos e de Dados (sob demanda / reativos)]
  ├── SaConsultaBanco (Buscas SQL e FTS5 locais via Datasette na porta 8002)
  ├── SaAuditaClassificacoes (Auditoria cruzada e cálculo de drift com Groq)
  ├── SaMineracaoRedes (Processos paralelos para análise de clusters de ataque e grafos)
  ├── SaAuditoriaFinanceira (Métricas de burn rate, Stripe e DRE)
  └── Hugging Face MCP (Integração e descoberta de ecossistema Hub)

[Datasette Server] (Porta 8002)
  └── sentinela_data.db (Espelhamento SQLite local imutável FTS5)

[Supabase / PostgreSQL] (Produção Nuvem)
  ├── candidatos
  ├── comentarios
  ├── fila_coleta
  ├── worker_rewards
  ├── worker_suggestions
  └── demais tabelas analíticas

[Frontend oficial]
  └── frontend/ (Next.js)
        └── components/warroom/ (Abas modularizadas: targets, alerts, analise)

[Dashboard local]
  └── local_dashboard.html + SSE do Watchdog (Sala de Controle com Coleta Direcionada)
```

## 3. Pipeline atual de inteligência

1. claim atômico da fila em `core/queue_manager.py` com SELECT FOR UPDATE SKIP LOCKED
2. coleta de comentários com scraper V2 (InstagramScraperV2 com ScrapeAgent e DOM Healing)
3. triagem rápida via `SaFastDrop` (léxico local puro em Python) para descarte de neutros/lixo
4. classificação de comentários suspeitos restantes via `WkClassificaComentarios`
5. reanálise de baixa confiança como tarefa de utilidade secundária
6. disparo reativo em background de subagentes analíticos (`SaMineracaoRedes` & `SaAuditoriaFinanceira`)
7. atualização de métricas financeiras, telemetria e grafos de influência


## 3.1 Estado atual dos workers

Contrato oficial:

- `workers/base/worker_base.py`
- `workers/base/cycle_result.py`

Workers cíclicos ativos no runtime:

- `WkColetaInstagram` — coleta Instagram com fila atômica (`workers/scrapers/wk_coleta_instagram.py`)
- `WkClassificaComentarios` — classificador oficial PASA (`workers/processors/wk_classifica_comentarios.py`)
- `WkPesquisaAlvos` — curadoria de alvos, desabilitado por padrão (`workers/processors/wk_pesquisa_alvos.py`)
- `WkGeraAlertas` — monitoramento e alertas (`workers/processors/wk_gera_alertas.py`)
- `WkAnalisaTendencias` — análise de tendências (`workers/analytics/wk_analisa_tendencias.py`)
- `WkEscaneiaCandidatos` — cadastro de candidatos (`workers/processors/wk_escaneia_candidatos.py`)
- `WkAplicaSugestoes` — aplicação de sugestões de autocura (`workers/ai/wk_aplica_sugestoes.py`)
- `WkGeraDossies` — geração de dossiês PDF (`workers/processors/wk_gera_dossies.py`)

Subagentes analíticos (sob demanda / reativos):

- `SaAuditaClassificacoes` — auditoria cruzada anti-alucinação (`workers/ai/sa_audita_classificacoes.py`)
- `SaMineracaoRedes` — mineração de redes coordenada (`workers/analytics/sa_mineracao_redes.py`)
- `SaAuditoriaFinanceira` — gestão financeira e burn rate (`workers/financial/sa_auditoria_financeira.py`)
- `SaRevisaoOnline` — classificação cloud para suspeitos (`workers/ai/sa_revisao_online.py`)
- `SaConsultaBanco` — consultas SQL/FTS5 via Datasette (`workers/ai/sa_consulta_banco.py`)
- `SaDiagnosticaSistemas` — diagnóstico de saúde do sistema (`workers/ai/sa_diagnostica_sistemas.py`)
- `DocFetcher` — sincronização de docs de referência (`workers/ai/doc_fetcher.py`)

Mudanças já aplicadas:

- remoção dos contratos legados em `workers/core/`
- remoção de entrypoints legados paralelos ao runtime moderno
- alinhamento de scripts operacionais com `main_runner.py`
- `TargetResearchWorker` agora nasce desabilitado por padrão

## 4. Camada de IA em produção (PASA v90.8)

Pipeline Event-Driven (Fase 9) com `EventBus` (`core.event_bus`):

- **Triagem local**: `ollama` (llama3.2:1b, < 2s por comentário) com auto-start e fallback antissangria (gera "ERRO" em vez de "SUSPEITO" em caso de indisponibilidade).
- **Perícia cloud**: Sabia-4 (Maritaca, primário) → Mistral → Groq → OpenRouter
- **Fallback profundo**: `core/fallback_llm.py`
- **Circuit Breaker**: Providers com 401/403 removidos permanentemente; 429 suspensos por 300s. Erros locais engatilham alertas WhatsApp.

Notas:
- LiteRT não integra mais o processamento ativo.
- A reanálise de baixa confiança foi desacoplada do termômetro de alvos.
- O pipeline reativo (EventBus) substitui polling constante — overhead real: ~2ms por sinal.

## 5. Fila e concorrência

O estado real do código mostra:

- trava atômica com `SELECT FOR UPDATE SKIP LOCKED`
- suporte a release de locks expirados
- fallback compatível quando RPC/migração não está disponível
- tabela `lotes_analises` e RPC `reivindicar_lote_analise` para controle atômico e concorrência horizontal de subagentes analíticos (`SaMineracaoRedes`), garantindo que tarefas CPU-bound de grafos não sejam duplicadas em réplicas simultâneas da engine.

Portanto, a fila distribuída via lock atômico já está operacional em nível de código.
PGMQ permanece como alternativa futura, não como dependência atual.

## 6. Watchdog e operação local

O Watchdog atual:

- sobe o dashboard local
- expõe SSE em `/api/stream`
- possui rotas de controle `/api/server/start`, `/api/server/stop` e `/api/server/restart`
- registra métricas e feedback humano de classificação
- verifica credenciais do Instagram
- garante disponibilidade do Ollama
- gerencia a inicialização automática do servidor Datasette na porta 8002

## 7. Frontends

Há dois contextos distintos:

- `frontend/` é o frontend oficial
- `local_dashboard.html` é o painel operacional local do watchdog

Esses papéis não devem ser confundidos.

## 8. O que não é mais contrato atual

Os itens abaixo aparecem em documentos antigos, mas não representam a verdade operacional atual:

- LiteRT como etapa padrão do pipeline
- `proposta_frontend/` como frontend oficial
- Zyte como eixo principal da coleta
- PGMQ como mecanismo já implantado
- Gemini direto como classificador principal de produção
- `core/orquestrador.py` como entrypoint válido
- `ClassifierWorker` como worker suportado
- `official_solenya_daemon.py` como daemon ativo
- `ai_processor_worker.py` como nome de arquivo do classificador (real: `wk_classifica_comentarios.py`)
- `treasurer_agent.py`, `network_agent.py`, `alert_worker.py`, `dossier_worker.py`, `target_research_worker.py` — nomes legados de arquivos que foram renomeados com prefixo `wk_`/`sa_`
- `researcher_mode` como "ativo por padrão" — na verdade é **desabilitado por padrão**
- Voyant Server (Java) e `SaVoyant` como componentes ativos (expurgados na v96.2, substituídos pelo `SaFastDrop`)

## 9. Fontes de verdade

- operação: `STATE.md`
- planejamento: `ROADMAP.md`
- auditoria documental: `docs/DOCUMENTATION_AUDIT.md`

## 10. Ajustes recentes de produto (frontend + monetização)

Atualizações consolidadas no ciclo mais recente:

- integração de checkout do frontend com `API_BASE_URL` centralizado
- correção de robustez de AdSense com tentativa/retry até disponibilidade de `adsbygoogle`
- conclusão da página `frontend/app/relatorios/page.tsx` consumindo backend FastAPI real
- conexão de CTAs e botões sem ação em páginas chave
- redução de ruído visual na home/sidebar e aumento de usabilidade em alvos de clique
- proteção de mock de pagamento por variável explícita (`STRIPE_ALLOW_MOCK_PAYMENTS`)

Esse ajustes devem ser considerados baseline atual do frontend oficial.

## 11. Subagentes Analíticos e de Dados (PASA v88.2 / v97.6)

A arquitetura foi migrada para subagentes especializados executados de forma reativa ou sob demanda, todos herdando da classe base `BaseSubAgent` para offloading de CPU (subprocessos) e I/O (threads):

- **SaFastDrop** (`workers/ai/sa_fast_drop.py`): Subagente de Triagem Fast-Drop Léxica. Desenvolvido para substituir integralmente o Voyant Tools em Java. Utiliza regras locais de string e dicionários em Python puro para filtrar rapidamente comentários neutros de forma determinística, diminuindo em até 70% o uso de APIs de IA em nuvem.
- **SaConsultaBanco** (`workers/ai/sa_consulta_banco.py`): Desacopla a leitura de dados históricos de produção (Supabase) via API HTTP do Datasette local na porta `8002`, provendo buscas FTS5 ultra-velozes.
- **SaAuditaClassificacoes** (`workers/ai/sa_audita_classificacoes.py`): Subagente de curadoria cruzada anti-alucinação. Consome o `SaConsultaBanco` e efetua reclassificações via cascata de IA com circuit breaker para calcular o drift do modelo, gerando sugestões de prioridade `HIGH` em `worker_suggestions`.
- **SaMineracaoRedes** (`workers/analytics/sa_mineracao_redes.py`): Analisa grafos de hostilidade e detecta campanhas coordenadas organizadas (clusters de ataque) em processos filhos separados (`ProcessPoolExecutor`), persistindo os dados e gerando relatórios físicos para o frontend com claims atômicos concorrentes.
- **SaAuditoriaFinanceira** (`workers/financial/sa_auditoria_financeira.py`): Efetua auditoria de saldos de CI inconsistentes, monitora conectividade do Stripe e gera relatórios DRE consolidados diários.

## 12. Extrator Multi-Camada de Comentários (v98.0)

O `InstagramScraperV2` (`core/instagram_scraper_v2.py`) opera com **4 camadas de extracão** em ordem de prioridade:

| Camada | Método | Quando ativa | Retorno esperado |
|---|---|---|---|
| **1. API Interna** | `_fetch_comments_via_api()` via `httpx` | Quando `pk` e `session_id` estão disponíveis | JSON completo com paginação `next_max_id` |
| **2. XHR Interceptado** | `_parse_captured_json()` | Sempre (em paralelo) | JSON de `graphql/comments` capturado pelo Playwright |
| **3. Scripts Inline** | `_extract_from_scripts()` | Fallback | Tags `<script type="application/json">` com comentários |
| **4. DOM Visual** | `_extract_from_dom()` | Último recurso | Links de perfil + spans `dir="auto"` |

### Captura Proativa de Credenciais HTTP

O interceptador `_handle_response()` monitora **todas** as respostas do Instagram e extrai automaticamente:
- `csrftoken` (do cookie da requisição)
- `sessionid` ativo
- `pk` (ID numérico do post) via `_try_extract_pk_from_data()` nos XHRs de mídia

Iso elimina a necessidade de etapas manuais de resolução antes de chamar a API interna.

### Wait Strategy (Fase 1)

Substitui sleeps fixos por esperas inteligentes:
- `wait_for_selector('article time, ...')` — aguarda timestamp do post antes de ler data
- `wait_for_response(lambda r: 'comments' in r.url)` — aguarda XHR de comentários antes de extrair

### Sticky Proxy Binding

Variáveis de ambiente suportadas (por ordem de prioridade):
1. `PROXY_URL_TEMPLATE` com `{SESSION_ID}` — **sticky residencial** (recomendado)
2. `PROXY_LIST` — roundrobin (legado)
3. `PROXY_URL` — fixo (legado)

Cada sessão do Instagram (`SESSION_1`, `SESSION_2`, ...) recebe um `sticky_proxy_id` SHA256 determinístico. O IP residencial é mantido estável durante todo o `scrape_profile()` e só é trocado junto com a troca de sessão.