# Auditoria da Documentação — 2026-06-03

Esta auditoria classifica a documentação do workspace em quatro grupos:

- **certa**: aderente ao código atual
- **parcial**: útil, mas com trechos desatualizados
- **histórica**: serve como contexto
- **lixo operacional**: não deve orientar implementação atual

## 1. Documentos certos

- `README.md`
- `STATE.md`
- `ROADMAP.md`
- `docs/SYSTEM_CONTEXT.md`
- `docs/index_documentacao.md`
- `docs/DOCUMENTATION_AUDIT.md`

## 2. Documentos parciais

### `walkthrough.md`
Serve para registrar decisões recentes, mas estava desatualizado em relação a LiteRT e ao estado da fila.

### `task.md`
Serve como checklist da rodada, não como documento arquitetural.

### `docs/project_functions_v58.md`
Continua útil como contexto funcional, mas não representa mais a topologia atual.

### `docs/database_schema_v58.md`
Útil como referência estrutural, porém precisa ser sempre validado contra o banco real e o código.

### `docs/PADRONIZACAO_LINGUISTICA_ANALITICA.md`
Metodologia ainda útil, mas referências a engines antigas devem ser lidas com cautela.

## 3. Documentos históricos

Use apenas para rastreabilidade:

- `docs/archive/**`
- `docs/superpowers/**`
- `docs/ARCHITECTURE_PASA_V50.md`
- `docs/ARCHITECTURE_PASA_V84.md`
- `docs/ARCHITECTURE_PASA_V86.md`
- PRDs antigos fora da documentação viva
- planos de migração e PRDs de fases antigas

## 4. Lixo operacional

Estes conteúdos não devem guiar trabalho novo sem validação direta no código:

- qualquer documento que trate LiteRT como componente ativo obrigatório do pipeline
- qualquer documento que trate `proposta_frontend/` como frontend oficial
- qualquer documento que trate PGMQ como solução já implantada no runtime atual
- qualquer documento que trate Gemini direto como classificador oficial de produção

## 5. Achados objetivos da auditoria

### Certo no código

- `AIProcessorWorker` é o classificador oficial
- `ollama` continua ativo na triagem local
- o fallback profundo existe em `core/fallback_llm.py`
- a fila atômica com `SELECT FOR UPDATE SKIP LOCKED` já existe em `core/queue_manager.py`
- o watchdog expõe SSE e controle remoto do runner
- o contrato oficial de worker está em `workers/base/worker_base.py`
- `TargetResearchWorker` ficou opcional e controlado por `RESEARCHER_MODE`

### Errado na documentação antiga

- LiteRT como engine ativa de processamento
- PGMQ como base já operacional
- `proposta_frontend/` como diretório oficial
- Zyte como centro da estratégia atual
- `ClassifierWorker` como classificador ativo
- `core/orquestrador.py` como entrypoint operacional
- `official_solenya_daemon.py` como daemon suportado

### Ainda serve

- documentação metodológica
- docs de banco
- docs de fluxo antigo como contexto de evolução

### É lixo no workspace para fins de execução

- specs antigas tratadas como se fossem estado atual
- textos duplicados/corrompidos em `STATE.md` anterior
- checklists antigos usados como arquitetura
- entrypoints paralelos legados competindo com `main_runner.py`

## 5.1 Refatorações de workers já documentadas

- expurgo dos contratos e entrypoints legados que conflitam com o runtime oficial
- absorção de lógica útil do legado em componentes modernos, sem preservar os entrypoints antigos
- alinhamento dos scripts de operação noturna e work session com o fluxo oficial
- desligamento padrão do `researcher-01` para impedir ciclos vazios sem backlog real

## 6. Regra de manutenção daqui para frente

1. toda mudança relevante deve atualizar `STATE.md`
2. toda mudança de direção deve atualizar `ROADMAP.md`
3. docs históricas não podem ser promovidas a fonte de verdade
4. quando um componente sair do runtime, ele deve ser removido da documentação central no mesmo ciclo