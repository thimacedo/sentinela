---
id: 969ae71a
title: "[T2] Validar sessão Instagram via Zyte e tratar login wall"
status: "Backlog"
priority: "High"
order: 20
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Sessão expirando ou bloqueada por login wall do Instagram durante a extração via Zyte.

## Solution
Implementar lógica de detecção de login wall, rotacionar sessionid e aplicar backoff conforme necessário via Zyte.

## Implementation Details
- Monitorar estados de resposta do Zyte (200 vs 302/redirect).
- Rotacionar sessionid quando detectado login wall.
- Aplicar estratégia de backoff.
