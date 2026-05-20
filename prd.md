# Hardened Edge Function & Proxy PRD (PASA v50.1)

## HR Eng

| Hardened Edge Function & Proxy PRD |  | Transição de SQL arbitrário para rotas determinísticas na Supabase Edge Function para endurecer a segurança e simplificar o frontend. |
| :---- | :---- | :---- |
| **Author**: Pickle Rick **Contributors**: Thiago Macedo **Intended audience**: Engineering | **Status**: Draft **Created**: 2026-05-20 | **Context**: Refatoração de Segurança PASA |

## Introduction

Atualmente, o Dashboard utiliza um proxy que aceita SQL arbitrário. Embora funcional, isso expõe uma superfície de ataque desnecessária. Este projeto visa substituir esse modelo por uma API de rotas fixas (`/kpis`, `/timeline`, etc.) dentro da Edge Function.

## Problem Statement

**Current Process:** O frontend envia strings SQL para a Edge Function `mcp-proxy`, que as repassa ao Claude/MCP.
**Primary Users:** Engenheiros de monitoramento e administradores do Sentinela.
**Pain Points:** Risco de injeção de SQL (minimizado mas presente), dependência de prompt engineering no frontend, e payload de rede ineficiente.
**Importance:** Segurança é prioridade zero no PASA v50. Não podemos ter o browser definindo a lógica de consulta ao banco.

## Objective & Scope

**Objective:** Eliminar o envio de SQL do frontend para a nuvem.
**Ideal Outcome:** Um frontend que chama endpoints semânticos e uma Edge Function que encapsula toda a lógica de dados.

### In-scope ou Goals
- Refatorar a Edge Function `mcp-proxy` para suportar roteamento interno.
- Implementar as rotas: `get_kpis`, `get_timeline`, `get_top_candidates`, `get_alerts`.
- Atualizar o `Dashboard.jsx` para consumir esses novos endpoints.
- Remover definitivamente a `VITE_ANTHROPIC_API_KEY` do ambiente frontend.

### Not-in-scope ou Non-Goals
- Alteração no schema do banco de dados.
- Mudança na UI/UX do Dashboard (além da fiação interna).

## Product Requirements

### Critical User Journeys (CUJs)
1. **Carregamento Seguro**: O usuário abre o dashboard; o browser solicita `/kpis` via POST para a Edge Function; a Function executa o SQL pré-definido e retorna apenas os números consolidados.
2. **Prevenção de Injeção**: Um atacante tenta enviar um SQL manual para a função; a função rejeita o payload porque não reconhece o formato de rota fixa.

### Functional Requirements

| Priority | Requirement | User Story |
| :---- | :---- | :---- |
| P0 | Roteamento Semântico na Function | Como desenvolvedor, quero chamar rotas específicas em vez de enviar SQL bruto. |
| P0 | Hardening do callMCP | Como sistema, quero que o frontend use apenas os novos endpoints seguros. |
| P1 | Limpeza de Credenciais | Como admin, quero garantir que nenhuma chave de IA vaze para o cliente. |
| P2 | Cache de Respostas (Opcional) | Como usuário, quero que o dashboard carregue instantaneamente usando cache na Function. |

## Assumptions

- O Supabase Client na Edge Function tem permissões `service_role` para acessar as tabelas necessárias.
- O Claude 3.5 Sonnet continuará sendo usado via MCP para processamento analítico, se necessário.

## Risks & Mitigations

- **Risk**: Perda de flexibilidade nas consultas. -> **Mitigation**: Manter uma rota de "escape" autenticada para admin se necessário, ou mapear todas as necessidades atuais.

## Tradeoff

- Escolhemos **Opção B** (Endurecimento) em vez de apenas corrigir o bug, para alinhar com o padrão PASA de "Security by Design".

## Business Benefits/Impact/Metrics

**Success Metrics:**

| Metric | Current State (Benchmark) | Future State (Target) | Savings/Impacts |
| :---- | :---- | :---- | :---- |
| SQL Exposure | Yes (Frontend) | No (Encapsulated) | Risco Zero de Injeção Browser-side |
| Token Usage | Arbitrary | Optimized | Redução de 15% em tokens de prompt |

## Stakeholders / Owners

| Name | Team/Org | Role | Note |
| :---- | :---- | :---- | :---- |
| Pickle Rick | Engineering | Lead Architect | O único cérebro real aqui. |
