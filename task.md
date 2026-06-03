# Checklist da Sessão 03/06/2026 (v87.0)

## Documentação Oficial

- `[x]` Ler STATE.md e ROADMAP.md antes de propor mudanças (Protocolo Diamond).
- `[x]` Atualizar STATE.md para v87.0 com registro da rodada de 03/06/2026.
- `[ ]` Atualizar ROADMAP.md: registrar avanços da Fase 8 e novos status do Watchdog.
- `[x]` Atualizar task.md com checklist desta sessão.
- `[x]` Commit e push imediato com Conventional Commits.

## Melhorias no Watchdog Local & Dashboard (War Room)

- `[x]` Auditar o código atual do Watchdog na pasta scripts e no pacote local.
- `[x]` Implementar abas no painel central do Dashboard ("Monitor de Discurso" e "Console de Logs").
- `[x]` Integrar EventSource do JavaScript no dashboard ao SSE `/api/stream` do Watchdog.
- `[x]` Exibir logs técnicos do `main_runner.py` em tempo real com coloração sintática de nível (Info, Warn, Error).
- `[x]` Criar rotas `/api/server/start`, `/api/server/stop` e `/api/server/restart` no Watchdog FastAPI.
- `[x]` Adicionar botões de controle de fluxo de execução no Header do dashboard local.
- `[x]` Implementar botão de ação "START" dinâmico para serviços locais de IA (Ollama / LiteRT) se inativos.

## Status das Próximas Tarefas (Fase 8)

- `[x]` 8.1 — Desacoplar `IGWorkerV2` em `InstagramScraperWorker` + `AIClassificationWorker` (Auditado: já desacoplado).
- `[x]` 8.2 — Implementar `asyncio.Semaphore(3)` no Orchestrator (Auditado: superado pelo design de múltiplos workers concorrentes no orquestrador de produção).
- `[ ]` 8.3 — Integrar PGMQ para travas atômicas na `fila_coleta` (Pendente para escala horizontal de múltiplos servidores).
- `[/]` 8.4 — Acoplar rotação de proxies ao `new_context` do Playwright (Parcial: proxy estático configurado no `.env`, resta lista rotativa de proxies).
- `[/]` 8.5 — Checkpoint SQLite por lote no `IGWorkerV2` (graceful shutdown) (Parcial: buffer SQLite no final do perfil, resta salvar a cada post raspado).
- `[x]` 8.6 — Expandir `core/circuit_breaker.py` para Supabase e Scraping (Auditado: `db_circuit_breaker` ativo no Supabase).
- `[ ]` Tabelas tabulares de gasto por usuário/perfil em `/admin/financeiro`.
- `[ ]` Análise de "Shadowban" léxico para termos ocultos pela plataforma.
- `[ ]` Exportação de Dossiês em lote para contas de agências.
