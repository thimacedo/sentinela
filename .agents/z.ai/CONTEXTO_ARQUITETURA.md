# Contexto de Arquitetura — Sentinela (v97.0)
**Destinatário:** z.ai | **Última Atualização:** 11 de Junho de 2026

Este documento serve como mapa de navegação arquitetural e técnica para que o **z.ai** compreenda a formação e o funcionamento atual do ecossistema do **Sentinela**.

---

## 🗺️ Mapa de Referência do Repositório

### 1. Documentação de Diretrizes e Status
* **[GEMINI.md](file:///c:/projetos/sentinela/GEMINI.md)**: Manual de engenharia com regras de isolamento, protocolos de escrita (PASA v50.1) e a classificação de IA.
* **[STATE.md](file:///c:/projetos/sentinela/STATE.md)**: Status de cada subsistema (Coleta, Inteligência, Dashboard e SRE) e histórico recente de implementações.
* **[ROADMAP.md](file:///c:/projetos/sentinela/ROADMAP.md)**: O cronograma de evolução e marcos técnicos da aplicação.
* **[AGENTS_SYNC.md](file:///c:/projetos/sentinela/AGENTS_SYNC.md)**: Contrato de isolamento e governança dos agentes de IA.

### 2. Agentes de IA Cognitivos (OODA Loops)
* **[sre_agent.py](file:///c:/projetos/sentinela/core/autopilot/sre_agent.py)**: Agente de SRE Autônomo do Watchdog. Monitora portas (`8001`, `8002`, `8009`), reinicia workers e se recupera cognitivamente de erros desconhecidos.
* **[agent.py](file:///c:/projetos/sentinela/core/agent_scraper/agent.py)**: O loop principal Observar-Orientar-Decidir-Agir do `ScrapeAgent` para lidar com mitigação de bloqueios e falhas de DOM.
* **[tools.py](file:///c:/projetos/sentinela/core/agent_scraper/tools.py)**: Registro declarativo de 8 ferramentas disponíveis para o `ScrapeAgent` (rotação de proxy, ajuste de delays, DOM healing, hibernação, etc.).
* **[dom_healing.py](file:///c:/projetos/sentinela/core/agent_scraper/dom_healing.py)**: Cura dinâmica de seletores baseada em capturas de screenshot e fragmentos de código via IA de visão Gemini Flash.
* **[cognitive_prioritizer.py](file:///c:/projetos/sentinela/core/agent_scraper/cognitive_prioritizer.py)**: Priorização dinâmica de alvos na fila de coleta usando scoring ponderado (volume de ódio, recência e relevância) no Supabase.
* **[persona_mode.py](file:///c:/projetos/sentinela/core/agent_scraper/persona_mode.py)**: Motor de simulação de trajetórias de mouse estocásticas (Curvas de Bézier) e pausas humanas para evitar detecções antibot.

### 3. Conectores e Executores (Workers)
* **[worker_adapter.py](file:///c:/projetos/sentinela/core/agent_scraper/worker_adapter.py)**: Adaptador do `ScrapeAgent` que envolve e estende a funcionalidade do worker de scraping clássico.
* **[wk_coleta_instagram.py](file:///c:/projetos/sentinela/workers/scrapers/wk_coleta_instagram.py)**: Worker de coleta física no Instagram. Executa sob controle do `ScrapeAgentAdapter` preservando buffers locais e idempotência do Supabase.
* **[instagram_scraper_v2.py](file:///c:/projetos/sentinela/core/instagram_scraper_v2.py)**: Motor Playwright de coleta que integra callbacks de monitoramento e o acionamento de auto-recuperação/HITL.

---

## ⚙️ Funcionamento das Integrações

### A. Fluxo de Coleta Inteligente (`ScrapeAgent` + `Worker`)
```
[Orquestrador/QueueManager] 
       │ (claim target prioritário via CognitivePrioritizer)
       ▼
[wk_coleta_instagram.py] 
       │ (inicia ciclo de coleta)
       ▼
[worker_adapter.py (ScrapeAgentAdapter)] ───► [persona_mode.py] (scroll/jitter)
       │
       ▼ (executa scraping real)
[instagram_scraper_v2.py] 
       │
       ├──► Se Sucesso: Persiste no Buffer SQLite + Supabase com upsert
       │
       └──► Se Erros (DOM alterado ou 3 posts vazios):
                 │
                 ▼ (Loop OODA)
           [agent.py (ScrapeAgent)]
                 │
                 ├──► Se RATE_LIMIT/IP_BLOCK: Aplica ferramentas determinísticas (tools.py)
                 │
                 └──► Se DOM_CHANGE: Aciona [dom_healing.py] (Cura via IA de visão Gemini)
                           │
                           ├──► Sucesso: Atualiza learned_selectors.json e reinicia
                           │
                           └──► Falha: HITL Fallback (Intervenção manual legada)
```

### B. Serviços de IA e Roteamento Multimodal
* O `core/ai_service.py` possui as chamadas estruturadas de texto.
* O patch `core/ai_service_vision_patch.py` estende o `AIService` adicionando o método `vision_completion`, roteando chamadas de visão **exclusivamente** para modelos Gemini da API do Google, contornando modelos locais e garantindo o processamento correto das capturas de tela do Playwright.
