# 🛰️ PROTOCOLO DE SINCRONIA INTER-AGENTES (SENTINELA v2.0)

Este arquivo documenta o progresso, a arquitetura atual e as próximas missões coordenadas entre o **Gemini CLI (Orquestrador)** e o **Antigravity CLI (Executor)**.

---

## 📜 DOCUMENTAÇÃO: SNAPSHOT DE ARQUITETURA (28/05/2026)

### 1. Motor de Execução (Rocket Mode)
- **Desacoplamento:** A pipeline linear foi destruída. Scrapers (`IGWorkerV2`, `IGZyteWorker`) agora são trabalhadores de I/O puro. A inteligência (IA) foi movida para o `AIProcessorWorker`.
- **Malha Assíncrona:** O sistema opera com múltiplos workers independentes rodando em loops `asyncio` paralelos.
- **Concorrência:** O `Orchestrator` agora gerencia um `asyncio.Semaphore`, permitindo múltiplas raspagens simultâneas.
- **Orquestração Unificada:** Implementado o `rocket.ps1` como gatilho central para missões paralelas.

### 2. Fluxo de Dados
1. **Coleta:** Scraper Worker pega alvo -> Extrai comentários brutos -> Aplica filtro léxico -> Salva no Supabase (com `processado_ia=False`) e no SQLite local (`local_buffer`).
2. **Perícia:** AIProcessorWorker detecta novos registros -> Classifica em lote (PASA v16.4) -> Atualiza registros no banco.
3. **Persistência:** O sistema utiliza uma estratégia de "Zero Loss", garantindo que falhas no cloud não interrompam a coleta via buffer local.

---

## 🚦 STATUS DA MISSÃO
- **Fase 1 (Rocket Mode):** ✅ CONCLUÍDA (Desacoplamento, Paralelismo, Escalonamento).
- **Extra:** Limpeza de "rebarbas" de IA no `ig_zyte.py` validada e concluída.
- **Fase 2 (Resiliência & Infra):** 🔄 EM ANDAMENTO (Circuit Breakers, Proxies, Graceful Shutdown).

---

## ⚡ COMANDOS FASE 2: RESILIÊNCIA E ANONIMATO (PRÓXIMOS PASSOS)

### Tarefa 3: Circuit Breaker Global (DB Protection)
- **Status:** Disponível para Antigravity.
- **Instrução:** Criar `db_circuit_breaker` no `core/circuit_breaker.py`. No `core/db.py`, se o Supabase falhar 5x, o sistema deve operar exclusivamente via `local_buffer` (SQLite) por 10 minutos.

### Tarefa 4: Rotação Dinâmica de Proxies (Stealth Mode)
- **Status:** Disponível para Antigravity.
- **Instrução:** Adicionar suporte a `proxy` no `Playwright` dentro do `InstagramScraperV2`. Usar `os.getenv("PROXY_LIST")` como fonte. Trocar de IP a cada troca de alvo.

### Tarefa 5: Encerramento Gracioso (Safety First)
- **Status:** Disponível para Antigravity.
- **Instrução:** Modificar `WorkerBase` para capturar interrupções e garantir que o `local_buffer.sync_with_supabase()` seja chamado antes de finalizar o processo.

### Tarefa 6 (NOVA): Sistema de Validação Mútua
- **Status:** Pendente após Fase 2.
- **Instrução:** Criar um script `tests/system_integrity_check.py` que valide se:
    1. A IA está classificando os itens pendentes.
    2. Os scrapers estão ignorando itens já processados.
    3. O banco de dados não possui registros duplicados (id_externo).

---

## 🔄 FEEDBACK DO ANTIGRAVITY
- ✅ **Refatoração Zyte:** Limpeza final do `ig_zyte.py` concluída. Motor 100% puro.
- **Fase 2:** Aguardando início da Tarefa 3 (Circuit Breaker).

---

## 🧠 DECISÕES DO ORQUESTRADOR (GEMINI)
- Prioridade máxima: **Resiliência do Banco de Dados**. Se o Supabase cair, o Rocket Mode de nada serve se os dados forem perdidos.
- Próxima Auditoria: Realizarei uma varredura nas tabelas de métricas para validar o ganho de performance após o desacoplamento.

---
## 🚀 NOVA MISSÃO UNIFICADA (28/05/2026 12:13:08)
**Solicitação do Usuário:** Iniciar Fase 2: Implementação de Resiliência (Circuit Breaker DB), Anonimato (Proxies) e Encerramento Gracioso
**Status:** AGUARDANDO AGENTES...
