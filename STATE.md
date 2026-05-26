# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-26 | branch: main_

## Status Operacional (v82.0)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v80.1: Título otimizado NewsHeader (whitespace-nowrap sóbrio), Mobile 100% OK, Build compilando com sucesso |
| Autopilot L3 | Operacional | v80.0: Heartbeat e Polling de Comandos Cloud integrados à telemetria remota |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload, Integração L3 Autopilot, Cleanup de Órfãos automático |
| Coleta Independente (IGWorkerV2) | Operacional | Motor V2 v71.0: Rotação Stealth, Solenya (Detecção de Bots), Buffer Adaptativo (SQLite local / Memória em Cloud) |
| Persistencia Supabase | OK | v80.0: Locking Atômico via RPC (`claim_fila_target`) e schema v80 integrado |
| Classificacao IA | OK | Cascade v70.3 + Processamento em lote Cloud (100 itens/rodada) via Actions |
| GitHub Actions (CI/CD) | Operacional | v82.0: Saneamento de pipelines legados concluído, suporte para Node 24 ativado e fallback robusto de secrets configurado |

## Descobertas Tecnicas (2026-05-26)
- **Saneamento e Resiliência do CI/CD (v82.0)**: Removidos workflows legados inativos que utilizavam o nome "ForenseNet". Padronização dos segredos de conexão do Supabase com fallbacks eficientes e migração silenciosa para suporte a Node 24.
- **Ajuste de Responsividade e Sobriedade do Título (v80.1)**: Redimensionamento e restrição de quebra de linha (`whitespace-nowrap`) no cabeçalho do portal para evitar vazamento horizontal e integrar harmoniosamente o layout às telas mobile e desktop.
- **Locking Atômico Cloud/Local (v80.0)**: Implementação da procedure PostgreSQL `claim_fila_target` com tratamento de concorrência. O locking via campos `locked_by` e `locked_until` garante exclusão mútua e impede que workers locais e workflows efêmeros do GitHub Actions coletem o mesmo perfil simultaneamente.
- **Execução Cloud Nativa (v80.0)**: Criação de scripts especializados com Auto-Anchoring para execução em contêineres temporários do GitHub Actions:
  - `cloud_scrape_cycle.py` (Raspagem cíclica com Jitter)
  - `cloud_queue_refresh.py` (Manutenção e repopulação da fila de coleta)
  - `cloud_classify_batch.py` (Classificação assíncrona de IA em lote)
- **Circuit Breaker & Fallback de Fila**: Caso o banco de dados remoto não tenha a função RPC aplicada, o `QueueManager` realiza fallback automático e transparente para queries clássicas sem lock, preservando a estabilidade do sistema local.

## Arquitetura de Integridade

```
[GitHub Actions Workflows] (Coleta, IA e Fila na Nuvem)
  ├── ig_scraper_cloud.yml ──> [cloud_scrape_cycle.py] ──> Supabase Remoto
  ├── intelligence_worker.yml ──> [cloud_classify_batch.py] ──> Supabase/Mistral
  └── queue_manager_cloud.yml ──> [cloud_queue_refresh.py] ──> Supabase Remoto
        │
        ▼ (Sincronização Atômica via claim_fila_target RPC)
        │
[Watchdog Local v61.7] (Guardião L2 + Hot-Reload)
  ├── [Autopilot v80.0] (Comando L3 + Diagnóstico IA + Auto-Patching)
  └── [Orchestrator v57.4] (Atomic Locking + Memory Flush + Process Cleanup)
        ├── [QueueManager v80.0] (RPC Lock + Auto-repopulação + Smart Backoff)
        └── [IGWorkerV2 v71.0] (Scraper Playwright + Stealth + Coordinated Bot Check)
```
