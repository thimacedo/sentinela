---
id: fase4_t2
title: "Implementar AIAdvisor"
status: Todo
priority: High
order: 20
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_fase4_epic.md
    title: Parent
---

## Problema
Workers degradam sem análise automática de causa.

## Solução
Criar workers/ai/advisor.py que analisa métricas via Groq e salva sugestões.

## Arquivos
- workers/ai/advisor.py

## Critério de aceitação
- analyze_and_suggest() gera sugestão e salva em worker_suggestions
- Sugestão tem status pending_review
- Nunca aplica patch automaticamente
