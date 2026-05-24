# MAPEAMENTO FUNCIONAL - SENTINELA (v58.0)
_Data: 24 de Maio de 2026_

Este documento descreve as principais funções lógicas e módulos do sistema, complementando o esquema de banco de dados para o desenvolvimento do novo frontend.

---

## 1. 🏗️ Orquestrador Central (`SentinelaOrchestrator`)
O "Cérebro" do sistema que gerencia a vida dos workers e a integridade da infraestrutura.

- **`register(worker)`**: Vincula novos agentes de coleta ao pool de execução.
- **`run_cycle_with_validation()`**: Executa o ciclo de um worker, valida o resultado e processa recompensas.
- **`_perform_self_healing()`**: Rotina de autocura que executa `malloc_trim` (flush de memória), limpa alvos estagnados (Zombie Cleanup) e dispara o Garbage Collector.
- **`claim_lock`**: Garantia de atomicidade para que múltiplos workers não escolham o mesmo alvo simultaneamente.

## 2. 🕷️ Motor de Coleta V2 (`InstagramScraperV2`)
Motor independente baseado em Playwright para extração forense de dados.

- **`scrape_profile(username)`**: Fluxo principal de navegação, bypass de login wall e extração de posts.
- **`_validate_target_identity()`**: Proteção contra redirects e perfis inválidos/privados.
- **`_extract_shortcodes()`**: Identifica posts no grid, detectando sinalizadores de **Posts Fixados (Pins)**.
- **`_scrape_post()`**: Abre o modal, verifica a idade do post (limite de 7 dias) e extrai comentários.
- **Tiers de Resiliência**: Tenta capturar dados via (1) Network Interception (GraphQL) -> (2) Scripts JSON -> (3) Heurística DOM.

## 3. 🧠 Serviço de Inteligência (`AIService`)
Motor de classificação híbrida em cascata seguindo o MCA v2.2.

- **`classify_text(text)`**: Roteamento dinâmico entre provedores:
    - **Tier 0**: LiteRT / Ollama (Local/Velocidade).
    - **Tier 1**: Mistral Nemo (Cloud/Precisão).
    - **Tier 2**: Groq Llama 3.3 (Cloud/Resiliência).
- **`_parse_json_response()`**: Interpretador resiliente para capturar confiança e categorias mesmo com variações de formato.
- **MCA v2.2**: Protocolo de classificação especializado em ironia técnica, hostilidade velada e misoginia política.

## 4. ⚖️ Motor de Recompensas (`RewardEngine`)
Sistema de gamificação e reputação para gestão de workers.

- **`process_result(cycle_result)`**: Calcula o ganho/perda de XP baseado na produtividade real.
- **`calculate_xp_delta()`**: 
    - Inserção Inédita: **+15.0 XP**.
    - Vazio Improdutivo: **-5.0 XP**.
    - Falha Técnica: **-15.0 XP**.
- **`resolve_tier()`**: Define a patente do worker (Platinum, Gold, Silver, Bronze, Critical) baseada no score (0-100).

## 5. 🔗 Gestor de Filas (`QueueManager`)
Despachante inteligente de alvos.

- **`claim_next_target()`**: Decide o próximo alvo seguindo a hierarquia:
    1. Manual (Forçado).
    2. Fila Prioritária (Prioridade 1 = Máxima).
    3. Justiça (Fairness 25%) - Força rotação global.
    4. Rotação Global (Mais antigo primeiro).

## 6. 🤖 SRE Advisor (`AIAdvisor`)
Analista virtual de falhas e melhoria de processo.

- **`analyze_and_suggest()`**: Disparado em falhas ou ciclos vazios. Analisa métricas + Documentação técnica (`DocFetcher`) para sugerir correções de rede, seletores ou credenciais.

## 🛡️ 7. Supervisor (`Watchdog`)
Guardião do sistema com dashboard local.

- **`guard()`**: Monitora o processo principal, reinicia em caso de crash e aplica patches de dependências.
- **`get_metrics()`**: Endpoint unificado que serve dados reais do Supabase para o dashboard de monitoramento.

---

## 🚩 Categorias de Classificação (MCA v2.2)
- **CAMPANHA_COORDENADA**: Detecção de robôs/comportamento inautêntico.
- **INSULTO_AD_HOMINEM**: Ataques pessoais/técnicos velados.
- **MISOGINIA_POLITICA**: Hostilidade de gênero contra alvos femininos.
- **MILICIA_DIGITAL**: Descrédito institucional coordenado.
- **ATAQUE_INSTITUCIONAL**: Hostilidade contra órgãos públicos.
- **NEUTRO / LIXO**: Mensagens orgânicas ou ruído técnico.
