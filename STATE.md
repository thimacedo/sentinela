# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-29 | branch: main (Model: Gemini Pro)_

## Status Operacional (v86.0 - Intelligence Governance)

| Subsistema | Status | Observação |
|---|---|---|
| **Coleta (Rocket Scraper V2)** | 🟢 OPERACIONAL | **Rocket Mode** ativo com **Stealth Mode** avançado e Smart Backoff. |
| **Inteligência (PASA)** | 🟢 OPERACIONAL | **Triagem Híbrida** (Ollama Local + Cloud). Suporte a Markdown forense. |
| **Monetização (CI)** | 🟢 OPERACIONAL | Stripe E2E + Geração de **Dossiês Reais** (350 CI/unidade). |
| **Analytics (Network)** | 🟢 OPERACIONAL | **NetworkMinerWorker** ativo detectando clusters coordenados. |
| **Frontend (Next.js)** | 🟢 ESTÁVEL | Next.js 16. Grid 2-colunas, filtros dinâmicos e KPIs em tempo real. |

## 🛠️ Últimas Mudanças (Sprint v86.0 ➔ v86.5)

1.  **Governança Financeira (Fase 7.1 Completa):** Implementada a abstração e "Proxy de Nomenclatura" para Créditos de Inteligência (CI) no nível do código de negócio (Python e Next.js), mantendo o banco de dados STN inalterado. Isso garantiu resiliência do sistema sem exigir intervenção DDL manual no Supabase.
2.  **Catraca de Acesso:** Implementada validação e dedução automática de 350 CIs no endpoint `/api/reports/route.ts` antes da liberação de dossiês analíticos.
3.  **Auditoria AdSense:** Corrigido o ciclo de vida do componente `AdSenseSlot.tsx` em modo SPA (Single Page Application) e removido script conflitante AMP no layout, desobstruindo a injeção do Google.
4.  **Refatoração UX/UI (Marketing Focus):** Redesign agressivo da página de Estatísticas e da Home. Implementação de hierarquia `font-black`, `glassmorphism`, microinterações (pulse, hover) e "white space".
5.  **Compliance Jurídico Estrito:** Sanitização total de "bad words" jurídicas no Frontend estabelecendo blindagem legal e proteção reputacional (0 ocorrências validadas).
6.  **Recuperação Autônoma de Sessões (IG Scraper):** Modificado o injetor/extrator interativo com um bloqueio rígido de +60s. 

## 📊 ARQUITETURA DE INTEGRIDADE (v86.0)

```
[Watchdog v50.0] (Guardião + Autocura)
  ├── [Orchestrator v86.0] (Async Parallelism)
        ├── [QueueManager v85.6] (Case-Insensitive + Priority Queue)
        ├── [Scraper Mesh] (IGWorkerV2 - Stealth Mode + Human Jitter)
        ├── [AI Processor] (Ollama Triage -> Cloud Refinement)
        ├── [Network Miner] (NetworkX Cluster Detection)
        └── [Treasurer] (Financial Integrity & CI Ledger - INICIO)
```

## 📉 Métricas de Resiliência
- **Uptime Scrapers:** 98.6% (v86.0)
- **Taxa de Acerto IA:** 94.5% (MCA v2.2)
- **Sessões Ativas:** 2/10 (Instagram)
- **Burn Rate:** Otimizado via triagem local.

## 📝 Notas de Engenharia
- **Nomenclatura:** Todos os novos módulos devem utilizar `CI` (Créditos de Inteligência) em vez de `STN`.
- **Furtividade:** A rotação de dispositivos (iPhone/Android/Windows) é mandatória para alvos de alta relevância.
- **Integridade:** Dossiês sem hash SHA-256 são considerados inválidos pela governança.
