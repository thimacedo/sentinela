# Arquitetura de Workers — Sentinela

Este diretório contém os workers e utilitários do runtime moderno do Sentinela.

## Contrato oficial

O contrato atual fica em:

- `workers/base/worker_base.py`
- `workers/base/cycle_result.py`

Todo worker novo deve:

1. herdar de `workers.base.worker_base.BaseWorker`
2. implementar `setup()`, `run_cycle()`, `teardown()` e `describe()`
3. retornar `CycleResult`
4. evitar loops próprios quando o orquestrador já controla o ciclo

## Estrutura atual

- `workers/scrapers/` — coleta
- `workers/processors/` — processamento e subagentes
- `workers/analytics/` — analytics derivados
- `workers/financial/` — telemetria financeira
- `workers/ai/` — workers auxiliares de inteligência e pesquisa
- `workers/orchestrator/` — coordenação do runtime moderno
- `workers/base/` — contrato oficial, reputação e memória

## O que foi removido

Os entrypoints e contratos legados que competiam com o runtime oficial foram expurgados:

- `core/orquestrador.py`
- `workers/core/base_worker.py`
- `workers/processors/classifier_worker.py`
- `workers/processors/queue_manager.py`
- `workers/processors/search_watcher.py`
- `workers/processors/cleanup_worker.py`
- `workers/analytics/report_worker.py`
- `workers/official_solenya_daemon.py`
- `workers/orchestrator_long_run.py`
- `workers/schedule_long_scrape.py`

## O que foi reaproveitado

Parte da lógica útil do legado foi preservada no runtime moderno:

- injeção de exemplos de padrão ouro incorporada a `core/ai_service.py`
- scanner documental mantido em `workers/processors/candidate_scanner.py`
- scripts auxiliares realinhados para o fluxo oficial
- `workers/official_solenya_daemon.py`
- `workers/orchestrator_long_run.py`
- `workers/schedule_long_scrape.py`

## O que foi reaproveitado

Parte da lógica útil do legado foi preservada no runtime moderno:

- injeção de exemplos de padrão ouro incorporada a `core/ai_service.py`
- scanner documental mantido em `workers/processors/candidate_scanner.py`
- scripts auxiliares realinhados para o fluxo oficial

## Regra prática

Se um fluxo precisar de:

- ciclo contínuo supervisionado, use `main_runner.py`
- observabilidade e controle operacional, use `watchdog`
- scanner documental, use `scripts/run_scanner_agent.py`

Não reintroduza entrypoints paralelos legados.
