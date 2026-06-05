# STATE.md — Sentinela
_last_updated: 2026-06-05 | branch: main_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | Scraper V2 ativo com ritmo conservador (10 a 30 min de cooldown) focado em constância e prevenção de bloqueios |
| Inteligência | 🟢 Operacional | Fila de processamento cíclico cadenciada e rotativa Round-Robin baseada em chaves de IA cloud (.env) e ollama local |
| Analytics de Rede | 🟢 Operacional | Subagente `SaMineracaoRedes` ativo de forma reativa/sob demanda |
| Financeiro | 🟢 Operacional | Subagente `SaAuditoriaFinanceira` ativo de forma reativa/sob demanda, com telemetria e burn rate diário de IA |
| Watchdog Local | 🟢 Operacional | Porta 8001, SSE, controle remoto, dashboard local premium e monitor dinâmico de chaves de IA ativo |
| Frontend oficial | 🟢 Estável | `frontend/` é o frontend oficial, com integração de relatórios reais e CTAs conectados |

## Verdades operacionais auditadas

1. O backend é iniciado por `main_runner.py`.
2. O watchdog local supervisiona a execução, gerencia os status dinâmicos de IA e publica logs por SSE.
3. O classificador oficial em produção é `workers/processors/wk_classifica_comentarios.py`.
4. A trava de instância única no `main_runner.py` e `watchdog` impede a execução redundante de múltiplos processos usando caminhos de lock absoluto baseados em `PROJECT_ROOT`.
5. O `cleanup_orphans()` é executado preventivamente no boot do `main_runner.py`, no setup de cada worker (`WkColetaInstagram` e `WkPesquisaAlvos`), no `run_all()` do orquestrador e ciclicamente na sua autocura.
6. A cadência de ciclos de processamento de todos os workers e agentes é lenta e constante: **10 min** (gold), **20 min** (silver/idle) e **30 min** (bronze) para proteção de sessões e cotas.
7. LiteRT não compõe mais o pipeline ativo de processamento.
8. A fila distribuída real hoje usa travas atômicas com `SELECT FOR UPDATE SKIP LOCKED`.
9. PGMQ permanece como possibilidade futura, não como base atual do runtime.
10. `frontend/` é o frontend oficial.
11. `local_dashboard.html` é o painel operacional local do watchdog, contendo seção de "Serviços de IA" dinâmica que exibe bolinhas cinzas (`bg-slate-600`) para serviços Cloud não configurados (status `DESATIVADO`).

## Achados da auditoria documental

### Certo

- watchdog com start/stop/restart e SSE
- `ollama` ativo
- `WkClassificaComentarios` como classificador central
- `WkPesquisaAlvos` com ativação controlada por `RESEARCHER_MODE`
- `queue_manager` com claim atômico
- Stripe com fallback mock controlado por flag (`STRIPE_ALLOW_MOCK_PAYMENTS`)
- AdSense com retry defensivo para evitar race condition de carregamento
- página de relatórios ligada ao backend FastAPI (`/api/v1/dossiers`)

### Refatorações de workers já concluídas

- `ClassifierWorker` foi removido do runtime e sua lógica útil de padrão ouro foi absorvida por `core/ai_service.py`
- entrypoints legados paralelos foram expurgados:
  - `core/orquestrador.py`
  - `workers/core/base_worker.py`
  - `workers/processors/queue_manager.py`
  - `workers/processors/search_watcher.py`
  - `workers/processors/cleanup_worker.py`
  - `workers/analytics/report_worker.py`
  - `workers/official_solenya_daemon.py`
  - `workers/orchestrator_long_run.py`
  - `workers/schedule_long_scrape.py`
- `researcher-01` não sobe mais por padrão sem backlog real
- `scripts/work_session.py` e `scripts/night_watch_pipeline.sh` foram alinhados ao runtime moderno

### Errado nos documentos antigos

- LiteRT descrito como engine ativa
- PGMQ descrito como implantado
- `proposta_frontend/` como frontend oficial
- Gemini tratado como classificador principal de produção

### Risco atual

O principal risco operacional hoje é a expiração ou bloqueio de cookies da sessão do Instagram (gerando respostas de feeds vazios):
- Necessidade de renovação periódica das cookies via script interativo no terminal.
- A mitigação do risco de taxa foi aplicada aumentando os cooldowns de todos os ciclos para 10 a 30 minutos de descanso.

## Situação da IA

### Ativo

- **Fila Circular Unificada**: Local (Ollama) e Cloud (Mistral, Groq, etc.) dividem o mesmo loop com rotacionamento Round-Robin.
- **Parametrização Diferenciada**:
  - **Cloud Providers**: Consomem o prompt completo enriquecido com `PADRONIZACAO_LINGUISTICA_ANALITICA.md` (PASA v16.3), `custom_rules.json` e o `classifier_gold_dataset.json`.
  - **Local (Ollama)**: Utiliza uma versão **reduzida** e otimizada ("DIRETRIZES ESSENCIAIS") para triagem rápida, visando evitar o *context bloat* e garantir respostas em < 2s.
- **Termômetro de Alvos (PASA v88.2)**: Reativada a classificação automática de temperatura (Frio/Morno/Quente) no fluxo de coleta. O status do alvo agora é atualizado imediatamente após a extração, garantindo o posicionamento correto na fila de prioridade.
- **Restrição de Reanálise**: A re-análise de comentários de baixa confiança permanece ativa para garantir a qualidade analítica, porém ela foi **desacoplada** do status do alvo. O termômetro do candidato (Frio/Morno/Quente) agora é atualizado **exclusivamente** durante os ciclos de coleta (scrape), baseando-se no timing e volume de dados frescos.
- **Circuit Breaker & Poda**: Provedores com erro 401/403 (chave/cota) são removidos da malha ativa em tempo real; erros 429 (rate limit) geram suspensão temporária de 60s.
- **Cache de I/O**: Prompts e datasets locais são carregados na RAM no boot para zero overhead de leitura em disco.
- **SaConsultaBanco (Subagente de dados)**: Integrado para consultas SQL e buscas FTS5 via porta 8002.

### Saneado

- Referências residuais a LiteRT removidas do pipeline de processamento ativo.
- Malha de fallback reordenada e sem provedores indisponíveis.

## Situação da fila

### Ativo no código

- claim atômico
- release atômico
- stale lock release
- fallback compatível quando RPC não existe

### Implicação

A documentação deve tratar a fila atômica como realidade atual.
PGMQ deve aparecer apenas como hipótese futura.

## Situação da documentação

### Fonte de verdade

- `STATE.md`
- `ROADMAP.md`
- `docs/SYSTEM_CONTEXT.md`
- `docs/DOCUMENTATION_AUDIT.md`

### Contexto histórico

- `docs/archive/**`
- `docs/superpowers/**`
- arquitetura PASA antiga

## Próximos passos recomendados

1. Habilitar RLS e criar políticas de acesso para as 15 tabelas que estão expostas no Supabase (incluindo `threat_alerts`, `worker_ledger`, `fallback_logs`, etc.).
2. Monitorar o consumo e o custo (burn rate) gerados nas últimas 24h através do SaAuditoriaFinanceira.
3. Acompanhar o progresso da re-classificação dos 17.734 comentários ERRO que foram recolocados na fila de processamento (2026-06-04).
4. Normalizar categorias legadas fora do MCA v2.2 (`POSITIVO`, `NEGATIVO`, `HATE`, `MILICIA_DIGITAL`, etc.) — re-analisar via ai_service para padronizar o schema.

## Últimas Operações (YOLO Test)

- **Teste de Operação Contínua (5 Minutos)**: Em 2026-06-04, um teste acelerado foi executado (`test_5min_operation.py`) para validar simultaneamente o pool de coleta (`WkColetaInstagram`) e o classificador da fila primária (`WkClassificaComentarios`).
- **Pipeline Reativo (Início da Fase 9)**: Em 2026-06-04, foi aprovada a otimização arquitetural para mover o sistema de um modelo "Polling-based" para "Event-Driven". O objetivo é conectar o Scraper diretamente ao AIProcessor via EventBus (sinalização em memória), zerando a latência de repouso do dado no banco.
- **Resultados e Auditoria**:
  - **Fila Atômica**: O mecanismo `queue_manager` funcionou perfeitamente realizando claims com `SKIP LOCKED` do Supabase.
  - **Coleta**: Scraper V2 autenticou, identificou postagens fixadas (FAST-SKIP) e avançou pelo grid alvo (`@dep.paulomagalhaes`) utilizando instâncias autônomas Headless do Playwright.
  - **Inteligência (Fallbacks Ativados)**: O Round-Robin com CircuitBreaker operou conforme esperado:
    - OLLAMA (Local) e MISTRAL (Cloud) operaram com sucesso contínuo.
    - MARITACA sofreu falha (403 Forbidden - Provável Chave Expirada/Sem Fundo) e sofreu **Poda Automática** via CircuitBreaker, sendo removido permanentemente da malha ativa, protegendo o runtime.
    - GROQ sofreu limitador de taxa (429 Too Many Requests) e foi temporariamente suspenso na rotação, direcionando a carga fluída para Ollama e Mistral sem interromper o serviço (graceful fallback).
  - **Conclusão**: O sistema operou de forma perfeitamente resiliente, sem quedas ou congelamentos (deadlocks), confirmando a robustez da arquitetura PASA e do roteamento adaptativo de LLM. O processo assíncrono finalizou corretamente.

## Auditoria de Inteligência (SaAuditaClassificacoes)

- **Falha de Persistência**: Em 2026-06-04, o `SaAuditaClassificacoes` detectou uma falha de schema ao tentar salvar dados de auditoria cruzada. O erro `PGRST204` confirmou a ausência da coluna `audit_data` na tabela `comentarios`.
- **Correção Aplicada**: Criada a migração `migrations/20260604_add_audit_data.sql` para adicionar a coluna `JSONB` necessária.
- **Detecção de Drift**: O agente reportou um **Drift de 26.7%** (4 divergências em 15 amostras) entre o classificador de produção e o auditor (Groq/Llama 3.3). O alerta de drift (> 20%) foi disparado, sugerindo necessidade de recalibragem dos prompts ou do threshold de confiança.
- **Relatórios de Rede**: O `SaMineracaoRedes` gerou novos relatórios em `frontend/public/reports/` identificando clusters de ataque coordenado com score de perigo máximo (100/100).