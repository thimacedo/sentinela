# Checklist da Sessão 02/06/2026 (v86.8)

## Documentação Oficial

- `[x]` Ler STATE.md e ROADMAP.md antes de propor mudanças (Protocolo Diamond).
- `[x]` Atualizar STATE.md para v86.8 com registro da rodada de 02/06/2026.
- `[x]` Atualizar ROADMAP.md: marcar Fase 7.2 parcialmente concluída e definir Fase 8.
- `[x]` Atualizar walkthrough.md com entregas das rodadas 01/06 e 02/06/2026.
- `[x]` Atualizar task.md com checklist desta sessão.
- `[x]` Commit e push imediato com Conventional Commits.

## Entregas Validadas (Commits Anteriores)

- `[x]` Sub-agente `reclassify_agent` definido e operacional.
  - `[x]` Script `scripts/reclassify_low_confidence.py` implementado.
  - `[x]` Fallback local (LiteRT/Ollama) adicionado ao reclassificador.
  - `[x]` Backoff dinâmico de 5s entre tentativas de API.
- `[x]` Sub-agente `researcher_agent` definido e operacional.
  - `[x]` Script `scripts/research_pdf_criteria.py` implementado.
  - `[x]` Consolidação em `config/custom_rules.json` e injeção no `SYSTEM_PROMPT`.
- `[x]` Método `_call_provider` restaurado em `core/ai_service.py`.
- `[x]` Rotação circular de fallback de IA implementada.
- `[x]` Credenciais forçadas via `load_dotenv(override=True)`.
- `[x]` Monitoramento de saúde do Ollama (11434) e LiteRT (9379) corrigido.
- `[x]` 6.760 comentários com ERRO devolvidos à fila de classificação.

## Próximas Tarefas (Fase 8)

- `[ ]` 8.1 — Desacoplar `IGWorkerV2` em `InstagramScraperWorker` + `AIClassificationWorker`.
- `[ ]` 8.2 — Implementar `asyncio.Semaphore(3)` no Orchestrator.
- `[ ]` 8.3 — Integrar PGMQ para travas atômicas na `fila_coleta`.
- `[ ]` 8.4 — Acoplar rotação de proxies ao `new_context` do Playwright.
- `[ ]` 8.5 — Checkpoint SQLite por lote no `IGWorkerV2` (graceful shutdown).
- `[ ]` 8.6 — Expandir `core/circuit_breaker.py` para Supabase e Scraping.
- `[ ]` Tabelas tabulares de gasto por usuário/perfil em `/admin/financeiro`.
- `[ ]` Análise de "Shadowban" léxico para termos ocultos pela plataforma.
- `[ ]` Exportação de Dossiês em lote para contas de agências.
