# STATE.md — Sentinela
_last_updated: 2026-06-03 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo, com fila atômica e fallback legado |
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
- `researcher_agent` e `scripts/research_pdf_criteria.py`
- `queue_manager` com claim atômico

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
- fallback legado quando RPC não existe

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
2. remover referências residuais a LiteRT do código e da UI operacional
3. revisar docs metodológicas antigas para reduzir contradição
4. corrigir itens sensíveis remanescentes do dashboard local