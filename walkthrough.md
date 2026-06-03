# Walkthrough — Estado Atual Auditável
_last_updated: 2026-06-03_

Este documento resume apenas o que continua válido após auditoria do código.

## 1. Pipeline ativo

- Watchdog supervisiona `main_runner.py`
- Orquestrador registra workers especializados
- `InstagramScraperWorker` coleta
- `AIProcessorWorker` classifica backlog e reanalisa baixa confiança
- `NetworkMiner` consolida rede
- `Treasurer` calcula indicadores
- `TargetResearchWorker` só entra no runtime quando `RESEARCHER_MODE` estiver habilitado

## 2. IA ativa

Camadas observadas no código:

1. `ollama` para triagem local
2. `mistral`, `groq`, `openrouter` para refino cloud
3. `FallbackLLM` como recuperação de desastre

## 3. O que mudou na auditoria

- LiteRT foi removido da documentação central porque não está mais no processamento ativo
- PGMQ deixou de ser tratado como item implantado; hoje a fila distribuída real é a trava atômica da `fila_coleta`
- o frontend oficial é `frontend/`
- o watchdog local virou parte importante da operação diária

## 4. Estado da fila

O código atual já suporta:

- claim atômico
- release atômico
- desbloqueio de lock expirado
- fallback para fluxo legado quando a RPC não existe

## 5. Estado da reclassificação

O script `scripts/reclassify_low_confidence.py`:

- prioriza cloud
- pode permitir fallback local com `ollama`
- não deve mais ser descrito como fluxo LiteRT/Ollama

## 6. Estado da refatoração de workers

Já foi concluído:

- expurgo dos entrypoints e contratos legados que competiam com o runtime moderno
- absorção da lógica útil do antigo `ClassifierWorker` em `core/ai_service.py`
- atualização dos scripts operacionais auxiliares
- desativação padrão do `researcher-01`

Ainda pendente:

- simplificar `workers/orchestrator/orchestrator.py`
- padronizar semântica de idle e `CycleResult`

## 7. Uso recomendado

Para iniciar trabalho novo:

1. leia `STATE.md`
2. leia `docs/SYSTEM_CONTEXT.md`
3. leia `ROADMAP.md`
4. valide no código