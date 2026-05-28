# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-28 | branch: main (Model: Gemini 3.5 Flash)_

## Status Operacional (v84.19)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v84.1: Consolidação AdSense e injeção otimizada. |
| Autopilot L3 | Operacional | v84.4: Proteção anti-detecção com cooldown de 6h. |
| Watchdog (Guardião) | Operacional | v84.17: Saneamento de codificação (Windows) e autocura absoluta. |
| Coleta (IGWorkerV2) | Operacional | v84.15: Pipeline INTEGRADO com IntelligenceService (Inline Research). |
| Pesquisa (Researcher) | Operacional | v84.19: Curadoria contínua, governança e rigor na distinção Influenciador vs Candidato. |
| Persistencia Supabase | OK | v84.14: Campos de governança e validação de identidade ativos. |
| Classificacao IA | OK | Cascade v84.2: Filtro lexical preventivo integrado. |

## ✅ CONSOLIDAÇÃO DA RODADA (v84.19)

### 1. Inteligência e Governança Unificada
- **Pipeline Integrado**: O coletor (`IGWorkerV2`) agora é consciente. Alvos novos passam por pesquisa e validação de escopo **antes** da primeira coleta, garantindo dados biográficos completos desde o início.
- **Governança de Escopo**: Alvos fora do escopo (perfis pessoais, spam) são detectados pela IA e **desativados automaticamente** (`purged_by_governance`).
- **Rigor de Classificação (v84.19)**: Refinamento do prompt para distinguir "Influenciadores Políticos" (ex: Luciano Huck) de "Candidatos Reais", exigindo evidência oficial para cargos eletivos.

### 2. Resiliência de Coleta e Resfriamento
- **Bypass de Interceptação (v84.11)**: Implementado `force=True` no clique do grid para ignorar overlays do Instagram.
- **Resfriamento Agressivo (v84.18)**: Alvos inativos ou com postagens antigas (> 7 dias) são reclassificados como `FRIO` no ato, protegendo a reputação dos workers via Smart Backoff.
- **Detecção Híbrida**: Aceitação de elementos `section` no fallback de URL para evitar erros de "posts vazios".

### 3. Estabilização e Infraestrutura Windows
- **Saneamento de Codificação**: Removidos emojis e caracteres especiais de todos os logs e scripts (`watchdog`, `start_watchdog.ps1`, `queue_manager`) para garantir compatibilidade com o terminal Windows e evitar caracteres corrompidos.
- **Correção de Herança**: Implementados métodos `setup/teardown` no `TargetResearchWorker`, resolvendo erros de instanciação.
- **Automação de Partida**: Criado script `start_watchdog.ps1` e instruções de Alias no PowerShell para inicialização rápida.

## 📋 ARQUITETURA DE INTEGRIDADE (v84.19)

```
[Watchdog v84.17] (Guardião Saneado + Autocura)
  ├── [Autopilot v84.4] (Anti-Detecção + Cooldown 6h)
  └── [Orchestrator v57.4]
        ├── [QueueManager v84.18] (Smart Backoff + Auto-Cooling + Filtro Governança)
        ├── [IGWorkerV2 v84.15] (Integrated Intel -> Force Click -> Fallback Híbrido)
        └── [IntelligenceService v84.19] (TSE/TRE + Validação de Escopo + IA Criteriosa)
```

## Descobertas Tecnicas (2026-05-28)
- **Rigor em IA**: Identificada tendência da IA em "projetar" cargos eletivos em celebridades; o prompt foi endurecido para exigir prova oficial do DivulgaCand.
- **Codificação de Terminal**: O Windows PowerShell exige logs sem caracteres non-ASCII para evitar falhas de leitura e visualização suja.
- **Dependência de Herança**: O uso de classes abstratas (`BaseWorker`) exige implementação total, mesmo que vazia, para evitar `TypeError` em runtime.
