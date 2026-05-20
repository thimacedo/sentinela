---
id: fase4_t1
title: "Implementar DocFetcher"
status: Todo
priority: High
order: 10
created: 2026-05-20
updated: 2026-05-20
links:
  - url: linear_ticket_fase4_epic.md
    title: Parent
---

## Problema
Workers sem acesso a documentação atualizada das APIs alvo.

## Solução
Criar workers/ai/doc_fetcher.py com cache local e TTL por fonte.

## Arquivos
- workers/ai/doc_fetcher.py
- workers/config/api_docs/*.md (seed já criado)

## Critério de aceitação
- get_relevant("instagram") retorna conteúdo de instagram.md
- refresh_all() atualiza arquivos expirados sem erro
