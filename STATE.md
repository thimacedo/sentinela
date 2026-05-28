# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-28 | branch: main (Model: Gemini 3.5 Flash)_

## Status Operacional (v84.20)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v84.1: Consolidação AdSense e injeção otimizada. |
| Autopilot L3 | Operacional | v84.4: Proteção anti-detecção com cooldown de 6h. |
| Watchdog (Guardião) | Operacional | v84.17: Saneamento de codificação (Windows) e autocura absoluta. |
| Coleta (IGWorkerV2) | Operacional | v84.15: Pipeline INTEGRADO com IntelligenceService (Inline Research). |
| Pesquisa (Researcher) | Operacional | v84.20: Purga automática de perfis inacessíveis (404/Privado) ativa. |
| Persistencia Supabase | OK | v84.14: Campos de governança e validação de identidade ativos. |
| Classificacao IA | OK | Cascade v84.2: Filtro lexical preventivo integrado. |

## ✅ CONSOLIDAÇÃO DA RODADA (28/05/2026)

### 1. Governança e Auto-Limpeza (v84.20)
- **Purga de Inacessíveis**: Alvos que resultam em erro 404 (Página não disponível) ou são perfis privados agora são desativados automaticamente pelo `IntelligenceService`. Isso elimina loops de avisos redundantes nos logs.
- **Deteção de Header**: Corrigido bug no motor V2 que ignorava falhas de carregamento biográfico; agora, a ausência de metadados força a reavaliação ou desativação do alvo.
- **Rigor Político**: IA instruída a distinguir rigorosamente "Influenciadores Políticos" de "Candidatos Reais", exigindo prova oficial para cargos eletivos.

### 2. Pipeline Unificado e Inteligência
- **Pesquisa Inline**: O coletor (`IGWorkerV2`) agora executa a pesquisa de dados biográficos em tempo real para novos alvos antes da primeira extração.
- **Curadoria Contínua**: O `researcher-01` opera em background atualizando dados obsoletos e limpando o banco de dados.
- **Resfriamento Inteligente (v84.18)**: Perfis sem atividade recente (> 7 dias) são marcados como `FRIO` e entram em hibernação automática para proteger os coletores.

### 3. Estabilização e Infraestrutura Windows
- **Logs Clean & Quiet**: Terminal saneado para Windows PowerShell; emojis e caracteres especiais removidos para evitar símbolos corrompidos (`ðŸš€`).
- **Resiliência de Clique**: Implementado `force=True` no Playwright para contornar overlays do Instagram que bloqueavam o grid.
- **Automação de Partida**: Criado `start_watchdog.ps1` e consolidado o fluxo de inicialização via `uv`.

## 📋 ARQUITETURA DE INTEGRIDADE (v84.20)

```
[Watchdog v84.17] (Guardião Saneado + Autocura)
  ├── [Autopilot v84.4] (Anti-Detecção + Cooldown 6h)
  └── [Orchestrator v57.4]
        ├── [QueueManager v84.18] (Smart Backoff + Auto-Cooling + Filtro Governança)
        ├── [IGWorkerV2 v84.15] (Integrated Intel -> Force Click -> Fallback Híbrido)
        └── [IntelligenceService v84.20] (Purga 404/Privado + IA Criteriosa + TSE/TRE)
```

## Descobertas Tecnicas (2026-05-28)
- **Loops de Validação**: Descobrimos que avisos recorrentes de "perfil inacessível" ocorrem quando o sistema falha em persistir uma decisão de governança negativa no banco; a v84.20 resolve isso.
- **Codificação Windows**: O terminal Windows requer explicitamente `PYTHONUTF8=1` e logs ASCII-safe para legibilidade total.
- **Resiliência DOM**: O uso de seletores `section` como fallback para `article` é essencial para lidar com o layout dinâmico de contas verificadas.
