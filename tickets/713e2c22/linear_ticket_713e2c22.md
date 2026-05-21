---
id: 713e2c22
title: "[T3] Implementar extração perfil → posts → comentários"
status: "Backlog"
priority: "High"
order: 30
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Extração incompleta: precisa percorrer a hierarquia correta perfil -> posts -> comentários.

## Solution
Criar worker que orquestra a navegação sequencial no Instagram usando Zyte.

## Implementation Details
- Navegação em cascata.
- Tratamento de paginação de comentários.
