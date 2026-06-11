# STATE.md — Sentinela
_last_updated: 2026-06-11 | branch: main | version: v96.0_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 com `upsert` idempotente. |
| Inteligência | 🟢 Operacional | Malha de IA resiliente + SaFastDrop local. |
| Dashboard | 🟢 Operacional | Painel "Decision Room" com API local cacheada. |
| SRE / Autocura | 🟢 Operacional | Agente de SRE Autônomo (`sre_agent.py`) ativo com Tool Calling. |

## Histórico Recente de Correções (v96.0)
1. **Agente de SRE Autônomo (Watchdog v52.0) (Concluído)**:
   - Transformação do `AutopilotManager` procedimental em um **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`).
   - Implementação de registro de ferramentas (**Tool Calling**) para autocura: `restart_worker`, `restart_main_runner`, `rotate_session` (via `SessionHealer`), `cooldown_target` (no Supabase) e `adjust_concurrency_and_jitter`.
   - Loop cognitivo OODA reativo: processa erros comuns deterministicamente a custo zero (0 tokens), e recorre a IA sob demanda (Gemini/Mistral em JSON estruturado) somente para erros de `DOM_CHANGE` ou `UNKNOWN`.
   - Expurgo completo do thread de inicialização do `VoyantServer.jar` (JVM) do watchdog, economizando recursos de CPU e RAM no boot.
   - Criado script de validação de SRE ([test_sre_agent.py](file:///c:/Projetos/sentinela/scratch/test_sre_agent.py)).
2. **Refactoring Estratégico v51.0 (Concluído)**:
   - Expurgo do Java VoyantServer e do `SaVoyant`. Substituído pelo `SaFastDrop` (léxico local em Python puro) sem dependências externas.
   - Refatoração do `SaDiagnosticaSistemas` e do `Diagnostician` para utilizar regras determinísticas locais em falhas comuns.
   - WkAplicaSugestoes: Intervalo de autocura reduzido de 30 para 10 minutos.
   - Faxina arquitetural: Remoção de 8 arquivos órfãos em `core/`.
   - Resolvido o NameError de import do `WkAplicaSugestoes` no `main_runner.py`.
