# Sentinela

Plataforma de monitoramento e inteligência política com coleta automatizada, classificação assistida por IA, mineração de rede, geração de dossiês e supervisão operacional via Watchdog.

## Estado atual

- Backend principal: `main_runner.py`
- Supervisão local: `watchdog/__init__.py`
- Frontend oficial: `frontend/`
- Dashboard local de operação: `local_dashboard.html`
- Fonte de verdade operacional: `STATE.md`
- Direção de produto/execução: `ROADMAP.md`

## Arquitetura real em produção

O fluxo atual observado no código é:

1. `watchdog` inicia e supervisiona `main_runner.py`
2. o orquestrador registra workers especializados
3. a fila usa claim atômico com `SELECT FOR UPDATE SKIP LOCKED` via RPCs do Supabase
4. o scraper coleta comentários e metadados
5. `AIProcessorWorker` classifica backlog com cascata:
   - `ollama` para triagem local
   - `mistral`, `groq` e `openrouter` na camada cloud
   - `FallbackLLM` como recuperação de desastre
6. `network-miner` consolida redes
7. `treasurer` atualiza indicadores financeiros
8. `researcher` atualiza heurísticas semânticas a partir das bases documentais

## Entrada oficial

```bash
python main_runner.py
```

## Supervisão operacional

```bash
python -m watchdog
```

ou pelos atalhos/scripts locais já existentes no workspace.

## Frontend oficial

O frontend oficial está em `frontend/` com Next.js.

- diretório de deploy: `frontend`
- não usar SQL bruto no frontend
- não expor chaves sensíveis do Supabase fora do backend

## Documentação recomendada

- `STATE.md` — estado operacional auditado
- `ROADMAP.md` — roadmap limpo e pendências reais
- `docs/SYSTEM_CONTEXT.md` — mapa técnico atual
- `docs/DOCUMENTATION_AUDIT.md` — auditoria do que serve, do que está defasado e do que é legado
- `docs/index_documentacao.md` — índice de leitura

## Regras práticas

1. Considere `STATE.md` como fonte de verdade de operação.
2. Considere `ROADMAP.md` como fonte de verdade de planejamento.
3. Trate `docs/archive/` e specs antigas como histórico, não como contrato atual.
4. LiteRT não faz mais parte do pipeline de processamento ativo.
5. O classificador oficial em produção é `workers/processors/ai_processor_worker.py`.

## Observação importante

O repositório contém documentação histórica de várias fases. Parte dela continua útil como contexto, mas não representa mais o estado real do sistema. Consulte a auditoria em `docs/DOCUMENTATION_AUDIT.md` antes de usar documentos antigos como base de implementação.