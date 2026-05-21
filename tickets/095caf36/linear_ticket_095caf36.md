---
id: 095caf36
title: "[T5] Integrar classificação IA pós-persistência"
status: Done
priority: Medium
order: 50
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

## Resultado
Classificação IA disparada após persistência em ambos os workers.
Limitada a 10 comentários por ciclo para evitar circuit breaker.
Cascade Groq -> Mistral -> OpenRouter operacional.
