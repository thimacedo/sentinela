---
id: 842307d7
title: "Refactor Edge Function for Semantic Routing"
status: Done
priority: High
order: 10
created: 2026-05-20
updated: 2026-05-21
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

## Resultado
supabase/functions/mcp-proxy/index.ts ja implementado com:
- ROUTES: allowlist de actions (get_kpis, get_timeline, get_top_candidates, get_alerts, get_queue, get_dossiers)
- SQL arbitrario bloqueado: body.sql retorna 403
- Allowlist de projectId via ALLOWED_PROJECT_IDS env
- Frontend oficial (proposta_frontend) nao usa mcp-proxy, usa /api/* FastAPI
