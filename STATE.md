# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-26 | branch: main_

## Status Operacional (v70.5)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v70.5: Redesign Newsroom (Editorial), Fundo Claro (Default), Sidebar Info, Mobile OK |
| Autopilot L3 | Operacional | v70.0: Diagnóstico semântico, Pulso de 5min, Health Engine integrado |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload, Integração L3 Autopilot, Cleanup de Órfãos automático |
| Coleta Independente (IGWorkerV2) | Operacional | Motor V2 v71.0: Rotação Stealth, Solenya (Detecção de Bots), Buffer SQLite, Filtro Léxico |
| Persistencia Supabase | OK | v70.1: Schema v65.2 verificado (analise_pericial), PGMQ ativo, Data Scrubbing |
| Classificacao IA | OK | Cascade v70.3: Hardening MCA v2.2, Fim do Viés Neutro, Escalação de Contradição Ativa |

## Descobertas Tecnicas (2026-05-26)
- **Redesign Newsroom (v70.5)**: Migração do War Room tático para um Centro de Informação Cívica. Identidade Editorial baseada em Azul/Esmeralda, Fundo Claro como padrão e componentes informativos (Timeline, Insights, Perfis).
- **Módulo Solenya (v71.0)**: Implementação de detecção de comportamento coordenado (Bots) via similaridade textual. Clusterização pré-IA economiza até 95% de tokens em ataques massivos, mantendo registros forenses completos.
- **Endurecimento de IA (v70.3)**: Implementação de "Escalação por Contradição". Se o modelo local descreve um ataque na análise mas marca como Neutro, a confiança é penalizada para 0.40, forçando a perícia Cloud. Prompt v70.3 focado em Realismo Forense.
- **Correção da Telemetria Forense (v70.2)**: Sincronização real do XP delta e persistência de métricas de performance (duração/erros) na tabela `worker_metrics`.
- **Integração Autopilot L3 (v70.0)**: O Watchdog agora hospeda o `AutopilotManager`, que analisa métricas de saúde do Supabase em tempo real. Implementados `Diagnostician` (IA para análise de logs/HTML) e `Patcher` (aplicação de hot-fixes automáticos).

## Arquitetura de Integridade

```
[Watchdog v61.7] (Guardião L2 + Hot-Reload)
  ├── [Autopilot v70.0] (Comando L3 + Diagnóstico IA + Auto-Patching)
  └── [Orchestrator v57.4] (Atomic Locking + Memory Flush + Process Cleanup)
        ├── [QueueManager v70.4] (Multi-tier + Fairness + Termômetro + Smart Backoff)
        └── [IGWorkerV2 v71.0] (Scraper Playwright + Stealth + Coordinated Bot Check)
              ├── [LocalBuffer v65.0] (Zero-Loss SQLite storage)
              ├── [LexicalFilter v65.0] (Pre-AI garbage disposal)
              └── [AIService v70.3] (Cascade Híbrido + Hardening MCA v2.2)
```
