---
id: b95403c6
title: "Harden Dashboard callMCP Integration"
status: Done
priority: High
order: 20
created: 2026-05-20
updated: 2026-05-21
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

## Resultado
Frontend oficial (proposta_frontend/src/) nao contem callMCP nem SQL bruto.
Toda comunicacao via /api/* endpoints FastAPI (api/index.py).
Dashboard.jsx legado isolado em src/ (nao deployado).
