# Sentinela — Referencia Arquitetural (PASA v50.1)
_last_updated: 2026-05-21_

## 1. Missao

Plataforma de inteligencia politica para deteccao automatizada de discurso de odio, desinformacao e atividade de milicia digital no Instagram brasileiro. Foco nas eleicoes de 2026.

## 2. Topologia de Infraestrutura

```
[Local / Render]
  watchdog.py
    └── main_runner.py
          └── SentinelaOrchestrator
                ├── IGZyteWorker      (Zyte API — Tier 3)
                └── IGHeadlessWorker  (Playwright — Tier 2)

[Vercel]
  proposta_frontend/   →  /api/*  →  api/index.py (FastAPI)
  supabase/functions/mcp-proxy/  (Edge Function — SQL semantico)

[Supabase]
  PostgreSQL + RLS
  Tables: candidatos, comentarios, fila_coleta, worker_rewards,
          worker_suggestions, worker_sessions, dossies, threat_alerts
```

## 3. Protocolo PASA v50.1

Todo comentario coletado passa pelo pipeline:

1. **Coleta** — Zyte API (JSON) → Browser Rendering → DOM fallback → Playwright
2. **Normalizacao** — `core/normalizer.py`
3. **Persistencia** — upsert `id_externo` (idempotente)
4. **Classificacao** — `AIService.classify_text()` cascade Groq → Mistral → OpenRouter
5. **Auditoria** — `pasa_auditor.py` + `AIAdvisor` (condicional, score<40)
6. **Alertas** — `AlertManager` → WhatsApp / Firebase

Categorias PASA: `NEUTRO`, `XENOFOBIA_REGIONAL`, `RACISMO_RELIGIOSO`, `VIOLENCIA_GENERO`, `MILICIA_DIGITAL`, `RACISMO_ESTRUTURAL`, `MISOGINIA_POLITICA`

## 4. Resiliencia Operacional

- **Circuit Breaker** — por provider de IA e por Zyte API (falhas fatais abrem por 1h, rate limit por 5min)
- **Watchdog** — monitora main_runner.py, reinicia em caso de crash
- **rotate_target idempotente** — upsert com on_conflict, nunca derruba por 23505
- **Blacklist de slots** — slots com login wall bloqueados no ciclo atual
- **Fallback em cascata** — Zyte JSON → Zyte Browser → Playwright headless
- **active_targets** — workers paralelos nunca processam o mesmo alvo

## 5. Estrategia de Coleta

- **Fila primaria**: `fila_coleta` (status=PENDENTE)
- **Fallback**: `candidatos` (order by last_scraped_at ASC)
- **Cooldown**: `last_scraped_at` atualizado apos coleta bem-sucedida
- **Paginacao**: `next_min_id` ate `max_comments_per_post=100` por post
- **Limite IA**: 10 classificacoes por ciclo para preservar circuit breakers

## 6. Seguranca

- SQL arbitrario bloqueado na Edge Function — apenas `{ action }` aceito
- `SUPABASE_SERVICE_KEY` exclusivo do backend
- `configs/instagram_storage_state.json` no .gitignore e .vercelignore
- AIAdvisor: apenas sugestoes com `status=pending_review` — nunca auto-aplica
- Sem hardcoding de credenciais — tudo via variaveis de ambiente

## 7. Frontend

- **Oficial**: `proposta_frontend/` — Next.js 16, React 19, Tailwind v4, shadcn/ui
- **Deploy**: Vercel (`Root Directory=proposta_frontend`)
- **Comunicacao**: `/api/*` FastAPI — sem SQL direto, sem chaves expostas
- **Tabs**: War Room, Analise Forense, Alvos, Dossies, Alertas, Rede, Fila de Coleta

## 8. SOP de Troubleshooting

| Sintoma | Acao |
|---|---|
| Login Wall Zyte slot=X | Renovar INSTAGRAM_SESSIONID_X |
| circuit_open zyte_api | Aguardar 10min ou verificar ZYTE_API_KEY |
| no_target_available | Normal — seen_targets limpo a cada ciclo |
| duplicate key fila_coleta | Corrigido — rotate_target em finally |
| IA classificados=0 | Verificar GROQ/MISTRAL/OPENROUTER API keys |
| score=0 tier=dry_run | Worker sem sessao valida ou sem target |
| Supabase offline | Verificar RLS policies e SUPABASE_URL/KEY |

## 9. Legado

- `archive_v17_2026/` — nao importar
- `.legacy_frontend/` — nao usar
- `src/` (Dashboard.jsx vanilla) — nao deployado, substituido por proposta_frontend
