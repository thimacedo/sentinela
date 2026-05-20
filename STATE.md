# 📊 STATE.md - Sentinela Democrática

**Última Atualização:** 2026-05-18
**Versão Core:** PASA v50.1 (God Mode Data Layer)
**Status do Sistema:** Operação Real Ativada (Full React Query)

## 1. Estado Atual do Ecossistema
O Sentinela Democrática concluiu a modernização completa do frontend. O War Room agora é uma Single Page Application (SPA) robusta em Next.js 16, com sincronização em tempo real via React Query e visualização analítica via Recharts. A camada de dados ("God Mode") elimina latências e garante a integridade da informação forense.

## 2. Componentes Principais (v50.1)

### Frontend (Modernização Completa)
- **War Room Dashboard:** Interface unificada com abas funcionais para Geral, Forense, Alvos, Dossiês, Alertas, Rede e Fila.
- **God Mode Data Layer:** Implementação total de React Query para cache, pre-fetching e auto-refresh (10s-60s).
- **Análise Visual:** Gráficos de série temporal integrados para detecção de picos de atividade hostil.
- **Telemetria de Workers:** Monitoramento em tempo real da saúde e vazão dos motores de coleta.


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
