---
id: 713e2c22
title: "[T3] Implementar extração perfil → posts → comentários"
status: Done
priority: High
order: 30
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

## Resultado
- _fetch_comments_paginated(): paginacao via next_min_id ate max_comments_per_post (default 100)
- Loop interrompe quando next_min_id ausente ou repetido
- max_comments_per_post configuravel via config dict do worker
- Hierarquia completa: perfil -> posts (max_posts) -> comentarios paginados
