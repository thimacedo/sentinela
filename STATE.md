# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-28 | branch: main (Model: Claude Sonnet 4.6)_

## Status Operacional (v85.0 - Rocket Mode)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v84.1: Consolidação AdSense e injeção otimizada. |
| Autopilot L3 | Operacional | v84.21: Diagnóstico técnico via chat_completion restaurado. |
| Watchdog (Guardião) | Operacional | v84.17: Saneamento de codificação (Windows) e autocura absoluta. |
| Coleta (Rocket Scraper) | Operacional | v85.0: Desacoplado da IA. Paralelismo assíncrono via Semaphore. |
| Perícia (AI Processor) | Operacional | v85.0: Worker dedicado para classificação PASA em lote. |
| Persistencia Supabase | OK | v85.0: Protegido por Circuit Breaker Global (DB Protection). |
| Graceful Shutdown | Ativo | v85.0: Checkpointing de dados em caso de interrupção (SIGINT). |

## ✅ CONSOLIDAÇÃO DA RODADA (28/05/2026)

### 1. Rocket Mode: Desacoplamento e Performance (v85.0)
- **Arquitetura Assíncrona**: O Sentinela agora opera como uma malha de workers independentes. Os coletores (Scrapers) focam exclusivamente em I/O, enquanto o `AIProcessorWorker` gerencia a perícia PASA em lote.
- **Paralelismo Real**: O Orquestrador utiliza `asyncio.Semaphore` para permitir múltiplas coletas simultâneas, otimizando o tempo de atividade e a taxa de ingestão de dados.

### 2. Resiliência e Integridade de Dados
- **Circuit Breaker DB**: Implementado `db_circuit_breaker` que protege o Supabase contra enxurradas de requests em caso de instabilidade, chaveando para o `local_buffer` (SQLite) automaticamente.
- **Graceful Shutdown**: Sistema de "Pouso de Emergência" via `shutdown_event`. Se o processo for encerrado, os scrapers interrompem a paginação e retornam os dados coletados até o momento para salvamento seguro.

### 3. Sincronia Inter-Agentes
- **Canal AGENTS_SYNC**: Estabelecido protocolo de comunicação entre Gemini e Antigravity para orquestração de missões complexas.
- **Rocket Launcher**: Criado `rocket.ps1` como gatilho unificado para disparar missões paralelas.

## 📋 ARQUITETURA DE INTEGRIDADE (v85.0)

```
[Watchdog v84.17] (Guardião Saneado + Autocura)
  ├── [Graceful Shutdown Handler] (SIGINT/SIGTERM -> shutdown_event)
  └── [Orchestrator v85.0] (Semaphore Parallelism)
        ├── [QueueManager v84.18] (Smart Backoff + Auto-Cooling)
        ├── [Scraper Mesh] (IGWorkerV2, IGZyteWorker - Pure I/O)
        │     └── [Circuit Breaker DB] (Supabase Protection)
        └── [AI Processor Mesh] (AIProcessorWorker - Batch Pericia)
```

## Descobertas Tecnicas (2026-05-28)
- **Loops de Validação**: Descobrimos que avisos recorrentes de "perfil inacessível" ocorrem quando o sistema falha em persistir uma decisão de governança negativa no banco; a v84.20 resolve isso.
- **Codificação Windows**: O terminal Windows requer explicitamente `PYTHONUTF8=1` e logs ASCII-safe para legibilidade total.
- **Resiliência DOM**: O uso de seletores `section` como fallback para `article` é essencial para lidar com o layout dinâmico de contas verificadas.
