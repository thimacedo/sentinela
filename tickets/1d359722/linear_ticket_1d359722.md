---
id: 1d359722
title: "[T4] Persistir comentários reais com upsert id_externo"
status: Done
priority: Medium
order: 40
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

## Resultado
upsert com on_conflict=id_externo + ignore_duplicates=True implementado.
Duplicados contados corretamente (150 duplicados sem crash).
