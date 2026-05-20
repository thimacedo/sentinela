# 📊 STATE.md - Sentinela Democrática

**Última Atualização:** 2026-05-18
**Versão Core:** PASA v50.0 (Diamond Real Data)
**Status do Sistema:** Operação Real Ativada (Zero Mocks)

## 1. Estado Atual do Ecossistema
O Sentinela Democrática concluiu a transição para o pipeline de dados 100% reais. O Nó Local (War Room) agora opera com coleta ativa via Playwright, processamento de IA em massa (Gemini/Groq) e auditoria anti-alucinação. Todas as simulações e dados fictícios foram removidos do repositório.

## 2. Componentes Principais (v50.0)

### Frontend (Modernização)
- **War Room Dashboard:** 100% funcional com Next.js 16 e Tailwind v4.
- **Integração Supabase:** Componentes `DashboardStats`, `TargetsTab` e `ForensicTab` consumindo dados reais via `@supabase/supabase-js`.
- **Zero Mocks:** Remoção total de placeholders estáticos; o frontend agora reflete fielmente o estado das tabelas `candidatos` e `comentarios`.

### Nó Local & Coleta (Real)
- **InstagramWorker:** Ativado com motor Playwright (`scraper_headless.py`). Realiza raspagem via navegação por modal e extração de comentários autênticos.
- **Scrapy Standby:** Motor Scrapy disponível em `InstagramScrapyWorker` para volumes massivos (mantido OFF).
- **Integridade:** Monitor de API (`api/monitor.py`) blindado contra dados fake; reporta erro ou zero em falhas no Supabase.

### Inteligência Analítica
- **Classificação IA:** Motor real ativado via `AIService` (Gemini 1.5 Flash + Groq Cascading).
- **CCF Framework:** Classificação baseada em Densidade, Sincronia e Performatividade.
- **Auditoria:** `AuditWorker` ativo para verificação cruzada e detecção de deriva (Drift Check).

### Governança e Interface
- **War Room UI:** Redesenhada para visual sutil e moderno com cores ANSI e logs em tempo real.
- **Watchdog:** Guardião ativo com auto-cura de dependências e alertas via WhatsApp (CallMeBot).

## 3. Proteções Jurídicas e Acadêmicas
- **MCA v2.2:** Manual de Classificação Analítica consolidado.
- **Terminologia:** Uso estrito de "Indícios Analíticos" e "Informação Situacional" para evitar conflitos forenses.
