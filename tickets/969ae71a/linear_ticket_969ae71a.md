---
id: 969ae71a
title: "[T2] Validar sessão Instagram via Zyte e tratar login wall"
status: Done
priority: High
order: 20
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

## Resultado
- _build_session_cookie(): selecao sequencial de slots (nao mais aleatoria)
- Slots com login wall adicionados a _blocked_slots e ignorados nas proximas tentativas
- Fallback para sessionid extraido do storage_state do Playwright
- Login wall detectado por multiplos indicadores (login-form, Log in to Instagram, etc)
