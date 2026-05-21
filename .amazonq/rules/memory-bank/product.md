# Sentinela Democrática — Product Overview

## Purpose
Sentinela Democrática is a political intelligence and threat monitoring platform designed to detect hate speech, disinformation, and coordinated digital militia activity in Brazilian political social media (primarily Instagram). It operates under the PASA (Protocolo de Análise Semântica e Ameaças) framework, currently at v50.1.

## Core Value Proposition
- Automated collection of political comments from Instagram profiles of Brazilian candidates
- AI-powered forensic classification of hate speech using multi-provider LLM cascade
- Real-time threat alerting and dossier generation for monitored political targets
- Operational war room dashboard for analysts to review, classify, and act on threats

## Key Features

### Data Collection
- Multi-tier Instagram scraping: Zyte API (Tier 3), Playwright headless (Tier 2)
- Priority-based target queue with cooldown management
- Scrapy-based spider infrastructure (`sentinela_novo/`, `sentinela_scraper/`, `sentinela_scrapy/`)
- Session management for authenticated Instagram access

### AI Classification (PASA Engine)
- Cascading AI providers: Groq → Mistral → OpenRouter (fallback chain)
- Circuit breaker pattern per provider to handle API failures gracefully
- Categories: NEUTRO, XENOFOBIA_REGIONAL, RACISMO_RELIGIOSO, VIOLÊNCIA_GÊNERO, MILICIA_DIGITAL, RACISMO_ESTRUTURAL, MISOGINIA_POLITICA
- Forensic linguistic analysis based on Vichi methodology

### Backend Workers
- Async worker architecture with `BaseWorker` ABC contract
- `SentinelaOrchestrator` manages worker lifecycle and cycle execution
- `RewardEngine` scores worker performance per cycle (tier-based intervals)
- `AIAdvisor` provides adaptive suggestions when workers degrade

### Alerting & Reporting
- WhatsApp and Firebase push alerts for high-severity threats
- PDF dossier generation for monitored candidates
- KPI snapshots and performance ledger tracking

### Frontend (War Room)
- Next.js 16 + React 19 + TypeScript dashboard (`proposta_frontend/`)
- Tabs: War Room, Forensic Analysis, Target Management, Dossiers, Alerts, Network Analysis, Collection Queue
- Dark theme (bg `#020817`) with Tailwind CSS v4 + shadcn/ui + Radix UI
- Deployed on Vercel with `Root Directory = proposta_frontend`

## Target Users
- Political campaign analysts and security teams
- Democratic oversight organizations monitoring Brazilian elections (2026 cycle)
- Forensic linguists and researchers studying online political violence

## Election Context
Focused on the 2026 Brazilian elections — candidate profiles, regional reports, and priority targets are pre-loaded for all 27 states.
