# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-23 | branch: feat/autonomous-workers_

## Status Operacional

| Subsistema | Status | Observacao |
|---|---|---|
| Coleta Zyte (IGZyteWorker) | Desativado | Desativado via ENABLE_ZYTE=false no .env |
| Coleta Headless (IGHeadlessWorker) | Operacional | 150 comentarios/ciclo validados em producao |
| Persistencia Supabase | OK | upsert id_externo, ignore_duplicates, duplicados contados corretamente |
| Classificacao IA | OK | 10/ciclo normal, batch de 50 no cooldown, cascade Mistral->Groq |
| Fila de Coleta | OK | rotate_target idempotente, 23505 tratado |
| RewardEngine | Operacional | score/tier/badges persistidos, get_interval() por tier |
| AIAdvisor | Condicional | Acionado apenas score<40 ou tier critical/db_failed |
| Watchdog | Operacional | Sem restarts em producao |
| Frontend (proposta_frontend) | Deployado | Vercel, Next.js 16, /api/* FastAPI |
| Edge Function (mcp-proxy) | Operacional | SQL arbitrario bloqueado, ROUTES semanticas |

## Arquitetura Atual (v50.1)

```
watchdog.py
  └── main_runner.py
        └── SentinelaOrchestrator
              ├── _active_targets: set  (compartilhado entre workers)
              ├── IGZyteWorker (ig-zyte-01)
              │     ├── _build_session_cookie()  → slots sequenciais + blacklist + storage_state
              │     ├── fetch_comments_via_zyte() → perfil → posts → _fetch_comments_paginated()
              │     ├── persist_comments()        → upsert id_externo
              │     └── classify_comments()       → limite 10/ciclo
              └── IGHeadlessWorker (ig-headless-01)
                    ├── InstagramHeadlessScraper  → Playwright + IdentityManager
                    ├── persist_comments()        → upsert id_externo
                    └── classify_comments()       → limite 10/ciclo

CycleResult → RewardEngine.process_result() → RewardSummary (score, tier, badges)
           → MemoryStore.save_reward()       → worker_rewards (Supabase)
           → AIAdvisor (condicional)         → worker_suggestions (Supabase)
```

## Fluxo de Dados

```
Instagram
  └── Zyte API / Playwright
        └── comentarios (Supabase)
              └── AIService.classify_text()  [Mistral → Groq → OpenRouter]
                    └── comentarios.processado_ia = True
                          └── AlertManager → WhatsApp / Firebase
                          └── DossierWorker → PDF
```

## Sessoes e Autenticacao

- `INSTAGRAM_SESSIONID*` — slots sequenciais, slots com login wall adicionados a `_blocked_slots`
- `INSTAGRAM_COOKIE_FULL` — prioridade maxima se presente, atualizado automaticamente pelo script `scripts/export_playwright_cookies.py`
- `configs/instagram_storage_state.json` — fallback Playwright (validado via `scripts/probe_t3_2_storage.py`)
- Validacao do storage_state: abre perfil real do Supabase, checa URL + HTML (sem seletores frageis)

## Fila de Coleta

- Fonte primaria: `fila_coleta` (status=PENDENTE)
- Fallback: `candidatos` (status_monitoramento=Ativo, order by last_scraped_at ASC)
- `rotate_target()`: upsert com on_conflict=candidato_id,data_agendada + ignore_duplicates
- `active_targets`: set compartilhado via orquestrador — workers pegam alvos diferentes no mesmo ciclo

## Sistema de Recompensas

| Tier | Score | Intervalo |
|---|---|---|
| platinum | >= 85 | 120s |
| gold | >= 70 | 180s |
| silver | >= 50 | 300s |
| bronze | >= 25 | 480s |
| critical | < 25 | 600s |
| db_failed | — | 600s |

Score calculado por: extracted (+1.0/item, max 15) + inserted (+2.0/item, max 25) + classified (+1.5/item, max 15) + duplicated (+0.3/item, max 5) - failed (-5.0/item, max -35) + bonus perfeicao (+10 se success_rate>=95 e failed==0)

## Variaveis de Ambiente Necessarias

```
# Supabase
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY   # backend only, nunca frontend

# Instagram
ZYTE_API_KEY
INSTAGRAM_SESSIONID    # slot principal
INSTAGRAM_SESSIONID_2  # slot adicional (opcional)
INSTAGRAM_COOKIE_FULL  # cookie completo (opcional, prioridade maxima)

# IA
MISTRAL_API_KEY
GROQ_API_KEY
OPENROUTER_API_KEY

# Seguranca
DASHBOARD_PIN
SENTINELA_ADMIN_TOTP_SECRET
WATCHDOG_ACTIVE        # true = formato de log compacto
```

## Regras Criticas

1. Nunca enviar SQL bruto pelo frontend
2. `SUPABASE_SERVICE_KEY` apenas no backend
3. Nunca importar de `archive_v17_2026/` ou `.legacy_frontend/`
4. `configs/instagram_storage_state.json` nunca commitar (protegido no .gitignore)
5. AIAdvisor nunca aplica patches automaticamente — apenas salva sugestoes com status=pending_review

## Comandos Operacionais

```bash
# Backend
python main_runner.py          # orquestrador principal
python watchdog.py             # supervisor com auto-restart

# Validacao de sessao
python scripts/probe_t3_2_storage.py

# Frontend
cd proposta_frontend && bun run dev
cd proposta_frontend && bun run build

# Migrations
python scripts/apply_migration.py
```

## Ultimas Atualizacoes (Refatoracao Raspagem e Classificacao)
- Corrigidos wrappers de modulos: `InstagramWorker` agindo como proxy para `IGZyteWorker`.
- Adicionada injecao de cookies (`requestCookies`) no `IGZyteWorker` permitindo fallback de Browser Rendering via Zyte com sessoes autenticadas.
- Resolvido conversao de shortcode para `media_id` para lidar com DOM scraping.
- Corrigida referencia da ForeignKey na tabela `comentarios`, usando `candidato_id` mapeado para o `username` do alvo.
- Teste completo end-to-end rodando com sucesso no alvo `lulaoficial`, incluindo extracao, persistencia e classificacao por IA (fallback Mistral ativado devido a limite Groq).
- Corrigido constraint `worker_rewards_tier_check` em `reward_engine.py` rebaixando o tier `platinum` para `gold` garantindo persistencia da gamificacao dos workers sem crash do Orquestrador.
- Restabelecida a API Mistral como motor primário e Groq como fallback secundário para evitar problemas de quota e API keys ausentes no ambiente.
- Implementada classificação em lote de até 50 comentários quando a coleta Zyte está em cooldown.
- Removido o limite rígido de 10 classificações por ciclo nos scrapers `IGZyteWorker` e `IGHeadlessWorker`, classificando todos os itens novos de forma imediata (Fase 4 - executado por Gemini 3.5 Flash).
- Corrigida a inicialização do Supabase no dashboard local (`local_dashboard.html`) renomeando as constantes para evitar colisão com o construtor `window.URL` nativo do JS.
- Silenciados os warnings do Tailwind CDN no console do painel local.
- Adicionado tratamento para requisições de `/favicon.ico` no servidor FastAPI do watchdog para eliminar os erros 404.
- Corrigida falha de inserção de caracteres nulos (\u0000) no Supabase (Erro 22P05) através de sanitização automática no serviço de IA (ai_service.py) e na persistência inicial de comentários nos workers oficiais ig_zyte.py e ig_headless.py.
- Atualizados modelos de IA descontinuados para llama-3.3-70b-versatile na Groq e openrouter/free no OpenRouter (Fase 4 - executado por gemini-2.5-pro-preview).
- Criado o ponto de entrada watchdog/__main__.py habilitando a execução nativa e modular do supervisor via python -m watchdog.
- Corrigido problema de alvos repetidos na fila através da antecipação de mark_candidate_scraped no início do ciclo de execução dos scrapers, assegurando o cooldown mesmo em coletas vazias ou com erro (Fase 4 - executado por gemini-2.5-pro-preview).
- Corrigidas as falhas de falso-positivo de reputação: coletas vazias legítimas (no_comments_found) deixam de sofrer penalidade de -15 de XP, e suspensões por reputação zero nos orquestradores foram limitadas apenas a ciclos com perda real de pontuação (delta < 0), eliminando loops de suspensão indevida (Fase 4 - executado por gemini-2.5-pro-preview).
# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-23 | branch: feat/autonomous-workers_

## Status Operacional

| Subsistema | Status | Observacao |
|---|---|---|
| Coleta Zyte (IGZyteWorker) | Desativado | Desativado via ENABLE_ZYTE=false no .env |
| Coleta Headless (IGHeadlessWorker) | Operacional | 150 comentarios/ciclo validados em producao |
| Persistencia Supabase | OK | upsert id_externo, ignore_duplicates, duplicados contados corretamente |
| Classificacao IA | OK | 10/ciclo normal, batch de 50 no cooldown, cascade Mistral->Groq |
| Fila de Coleta | OK | rotate_target idempotente, 23505 tratado |
| RewardEngine | Operacional | score/tier/badges persistidos, get_interval() por tier |
| AIAdvisor | Condicional | Acionado apenas score<40 ou tier critical/db_failed |
| Watchdog | Operacional | Sem restarts em producao |
| Frontend (proposta_frontend) | Deployado | Vercel, Next.js 16, /api/* FastAPI |
| Edge Function (mcp-proxy) | Operacional | SQL arbitrario bloqueado, ROUTES semanticas |

## Arquitetura Atual (v50.1)

```
watchdog.py
  └── main_runner.py
        └── SentinelaOrchestrator
              ├── _active_targets: set  (compartilhado entre workers)
              ├── IGZyteWorker (ig-zyte-01)
              │     ├── _build_session_cookie()  → slots sequenciais + blacklist + storage_state
              │     ├── fetch_comments_via_zyte() → perfil → posts → _fetch_comments_paginated()
              │     ├── persist_comments()        → upsert id_externo
              │     └── classify_comments()       → limite 10/ciclo
              └── IGHeadlessWorker (ig-headless-01)
                    ├── InstagramHeadlessScraper  → Playwright + IdentityManager
                    ├── persist_comments()        → upsert id_externo
                    └── classify_comments()       → limite 10/ciclo

CycleResult → RewardEngine.process_result() → RewardSummary (score, tier, badges)
           → MemoryStore.save_reward()       → worker_rewards (Supabase)
           → AIAdvisor (condicional)         → worker_suggestions (Supabase)
```

## Fluxo de Dados

```
Instagram
  └── Zyte API / Playwright
        └── comentarios (Supabase)
              └── AIService.classify_text()  [Mistral → Groq → OpenRouter]
                    └── comentarios.processado_ia = True
                          └── AlertManager → WhatsApp / Firebase
                          └── DossierWorker → PDF
```

## Sessoes e Autenticacao

- `INSTAGRAM_SESSIONID*` — slots sequenciais, slots com login wall adicionados a `_blocked_slots`
- `INSTAGRAM_COOKIE_FULL` — prioridade maxima se presente, atualizado automaticamente pelo script `scripts/export_playwright_cookies.py`
- `configs/instagram_storage_state.json` — fallback Playwright (validado via `scripts/probe_t3_2_storage.py`)
- Validacao do storage_state: abre perfil real do Supabase, checa URL + HTML (sem seletores frageis)

## Fila de Coleta

- Fonte primaria: `fila_coleta` (status=PENDENTE)
- Fallback: `candidatos` (status_monitoramento=Ativo, order by last_scraped_at ASC)
- `rotate_target()`: upsert com on_conflict=candidato_id,data_agendada + ignore_duplicates
- `active_targets`: set compartilhado via orquestrador — workers pegam alvos diferentes no mesmo ciclo

## Sistema de Recompensas

| Tier | Score | Intervalo |
|---|---|---|
| platinum | >= 85 | 120s |
| gold | >= 70 | 180s |
| silver | >= 50 | 300s |
| bronze | >= 25 | 480s |
| critical | < 25 | 600s |
| db_failed | — | 600s |

Score calculado por: extracted (+1.0/item, max 15) + inserted (+2.0/item, max 25) + classified (+1.5/item, max 15) + duplicated (+0.3/item, max 5) - failed (-5.0/item, max -35) + bonus perfeicao (+10 se success_rate>=95 e failed==0)

## Variaveis de Ambiente Necessarias

```
# Supabase
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY   # backend only, nunca frontend

# Instagram
ZYTE_API_KEY
INSTAGRAM_SESSIONID    # slot principal
INSTAGRAM_SESSIONID_2  # slot adicional (opcional)
INSTAGRAM_COOKIE_FULL  # cookie completo (opcional, prioridade maxima)

# IA
MISTRAL_API_KEY
GROQ_API_KEY
OPENROUTER_API_KEY

# Seguranca
DASHBOARD_PIN
SENTINELA_ADMIN_TOTP_SECRET
WATCHDOG_ACTIVE        # true = formato de log compacto
```

## Regras Criticas

1. Nunca enviar SQL bruto pelo frontend
2. `SUPABASE_SERVICE_KEY` apenas no backend
3. Nunca importar de `archive_v17_2026/` ou `.legacy_frontend/`
4. `configs/instagram_storage_state.json` nunca commitar (protegido no .gitignore)
5. AIAdvisor nunca aplica patches automaticamente — apenas salva sugestoes com status=pending_review

## Comandos Operacionais

```bash
# Backend
python main_runner.py          # orquestrador principal
python watchdog.py             # supervisor com auto-restart

# Validacao de sessao
python scripts/probe_t3_2_storage.py

# Frontend
cd proposta_frontend && bun run dev
cd proposta_frontend && bun run build

# Migrations
python scripts/apply_migration.py
```

## Ultimas Atualizacoes (Refatoracao Raspagem e Classificacao)
- Corrigidos wrappers de modulos: `InstagramWorker` agindo como proxy para `IGZyteWorker`.
- Adicionada injecao de cookies (`requestCookies`) no `IGZyteWorker` permitindo fallback de Browser Rendering via Zyte com sessoes autenticadas.
- Resolvido conversao de shortcode para `media_id` para lidar com DOM scraping.
- Corrigida referencia da ForeignKey na tabela `comentarios`, usando `candidato_id` mapeado para o `username` do alvo.
- Teste completo end-to-end rodando com sucesso no alvo `lulaoficial`, incluindo extracao, persistencia e classificacao por IA (fallback Mistral ativado devido a limite Groq).
- Corrigido constraint `worker_rewards_tier_check` em `reward_engine.py` rebaixando o tier `platinum` para `gold` garantindo persistencia da gamificacao dos workers sem crash do Orquestrador.
- Restabelecida a API Mistral como motor primário e Groq como fallback secundário para evitar problemas de quota e API keys ausentes no ambiente.
- Implementada classificação em lote de até 50 comentários quando a coleta Zyte está em cooldown.
- Removido o limite rígido de 10 classificações por ciclo nos scrapers `IGZyteWorker` e `IGHeadlessWorker`, classificando todos os itens novos de forma imediata (Fase 4 - executado por Gemini 3.5 Flash).
- Corrigida a inicialização do Supabase no dashboard local (`local_dashboard.html`) renomeando as constantes para evitar colisão com o construtor `window.URL` nativo do JS.
- Silenciados os warnings do Tailwind CDN no console do painel local.
- Adicionado tratamento para requisições de `/favicon.ico` no servidor FastAPI do watchdog para eliminar os erros 404.
- Corrigida falha de inserção de caracteres nulos (\u0000) no Supabase (Erro 22P05) através de sanitização automática no serviço de IA (ai_service.py) e na persistência inicial de comentários nos workers oficiais ig_zyte.py e ig_headless.py.
- Atualizados modelos de IA descontinuados para llama-3.3-70b-versatile na Groq e openrouter/free no OpenRouter (Fase 4 - executado por gemini-2.5-pro-preview).
- Criado o ponto de entrada watchdog/__main__.py habilitando a execução nativa e modular do supervisor via python -m watchdog.
- Corrigido problema de alvos repetidos na fila através da antecipação de mark_candidate_scraped no início do ciclo de execução dos scrapers, assegurando o cooldown mesmo em coletas vazias ou com erro (Fase 4 - executado por gemini-2.5-pro-preview).
- Corrigidas as falhas de falso-positivo de reputação: coletas vazias legítimas (no_comments_found) deixam de sofrer penalidade de -15 de XP, e suspensões por reputação zero nos orquestradores foram limitadas apenas a ciclos com perda real de pontuação (delta < 0), eliminando loops de suspensão indevida (Fase 4 - executado por gemini-2.5-pro-preview).
- Elevado o nível de log de sucesso da classificação de IA individual para INFO no core/ai_service.py, incluindo o texto do comentário formatado, decodificado de escapes unicode e truncado a 60 caracteres no log do terminal para auditoria direta e clara (Fase 4 - executado por gemini-2.5-pro-preview).
- Retomado o daemon de sincronização automática e classificação de comentários neutros (`scripts/auto_sync_daemon.py` e `scripts/reclassify_csv.py`) após interrupção. Corrigida a detecção de inatividade de processos instalando a biblioteca `psutil` no `.venv` do projeto, eliminando o fallback com `wmic` no Windows 11 e garantindo monitoramento e sincronização periódicos do progresso local (executado por Gemini 3.5 Flash).
- Implementada rotação de logs rotativos of 5MB (max 3 backups) para `logs/main_runner.log` e adicionada flag `ENABLE_ZYTE` no orquestrador `main_runner.py` permitindo desativar o worker da Zyte em favor de coleta 100% headless local (Playwright). Suavizados logs repetitivos em `core/instagram_headless.py` e `workers/scrapers/ig_zyte.py` de INFO para DEBUG (Fase 4 - executado por Claude Sonnet 4.6 (Thinking)).
- Implementada a técnica de interceptação de tráfego de rede (Network Interception) via Playwright em `core/instagram_headless.py` para capturar os payloads JSON das requisições AJAX/GraphQL do Instagram. Isso permite coletar dados ricos (ID real do comentário, autor original e timestamp real da publicação), contornando a fragilidade de seletores CSS visuais, com suporte a fallback resiliente baseado no DOM tradicional (Fase 4 - executado por Claude Sonnet 4.6 (Thinking)).
- Resolvido o bug de "SEM PULSOS DETECTADOS NO PERÍODO" no gráfico de atividade temporal do dashboard implementando fallback resiliente do Supabase Client em `frontend/components/warroom/ActivityChart.tsx` para consultar, agrupar e ordenar dinamicamente a série temporal baseando-se na tabela de comentários (Fase 4 - executado por Claude Sonnet 4.6 (Thinking)).
- Corrigida a falha de contagem limitada a 1.000 registros no volume analisado e o gráfico zerado em produção no frontend, adicionando lançamento explícito de erro (`throw new Error`) em caso de respostas de API não sucedidas (404/500), ativando corretamente o fallback do Supabase Client. Otimizada a query de contagem usando a coluna `'id'` no select para maior velocidade e precisão no PostgREST (Fase 4 - executado por Claude Sonnet 4.6 (Thinking)).
- Implementado fallback resiliente do Supabase Client no feed de alertas ativos (`frontend/components/warroom/AlertsTab.tsx`) para puxar os alertas (comentários classificados com `is_hate = true`) diretamente do banco de dados quando a API HTTP falhar, mapeando dinamicamente a coluna `candidato_id` para o nome de usuário correspondente (Fase 4 - executado por Claude Sonnet 4.6 (Thinking)).
