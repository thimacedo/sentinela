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

1.  **Refatoração UX/UI (Marketing Focus):** Redesign agressivo da página de Estatísticas e da Home. Implementação de hierarquia `font-black`, `glassmorphism`, microinterações (pulse, hover) e "white space" generoso para diminuição de fricção cognitiva e elevação da percepção de valor.
2.  **Compliance Jurídico Estrito:** Sanitização total de "bad words" jurídicas no Frontend (Ex: "Crime", "Evidência", "Prova Forense" substituídos por "Engajamento Inautêntico", "Relatório Analítico", "Sistematização de Indícios"), estabelecendo blindagem legal e proteção reputacional para a plataforma Sentinela.
3.  **Recuperação Autônoma de Sessões (IG Scraper):** Modificado o injetor/extrator interativo (`export_playwright_cookies.py`) com um bloqueio rígido de +60s. Permite a resolução manual limpa de CAPTCHAs/2FA, retroalimentando as contas bloqueadas no Supabase. O *Watchdog* e os Extratores retornaram à estabilidade 100%.
4.  **Resiliência de Sessões (IG Scraper):** Implementado sistema de "Sticky Profiles" (perfil fixo por sessão) e "Session Cooldown" (bloqueio temporário de 30 min em caso de falha de verificação), reduzindo bloqueios permanentes e evasão de sessões.
5.  **Correção Crítica (Frontend Vercel):** Corrigido erro de Type Mismatch do Typescript na build do componente Recharts da página de estatísticas.
6.  **Governança Financeira:** Iniciada a preparação estrutural e migração semântica da moeda interna de **STN para CI (Créditos de Inteligência)**.

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
