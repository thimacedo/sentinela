# Índice de Documentação — Sentinela

Este índice foi atualizado em `2026-06-12` para refletir o estado real do workspace na versão `v97.6`.

## 1. Fonte de verdade

- `STATE.md` — estado operacional atual, subsistemas ativos, riscos e decisões recentes
- `ROADMAP.md` — entregas concluídas, pendências reais e próximos passos
- `docs/SYSTEM_CONTEXT.md` — visão técnica consolidada do sistema atual
- `docs/DOCUMENTATION_AUDIT.md` — classificação da documentação: válida, parcial, histórica ou lixo operacional
- `docs/index_documentacao.md` — este índice

## 2. Documentação de workers (docs/workers/)

Todos os arquivos abaixo estão sincronizados com a versão `v97.6` com caminhos e classes corretas:

| Worker / Subagente | Arquivo de Documentação | Código de Produção |
|---|---|---|
| Scraper Instagram | `docs/ARCH_AUTOHEALING.md` (Coleta) | `workers/scrapers/wk_coleta_instagram.py` |
| Classificador Oficial | `docs/workers/AI_PROCESSOR_WORKER.md` | `workers/processors/wk_classifica_comentarios.py` |
| Pré-Triagem Fast-Drop | `docs/workers/SA_FAST_DROP.md` | `workers/ai/sa_fast_drop.py` |
| Auditoria Financeira | `docs/workers/TREASURER_AGENT.md` | `workers/financial/sa_auditoria_financeira.py` |
| Mineração de Redes | `docs/workers/NETWORK_MINER_AGENT.md` | `workers/analytics/sa_mineracao_redes.py` |
| Geração de Alertas | `docs/workers/ALERT_WORKER.md` | `workers/processors/wk_gera_alertas.py` |
| Geração de Dossiês | `docs/workers/DOSSIER_WORKER.md` | `workers/processors/wk_gera_dossies.py` |
| Curadoria de Alvos | `docs/workers/TARGET_RESEARCH_WORKER.md` | `workers/processors/wk_pesquisa_alvos.py` |

## 3. Documentação ainda útil

- `docs/database_schema_v58.md` — referência estrutural de banco
- `docs/project_functions_v58.md` — contexto funcional histórico ainda parcialmente útil
- `docs/archive/REFATORACAO_FRONTEND.md` — contexto da evolução do frontend (arquivado)
- `docs/RESILIENCIA_LOGIN_INSTAGRAM.md` — detalhes da operação de login/coleta
- `docs/PADRONIZACAO_LINGUISTICA_ANALITICA.md` — referência metodológica da classificação

## 4. Documentos operacionais ativos

- `walkthrough.md` — walkthrough enxuto das entregas recentes
- `task.md` — checklist operacional da rodada atual
- `docs/operations/INSTAGRAM_SCRAPER_V2.md` — referência de coleta

## 5. Documentação histórica (Depreciada / Legada)

Use apenas para contexto e rastreabilidade:

- `docs/archive/`
- `docs/superpowers/`
- `docs/workers/SA_VOYANT.md` (Substituído pelo SaFastDrop na v96.2)
- `docs/VOYANT_INTEGRATION.md` (Expurgado na v96.2)
- `docs/DOCUMENTACAO_INFRA_V50.1.md`
- `docs/ARCHITECTURE_PASA_V50.md`
- `docs/archive/ARCHITECTURE_PASA_V84.md`
- `docs/archive/ARCHITECTURE_PASA_V86.md`
- `docs/archive/PHASE_1_IMPLEMENTATION_SUMMARY.md`
- `docs/archive/future_modules_plan.md`
- PRDs e planos de fases antigas

## 6. Regra de uso

Antes de iniciar qualquer trabalho:

1. leia `STATE.md`
2. leia `ROADMAP.md`
3. valide no código
4. só depois use docs históricas como apoio

---

_Última atualização do índice: 2026-06-12 (v97.6)_
