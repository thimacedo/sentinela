# Sentinela — Contexto do Sistema
_last_updated: 2026-06-05_

## 1. Missão

O Sentinela é uma plataforma de monitoramento político com foco em:

- coleta automatizada de conteúdo público
- classificação de hostilidade e risco informacional
- mineração de redes e sinais coordenados
- produção de relatórios e dossiês
- operação supervisionada por watchdog local

## 2. Topologia atual

```text
[Watchdog Local] (Porta 8001)
  └── main_runner.py
        └── Orquestrador
              ├── InstagramWorker
              ├── AIProcessorWorker
              └── TargetResearchWorker (opcional por RESEARCHER_MODE)

[Subagentes Analíticos e de Dados]
  ├── SaConsultaBanco: Prover consultas SQL locais leves via Datasette
  ├── SaAuditaClassificacoes: Auditoria cruzada anti-alucinação sob demanda (Groq)
  ├── SaMineracaoRedes: Análise de redes coordenadas e clusters reativa
  └── SaAuditoriaFinanceira: Auditoria financeira e fechamento diário reativo

[Datasette Server] (Porta 8002)
  └── sentinela_data.db (Espelhamento SQLite local imutável FTS5)

[Supabase / PostgreSQL] (Produção Nuvem)
  ├── candidatos
  ├── comentarios
  ├── fila_coleta
  ├── worker_rewards
  ├── worker_suggestions
  └── demais tabelas analíticas

[Frontend oficial]
  └── frontend/ (Next.js)

[Dashboard local]
  └── local_dashboard.html + SSE do Watchdog
```

## 3. Pipeline atual de inteligência

1. claim atômico da fila em `core/queue_manager.py`
2. coleta de comentários com scraper V2
3. classificação do backlog via `core/ai_service.py`
4. reanálise de baixa confiança como tarefa de utilidade
5. disparo reativo em background de subagentes analíticos (`NetworkMinerAgent` & `TreasurerAgent`)
6. atualização de métricas financeiras, telemetria e grafos de influência


## 3.1 Estado atual dos workers

Contrato oficial:

- `workers/base/worker_base.py`
- `workers/base/cycle_result.py`

Workers cíclicos ativos no runtime:

- `InstagramWorker` (coleta estrutural)
- `AIProcessorWorker` (classificação principal)
- `TargetResearchWorker` (quando habilitado via `RESEARCHER_MODE`)

Subagentes analíticos (sob demanda / reativos):

- `SaAuditaClassificacoes` (auditoria cruzada)
- `SaMineracaoRedes` (mineração de redes coordenada)
- `SaAuditoriaFinanceira` (gestão financeira e de XP)

Mudanças já aplicadas:

- remoção dos contratos legados em `workers/core/`
- remoção de entrypoints legados paralelos ao runtime moderno
- alinhamento de scripts operacionais com `main_runner.py`
- `TargetResearchWorker` agora nasce desabilitado por padrão

## 4. Camada de IA em produção

O pipeline ativo identificado no código é:

- triagem local: `ollama`
- refino cloud: `mistral`, `groq`, `openrouter`
- fallback profundo: `core/fallback_llm.py`

Observações:

- LiteRT não integra mais o processamento ativo.
- O reclassificador `scripts/reclassify_low_confidence.py` usa cloud-first e pode permitir fallback local com `ollama`.
- O `FallbackLLM` depende de `config/fallback_providers.yaml`, mas parte dessa malha está sujeita a indisponibilidade de quota/configuração.

## 5. Fila e concorrência

O estado real do código mostra:

- trava atômica com `SELECT FOR UPDATE SKIP LOCKED`
- suporte a release de locks expirados
- fallback compatível quando RPC/migração não está disponível
- tabela `lotes_analises` e RPC `reivindicar_lote_analise` para controle atômico e concorrência horizontal de subagentes analíticos (`SaMineracaoRedes`), garantindo que tarefas CPU-bound de grafos não sejam duplicadas em réplicas simultâneas da engine.

Portanto, a fila distribuída via lock atômico já está operacional em nível de código.
PGMQ permanece como alternativa futura, não como dependência atual.

## 6. Watchdog e operação local

O Watchdog atual:

- sobe o dashboard local
- expõe SSE em `/api/stream`
- possui rotas de controle `/api/server/start`, `/api/server/stop` e `/api/server/restart`
- registra métricas e feedback humano de classificação
- verifica credenciais do Instagram
- garante disponibilidade do Ollama
- gerencia a inicialização automática do servidor Datasette na porta 8002

## 7. Frontends

Há dois contextos distintos:

- `frontend/` é o frontend oficial
- `local_dashboard.html` é o painel operacional local do watchdog

Esses papéis não devem ser confundidos.

## 8. O que não é mais contrato atual

Os itens abaixo aparecem em documentos antigos, mas não representam a verdade operacional atual:

- LiteRT como etapa padrão do pipeline
- `proposta_frontend/` como frontend oficial
- Zyte como eixo principal da coleta
- PGMQ como mecanismo já implantado
- Gemini como classificador oficial principal
- `core/orquestrador.py` como entrypoint válido
- `ClassifierWorker` como worker suportado
- `official_solenya_daemon.py` como daemon ativo

## 9. Fontes de verdade

- operação: `STATE.md`
- planejamento: `ROADMAP.md`
- auditoria documental: `docs/DOCUMENTATION_AUDIT.md`

## 10. Ajustes recentes de produto (frontend + monetização)

Atualizações consolidadas no ciclo mais recente:

- integração de checkout do frontend com `API_BASE_URL` centralizado
- correção de robustez de AdSense com tentativa/retry até disponibilidade de `adsbygoogle`
- conclusão da página `frontend/app/relatorios/page.tsx` consumindo backend FastAPI real
- conexão de CTAs e botões sem ação em páginas chave
- redução de ruído visual na home/sidebar e aumento de usabilidade em alvos de clique
- proteção de mock de pagamento por variável explícita (`STRIPE_ALLOW_MOCK_PAYMENTS`)

Esses ajustes devem ser considerados baseline atual do frontend oficial.

## 11. Subagentes Analíticos e de Dados (PASA v88.2)

A arquitetura foi migrada para subagentes especializados executados de forma reativa ou sob demanda, todos herdando da classe base `BaseSubAgent` para offloading de CPU (subprocessos) e I/O (threads):

- **SaConsultaBanco** (`workers/ai/sa_consulta_banco.py`): Desacopla a leitura de dados históricos de produção (Supabase) via API HTTP do Datasette local na porta `8002`, provendo buscas FTS5 ultra-velozes.
- **SaAuditaClassificacoes** (`workers/ai/sa_audita_classificacoes.py`): Subagente de curadoria cruzada anti-alucinação. Consome o `SaConsultaBanco` e efetua reclassificações via cascata de IA com circuit breaker para calcular o drift do modelo, gerando sugestões de prioridade `HIGH` em `worker_suggestions`.
- **SaMineracaoRedes** (`workers/analytics/sa_mineracao_redes.py`): Analisa grafos de hostilidade e detecta campanhas coordenadas organizadas (clusters de ataque) em processos filhos separados (`ProcessPoolExecutor`), persistindo os dados e gerando relatórios físicos para o frontend com claims atômicos concorrentes.
- **SaAuditoriaFinanceira** (`workers/financial/sa_auditoria_financeira.py`): Efetua auditoria de saldos de CI inconsistentes, monitora conectividade do Stripe e gera relatórios DRE consolidados diários.