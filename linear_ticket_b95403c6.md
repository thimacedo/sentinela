---
id: b95403c6
title: "Harden Dashboard callMCP Integration"
status: "Todo"
priority: "High"
order: 20
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
O frontend ainda envia SQL para a nuvem.

## Solution
Atualizar `Dashboard.jsx` para chamar os endpoints semânticos da Edge Function.

## Implementation Details
- Modificar `callMCP(projectId, action)` para enviar a `action` no body.
- Atualizar todos os `safeCall` para passar a `action` correta (ex: `get_kpis`) em vez de SQL bruto.
