# STATE.md — Sentinela
_last_updated: 2026-06-03 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo, com fila atômica e fallback compatível quando RPC não existe |
| Inteligência | 🟡 Operacional com degradação | `ollama` ativo localmente; cloud sujeito a 429/quota; fallback profundo existe mas precisa saneamento de providers |
| Analytics de Rede | 🟢 Operacional | `network-miner` em execução |
| Financeiro | 🟢 Operacional | `treasurer` ativo |
| Watchdog Local | 🟢 Operacional | SSE, controle remoto e dashboard local funcionando |
| Frontend oficial | 🟢 Estável | `frontend/` é o frontend oficial |

## Verdades operacionais auditadas

1. O backend é iniciado por `main_runner.py`.
2. O watchdog local supervisiona a execução e publica logs por SSE.
3. O classificador oficial em produção é `workers/processors/ai_processor_worker.py`.
4. A cascata de IA ativa é:
   - `ollama` na triagem local
   - `mistral`, `groq` e `openrouter` no refino cloud
   - `FallbackLLM` em cenário de desastre
5. LiteRT não compõe mais o pipeline ativo de processamento.
6. A fila distribuída real hoje usa travas atômicas com `SELECT FOR UPDATE SKIP LOCKED`.
7. PGMQ permanece como possibilidade futura, não como base atual do runtime.
8. `frontend/` é o frontend oficial.
9. `local_dashboard.html` é o painel operacional local do watchdog, não o frontend oficial do produto.

## Achados da auditoria documental

### Certo

- watchdog com start/stop/restart e SSE
- `ollama` ativo
- `AIProcessorWorker` como classificador central
- `TargetResearchWorker` com ativação controlada por `RESEARCHER_MODE`
- `queue_manager` com claim atômico

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

O principal risco operacional hoje não é ausência de pipeline, e sim degradação da malha cloud/fallback:

- `429` em providers principais
- providers de fallback com erros de quota/configuração
- necessidade de saneamento em `config/fallback_providers.yaml`

## Situação da IA

### Ativo

- triagem local com `ollama`
- refinamento cloud
- reanálise de baixa confiança
- fallback profundo por `FallbackLLM`

### Pendente de saneamento

- remover referências residuais a LiteRT
- revisar providers de fallback indisponíveis
- reduzir ruído de tentativas quando todos os providers externos estiverem indisponíveis

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

1. sanear `config/fallback_providers.yaml`
2. simplificar `workers/orchestrator/orchestrator.py` removendo duplicidade entre `run_cycle_with_validation` e `run_cycle_with_validation_v2`
3. padronizar semântica de idle e `CycleResult` entre workers ativos
4. revisar docs metodológicas antigas para reduzir contradição