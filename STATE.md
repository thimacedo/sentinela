# 📊 STATE.md — Sentinela
_last_updated: 2026-05-20_
_Versão Core: PASA v50.1 (God Mode Data Layer)_
_Status: Produção Controlada (Aprovado)_

---

## 1. Status de Produção — v50.1-final
O caminho crítico de produção foi saneado, eliminando dependências legadas e consolidando a arquitetura.

- **Entrada oficial backend**: `main_runner.py`
- **Supervisor local**: `watchdog.py`
- **Orquestrador ativo**: `workers/orchestrator/orchestrator.py`
- **Frontend oficial**: `proposta_frontend/`
- **Deploy Vercel**: `Root Directory = proposta_frontend`
- **Legado isolado**: `archive_v17_2026/`

Componentes como `local_server.py`, `app/` e scrapers legados foram expurgados do caminho de execução e não devem ser reativados sem revisão arquitetural.

---

## 2. Critérios de Aceite para Produção Controlada
- [x] Vercel configurada com `Root Directory = proposta_frontend`
- [x] O build na Vercel utiliza `npm run build` e não artefatos pré-construídos.
- [x] URL pública responde sem 404.
- [x] Backend local (main_runner + watchdog) operacional e estável.
- [x] Legado isolado em `archive_v17_2026/`.

---

## 3. Variáveis de Ambiente
- **Frontend (Públicas)**: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_MCP_PROXY_URL`.
- **Backend (Privadas)**: `SUPABASE_SERVICE_KEY`, `INSTAGRAM_SESSIONID`, `ZYTE_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `CALLMEBOT_KEY`.
