# STATE.md — Sentinela Democratica (Fonte de Verdade)
_last_updated: 2026-05-28 | branch: main (Model: Gemini 3.5 Flash)_

## Status Operacional (v84.6)

| Subsistema | Status | Observacao |
|---|---|---|
| Frontend (nextjs) | Operacional | v84.1: Consolidação da integração AdSense. Removidos todos os placeholders e otimizada a injeção não-bloqueante do script do AdSense com a estratégia afterInteractive no RootLayout. |
| Autopilot L3 | Operacional | v84.4: Proteção anti-detecção com cooldown de 6h e cura preventiva estendida para 24h. |
| Watchdog (Guardião) | Operacional | v61.7: Hot-Reload, Integração L3 Autopilot, Cleanup de Órfãos automático |
| Coleta Independente (IGWorkerV2) | Operacional | v84.6: Sessões restauradas manualmente pelo usuário (`SESSION_2` e `SESSION_VAL`). Operação de raspagem validada com sucesso em alvos públicos. |
| Persistencia Supabase | OK | v80.0: Locking Atômico via RPC (`claim_fila_target`) e schema v80 integrado |
| Classificacao IA | OK | Cascade v84.2: Filtro lexical preventivo integrado diretamente no classify_text para evitar chamadas de IA desnecessárias e falsos positivos de menções puras (@username). Saneamento de dados aplicado com sucesso. |
| GitHub Actions (CI/CD) | Operacional | v82.1: Saneamento concluído, suporte a Node 24 ativo e blindagem global contra crashes de credenciais de IA |
| Relatórios Comerciais | Implementado | Geração diária, UI, API, visualizador e exportação a PDF client-side integrada (v83.6) |

## ✅ SESSÕES RESTAURADAS
- **Status**: Operacional. As sessões `INSTAGRAM_SESSIONID_2` e `INSTAGRAM_SESSIONID_VAL` foram validadas como funcionais para extração de dados.
- **Ações Realizadas**:
  1. Teste de validação realizado em alvos públicos (@lulaoficial) com sucesso de extração de grid.
  2. Atualização dos metadados de estado para refletir a retomada da coleta.
  3. O serviço do Watchdog/Runner deve ser mantido ativo para processar a fila represada.

## Descobertas Tecnicas (2026-05-28)
- **Ciclo de Inteligência Contínua (v84.9)**: Evolução do `TargetResearchWorker` de um script CLI para um Worker persistente integrado ao orquestrador. O motor agora executa rotinas de curadoria automática (70% do tempo) e pesquisa de novos alvos (30%), garantindo que nenhum alvo permaneça com dados `DESCONHECIDO`.
- **Sistema de Recompensas de Inteligência (v84.9)**: Integrado o RewardEngine com suporte a deltas de XP pré-calculados. O pesquisador é premiado (+15 XP) por fichas de alta precisão e punido (-5 a -10 XP) por informações imprecisas, vazias ou perfis inacessíveis, forçando a busca por melhores fontes.
- **Inclusão Inteligente de Alvos (v84.8)**: Implementado o `TargetResearchWorker` e o script `scripts/add_target.py`.
- **Expansão do Monitoramento (v84.7)**: Novos alvos `@rncomjorge` e `@sirlenojr` adicionados à base de dados com status `ATIVO`.
- **Recuperação de Sessão (v84.6)**: Sessões do Instagram restauradas via intervenção manual.
 Identificamos que a nova chave `INSTAGRAM_SESSIONID_VAL` é funcional, juntamente com `INSTAGRAM_SESSIONID_2`. O motor V2 foi testado e confirmou a capacidade de visualizar postagens, superando o bloqueio anterior.
- **Ativação da Fase 4 (AIAdvisor → Workers) (v84.5)**: Integrado o fluxo de auto-diagnóstico onde falhas críticas de coleta (como `junk_detected` ou `session_blocked`) acionam automaticamente o `AIAdvisor`. O advisor consulta o `DocFetcher` (cache local de documentação técnica) para gerar sugestões de correção em tempo real, que são persistidas para auditoria.

## Descobertas Tecnicas (2026-05-27)
- **Correcao de Timeout de Scraping e Renovacao de Sessao (v84.3)**: Identificado e resolvido o erro `ElementHandle.click: Timeout 30000ms exceeded` no `instagram_scraper_v2.py`. A abertura de posts foi refatorada para usar navegacao direta por URL (`/p/{shortcode}/`) como estrategia primaria, eliminando a dependencia fragil do clique DOM no grid de postagens. O metodo `close_post_modal` foi atualizado para usar `page.go_back()` de forma consistente. Paralelamente, o script `export_playwright_cookies.py` foi blindado contra o `TargetClosedError` do Playwright, que ocorria quando o Instagram redirecionava a pagina SPA durante a etapa de coleta de cookies pos-login, adicionando re-navegacao para a home antes da captura e tratamento explicito da excecao.
- **Filtro Lexical Preventivo no Fluxo Global de IA e Saneamento de Dados (v84.2)**: Consolidamos a blindagem contra falsos positivos inserindo o `lexical_filter` diretamente no método principal de classificação (`classify_text` no `ai_service.py`), garantindo que qualquer fluxo (scrape direto, reclassificação ou processamento em lote) descarte menções puras a usuários e lixo como `NEUTRO` imediatamente. Adicionalmente, desenvolvemos e executamos o script `saneamento_lexical.py`, corrigindo com sucesso no Supabase remoto 11 comentários antigos que haviam sido classificados erroneamente como ódio, regularizando os dados históricos dos candidatos e alertas.
- **Consolidação do AdSense e Prontidão para Monetização (v84.1)**: Removidos todos os placeholders do AdSense (`PLACEHOLDER_SLOT_ID`) nas rotas `/alvos` e `/alertas`, substituindo-os pelo identificador de slot oficial funcional (`2020882637`). Adicionalmente, reestruturamos a inclusão do script global do Google AdSense no `layout.tsx` para rodar fora da tag `<head>` utilizando o componente `Script` nativo do Next.js com a estratégia de carregamento `afterInteractive`, eliminando warnings de hidratação no StrictMode/Turbopack e garantindo a exibição e renderização corretas dos anúncios conforme a folha de estilo de rede social com rolagem infinita.
- **Alinhamento e Padronização Global de IA (v84.0)**: Realinhamento total do motor de IA (`ai_service.py`) com os critérios oficiais de treinamento do `CRITERIOS_TREINAMENTO.md`. Padronizamos as categorias na IA com o dicionário de banco/API da `PASA_CONFIG`, e adicionamos a Blindagem contra Falsos Positivos (Protocolo de Defesa) tanto no prompt local (LiteRT/Ollama) quanto no refinamento Cloud. Adicionalmente, mitigamos possíveis erros de quebra de API ao expor o alias de compatibilidade `classify` (usado por `pasa_auditor` e `ad_processor`) e ao injetar os aliases `category`/`confidence` nas respostas JSON do parser.
- **Filtro Léxico Dinâmico Contra Falsos Positivos de Menção (v83.9)**: Identificada e resolvida regressão na classificação automática de comentários. Marcações isoladas (ex: `@username`) estavam alcançando o classificador IA e gerando falsos positivos de `INSULTO_AD_HOMINEM`. Corrigimos o motor estendendo o `LexicalFilter` para expurgar comentários compostos estritamente de marcações de usuário e emojis/pontuações antes de enviar para classificação de IA, com sucesso absoluto validado por testes locais.
- **Integração de Recursos Interativos e Investigação Cívica no Frontend (v83.8)**: Atribuição de funcionalidade premium aos botões estáticos identificados. Implementamos carregamento progressivo de dados na Central de Análises (`AnaliseTab.tsx`); criamos um painel de filtros de pesquisa e risco em tempo real para Candidatos Monitorados (`TargetsTab.tsx`); e desenvolvemos um modal completo de Investigação Cívica e Descarte de falsos positivos na aba de Alertas de Segurança (`AlertsTab.tsx`), com persistência de `analise_pericial` (análise analítica) integrada ao endpoint de auditoria do backend e invalidação de cache do React Query.
- **Automação de Cookies e Rotação Stealth de Alta Disponibilidade (v83.7)**: Integrado o script unificado `export_playwright_cookies.py` ao `SessionHealer` sob o controle do `AutopilotManager`. Implementada a cura preventiva de cookies automática a cada 12 horas e o re-login forçado sob demanda ao detectar degradação (`SESSION_EXPIRED`). Adicionalmente, expandimos o motor com geração dinâmica de assinaturas Chrome/Firefox/Safari e injeção coerente de `Accept-Language` dinâmico para evasão de bloqueios.
- **Resiliência do Modal e Conexão de Browser do InstagramScraperV2 (v83.6)**: Implementação de proteção robusta contra erros de conexão fechada e timeouts de clique de modais. Adicionados timeouts de clique de 10s e monitoramento contínuo de `page.is_closed()` no processamento de postagens do feed, abortando o processamento imediatamente em caso de fechamento do navegador. Isso evitou com sucesso falhas subsequentes em cascata e eliminou alertas repetidos de screenshots em páginas inválidas.
- **Visualizador de Relatórios Corporativos com Conversão em PDF Client-Side (v83.6)**: Criada a rota de visualização de relatórios em markdown `/relatorios/visualizar` no Next.js com parser nativo em TypeScript. Adicionado suporte a tabelas, títulos e listas com folha de estilo de impressão integrada que permite a exportação estática perfeita e conversão em PDF corporativo de alta fidelidade via `window.print()` do navegador sem dependências extras.
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
