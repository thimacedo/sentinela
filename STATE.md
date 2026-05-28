# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-28 | branch: main (Model: Gemini 3.5 Flash)_

## Status Operacional (v84.14)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v84.1: Consolidação AdSense e injeção otimizada. |
| Autopilot L3 | Operacional | v84.4: Proteção anti-detecção com cooldown de 6h. |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload e Cleanup de Órfãos automático. |
| Coleta (IGWorkerV2) | Operacional | v84.11: Clique forçado (`force=True`) e fallback resiliente (article/section). |
| Pesquisa (Researcher) | Operacional | v84.14: Inteligência contínua, governança de escopo e resiliência a schema. |
| Persistencia Supabase | OK | v84.14: Novos campos de governança (pendente aplicação SQL manual). |
| Classificacao IA | OK | Cascade v84.2: Filtro lexical preventivo integrado. |

## ✅ CONSOLIDAÇÃO DA RODADA (28/05/2026)

### 1. Restauração e Resiliência de Coleta
- **Recuperação de Sessão**: Sessões `SESSION_2` e `SESSION_VAL` restauradas e validadas.
- **Bypass de Interceptação**: Implementado `force=True` no clique do grid para ignorar overlays do Instagram (v84.11).
- **Detecção Híbrida**: O motor agora aceita elementos `section` no fallback de URL, eliminando o erro de "posts vazios".

### 2. Inteligência e Governança (TargetResearchWorker)
- **Pesquisa Inteligente**: Novo worker que automatiza a coleta de Bio/Seguidores e cruza com dados do TSE/TRE via IA (Mistral).
- **Curadoria Automática**: O sistema dedica 70% do tempo do pesquisador para atualizar dados `DESCONHECIDO` no banco.
- **Purga de Escopo**: Alvos fora do escopo (perfis pessoais) são desativados automaticamente (`status_monitoramento = DESATIVADO`).
- **Sistema de Recompensa**: Pesquisador recebe XP (+15/-10) baseado na qualidade e validação das informações.

### 3. Otimização de Infraestrutura e Interface
- **Logs Clean/Quiet**: Nível global em `WARNING`. Apenas loggers operacionais em `INFO`. Silenciamento de dependências barulhentas.
- **Resfriamento Automático**: Alvos sem posts novos são marcados como `FRIO` imediatamente para evitar punição dos workers.
- **Restauração de Ambiente**: Reinstalação completa de dependências via `uv` após reset acidental de `.venv`.

## 🚨 AÇÃO MANUAL REQUERIDA (DB SCHEMA)
Para ativar totalmente a governança e evitar avisos de log, execute no SQL Editor do Supabase:
```sql
ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS identidade_validada BOOLEAN DEFAULT NULL;
ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS motivo_desativacao TEXT DEFAULT NULL;

COMMENT ON COLUMN candidatos.identidade_validada IS 'Define se o alvo foi validado pelo TargetResearchWorker como pertencente ao escopo do projeto.';
COMMENT ON COLUMN candidatos.motivo_desativacao IS 'Justificativa para a negativa de validação ou desativação do alvo.';
```

## Descobertas Tecnicas (2026-05-28)
- **Anti-Crash no Worker (v84.14)**: Identificada necessidade de inicialização explícita de variáveis de controle antes de blocos try/except de banco para evitar `UnboundLocalError`.
- **Dinâmica de Overlays (v84.11)**: O Instagram introduziu camadas invisíveis no grid que interceptam ponteiros de clique; o uso de `force=True` no Playwright neutraliza este comportamento.
- **Evolução do RewardEngine (v84.13)**: O sistema de XP agora suporta deltas pré-calculados vindos de metadados, permitindo que workers de inteligência sejam avaliados por qualidade.

## Arquitetura de Integridade (v84.14)

```
[Watchdog v61.7] (Guardião L2 + Hot-Reload)
  ├── [Autopilot v84.4] (Anti-Detecção + Cooldown 6h)
  └── [Orchestrator v57.4]
        ├── [QueueManager v84.13] (Smart Backoff + Auto-Cooling + Filtro Governança)
        ├── [IGWorkerV2 v84.11] (Force Click + Fallback Híbrido)
        └── [Researcher v84.14] (Pesquisa TSE/TRE + Validação de Escopo + IA Curadoria)
```
