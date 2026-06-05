# Project: Sentinela Watchdog & Backend Resilience

## Architecture
- Module/package boundaries:
  - `watchdog/`: Runs the system tray (pystray) and a FastAPI/uvicorn server (port 8001), supervising `main_runner.py` via subprocess.
  - `main_runner.py`: Orchestrates all active background workers.
  - `core/health_check.py`: Pings Instagram and local Ollama, ensuring startup health.
  - `scripts/export_to_sqlite.py`: Synchronizes remote Supabase database with a local SQLite database for local Datasette exploration (port 8002).
- Data flow:
  - Remote Supabase holds queue, candidates, and logs.
  - Watchdog guard thread starts `main_runner.py`.
  - On cooldown (idle state), Watchdog runs local Datasette synchronization.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Milestone 1: Exploração e Causa Raiz | Investigação de erros na thread guard, loops de hibernação, IA concorrente e exportação para SQLite | none | IN_PROGRESS |
| 2 | Milestone 2: Estabilização do Loop e Reloader | Proteção contra falhas fatais na thread guard, hibernação responsiva / interrompível e resets automáticos | M1 | PLANNED |
| 3 | Milestone 3: Desacoplamento e Sincronização Não-Bloqueante | Remover operações pesadas de IA do guard, isolar a sincronização SQLite/Datasette em thread background | M2 | PLANNED |
| 4 | Milestone 4: Validação e Auditoria | Executar todos os 12 testes pytest (100% pass) e rodar auditoria forense | M3 | PLANNED |

## Interface Contracts
- `watchdog/state` (WatchdogState): Thread-safe state holder. Keep attributes `should_run`, `status`, `restarts`, `code_errors`, `fast_crashes` updated.
- `scripts/export_to_sqlite:export_to_sqlite()`: Synchronous, executes network calls. Must be run in a non-blocking background thread from `guard()`.
