# CONTEXTO DO PROJETO SENTINELA

## 1. Visão Geral
Sistema de workers autônomos para coleta e processamento de dados, utilizando Supabase como back-end de persistência e orquestração. O sistema foca em resiliência, meritocracia (reward engine) e auto-gestão (base worker).

## 2. Arquitetura Core
- **`workers/base/memory_store.py`**: Singleton de I/O. Interface exclusiva com Supabase (tabelas: `worker_metrics`, `worker_rewards`, `worker_suggestions`, `worker_docs_cache`).
- **`workers/base/reward_engine.py`**: Motor de avaliação. Calcula score, tiers e recomendações baseadas em métricas de ciclo.
- **`workers/base/worker_base.py`**: Contrato base (`BaseWorker`). Ciclo de vida: `setup` → `run_cycle` (loop) → `teardown`.

## 3. Mandamentos de Desenvolvimento
1. **Infraestrutura**: O banco é SEMPRE remoto (Supabase). Proibido tentar subir Docker ou Supabase local.
2. **Qualidade**: Todo código deve ser validado com um script de teste dedicado (`teste_*.py`).
3. **Persistência**: Qualquer mudança estrutural exige migration no diretório `supabase/migrations/`.
4. **Comunicação**: O agente deve responder estritamente em **pt-BR** (conforme regras do repositório).
5. **Autonomia**: Workers devem ser capazes de rodar o loop `start()` sem intervenção manual.

## 4. Estado Atual (Snapshot)
- Tabelas do banco remoto estão criadas e validadas.
- Estrutura base (`memory`, `reward`, `worker`) implementada e commitada.

## 5. Próximo Passo
- Implementar o `ai_advisor.py` ou workers específicos de coleta (fase 3.5 em diante).
