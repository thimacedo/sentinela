# CONTEXTO DO PROJETO SENTINELA
_last_updated: 2026-05-20_

---

## 1. Visão Geral

Sistema de workers autônomos para coleta e processamento de dados, utilizando Supabase como back-end exclusivo de persistência e orquestração.

Pilares do sistema:
- **Resiliência**: workers se recuperam de falhas sem intervenção manual
- **Meritocracia**: reward engine avalia e pontua cada ciclo de execução
- **Auto-gestão**: base worker gerencia o ciclo de vida completo via `start()`

---

## 2. Arquitetura Core

### Mapa de dependências
```
WorkerEspecífico
    └── BaseWorker          (workers/base/worker_base.py)
            ├── MemoryStore (workers/base/memory_store.py)  →  Supabase
            └── RewardEngine(workers/base/reward_engine.py)
```

### Módulos

**`workers/base/memory_store.py`** — Singleton de I/O
- Interface exclusiva com o Supabase (nenhum outro módulo acessa o banco diretamente)
- Tabelas gerenciadas: ver seção 3

**`workers/base/reward_engine.py`** — Motor de avaliação
- Recebe métricas de um ciclo e calcula: `score`, `tier` e `recomendações`
- Critério de ciclo bem-sucedido: ciclo sem exceção não tratada, com ao menos 1 item coletado/processado e tempo de execução dentro do timeout configurado
- Tiers: `bronze` < `silver` < `gold` < `platinum` (baseado em score acumulado)

**`workers/base/worker_base.py`** — Contrato base
- Classe abstrata `BaseWorker`
- Ciclo de vida obrigatório: `setup()` → loop de `run_cycle()` → `teardown()`
- `start()` gerencia o loop, captura exceções e chama `teardown()` no finally

---

## 3. Schema do Banco (Supabase)

### `worker_metrics`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | uuid PK | Identificador único |
| `worker_id` | text | Nome/ID do worker |
| `cycle_at` | timestamptz | Timestamp do ciclo |
| `items_processed` | int | Itens coletados/processados no ciclo |
| `errors` | int | Erros não fatais no ciclo |
| `duration_ms` | int | Duração do ciclo em ms |
| `success` | bool | Ciclo concluiu sem exceção fatal |

### `worker_rewards`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | uuid PK | Identificador único |
| `worker_id` | text | Nome/ID do worker |
| `score` | float | Score calculado pelo reward engine |
| `tier` | text | bronze / silver / gold / platinum |
| `evaluated_at` | timestamptz | Timestamp da avaliação |

### `worker_suggestions`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | uuid PK | Identificador único |
| `worker_id` | text | Worker que gerou a sugestão |
| `suggestion` | text | Texto da sugestão de melhoria |
| `created_at` | timestamptz | Timestamp de criação |
| `applied` | bool | Se a sugestão foi aplicada |

### `worker_docs_cache`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | uuid PK | Identificador único |
| `doc_key` | text UNIQUE | Chave de identificação do documento |
| `content` | text | Conteúdo cacheado |
| `cached_at` | timestamptz | Timestamp do cache |
| `expires_at` | timestamptz | Expiração (null = sem expiração) |

> Escrita/leitura da `worker_docs_cache` é feita exclusivamente pelo `ai_advisor.py`
> para evitar re-fetching de documentação já processada.

---

## 4. Mandamentos de Desenvolvimento

1. **Infraestrutura**: O banco é SEMPRE remoto (Supabase). Proibido tentar subir Docker ou Supabase local.

2. **Qualidade**: Todo código deve ser validado com um script de teste dedicado (`teste_<modulo>.py`) antes do commit. Mínimo de 4 assertions por script.

3. **Persistência**: Mudanças estruturais exigem migration em `supabase/migrations/`. Conta como mudança estrutural: adicionar/remover coluna, novo índice, nova tabela, alteração de tipo ou constraint.

4. **Comunicação**: O agente deve responder estritamente em **pt-BR** (conforme regras do repositório).

5. **Autonomia**: Workers devem rodar o loop `start()` sem intervenção manual. Exceções devem ser capturadas, logadas e não devem derrubar o processo.

6. **Acesso ao banco**: Apenas `MemoryStore` acessa o Supabase. Workers e outros módulos nunca instanciam o client diretamente.

---

## 5. Variáveis de Ambiente

Obrigatórias em todos os contextos de execução:

| Variável | Descrição |
|----------|-----------|
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_SERVICE_KEY` | Chave service_role (somente backend) |

Opcionais por worker:

| Variável | Descrição |
|----------|-----------|
| `INSTAGRAM_ACCESS_TOKEN` | Token OAuth Instagram Graph API |
| `ZYTE_API_KEY` | Chave de autenticação Zyte |

---

## 6. Estado Atual (Snapshot)

```
[✅] Fase 1  — Definição de arquitetura e schema do banco
[✅] Fase 2  — Migrations e tabelas criadas e validadas no Supabase remoto
[✅] Fase 3  — Estrutura base implementada e commitada
               ├── memory_store.py  (4/4 testes passando)
               ├── reward_engine.py (4 cenários passando)
               └── worker_base.py
[🔜] Fase 4  — Camada de IA (ai_advisor.py) e workers de coleta
```

---

## 7. Próximos Passos (Fase 4)

### `workers/ai/ai_advisor.py`
- Consome `worker_docs_cache` para evitar re-fetching
- Recebe métricas e sugestões e gera recomendações via LLM
- Integra com `BaseWorker` como worker autônomo

### Workers de coleta
- `workers/instagram/` — coleta de comentários via Instagram Graph API
- Cada worker herda de `BaseWorker` e implementa `setup()`, `run_cycle()`, `teardown()`
- Documentação de referência em `workers/config/api_docs/`
