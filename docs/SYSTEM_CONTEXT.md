# Sentinela — Contexto do Sistema
_last_updated: 2026-06-03_

## 1. Missão

O Sentinela é uma plataforma de monitoramento político com foco em:

- coleta automatizada de conteúdo público
- classificação de hostilidade e risco informacional
- mineração de redes e sinais coordenados
- produção de relatórios e dossiês
- operação supervisionada por watchdog local

## 2. Topologia atual

```text
[Watchdog Local]
  └── main_runner.py
        └── Orquestrador
              ├── InstagramScraperWorker
              ├── AIProcessorWorker
              ├── NetworkMinerWorker
              ├── TreasurerWorker
              └── TargetResearchWorker (opcional por RESEARCHER_MODE)

[Supabase / PostgreSQL]
  ├── candidatos
  ├── comentarios
  ├── fila_coleta
  ├── worker_rewards
  ├── worker_suggestions
  └── demais tabelas analíticas

[Frontend oficial]
  └── frontend/ (Next.js)

[Dashboard local]
  └── local_dashboard.html + SSE do Watchdog
```

## 3. Pipeline atual de inteligência

1. claim atômico da fila em `core/queue_manager.py`
2. coleta de comentários com scraper V2
3. persistência no banco
4. classificação do backlog via `core/ai_service.py`
5. reanálise de baixa confiança como tarefa de utilidade
6. mineração de rede
7. atualização de métricas financeiras e telemetria

## 3.1 Estado atual dos workers

Contrato oficial:

- `workers/base/worker_base.py`
- `workers/base/cycle_result.py`

Workers ativos observados no runtime:

- `InstagramScraperWorker`
- `AIProcessorWorker`
- `NetworkMinerWorker`
- `TreasurerWorker`
- `TargetResearchWorker` quando habilitado

Mudanças já aplicadas:

- remoção dos contratos legados em `workers/core/`
- remoção de entrypoints legados paralelos ao runtime moderno
- alinhamento de scripts operacionais com `main_runner.py`
- `TargetResearchWorker` agora nasce desabilitado por padrão

## 4. Camada de IA em produção

O pipeline ativo identificado no código é:

- triagem local: `ollama`
- refino cloud: `mistral`, `groq`, `openrouter`
- fallback profundo: `core/fallback_llm.py`

Observações:

- LiteRT não integra mais o processamento ativo.
- O reclassificador `scripts/reclassify_low_confidence.py` usa cloud-first e pode permitir fallback local com `ollama`.
- O `FallbackLLM` depende de `config/fallback_providers.yaml`, mas parte dessa malha está sujeita a indisponibilidade de quota/configuração.

## 5. Fila e concorrência

O estado real do código mostra:

- trava atômica com `SELECT FOR UPDATE SKIP LOCKED`
- suporte a release de locks expirados
- fallback compatível quando RPC/migração não está disponível

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
- Gemini como classificador oficial principal
- `core/orquestrador.py` como entrypoint válido
- `ClassifierWorker` como worker suportado
- `official_solenya_daemon.py` como daemon ativo

## 9. Fontes de verdade

- operação: `STATE.md`
- planejamento: `ROADMAP.md`
- auditoria documental: `docs/DOCUMENTATION_AUDIT.md`