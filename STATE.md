# STATE.md — Sentinela
_last_updated: 2026-06-09 | branch: main | version: v94.8_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 com `upsert` idempotente e `returning='minimal'`. |
| Inteligência | 🟢 Operacional | Malha de IA (Mistral) estável. Circuit Breakers ativos para Ollama e Voyant. |
| Dashboard | 🟢 Operacional | Painel "Decision Room" v94.7 com API local cacheada (Estratégia B). |
| Diagnóstico | 🟢 Operacional | Painel de controle de Workers integrado via `/api/metrics`. |

## Histórico Recente de Correções (v94.8)
1. **Resiliência do Autopilot**: Proteção do `main_runner` contra limpeza agressiva de processos.
2. **Estabilização Voyant**: Implementação de *Circuit Breaker* léxico e execução silenciosa (*headless*).
3. **Frontend**: Migração de consulta direta ao Supabase para API local cacheada; remoção de re-renderização redundante (idempotência).
4. **Sala de Controle**: Adição de comandos de `restart`, `add_target`, `force_scrape` e `remove_target` via Dashboard.
5. **Correção de Query**: Ajuste de sintaxe para `not.is` em queries de filtro no Supabase.
