---
id: fase4_t3
title: "Implementar Workers Concretos"
status: Todo
priority: High
order: 30
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_fase4_epic.md
    title: Parent
---

## Problema
Sem coleta real de dados do Instagram.

## Solução
Implementar IGHeadlessWorker e IGZyteWorker herdando de BaseWorker.

## Arquivos
- workers/scrapers/ig_headless.py
- workers/scrapers/ig_zyte.py

## Critério de aceitação
- 1 ciclo isolado coleta >= 1 item sem erro
- WorkerMetrics retornado corretamente
