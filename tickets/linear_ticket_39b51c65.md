---
id: 39b51c65
title: "Credential Sanitization & Environment Cleanup"
status: Done
priority: Medium
order: 30
created: 2026-05-20
updated: 2026-05-21
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

## Resultado
- ANTHROPIC_API_KEY nao encontrada em nenhum frontend (proposta_frontend, frontend, src/)
- Usada apenas como env var do servidor na Edge Function mcp-proxy
- .vercelignore reescrito (estava corrompido UTF-16): protege workers/, core/, configs/, .env*, sessoes
- Frontend oficial nao expoe nenhuma chave sensivel
