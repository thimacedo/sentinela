# Project: Sentinela Watchdog & Backend Resilience

## Architecture
- Module/package boundaries:
  - `watchdog/`: Supervisão de processos, Dashboards (v91.3) e gestão de chaves de API.
  - `main_runner.py`: Orquestração de Workers e Subagentes.
  - `core/voyant_service.py`: Motor determinístico de PLN (Trombone API) para triagem rápida.
  - `scripts/export_to_sqlite.py`: Sincronização SQLite/Datasette (modo WAL).
- Data flow:
  - Remote Supabase (Queue/Data) ➔ Voyant Triage (Local) ➔ AI Classification (Híbrida).
  - VoyantServer (Porta 8888): Motor de PLN determinístico local.
  - Datasette (Porta 8002): Explorador SQL local FTS5.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Milestone 1: Exploração e Causa Raiz | Investigação de erros na thread guard, loops de hibernação, IA concorrente e exportação para SQLite | none | ✅ DONE |
| 2 | Milestone 2: Estabilização do Loop e Reloader | Proteção contra falhas fatais na thread guard, hibernação responsiva / interrompível e resets automáticos | M1 | ✅ DONE |
| 3 | Milestone 3: Desacoplamento e Sincronização Não-Bloqueante | Remover operações pesadas de IA do guard, isolar a sincronização SQLite/Datasette em thread background | M2 | ✅ DONE |
| 4 | Milestone 4: Validação e Auditoria | Executar todos os 12 testes pytest (100% pass) e rodar auditoria técnica v94.5 | M3 | ✅ DONE |

## Interface Contracts
- `watchdog/state` (WatchdogState): Thread-safe state holder. Keep attributes `should_run`, `status`, `restarts`, `code_errors`, `fast_crashes` updated.
- `scripts/export_to_sqlite:export_to_sqlite()`: Synchronous, executes network calls. Must be run in a non-blocking background thread from `guard()`.
