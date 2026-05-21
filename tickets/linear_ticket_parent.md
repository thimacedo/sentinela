---
id: 19d172be
title: "[Epic] Hardened Edge Function & Proxy (PASA v50.1)"
status: "Todo"
priority: "High"
order: 0
created: 2026-05-20
updated: 2026-05-20
links:
  - url: prd.md
    title: PRD
---

# Description

## Problem to solve
O sistema atual permite SQL arbitrário vindo do frontend, o que é inseguro e ineficiente.

## Solution
Implementar roteamento semântico na Edge Function e endurecer o frontend para usar endpoints fixos.

## Implementation Details
- Ticket 1: Refatoração da Edge Function.
- Ticket 2: Atualização do Dashboard.jsx.
- Ticket 3: Saneamento de credenciais.
