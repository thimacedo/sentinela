# Documentação — Sentinela

> ⚠️ **Esta página foi substituída.** O índice oficial de documentação é `docs/index_documentacao.md`.

## Fonte de verdade

| Documento | Propósito |
|---|---|
| `STATE.md` | Estado operacional atual, subsistemas ativos, riscos |
| `ROADMAP.md` | Entregas concluídas, pendências reais, próximos passos |
| `docs/SYSTEM_CONTEXT.md` | Visão técnica consolidada do sistema |
| `docs/DOCUMENTATION_AUDIT.md` | Classificação: válida, parcial, histórica ou lixo operacional |
| `docs/index_documentacao.md` | Índice de leitura em português |

## Regra de uso

Antes de iniciar qualquer trabalho:

1. Leia `STATE.md`
2. Leia `ROADMAP.md`
3. Valide no código
4. Só depois use docs históricas como apoio

## workers/ docs atualizados (v90.8)

| Worker | Localização correta |
|---|---|
| Classificador | `workers/processors/wk_classifica_comentarios.py` |
| Treasurer | `workers/financial/sa_auditoria_financeira.py` |
| Network Miner | `workers/analytics/sa_mineracao_redes.py` |
| Alerts | `workers/processors/wk_gera_alertas.py` |
| Dossier | `workers/processors/wk_gera_dossies.py` |
| Target Research | `workers/processors/wk_pesquisa_alvos.py` |

---

_Last updated: 2026-06-07 | docs/index.md — substituído por redirect_
