# Task — Auditoria e Limpeza de Documentação
_last_updated: 2026-06-04_

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
- [x] Remover referências residuais a LiteRT no código operacional (limpeza de .env e health_check.py)
- [x] Sanear `config/fallback_providers.yaml` com providers realmente utilizáveis e ativos
- [x] Simplificar e unificar `workers/orchestrator/orchestrator.py` eliminando duplicidade
- [x] Padronizar semântica de idle entre workers ativos com Smart Wait de 10 min

## Pendências reais

- [ ] Corrigir sistema de alertas de WhatsApp (CallMeBot) — usuários reportam que não estão recebendo notificações.
- [ ] Resolver loop de auto-exclusão no `GuardLocker`: o processo está se identificando como zumbi e se matando no boot.
- [ ] Validar fluxo completo de coleta e classificação no Tray.
- [ ] Estabilizar Datasette (porta 8002) no Watchdog.
- [ ] revisar documentação metodológica histórica (limpar arquivamento obsoleto)

## Melhorias de Resiliência Concluídas

- [x] Adicionar status HTTP 400 (Bad Request) ao mecanismo de poda automática de provedores de IA
- [x] Aumentar timeout de verificação de sessão do Playwright de 30s para 45s para mitigar instabilidade de rede
- [x] Ajustar design semântico de cores do badge de ERRO para Roxo/Purple (distinto de Ódio e Neutro)
- [x] Inverter console de logs do watchdog local para exibir logs recentes no topo (prepend)
- [x] Comentar provedores de fallback inoperantes (deepseek_chat, openrouter, google_gemini, zhipu_glm4) no YAML de configuração para evitar erros no boot
- [x] Corrigir erro HTTP 400 no boot do DossierWorker inicializando status_column como None (fallback seguro para tabela vazia)
- [x] Limitar altura vertical do dashboard local no desktop à viewport (100vh) com rolagens internas independentes