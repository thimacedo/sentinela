---
id: 095caf36
title: "[T5] Integrar classificação IA pós-persistência"
status: "Backlog"
priority: "Medium"
order: 50
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Os comentários persistem mas não são classificados automaticamente.

## Solution
Disparar worker de IA após a persistência bem-sucedida do comentário.

## Implementation Details
- Event-driven (DB trigger ou Pub/Sub).
