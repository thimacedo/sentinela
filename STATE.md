# STATE.md — Sentinela
_last_updated: 2026-06-04 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo, com fila atômica e fallback compatível quando RPC não existe |
| Inteligência | 🟡 Operacional com degradação | `ollama` ativo localmente; cloud sujeito a 429/quota; fallback profundo existe mas precisa saneamento de providers |
| Analytics de Rede | 🟢 Operacional | Subagente `NetworkMinerAgent` ativo de forma reativa/sob demanda |
| Financeiro | 🟢 Operacional | Subagente `TreasurerAgent` ativo de forma reativa/sob demanda |
| Watchdog Local | 🟢 Operacional | SSE, controle remoto e dashboard local funcionando |
| Frontend oficial | 🟢 Estável | `frontend/` é o frontend oficial, com integração de relatórios no backend real e CTAs conectados |

## Verdades operacionais auditadas

1. O backend é iniciado por `main_runner.py`.
2. O watchdog local supervisiona a execução e publica logs por SSE.
3. O classificador oficial em produção é `workers/processors/ai_processor_worker.py`.
4. A cascata de IA ativa agora é uma fila unificada (Unified Rotation Queue):
   - Fila primária unificada: `ollama`, `mistral` e os fallbacks (`groq`, `openrouter`, `deepseek`, etc.) em rotação Round-Robin.
   - Delay rigoroso mínimo de 1.0s imposto a cada chamada para evitar rate limit.
   - Penalidade automatizada e global (`_handle_provider_error`): +60s para 429, +30s geral com rebaixamento, e remoção/expurgo permanente para erros críticos de cota (401, 402, 404).
5. LiteRT não compõe mais o pipeline ativo de processamento.
6. A fila distribuída real hoje usa travas atômicas com `SELECT FOR UPDATE SKIP LOCKED`.
7. PGMQ permanece como possibilidade futura, não como base atual do runtime.
8. `frontend/` é o frontend oficial.
9. `local_dashboard.html` é o painel operacional local do watchdog, totalmente refatorado com UI Premium, Glassmorphism, layout responsivo dinâmico para desktop (`calc(100vh - 290px)`), telemetria e alvos perfeitamente visíveis e roláveis, auto-reload automático periódico a cada 10 segundos com trava anti-concorrência, e seção "Serviços de IA" com classificação explícita de cada provedor em `(local)` ou `(cloud)`.

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

O principal risco operacional hoje não é ausência de pipeline, e sim degradação da malha cloud/fallback e drift de configuração de produção:

- `429` em providers principais
- providers de fallback com erros de quota/configuração
- necessidade de saneamento em `config/fallback_providers.yaml`
- variáveis de ambiente Stripe e frontend não padronizadas entre ambientes podem quebrar checkout/retorno

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

1. revisar docs metodológicas antigas para reduzir contradição
2. monitorar performance da nova malha de fallback do orquestrador unificado