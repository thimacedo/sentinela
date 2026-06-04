# STATE.md — Sentinela
_last_updated: 2026-06-04 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo, com fila atômica, faxina de zumbis no boot e recuperação resiliente via sqlite buffer |
| Inteligência | 🟢 Operacional | Malha de IA ativa e dinâmica: ollama local monitorado e provedores de nuvem configurados via chaves no .env (groq, deepseek, openrouter, gemini) |
| Analytics de Rede | 🟢 Operacional | Subagente `NetworkMinerAgent` ativo de forma reativa/sob demanda |
| Financeiro | 🟢 Operacional | Subagente `TreasurerAgent` ativo de forma reativa/sob demanda, com telemetria e burn rate diário de IA |
| Watchdog Local | 🟢 Operacional | Porta 8001, SSE, controle remoto, dashboard local premium e monitor dinâmico de chaves de IA ativo |
| Frontend oficial | 🟢 Estável | `frontend/` é o frontend oficial, com integração de relatórios reais e CTAs conectados |

## Verdades operacionais auditadas

1. O backend é iniciado por `main_runner.py`.
2. O watchdog local supervisiona a execução, gerencia os status dinâmicos de IA e publica logs por SSE.
3. O classificador oficial em produção é `workers/processors/ai_processor_worker.py`.
4. A trava de instância única no `main_runner.py` e `watchdog` impede a execução redundante de múltiplos processos usando caminhos de lock absoluto baseados em `PROJECT_ROOT`.
5. O `cleanup_orphans()` é executado preventivamente no boot do `main_runner.py`, no setup de cada worker (`InstagramScraperWorker` e `TargetResearchWorker`), no `run_all()` do orquestrador e ciclicamente na sua autocura.
6. LiteRT não compõe mais o pipeline ativo de processamento.
7. A fila distribuída real hoje usa travas atômicas com `SELECT FOR UPDATE SKIP LOCKED`.
8. PGMQ permanece como possibilidade futura, não como base atual do runtime.
9. `frontend/` é o frontend oficial.
10. `local_dashboard.html` é o painel operacional local do watchdog, contendo seção de "Serviços de IA" dinâmica que exibe bolinhas cinzas (`bg-slate-600`) para serviços Cloud não configurados (status `DESATIVADO`).

## Achados da auditoria documental

### Certo

- watchdog com start/stop/restart e SSE
- `ollama` ativo
- `AIProcessorWorker` como classificador central
- `TargetResearchWorker` com ativação controlada por `RESEARCHER_MODE`
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
- providers de fallback com erros de quota/configuração (remediado via Unified Rotation Queue).

## Situação da IA

### Ativo

- fila circular unificada: local e cloud dividem o mesmo loop com rotacionamento Round-Robin
- reanálise de baixa confiança (usando exclusivamente cloud da fila unificada)
- fallback estruturado injetado ativamente na fila com **Poda Automática** (provedores são banidos instantaneamente em caso de erro 401/402/404)
- padronização léxica forçada via `PADRONIZACAO_LINGUISTICA_ANALITICA.md` incondicionalmente em todos os providers
- **Cache de I/O**: Prompts e datasets locais são carregados na RAM (Zero overhead de leitura em disco no event-loop)
- **DatabaseAgent (Subagente de dados)**: Integrado e disponível em `workers.ai.DatabaseAgent`. Esse subagente consome a API JSON do Datasette local na porta `8002` para fornecer consultas SQL assíncronas, buscas textuais indexadas (FTS5) e estatísticas analíticas para os demais workers do ecossistema de forma desacoplada.

### Saneado

- referências residuais a LiteRT removidas
- malha de fallback reordenada e sem provedores indisponíveis (como eden_ai e cerebras)

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
- arquiteturas PASA antigas

## Próximos passos recomendados

1. Habilitar RLS e criar políticas de acesso para as 15 tabelas que estão expostas no Supabase (incluindo `threat_alerts`, `worker_ledger`, `fallback_logs`, etc.).
2. Monitorar o consumo e o custo (burn rate) gerados nas últimas 24h através do TreasurerAgent.