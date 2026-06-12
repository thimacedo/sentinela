# 🧠 DOCUMENTAÇÃO: AUTOCURA E RESILIÊNCIA OPERACIONAL (v97.6)

O sistema Sentinela Democrática implementa uma arquitetura de **Autonomia Biológica**, onde falhas operacionais e de infraestrutura são monitoradas, diagnosticadas e tratadas de forma reativa e autônoma, sem necessidade de intervenção humana constante.

---

## 🛡️ Camadas de Autocura e Resiliência

### 1. Nível de Infraestrutura e Processos (Watchdog & SRE Agent)
O Watchdog atua como supervisor global da aplicação e hospeda o **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`):
*   **Loop Cognitivo OODA**: O SRE Agent executa um loop de Observação, Orientação, Decisão e Ação que monitora os logs em tempo real.
*   **Tratamento Determinístico de Falhas**: Erros de rede, timeouts ou rate-limits comuns são mitigados com custo zero de tokens.
*   **Cura por Tool Calling**: Sob falhas complexas ou desconhecidas, o SRE Agent executa ações atômicas de cura por registro de ferramentas:
    *   `restart_main_runner`: Restart do orquestrador principal ao detectar crash de comunicação IPC (`EPIPE`) do Playwright.
    *   `restart_worker`: Reinício de threads ou instâncias específicas.
    *   `rotate_session` (via `SessionHealer`): Invalidação e rotatividade de sessões sob detecção de bloqueios.
    *   `cooldown_target`: Cooldown temporário de alvos que estejam gerando excesso de rate limit.
*   **Bypass Headless de Console**: O Watchdog ignora chamadas de UI no boot quando desanexado do console, evitando travamento silencioso de DLLs gráficas de bandeja no Windows.
*   **Estabilização IPv6**: Uso direto do endereço local IPv4 (`127.0.0.1:8001`) nas requisições internas, contornando falhas de resolução de nome IPv6 `[::1]` no Windows.

### 2. Nível de Coleta e Scraper (DOM Healing)
A coleta é governada pelo `wk_coleta_instagram.py` que se apoia no `InstagramScraperV2` e no loop cognitivo do `ScrapeAgent`:
*   **DOM Healing (Autocura de Seletores)**: Se a estrutura DOM do Instagram mudar e o Playwright não encontrar um botão ou elemento crítico de scrap, o ScrapeAgent aciona a visão computacional do **Gemini 2.5 Flash** para examinar um screenshot da página em tempo real.
*   **Cache de Seletores Aprendidos**: Uma vez que o Gemini Flash deduz o novo seletor CSS correto para interagir, o sistema armazena a regra no arquivo `configs/learned_selectors.json` (Cache Hit). Ciclos de coleta posteriores usarão diretamente o seletor aprendido sem incorrer em novas chamadas de API de visão (economia de burn rate).
*   **Comportamento Humano Estocástico**: Motor de persona (`persona_mode.py`) que imita cliques, velocidades e scrolls humanos para prevenir ativamente o banimento e desafios CAPTCHA.

### 3. Diagnóstico Granular de Coleta Zero
Para fins de observabilidade, coletas que retornam 0 comentários não são mais tratadas como falha genérica. O worker `WkColetaInstagram` analisa os contadores locais e clasifica a causa exata em seu `CycleResult`:
*   `no_posts_found`: O perfil pesquisado não possui publicações visíveis ou é privado.
*   `no_comments_in_posts`: Posts encontrados com sucesso, mas nenhum comentário recente existe.
*   `playwright_error`: Falha técnica de renderização ou rede do navegador.
*   `junk_detected`: Detecção de bloqueios, desafios visuais ou páginas corrompidas.

O orquestrador (`SentinelaOrchestrator`) mapeia esses códigos deterministicamente e salva sugestões específicas de autocura no banco (tabela `worker_suggestions`).

### 4. Nível de Inteligência (Cascata PASA e SaFastDrop)
*   **SaFastDrop**: Filtro léxico ultra-veloz em Python puro local. Substitui por completo a dependência do antigo Voyant Server em Java (JVM), reduzindo custos de memória.
*   **Circuit Breakers**: Desativação em tempo real de provedores de IA sob erros de autorização (401/403) e cooldowns exponenciais (300s) em caso de limite de cota (429), desviando o tráfego analítico para o Ollama local e para o `FallbackLLM`.

---

## 📊 Rastreabilidade e Persistência

1.  **Métricas Atômicas**: Gravadas na tabela `worker_runs` e `worker_metrics` do Supabase remoto a cada ciclo.
2.  **Transações Seguras**: Locks de concorrência horizontal no Supabase via `SELECT FOR UPDATE SKIP LOCKED` e claim de fila concorrente.
3.  **Idempotência**: Todas as escritas e cadastros no Supabase usam `on_conflict` (upsert) para evitar duplicidade e manter a integridade dos dados históricos.

---

## 🚀 Validação de Resiliência

Para forçar testes e validar o comportamento de autocura:
*   Para monitorar o stream SSE em tempo real: `python scratch/monitor_coleta.py`
*   Para acionar a autocura sob um alvo forçado: `python scratch/set_priority.py` (insere candidato com prioridade 0)
*   Dashboard local em: `http://127.0.0.1:8001` (Sala de Controle)
