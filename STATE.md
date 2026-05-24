# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-24 | branch: main_

## Status Operacional

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | War Room v54.3: Design Profissional (Slate/Emerald), Flexbox (sem sobreposição), Dossiês e Rede CONGELADOS |
| AI-SRE Advisor | Operacional | v53.1: Diagnóstico via open-mistral-nemo funcional |
| Coleta Independente (IGWorkerV2) | Operacional | Motor Playwright V2 com rotação de sessões, filtros de pins e idade (7d) |
| Persistencia Supabase | OK | upsert id_externo, ignore_duplicates, duplicados contados corretamente |
| Classificacao IA | OK | Cascade real v55.0 Mistral->Groq com sensibilidade Ad Hominem endurecida |
| Fila de Coleta | Operacional | v55.1: Multi-tier (Manual > Prioridade > Rotação) + Fairness 25% + Atomic Locking |
| RewardEngine | Operacional | score/tier/badges persistidos, get_interval() por tier |
| AIAdvisor | Condicional | Acionado apenas score<40 ou tier critical/db_failed |
| Watchdog | Operacional | v55.3: Alinhado com Supabase/MemoryStore e requirements-workers.txt |
| Renovação de Sessões (export_playwright_cookies.py) | Operacional | Autenticação automatizada de multi-contas |

## Descobertas Tecnicas (2026-05-24)
- **Integridade Forense e Calibração de IA (v55.0)**: Implementada validação rigorosa de alvos no motor V2, detectando redirecionamentos de username, páginas 404 e contas privadas. O `AIService` foi recalibrado (MCA v2.2) para endurecer a detecção de hostilidade técnica velada e ad hominem polido, reduzindo drasticamente falsos negativos persistentes.
- **Otimização de Prioridades e Distribuição (v55.1)**: O `QueueManager` foi refatorado para suportar um fluxo de decisão multinível: alvos manuais possuem precedência total, seguidos por itens da `fila_coleta` (ordenados pelo campo `prioridade` e antiguidade), e finalmente a rotação global de candidatos ativos (baseada em `last_scraped_at`). Introduziu-se um **Mecanismo de Fairness de 25%**, que força a seleção via rotação global periodicamente para garantir que nenhum alvo fique estagnado. Adicionalmente, o `IGWorkerV2` agora utiliza um bloqueio atômico (`claim_lock`) compartilhado via orquestrador, eliminando riscos de colisão onde múltiplos workers tentariam processar o mesmo perfil simultaneamente.
- **Filtro de Posts Fixados e Velhos (v54.4)**: O motor `InstagramScraperV2` foi aprimorado para lidar com posts fixados (pinned) e limite temporal de relevância. Agora, o sistema identifica posts fixados no grid via seletores SVG/Aria e, ao abrir o modal, valida a data de publicação (`datetime` do elemento `<time>`). Posts com mais de 7 dias de idade são automaticamente ignorados, e o loop de raspagem avança para os posts subsequentes no grid até atingir o limite de sucessos definido (`max_posts`). Isso evita a redundância cíclica de dados e foca o processamento em informações inéditas.
- **Design Profissional e Modularização (v54.3)**: O frontend foi integralmente reestruturado para um layout Flexbox que elimina a sobreposição do menu. A paleta foi suavizada para Slate/Emerald e a lógica de dados foi isolada no hook `useSystemInformation`. Módulos de **Workers** (removido), **Dossiês** e **Rede** (congelados) foram ajustados para refletir o foco operacional atual.
- **Evolução Tática do Frontend (v53.1)**: O frontend foi integralmente reestruturado de um modelo baseado em abas (tabs) para uma interface de comando **"War Room"** com Sidebar persistente e funcional. Implementou-se um tema visual inspirado em terminais táticos (CRT/Scanlines) com gerenciamento de estado global via Zustand (`useUIStore`). Cada módulo operacional (Perícia, Alvos, Alertas, Rede, Workers, Dossiês) agora possui sua própria rota dedicada. Corrigidos erros de sintaxe no `ActivityChart.tsx` que impediam o build na Vercel.
- **Integração AI-SRE Advisor (v53.1)**: O `AIAdvisor` agora atua como um SRE (Site Reliability Engineer) virtual, processando métricas de falha com o modelo `open-mistral-nemo` para sugerir correções de rede e rate-limit, aproximando o Sentinela de uma operação de "Auto-Cura" (Self-Healing).
- **AIAdvisor AI-Driven (v53.0)**: Implementada a integração real do `AIAdvisor` com o `AIService` (Mistral/Groq). Agora, quando um worker apresenta performance degradada (score < 40 ou tier critical), o Advisor analisa automaticamente as métricas do ciclo e a documentação técnica (via `DocFetcher`) para gerar sugestões técnicas acionáveis e as persiste na tabela `worker_suggestions` do Supabase com status `pending_review`.
- **DocFetcher com TTL**: O `DocFetcher` foi aprimorado para gerenciar o cache de documentação técnica com suporte a TTL (Time-To-Live) de 1h, garantindo que o Advisor utilize informações atualizadas sobre as APIs alvo.
- **Validação do Motor V2**: O `InstagramScraperV2` foi testado e validado em ambiente de produção (via script `test_scraper_v2.py`), confirmando a eficácia da navegação via modal e a captura estruturada de comentários mesmo sob desafios de renderização dinâmica.
- **Saneamento de Deploy Render**: O arquivo `render.yaml` foi reescrito para suportar o novo orquestrador (`main_runner.py`), utilizando o conjunto completo de dependências (`requirements-workers.txt`) e garantindo a instalação automatizada dos binários do Playwright (`playwright install chromium`).
- **Inserção Direta de Alvos**: Inserido o perfil `@janainacpaschoal` diretamente na base via script `scratch/insert_janaina.py`, com ativação imediata na `fila_coleta`. Adicionalmente, o alvo `@henriquealvesoficial` foi inativado permanentemente.

## Arquitetura Atual (v55.3)

```
watchdog.py (Garante main_runner e dashboard local)
  └── main_runner.py (Orquestrador Core)
        └── SentinelaOrchestrator
              ├── _active_targets: set (Deduplicação paralela)
              ├── claim_lock: asyncio.Lock (Atomicidade)
              └── IGWorkerV2 (ig-v2-01)
                    ├── InstagramScraperV2 (Motor Playwright V2)
                    │     ├── Filtro Pins/7d/Integridade
                    │     └── Tiers de Resiliência: GraphQL -> JS -> DOM
                    └── AIService (Cascade v55.0)
                          ├── Tier 0: LiteRT/Ollama (Local)
                          ├── Tier 1: Mistral Nemo (Cloud)
                          └── Tier 2: Groq Llama 3.3 (Cloud)
```

## Sistema de Recompensas e Cooldown

| Tier | Reputation | Intervalo | Observação |
|---|---|---|---|
| Platinum | >= 85 | 120s | Elite operacional |
| Gold | >= 70 | 180s | Estável |
| Silver | >= 50 | 300s | Padrão |
| Bronze | >= 25 | 480s | Atenção necessária |
| Critical | < 25 | 600s | Gatilho AI-SRE Advisor |
| DB_Failed | — | 600s | Gatilho AI-SRE Advisor |

## Fila de Coleta (v55.1)

1. **Manual**: Via Config/Env (Precedência total).
2. **Prioritária**: `fila_coleta` (order by prioridade DESC, created_at ASC).
3. **Justiça (Fairness 25%)**: Rotação forçada via candidatos ativos.
4. **Global**: `candidatos` (order by last_scraped_at ASC).
