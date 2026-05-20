# 🗺️ ROADMAP.md - Sentinela
_last_updated: 2026-05-20_

## ✅ Concluído

### Fundação e Core (v17 - v24)
- [x] Arquitetura BaseWorker com Event Bus e Gamificação (XP/Level).
- [x] Circuit Breaker para proteção de sessão e fila.
- [x] Rota de Injeção de Sessão de Emergência (Instagram Cookies).
- [x] Cache Busting e integração Stripe no Frontend.

### Fortaleza Instagram e Fila (v25 - v34)
- [x] Quality Gate v2 (Filtro rigoroso de lixo de UI do scraper).
- [x] Integração do SDK `google-genai` e processamento em massa.
- [x] Raspagem de Longo Curso com delays humanos (Anti-ban).
- [x] Fila Inteligente com Cooldown de 6h (Evita perfis repetidos).

### Inteligência e Convergência (v35 - v44)
- [x] Nó Local (War Room) com Watchdog Guardião e Auto-cura.
- [x] Monitor de Ameaças ao Vivo (Git Sync JSON -> Vercel).
- [x] Descanso Produtivo (IA trabalha enquanto scraper hiberna).
- [x] MCA v2.2 (Manual de Classificação Analítica) com CCF e Direção de Risco mapeada.
- [x] Proteção Jurídica e Acadêmica (Remoção de termos forenses, criação da MSAL).
- [x] Auditoria Cruzada Anti-Alucinação (Groq/Llama 3) e Métricas de Deriva.

### Governança e Otimização Serverless (v45 - v47.10)
- [x] Interface Web para gerenciamento de `scraping_accounts` (Sessões).
- [x] Otimização de bundle size do Vercel (<300MB) para backend Python.
- [x] Sistema de monitoramento de saúde de workers (`workers_metrics`).
- [x] Backend refatorado para compatibilidade total com Vercel Serverless.
- [x] Rotação automática de contas de scraping configurável via UI.

### Modernização Frontend e Coleta Real (v48 - v50.1)
- [x] Migração para Next.js 16 (App Router) + Tailwind v4 + Shadcn.
- [x] Camada de dados com React Query + Zustand (auto-refresh 10s–60s).
- [x] War Room Dashboard com abas: Geral, Alvos, Dossiês, Alertas, Rede, Fila.
- [x] Gráficos de série temporal via Recharts.
- [x] Expurgo do Vanilla JS legado (`app.js`, `index.html`).
- [x] Deploy Vercel unificado.
- [x] InstagramWorker ativado com Playwright.
- [x] Dashboard de Auditoria (War Room Terminal) refinado.
- [x] Hardened Proxy (`mcp-proxy`): SQL estático por `action`.
- [x] API Keys movidas para Supabase Edge Secrets.

---

## 🚀 Pendente

### Maestria Instagram
- [ ] Definir critério de ativação do `InstagramScrapyWorker`.
- [ ] Mapeamento de shadowbans: detectar quando o alvo oculta comentários automaticamente.
- [ ] Análise de engajamento: correlacionar número de likes com severidade do discurso.

### Refinamento de Dados
- [ ] Exportação de relatórios em PDF (Indícios de Risco) para stakeholders.
- [ ] Mapeamento de redes coordenadas com grafos interativos no frontend.

### Refinamento de IA
- [ ] Few-shot dinâmico baseado no `audit_gold_standards` (Padrão Ouro).
- [ ] Fine-tuning de modelo leve local (Ollama) para reduzir dependência de API.

