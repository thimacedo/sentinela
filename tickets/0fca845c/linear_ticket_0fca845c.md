---
id: 0fca845c
title: "[T1] Corrigir persist_comments para schema real da tabela comentarios"
status: "Todo"
priority: "High"
order: 10
created: 2026-05-21
updated: 2026-05-21
links:
  - url: ../epic_zyte_v50_1/linear_ticket_zyte_parent.md
    title: Parent Ticket
---

# Description

## Problem to solve
Erro de persistência: campos 'data_postagem' inexistentes na tabela comentarios.

## Solution
Atualizar a função de persistência para usar 'data_publicacao' e 'post_shortcode'.

## Implementation Details
- Mapeamento direto de campos conforme schema SQL da tabela.
