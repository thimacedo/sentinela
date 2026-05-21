---
id: 02ec93bd
title: "[T6] Validação runtime: simulated=False, db=ok, ia=ok/pendente"
status: Done
priority: Medium
order: 60
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

## Resultado
Validado em produção via watchdog.py:
- simulated=False confirmado em ambos os workers
- db=ok (150 inseridos/duplicados sem crash)
- ia=nao (correto — tudo duplicado, inserted=0, IA não chamada)
- rotate_target idempotente (23505 não derruba mais)
- watchdog não reiniciou
