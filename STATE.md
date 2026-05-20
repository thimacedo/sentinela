# 📊 STATE.md — Sentinela
_last_updated: 2026-05-20_
_Versão Core: PASA v50.1 (God Mode Data Layer)_
_Status: Operação Real Ativa_

---

## 1. Estado Atual do Ecossistema
O Sentinela concluiu a modernização completa do frontend e da camada de segurança. O War Room é uma SPA em Next.js 16 com sincronização em tempo real via React Query e visualização analítica via Recharts. O backend foi migrado para arquitetura Hardened Proxy, eliminando exposição de SQL e credenciais no cliente.

---

## 2. Componentes Principais (v50.1)

### Frontend
| Componente | Status | Descrição |
|------------|--------|-----------|
| War Room Dashboard | ✅ Ativo | Abas: Geral, Alvos, Dossiês, Alertas, Rede, Fila |
| React Query Data Layer | ✅ Ativo | Cache, pre-fetching e auto-refresh (10s–60s) |
| Gráficos Recharts | ✅ Ativo | Série temporal para detecção de picos de atividade |
| Telemetria de Workers | ✅ Ativo | Monitoramento em tempo real de saúde e vazão |
| Legado Vanilla JS | ✅ Removido | `app.js` e `index.html` expurgados |

### Backend e Segurança
| Componente | Status | Descrição |
|------------|--------|-----------|
| Hardened Proxy (`mcp-proxy`) | ✅ Ativo | SQL estático por `action`; sem SQL bruto no frontend |
| API Keys | ✅ Migrado | Movidas para Supabase Edge Secrets |
| RLS Supabase | ✅ Ativo | Row Level Security configurada em todas as tabelas |

### Coleta
| Componente | Status | Descrição |
|------------|--------|-----------|
| InstagramWorker (Playwright) | ✅ Ativo | Extração de comentários via navegação por Modal |
| InstagramScrapyWorker | ⏸️ Stand-by | Motor para volumes massivos — aguarda critério de ativação |
### Orquestração de Fluxo (Dual-Engine)
| Componente | Status | Descrição |
|------------|--------|-----------|
| `main_runner.py` | ✅ Ativo | Consumidor de filas (pg_queue). Roda `AlertWorker`, `CleanupWorker`. |
| `orchestrator.py`| ✅ Ativo | Iniciador de scrapers (`IGZyteWorker`). Roda ciclo de coleta. |

### Inteligência Analítica
| Componente | Status | Descrição |
|------------|--------|-----------|
| AIService (Gemini 1.5 Flash) | ✅ Ativo | Classificação primária de risco e padrões de discurso |
| Auditoria Cruzada (Groq/Llama 3) | ✅ Ativo | Validação anti-alucinação e detecção de deriva |
| CCF Framework | ✅ Ativo | Classificação por Densidade, Sincronia e Performatividade |
| MCA v2.2 | ✅ Vigente | Manual de Classificação Analítica — referência obrigatória |

---

## 3. Proteções Jurídicas e Acadêmicas
- **MCA v2.2** vigente como referência de classificação.
- **Terminologia obrigatória**: "Indícios Analíticos", "Informação Situacional", "análise analítica".
- **Termos proibidos em todo o projeto**: "forense", "prova", "evidência".

---

## 4. Abordagens Descartadas (Anti-Regressão)
> Proibido retomar qualquer item desta lista.

| Abordagem | Motivo |
|-----------|--------|
| SQL bruto enviado pelo frontend | Vetor de injeção — substituído por Hardened Proxy |
| `ANON_KEY` com acesso de escrita | Risco de bypass de RLS |
| ORM no frontend | Overhead de bundle + acoplamento ao schema |
| Rotação forçada de `sessionid` | Aumenta risco de ban — usar backoff exponencial |
| Mocks/dados simulados em produção | Viola integridade analítica |
| Supabase/Docker local | Banco é sempre remoto |

---

## 5. Variáveis de Ambiente Obrigatórias

| Variável | Escopo | Descrição |
|----------|--------|-----------|
| `SUPABASE_URL` | Backend + Frontend | URL do projeto Supabase |
| `SUPABASE_ANON_KEY` | Frontend (leitura) | Chave pública — RLS deve estar ativa |
| `SUPABASE_SERVICE_KEY` | Backend apenas | Chave irrestrita — nunca expor no cliente |
| `INSTAGRAM_SESSIONID` | Backend | Cookie de sessão da conta focalizadora |
| `ZYTE_API_KEY` | Backend | Chave de autenticação Zyte |
| `GEMINI_API_KEY` | Backend | Chave Google AI (Gemini 1.5 Flash) |
| `GROQ_API_KEY` | Backend | Chave Groq (Llama 3) |
| `CALLMEBOT_KEY` | Backend | Chave WhatsApp para alertas do Watchdog |

---

## 6. Snapshot de Progresso

```
[✅] Fase 1 — Definição de arquitetura e schema do banco
[✅] Fase 2 — Migrations e tabelas criadas
[✅] Fase 3 — Estrutura base (memory, reward, base)
[✅] Fase 4 — DocFetcher, AIAdvisor e Workers (IGHeadless+IGZyte)
[✅] Fase 5 — Orquestração Massiva e Integração final
[✅] Fase 6 — Deploy e Monitoramento em Produção
---
## Frontend Oficial

O frontend oficial do Sentinela PASA v50.1 está em:

`proposta_frontend/`

A Vercel deve usar:

`Root Directory = proposta_frontend`

O backend Python permanece fora do deploy Vercel e roda localmente via:

`watchdog.py -> main_runner.py`
```
