---
id: fase4_t3
title: "Implementar Workers Concretos"
status: Done
priority: High
order: 30
created: 2026-05-20
updated: 2026-05-21
links:
  - url: linear_ticket_fase4_epic.md
    title: Parent
---

## Problema
Sem coleta real de dados do Instagram.

## Solução
IGHeadlessWorker e IGZyteWorker implementados herdando de BaseWorker.

## Resultado
- IGHeadlessWorker coleta via Playwright (150 comentários validados em produção)
- IGZyteWorker coleta via Zyte API com fallback headless
- CycleResult retornado corretamente em ambos
- active_targets compartilhado via orquestrador (workers pegam alvos diferentes)
