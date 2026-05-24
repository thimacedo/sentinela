# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-23 | branch: feat/autonomous-workers_

## Status Operacional

| Subsistema | Status | Observacao |
|---|---|---|
| Coleta Zyte (IGZyteWorker) | DESCARTADO | Substituído por IGWorkerV2 (independente) |
| Coleta Independente (IGWorkerV2) | Operacional | Motor Playwright V2 com rotação de sessões e backoff |
| Persistencia Supabase | OK | upsert id_externo, ignore_duplicates, duplicados contados corretamente |
| Classificacao IA | OK | 10/ciclo normal, batch de 50 no cooldown, cascade Mistral->Groq |
| Fila de Coleta | OK | rotate_target idempotente, 23505 tratado |
| RewardEngine | Operacional | score/tier/badges persistidos, get_interval() por tier |
| AIAdvisor | Condicional | Acionado apenas score<40 ou tier critical/db_failed |
| Watchdog | Operacional | Sem restarts em producao |
| Frontend (nextjs) | Deployado | Vercel, Next.js 16 (Estático na raiz), /api/* FastAPI |
| Edge Function (mcp-proxy) | Operacional | SQL arbitrario bloqueado, ROUTES semanticas |

## Descobertas Tecnicas (2026-05-23)
- **Implementação V2:** Criado `InstagramScraperV2` em `core/` focado em Playwright puro.
- **Resiliência:** Implementada rotação automática entre múltiplas sessões (`INSTAGRAM_SESSIONID_N`) e backoff exponencial.
- **Extração Multi-camada:** O motor V2 tenta Interceptação de Rede > Scripts (data-sjs) > Heurística DOM.
- **Independência:** O sistema não depende mais do Zyte ou outros serviços pagos para raspagem básica.
- **Validado:** Testado com sucesso via `scripts/test_scraper_v2.py`.

## Arquitetura Atual (v52.0)

```
watchdog.py
  └── main_runner.py
        └── SentinelaOrchestrator
              ├── _active_targets: set  (compartilhado entre workers)
              └── IGWorkerV2 (ig-v2-01)
                    ├── InstagramScraperV2 (Playwright Nativo)
                    │     ├── Multi-Session Rotation
                    │     ├── Exponential Backoff
                    │     └── Multi-Tier Extraction (Network > Scripts > DOM)
                    ├── persist_comments() → upsert candidato_id,post_shortcode,id_externo
                    └── classify_comments()
```

[... resto do arquivo mantido ...]
