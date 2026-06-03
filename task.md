# Task — Auditoria e Limpeza de Documentação
_last_updated: 2026-06-03_

## Concluído

- [x] Auditar documentação central contra o código real
- [x] Confirmar que LiteRT saiu do pipeline ativo
- [x] Confirmar que a fila atômica já está implantada no código
- [x] Reescrever `README.md`
- [x] Reescrever `docs/index_documentacao.md`
- [x] Reescrever `docs/SYSTEM_CONTEXT.md`
- [x] Reescrever `ROADMAP.md`
- [x] Reescrever `walkthrough.md`
- [x] Criar `docs/DOCUMENTATION_AUDIT.md`
- [x] Limpar e reescrever `STATE.md`
- [x] Refatorar `researcher-01` para não subir sem backlog real
- [x] Expurgar contratos e entrypoints legados de workers
- [x] Absorver padrão ouro legado em `core/ai_service.py`
- [x] Atualizar scripts operacionais para o runtime moderno
- [x] Documentar o estado atual da refatoração de workers

## Pendências reais

- [ ] remover referências residuais a LiteRT no código operacional
- [ ] revisar documentação metodológica histórica
- [ ] sanear `config/fallback_providers.yaml` com providers realmente utilizáveis
- [ ] simplificar `workers/orchestrator/orchestrator.py`
- [ ] padronizar semântica de idle entre workers ativos