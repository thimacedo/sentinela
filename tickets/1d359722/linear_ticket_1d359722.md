---
id: 1d359722
title: "[T4] Persistir comentários reais com upsert id_externo"
status: "Backlog"
priority: "Medium"
order: 40
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Duplicação de comentários ou falta de atualização caso existam alterações.

## Solution
Implementar upsert (INSERT ON CONFLICT) usando o ID externo do Instagram.

## Implementation Details
- Configurar trigger ou lógica de aplicação para upsert.
