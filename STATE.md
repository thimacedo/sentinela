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

## 🛠️ Últimas Mudanças (Sprint v85.2 ➔ v86.0)

1.  **Motor de Coleta:** Implementado **Stealth Mode** com rotação de User-Agents/Viewports e bypass de fingerprint. Fim da trava de validação para novos alvos.
2.  **Inteligência Local:** Integrado **Ollama** para triagem inicial de custo zero. Redução de ~50% no consumo de APIs externas.
3.  **Dossiês Forenses:** Ativada a geração real de PDFs via `DossieService` com assinatura **SHA-256** e selo de integridade.
4.  **UX de Análise:** Implementada renderização **Markdown** nos cards e exibição do **Parecer Técnico** da IA. Correção de filtro dinâmico por URL.
5.  **Otimização Ociosa:** Implementado **Smart Wait** (10 min em idle) e **Background Utility Tasks** (re-análise automática).
6.  **Governança Financeira:** Iniciada migração semântica de **STN para CI (Créditos de Inteligência)**.

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
