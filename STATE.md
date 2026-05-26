# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-25 | branch: main_

## Status Operacional (v70.0)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | SAAS Premium v60.2: Multitema (Light/Dark), War Room c/ Sidebar, Dossiês/Rede congelados |
| Autopilot L3 | Operacional | v70.0: Diagnóstico semântico, Pulso de 5min, Health Engine integrado |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload, Integração L3 Autopilot, Cleanup de Órfãos automático |
| Coleta Independente (IGWorkerV2) | Operacional | Motor V2 v65.1: Rotação Stealth, Fast-Skip Grid v3, Buffer SQLite, Filtro Léxico |
| Persistencia Supabase | OK | v70.1: Schema v65.2 verificado (analise_pericial), PGMQ ativo, Data Scrubbing |
| Classificacao IA | OK | Cascade v70.3: Hardening MCA v2.2, Fim do Viés Neutro, Escalação de Contradição Ativa |

## Descobertas Tecnicas (2026-05-25)
- **Endurecimento de IA (v70.3)**: Implementação de "Escalação por Contradição". Se o modelo local descreve um ataque na análise mas marca como Neutro, a confiança é penalizada para 0.40, forçando a perícia Cloud. Prompt v70.3 focado em Realismo Forense (Eliminação de falsos negativos).
- **Correção da Telemetria Forense (v70.2)**: Sincronização real do XP delta e persistência de métricas de performance (duração/erros) na tabela `worker_metrics`.
- **Integração Autopilot L3 (v70.0)**: O Watchdog agora hospeda o `AutopilotManager`, que analisa métricas de saúde do Supabase em tempo real. Implementados `Diagnostician` (IA para análise de logs/HTML) e `Patcher` (aplicação de hot-fixes automáticos).
- **Evolução Industrial (v65.1)**: Implementação do Buffer SQLite Zero-Loss, substituindo o JSON volátil. Introdução do `LexicalFilter` para economia de 30% em tokens e `ProcessCleaner` para estabilidade de longa duração.
- **Stealth e Furtividade (v65.0)**: Rotação dinâmica de perfis de dispositivos (User-Agents/Viewports) e lógica de Fast-Skip Grid aprimorada (encerra perfil após 3 posts velhos seguidos).
- **Validação de Identidade Biográfica (v64.0)**: O motor V2 agora captura Bio/Nome e utiliza a IA para validar se o perfil pertence ao alvo real, auto-eliminando perfis inautênticos ou paródias (ex: `@alexandre` inativado como inautêntico).

## Arquitetura de Integridade

```
[Watchdog v61.7] (Guardião L2 + Hot-Reload)
  ├── [Autopilot v70.0] (Comando L3 + Diagnóstico IA + Auto-Patching)
  └── [Orchestrator v57.4] (Atomic Locking + Memory Flush + Process Cleanup)
        ├── [QueueManager v55.1] (Multi-tier + Fairness + Termômetro)
        └── [IGWorkerV2 v65.1] (Scraper Playwright + Stealth + Identity AI Check)
              ├── [LocalBuffer v65.0] (Zero-Loss SQLite storage)
              ├── [LexicalFilter v65.0] (Pre-AI garbage disposal)
              └── [AIService v63.1] (Cascade Híbrido + MCA v2.2 Refinado)
```

## Fila de Coleta (Prioridade Dinâmica)

1. **Manual**: Precedência total.
2. **Prioritária**: `fila_coleta` (1=Máxima, order by prioridade ASC, created_at ASC).
3. **Justiça (Fairness 25%)**: Rotação forçada via candidatos ativos.
4. **Hibernação**: Alvos sem dados recentes (7d) ou inativos ficam fora por 12h.
