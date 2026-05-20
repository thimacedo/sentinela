---
id: 39b51c65
title: "Credential Sanitization & Environment Cleanup"
status: "Todo"
priority: "Medium"
order: 30
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Vazamento potencial de `VITE_ANTHROPIC_API_KEY` e excesso de variáveis no Vercel.

## Solution
Remover chaves desnecessárias do frontend e validar o `.env.local`.

## Implementation Details
- Remover `VITE_ANTHROPIC_API_KEY` do `.env.local` e do Vercel.
- Garantir que apenas `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY` existam no frontend.
- Verificar `.vercelignore` para evitar uploads de arquivos sensíveis.
