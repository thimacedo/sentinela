# STATE.md — Sentinela
_last_updated: 2026-06-11 | branch: main | version: v95.0_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 com `upsert` idempotente. |
| Inteligência | 🟢 Operacional | Malha de IA resiliente + SaFastDrop local (0 Java, 0 LLM). |
| Dashboard | 🟢 Operacional | Painel "Decision Room" com API local cacheada. |
| Diagnóstico | 🟢 Operacional | Diagnóstico SRE determinístico local sem LLM para infraestrutura. |

## Histórico Recente de Correções (v95.0)
1. **Refactoring Estratégico v51.0 (Concluído)**:
   - Expurgo do Java VoyantServer e do `SaVoyant`. Substituído pelo `SaFastDrop` (léxico local em Python puro) sem dependências externas.
   - Refatoração do `SaDiagnosticaSistemas` e do `Diagnostician` (`diagnostician.py`) para utilizar regras determinísticas locais em falhas comuns (sessão, rede, rate limit, IP block), reservando chamadas de LLM apenas para `DOM_CHANGE`.
   - WkAplicaSugestoes: Intervalo de autocura reduzido de 30 para 10 minutos.
   - Faxina arquitetural: Remoção de 8 arquivos órfãos em `core/` (`pasa_auditor.py`, `classification_service.py`, `zyte_checker.py`, `offline_cache.py`, `meta_ad_service.py`, `predictive_service.py`, `firebase_alerter.py`, `firebase_init.py`).
   - Resolvido o NameError de import do `WkAplicaSugestoes` no `main_runner.py`.
2. **Otimização do Menu da Bandeja (Watchdog Tray)**:
   - Agrupamento inteligente de Subagentes e Workers em submenus (`Subagentes (SA)` e `Workers (WK)`), melhorando drasticamente a hierarquia visual e diminuindo o tamanho vertical do menu.
   - Expurgo definitivo do `DocFetcher` (Sincronizar Docs) do menu e inclusão do novo `SaFastDrop` (Pré-Triagem Léxica) com script de disparo sob demanda (`scripts/run_fast_drop.py`).
   - Correção do bug de codificação de caracteres não-ASCII (lambdas dynamic text) que deixava em branco/invisíveis os itens como "Erros de Código" no Windows.
