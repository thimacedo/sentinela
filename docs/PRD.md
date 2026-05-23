# AI Advisor (Fase 4) PRD

## HR Eng

| AI Advisor PRD |  | Módulo de inteligência para análise de métricas e sugestões dos workers. |
| :---- | :---- | :---- |
| **Author**: Pickle Rick | **Status**: Draft | **Context**: Sentinela v50.1 |

## Introduction
O `AI_Advisor` é o cérebro que avalia a performance dos workers e sugere melhorias baseadas em dados históricos, evitando re-fetching de documentação.

## Problem Statement
Atualmente os workers rodam cegos, sem um advisor que integre a lógica de análise de falhas com LLMs. O sistema precisa aprender com o tempo e evitar chamadas repetitivas de API.

## Objective & Scope
**Objective:** Reduzir o tempo de análise de falhas e otimizar chamadas de LLM.
**Ideal Outcome:** Um advisor que consome `worker_docs_cache` e gera recomendações precisas.

### In-scope
- Implementação de `workers/ai/ai_advisor.py`.
- Integração com `worker_base.py`.
- Lógica de cache para evitar re-fetching de docs.

## Product Requirements

### Critical User Journeys (CUJs)
1. **Análise de Falha**: Worker identifica falha -> Advisor analisa -> Sugestão gerada.
2. **Otimização de Cache**: Worker busca docs -> Advisor checa `worker_docs_cache` -> Se existir, retorna cache.

### Functional Requirements

| Priority | Requirement | User Story |
| :---- | :---- | :---- |
| P0 | Cache de Docs | Como worker, quero carregar docs de `worker_docs_cache` para economizar tokens. |
| P0 | Análise LLM | Como sistema, quero uma análise LLM sobre falhas recorrentes. |

## Assumptions
- O `gemini` tem acesso ao `worker_docs_cache` via `MemoryStore`.

## Risks & Mitigations
- **Risk**: Alucinação do modelo. -> **Mitigation**: Auditoria cruzada com Groq/Llama 3.

## Success Metrics
- Redução de latência de análise em 50%.
- Aumento da taxa de acerto do cache de docs.

---
