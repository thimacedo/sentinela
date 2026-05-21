---
id: 842307d7
title: "Refactor Edge Function for Semantic Routing"
status: "Todo"
priority: "High"
order: 10
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
O proxy atual aceita SQL arbitrário do browser.

## Solution
Modificar `supabase/functions/mcp-proxy/index.ts` para aceitar um `action` no body (ex: `get_kpis`) e executar o SQL correspondente no servidor.

## Implementation Details
- Mapear rotas: `get_kpis`, `get_timeline`, `get_top_candidates`, `get_alerts`.
- Validar payload.
- Bloquear qualquer entrada que não seja uma rota pré-definida.
