# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-24 | branch: feat/autonomous-workers_

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
| Classificacao IA | Operacional | Roteamento Híbrido: Local (Gemma/Ollama) + Cloud Cascade |
| Renovação de Sessões (export_playwright_cookies.py) | Operacional | Autenticação automatizada de multi-contas, suporte a login em etapas e atraso simulado |

## Descobertas Tecnicas (2026-05-24)
- **Sanitização Geral de Alvos via CSV**: Desenvolveu-se a rotina de importação e sincronização `scratch/apply_sanitization.py` que lê as edições do CSV do usuário. Sincronizou-se com o Supabase remoto a inativação de 78 alvos removidos, a atualização cadastral de 42 alvos modificados, e resolveu-se a integridade de chaves estrangeiras na `fila_coleta` limpando as referências antigas de usernames antes dos updates de candidatos.
- **Sanitização de Heurística DOM do Scraper**: Diagnosticou-se que a heurística DOM capturava textos estáticos de interface do Instagram (como "Também da Meta", "Instagram Lite", "Localizações", "Áudio original" e placeholders de comentário). Solucionou-se isso restringindo o escopo de varredura de spans ao interior do elemento `<article>` e expandindo a `commentTextBlacklist` com ações e termos funcionais (curtidas, áudio/som original, inputs).
- **Higienização de Alvos Duplicados (Guilherme Boulos)**: Identificou-se a existência de 4 registros ativos para Guilherme Boulos no Supabase. Inativou-se as duplicatas incorretas (`@guilherme_boulos`, `@boulos_oficial` e `@guilhermeboulos_sp`), centralizando o monitoramento no perfil oficial `@guilhermeboulos.oficial` (ID `141b5779-7a0d-41c5-867b-4b32810a48ea`), com o cargo corrigido de "Deputado Federal" e limpando-os da fila de coleta.
- **Resiliência contra DOM Dinâmico no Login**: O Instagram ofusca suas classes CSS e altera elementos do DOM (`name="email"` em vez de `username`). Solucionou-se isso usando seletores baseados em atributos funcionais e rótulos de acessibilidade (`aria-label`), além de digitação sequencial (`page.type()`) com atraso simulado (150ms) para desviar da heurística de preenchimento automatizado do Instagram.
- **Login em Múltiplas Etapas (Passkey/WebAuthn)**: Adaptou-se a rotina de login para prever telas sem campo de senha inicial. O script agora emula um clique de tecla `Enter` e aguarda a transição de rede de 4s para obter a renderização visual correta antes de preencher a senha.
- **Modularidade de Coleta:** Modularizou-se o fluxo de modal do `InstagramScraperV2` expondo as responsabilidades de abertura, rolagem e fechamento em funções públicas auxiliares (`open_post_modal`, `scroll_comment_column`, `close_post_modal`). Isso simplifica a manutenção e integração da mecânica de modal em outras rotinas e etapas.
- **Navegação V2 via Modal:** Diagnosticou-se que acessos a URLs diretas de posts (`/p/{shortcode}/`) no modo headless do Playwright travam em telas brancas por bloqueio silencioso do Instagram. Refatorou-se o motor para abrir postagens clicando nos elementos na própria tela do perfil (comportamento humano nativo) e fechando via clique de tecla Escape, restabelecendo a extração estruturada de comentários com sucesso.
- **Circuit Breaker Local:** Integrou-se o provedor local LiteRT (Gemma 3 1B) ao `ai_circuit_breaker`. Se o LiteRT local falhar seguidamente por estar offline, o circuito abre por 5 minutos, poupando timeouts repetitivos de 5.0s por comentário e otimizando a latência do lote de classificação.
- **Tratamento de Exceções Lote:** Refatorou-se `run_batch_classification` para capturar exceções específicas de banco ou de API e logá-las detalhadamente, evitando interrupções silenciosas.
- **Robustez de Ambiente no Watchdog:** Corrigiu-se a seleção do interpretador Python em `get_python_executable()`. Agora o watchdog detecta se a pasta `.venv` local está corrompida (ex.: sem o módulo `pip` íntegro) e prioriza o interpretador ativo que o iniciou (permitindo uso transparente sob o gerenciador `uv run`).

## Descobertas Tecnicas (2026-05-23)
- **Roteamento Híbrido:** Implementado suporte ao Ollama no `AIService`. O sistema pode agora priorizar modelos locais (Gemma 2B) via `ENABLE_LOCAL_AI=true`.
- **Implementação V2:** Criado `InstagramScraperV2` em `core/` focado em Playwright puro.
- **Resiliência:** Implementada rotação automática entre múltiplas sessões (`INSTAGRAM_SESSIONID_N`) e backoff exponencial.
- **Extração Multi-camada:** O motor V2 tenta Interceptação de Rede > Scripts (data-sjs) > Heurística DOM.
- **Independência:** O sistema não depende mais do Zyte ou outros serviços pagos para raspagem básica.
- **Validado:** Testado com sucesso via `scripts/test_scraper_v2.py`.

## Arquitetura Atual (v52.2)

```
watchdog.py
  └── main_runner.py
        └── SentinelaOrchestrator
              ├── _active_targets: set
              └── IGWorkerV2 (ig-v2-01)
                    ├── InstagramScraperV2 (V2 Engine)
                    └── AIService (Hybrid Router)
                          ├── Tier 00: LiteRT (Gemma 3 1B)
                          ├── Tier 0: Ollama (Gemma 2B)
                          ├── Tier 1: Mistral (Cloud)
                          ├── Tier 2: Groq (Llama 3.3)
                          └── Tier 3: OpenRouter (Security)
```

## Fluxo de Dados

```
Instagram Web (Comet) ➔ Playwright (V2 Engine) ➔ Supabase (REST) ➔ Gemini 1.5 (IA)
```

## Status do Watchdog
- **Autocura**: Reinício automático em caso de crash.
- **Dependency Healing**: Auto-pip-install se houver ImportErrors.
- **Anti-Loop**: Hibernação de 1h após 3 falhas rápidas.
- **Alertas**: WhatsApp via CallMeBot para erros críticos.
- **Dashboard**: Live SSE em http://localhost:8001.

## Sessoes e Autenticacao

- `INSTAGRAM_SESSIONID*` — slots sequenciais (SESSION_1 a SESSION_10), slots com login wall marcados como `blocked`.
- `INSTAGRAM_COOKIE_FULL` — prioridade maxima se presente.
- `configs/instagram_storage_state.json` — fallback Playwright.

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

## Variaveis de Ambiente Necessarias

```
# Supabase
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY

# Instagram
INSTAGRAM_SESSIONID    # slot principal
INSTAGRAM_SESSIONID_2  # slot adicional (até _10)
PLAYWRIGHT_HEADLESS    # default: true

# IA
MISTRAL_API_KEY
GROQ_API_KEY
OPENROUTER_API_KEY

# Seguranca
DASHBOARD_PIN
WATCHDOG_ACTIVE        # true = formato de log compacto
```

## Comandos Operacionais

```bash
# Backend (Supervisor)
python -m watchdog             # supervisor com dashboard live

# Backend (Direto)
python main_runner.py          # orquestrador principal

# Validacao de sessao
python scripts/test_scraper_v2.py
```

## Ultimas Atualizacoes (Refatoracao V2)
- **2026-05-24:** Integrado o LiteRT (Gemma 3 1B) ao `ai_circuit_breaker` para proteger a latência em lote e adicionado tratamento de logs e erros na classificação em lote. Corrigidos o NameError (`asyncio` ausente) no `ig_worker_v2` e a validação do interpretador Python do Watchdog. Refatorada a abertura de posts no motor InstagramScraperV2 para uso de modal (clique no feed) e modularizado o controle do modal em métodos públicos auxiliares (`open_post_modal`, `scroll_comment_column`, `close_post_modal`).
- Implementado `InstagramScraperV2` eliminando dependência do Zyte (Fase 5 - executado por Gemini 1.5 Flash).
- Refatorado `main_runner.py` e `watchdog` para rodar exclusivamente o novo motor V2.
- Removidas verificações de saúde do Zyte e Scrapy Cloud do Watchdog.
- Validada extração real com rotação de sessões e interceptação de rede.
