# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-27 | branch: feat/autonomous-workers (Model: Gemini 3.5 Flash)_

## Status Operacional (v83.5)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v83.5: Novas páginas institucionais (/termos, /metodologia, /lgpd, /privacidade) criadas. Ações de compartilhamento (clipboard), navegações em botões estáticos e links do rodapé corrigidos. Build e typecheck de produção concluídos com Turbopack em 8.0s |
| Autopilot L3 | Operacional | v80.0: Heartbeat e Polling de Comandos Cloud integrados à telemetria remota |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload, Integração L3 Autopilot, Cleanup de Órfãos automático |
| Coleta Independente (IGWorkerV2) | Operacional | Motor V2 v71.0: Rotação Stealth, Cookies renovados com sucesso via Playwright em 2026-05-27, Buffer Adaptativo (SQLite local / Memória em Cloud), Headless nativo ativado |
| Persistencia Supabase | OK | v80.0: Locking Atômico via RPC (`claim_fila_target`) e schema v80 integrado |
| Classificacao IA | OK | Cascade v70.3 + Processamento em lote Cloud (100 itens/rodada) via Actions |
| GitHub Actions (CI/CD) | Operacional | v82.1: Saneamento concluído, suporte a Node 24 ativo e blindagem global contra crashes de credenciais de IA |

## Descobertas Tecnicas (2026-05-27)
- **Páginas Institucionais e Navegação Funcional do Frontend (v83.5)**: Criadas as rotas e interfaces das páginas de rodapé regulatórias (`/termos`, `/metodologia`, `/lgpd`, `/privacidade`). Consertados todos os botões estáticos sem ação do dashboard, associando-os com navegações reais e implementada funcionalidade de compartilhamento com cópia para a área de transferência.
- **Adequação Linguística Legal do Frontend (v83.1)**: Removidas todas as strings que faziam uso de termos legalmente regulados (como "perícia", "forense", "prova", "evidência") em todo o frontend do Next.js. A rota física `/pericia` foi renomeada para `/analise` e o componente `ForensicTab.tsx` para `AnaliseTab.tsx`. O build e o typecheck do TypeScript concluíram com sucesso em 5.3s.
- **Renovação Automatizada de Cookies via Playwright (v83.0)**: Executada com sucesso a renovação dos cookies e sessionids das contas do Instagram (`tempareiapodcast` e `monitoramento.discurso`) utilizando o fluxo automatizado com usuário e senha do `.env` por meio do parâmetro `--force` no `export_playwright_cookies.py`. O arquivo `.env` foi atualizado com as chaves `INSTAGRAM_SESSIONID`, `INSTAGRAM_COOKIE_FULL` e `INSTAGRAM_SESSIONID_2`.
- **Blindagem de Efeito Colateral na Importação (v82.1)**: Configurados fallbacks com strings fictícias ("dummy") para as credenciais da API da OpenAI/Mistral no construtor do `AIService`. Isso previne crashes prematuros por falta de chaves em scripts que apenas importam o serviço (como o raspador de Instagram), mas que não executam classificação em tempo de execução.
- **Módulo Solenya (v71.0)**: Implementação de detecção de comportamento coordenado (Bots) via similaridade textual. Clusterização pré-IA economiza até 95% de tokens em ataques massivos, mantendo registros forenses completos.
- **Endurecimento de IA (v70.3)**: Implementação de "Escalação por Contradição". Se o modelo local descreve um ataque na análise mas marca como Neutro, a confiança é penalizada para 0.40, forçando a perícia Cloud. Prompt v70.3 focado em Realismo Forense.
- **Correção da Telemetria Forense (v70.2)**: Sincronização real do XP delta e persistência de métricas de performance (duração/erros) na tabela `worker_metrics`.
- **Integração Autopilot L3 (v70.0)**: O Watchdog agora hospeda o `AutopilotManager`, que analisa métricas de saúde do Supabase em tempo real. Implementados `Diagnostician` (IA para análise de logs/HTML) e `Patcher` (aplicação de hot-fixes automáticos).

## Arquitetura de Integridade

```
[Watchdog v61.7] (Guardião L2 + Hot-Reload)
  ├── [Autopilot v70.0] (Comando L3 + Diagnóstico IA + Auto-Patching)
  └── [Orchestrator v57.4] (Atomic Locking + Memory Flush + Process Cleanup)
        ├── [QueueManager v70.4] (Multi-tier + Fairness + Termômetro + Smart Backoff)
        └── [IGWorkerV2 v71.0] (Scraper Playwright + Stealth + Coordinated Bot Check)
              ├── [LocalBuffer v65.0] (Zero-Loss SQLite storage)
              ├── [LexicalFilter v65.0] (Pre-AI garbage disposal)
              └── [AIService v70.3] (Cascade Híbrido + Hardening MCA v2.2)
```
