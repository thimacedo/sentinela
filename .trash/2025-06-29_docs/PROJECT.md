# Projeto: Sentinela — Watchdog & Resiliência do Backend (v97.6)

## Arquitetura e Estrutura

### Limites de Módulos e Pacotes
*   `watchdog/`: Supervisão contínua de processos, logs via SSE (Server-Sent Events) na porta `8001` e dashboard operacional (`local_dashboard.html`).
*   `main_runner.py`: Ponto de entrada do orquestrador de subprocessos (`SentinelaOrchestrator`), responsável por gerenciar workers concorrentes e o consumo atômico de filas.
*   `core/`: Core do sistema de inteligência, incluindo:
    *   `core/ai_service.py`: Cascata resiliente de classificação de hostilidade baseada em IA (Ollama local ➔ Sabia-4 ➔ Nuvem).
    *   `core/agent_scraper/`: ScrapeAgent autônomo baseado em Loop Cognitivo OODA e auto-recuperação DOM (DOM Healing) via visão computacional do Gemini 2.5 Flash.
    *   `core/autopilot/sre_agent.py`: Agente de SRE Autônomo com inteligência de reativação rápida de processos e cooldown determinístico.
*   `workers/`: Implementações de workers em Python puro:
    *   `workers/scrapers/wk_coleta_instagram.py`: Scraper robusto do Instagram baseado no `InstagramScraperV2` e com rotina de Diagnóstico de Coleta Zero.
    *   `workers/processors/wk_classifica_comentarios.py`: Processador assíncrono oficial de classificação PASA com triagem léxica rápida (SaFastDrop) integrada.

### Fluxo de Dados Operacional
1.  **Orquestração & Fila**: `QueueManager` realiza o claim de alvos prioritários na `fila_coleta` do Supabase remoto com trava atômica `SELECT FOR UPDATE SKIP LOCKED`.
2.  **Raspagem & Autocura**: O worker de scraping faz a raspagem de posts e comentários. Se ocorrer uma quebra de seletores, o *DOM Healing* do Gemini Flash reconstrói a sintaxe e a armazena no cache local para ciclos posteriores.
3.  **Triagem Léxica (Fast-Drop)**: O `SaFastDrop` descarta rapidamente comentários neutros de forma local e com custo zero de tokens.
4.  **Classificação PASA**: O classificador `WkClassificaComentarios` processa os comentários suspeitos restantes usando a cascata de LLM.
5.  **Autocura de Infraestrutura**: O `sre_agent.py` monitora os logs e o status do backend em tempo real. Se ocorrer crash no Playwright (erros de IPC / EPIPE), o SRE executa restart do runner principal automaticamente.

---

## Marcos do Projeto (Milestones)

| # | Marco | Escopo | Status |
|---|---|---|---|
| 1 | Estabilização & Reloader | Proteção contra crash da thread guard, hibernação responsiva e recarga segura de workers | ✅ CONCLUÍDO |
| 2 | Desacoplamento de IA | Desacoplamento completo do thread principal do watchdog, rodando processamento pesado em background | ✅ CONCLUÍDO |
| 3 | Padronização de Workers | Renomeação de todos os workers para nomenclatura em português (`wk_`) e subagentes (`sa_`) | ✅ CONCLUÍDO |
| 4 | Resiliência SRE & Autocura | Implementação de `sre_agent.py` autônomo com auto-restart e bypass headless para bandeja | ✅ CONCLUÍDO |
| 5 | ScrapeAgent & DOM Healing | Loop OODA e regeneração visual de seletores com Gemini 2.5 Flash e cache learned selectors | ✅ CONCLUÍDO |
| 6 | Coleta Direcionada & Diagnóstico | Gatilho para forçar coleta instantânea e Diagnóstico Granular de Coleta Zero (v97.6) | ✅ CONCLUÍDO |

---

## Contratos de Interface Principais
*   `watchdog/state` (`WatchdogState`): Gerenciador thread-safe de estado operacional. Mantém atributos de `status`, `should_run`, `restarts` e estatísticas de erros.
*   `core/event_bus` (`AsyncLocalEventBus`): Barramento em memória de baixíssima latência (~2ms) que rege a reatividade entre workers de coleta e classificação.
