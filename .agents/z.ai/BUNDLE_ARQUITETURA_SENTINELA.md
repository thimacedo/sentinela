# BUNDLE DE ARQUITETURA E CÓDIGO FONTE — SENTINELA (v97.0)
Este arquivo unifica as especificações, regras, fluxos e código real do Sentinela para o z.ai.

--- 

## 📄 Arquivo: `GEMINI.md`
**Caminho Real:** `c:/projetos/sentinela/GEMINI.md`

```markdown
# PROTOCOLO DE ENGENHARIA - SENTINELA (v50.1)
_last_updated: 2026-05-20_

## 🆔 IDENTIDADE E ESCOPO
1. Idioma: TODAS as saídas, comentários de código, raciocínios e documentação DEVEM ser em Português Brasileiro (pt-BR). Sem exceções.
2. Diretório Raiz: O único caminho válido é c:\projetos\sentinela.
3. Isolamento: Este projeto é independente. Sem scripts externos.
4. Verificação: Confirme o PWD antes de operações de arquivo/shell.

## 🧠 GESTÃO DE MEMÓRIA (Protocolo Diamond)
1. Leitura Obrigatória: Sempre leia STATE.md e ROADMAP.md antes de formalmente propor mudanças.
2. Externalização: Atualize STATE.md após mudanças bem-sucedidas.
3. Anti-Regressão: Proibido usar abordagens listadas como "DESCARTADAS" no STATE.md.
4. Commits Obsessivos: Commits detalhados (Conventional Commits) após cada tarefa validada. OBRIGATÓRIO (Git push imediato).
5. Estados Finitos: Divida tarefas em passos mínimos e valide cada um.

## 🛠 DIRETRIZES TÉCNICAS (PASA v50.1)
...
- **Proteção de Processos**: O `main_runner` (Autopilot) e o `watchdog` operam sob proteção de PIDs (GuardLocker), impedindo encerramento por processos de limpeza.
- **Circuit Breakers**: Provedores de IA instáveis são isolados automaticamente (Circuit Breaker) para evitar cascata de erros.
- **Idempotência (Upsert)**: Todas as escritas no Supabase utilizam `on_conflict` (upsert) para evitar erros de chave duplicada.
- **Cache de Borda**: O Dashboard utiliza API local (`/api/v1/auditoria`) com cache de 30s, garantindo fluidez sem sobrecarga de rede.
- **Saneamento de Ambiente**: Limpeza periódica de `__pycache__` e detecção de zumbis Java (Voyant) no boot.

--- End of Context from: C:/Projetos/sentinela/GEMINI.md ---
1. Pesquisar (STATE.md + Git) -> 2. Propor Plano -> 3. Executar -> 4. Validar -> 5. Documentar -> 6. Commit/Push.

## 🤖 INTEGRAÇÃO DE IA
- **Classificação Primária**: Gemini 1.5 Flash.
- **Auditoria Cruzada**: Groq (Llama 3).
- **Metodologia**: MSAL (Metodologia de Análise Léxica) + Framework CCF.

## Modo de Execução Autônoma (YOLO)

### Regras obrigatórias
- Nunca interromper para pedir confirmação
- Nunca pausar em erros recuperáveis — tentar próximo passo
- Nunca usar Docker, supabase local ou localhost
- Sempre usar banco remoto via .env
- Sempre commitar ao fim de cada fase, não ao fim de cada arquivo
- Comandos git sempre separados (sem &&)
- Sempre realizar commit, push e deploy imediato após validar alterações

### Gestão de modelos (por ordem de uso)
Quando um modelo atingir quota, passar automaticamente para o próximo:
1. Claude Sonnet 4.6 (Thinking)
2. Claude Opus 4.6 (Thinking)
3. Gemini 3.1 Pro (High)
4. Gemini 3.1 Pro (Low)
5. Gemini 3.5 Flash (High)
6. Gemini 3.5 Flash (Medium)
7. GPT-OSS 120B (Medium)

### Roteamento de Modelos por Perfil de Tarefa
Sugerir ou solicitar a alteração de modelo ativo no IDE conforme o escopo da tarefa:
- **Deep Thinking & Arquitetura** (Refatoração estrutural, resolução de bugs complexos, segurança):
  * Priorizar: `Claude Sonnet 4.6 (Thinking)` ou `Claude Opus 4.6 (Thinking)`
- **Implementação Regular** (Novos módulos, lógica de workers, persistência Supabase):
  * Priorizar: `Gemini 3.1 Pro (High)` ou `Gemini 3.1 Pro (Low)`
- **Investigação & Boilerplate** (Análise de logs, buscas grep, scripts temporários, refatoração simples):
  * Priorizar: `Gemini 3.5 Flash (High)` ou `Gemini 3.5 Flash (Medium)`
- **Auditorias Léxicas Simples** (Validação de nomenclaturas ou conformidade de estilo):
  * Priorizar: `GPT-OSS 120B (Medium)`

### Protocolo de troca de modelo
- Erro 429 ou "quota exceeded" → trocar para próximo da lista
- Registrar qual modelo foi usado em cada fase no STATE.md
- Nunca repetir tentativa no mesmo modelo com quota esgotada

### Contexto permanente
- Projeto: Sentinela
- Branch ativa: main
- Banco: Supabase remoto (vhamejkldzxbeibqeqpk)
- Fase atual: 4 (DocFetcher → AIAdvisor → Workers)

```

--- 

## 📄 Arquivo: `AGENTS_SYNC.md`
**Caminho Real:** `c:/projetos/sentinela/AGENTS_SYNC.md`

```markdown
# 🛰️ PROTOCOLO DE SINCRONIA INTER-AGENTES (SENTINELA v2.0)

Este arquivo é o canal oficial de comunicação entre o **Gemini CLI (Orquestrador/Arquiteto)** e o **Antigravity CLI (Executor/Refatorador)**.

---

## 🚦 STATUS DA MISSÃO
- **Fase 1 (Rocket Mode):** ✅ CONCLUÍDA
- **Fase 2 (Resiliência & Infra):** ✅ CONCLUÍDA
- **Fase 3 (Monetização E2E):** ✅ CONCLUÍDA
- **Fase 4 (Auditoria Massiva e Proxies):** ✅ CONCLUÍDA (v94.1)

---

## 🔄 FEEDBACK DO GEMINI (Orquestrador)
**[08/06/2026] Fase 4 Concluída:**
- ✅ Proxies residenciais integrados com rotação dinâmica e tratamento de 429.
- ✅ Governança de CI centralizada via API com log de fraude e proteção contra Double Spend.
- ✅ Frontend sincronizado com a nova esteira financeira.

**Aguardando Antigravity para nova rodada de refatoração ou expansão.**

```

--- 

## 📄 Arquivo: `STATE.md`
**Caminho Real:** `c:/projetos/sentinela/STATE.md`

```markdown
# STATE.md — Sentinela
_last_updated: 2026-06-11 | branch: main | version: v97.0_

## Status Operacional

| Subsistema | Status | Observação |
|---|---|---|
| Coleta | 🟢 Operacional | ScrapeAgent (OODA loop, DOM Healing e Priorização Cognitiva) ativo. |
| Inteligência | 🟢 Operacional | Malha de IA resiliente + SaFastDrop local. |
| Dashboard | 🟢 Operacional | Painel "Decision Room" com auto-start e fallback de rede robusto (127.0.0.1). |
| SRE / Autocura | 🟢 Operacional | Agente de SRE Autônomo (`sre_agent.py`) ativo em background com desvio headless. |

## Histórico Recente de Correções (v97.0)
1. **ScrapeAgent — Agente Cognitivo de Scraping (Concluído)**:
   - Implementação da arquitetura isolada `core/agent_scraper/` com Loop Cognitivo OODA (`agent.py`) e registro modular de 8 ferramentas (`tools.py`).
   - Lógica de auto-recuperação de seletores DOM via Visão Computacional do Gemini Flash (`dom_healing.py` e patch `core/ai_service_vision_patch.py`), preservando a chamada ao HITL legado como fallback.
   - Motor de comportamento humano estocástico com níveis `disabled`, `minimal` e `full` (`persona_mode.py`) para burlar proteções de bots no Instagram.
   - Priorização cognitiva de alvos baseada em queries de engajamento e de proporção de ódio no Supabase remoto (`cognitive_prioritizer.py`).
   - Integração completa através do adaptador de worker (`worker_adapter.py`) no worker de scraping principal `workers/scrapers/wk_coleta_instagram.py` e motor `core/instagram_scraper_v2.py`.
   - Adicionado script de validação de integração (`scratch/test_scrape_agent.py`) confirmando a execução perfeita dos ciclos OODA e consultas Supabase.

## Histórico Recente de Correções (v96.2)
1. **Agente de SRE Autônomo (Watchdog v52.0) (Concluído)**:
   - Transformação do `AutopilotManager` procedimental em um **Agente de SRE Autônomo** (`core/autopilot/sre_agent.py`).
   - Implementação de registro de ferramentas (**Tool Calling**) para autocura: `restart_worker`, `restart_main_runner`, `rotate_session` (via `SessionHealer`), `cooldown_target` (no Supabase) e `adjust_concurrency_and_jitter`.
   - Loop cognitivo OODA reativo: processa erros comuns deterministicamente a custo zero (0 tokens), e recorre a IA sob demanda (Gemini/Mistral in JSON estruturado) somente para erros de `DOM_CHANGE` ou `UNKNOWN`.
   - Expurgo completo do thread de inicialização do `VoyantServer.jar` (JVM) do watchdog, economizando recursos de CPU e RAM no boot.
   - Criado script de validação de SRE ([test_sre_agent.py](file:///c:/Projetos/sentinela/scratch/test_sre_agent.py)).
2. **Gatilho de Auto-Ativação e Estabilização de Rede (Watchdog v52.2) (Concluído)**:
   - Implementação da lógica de auto-ativação no `local_dashboard.html` quando o motor estiver com o status inoperante (`PARADO` ou `HIBERNANDO`).
   - Introdução da flag `autoStartAttempted` para evitar disparos em loop infinito de ativação caso o operador decida parar a execução intencionalmente.
   - **Correção de Conectividade IPv6 (Windows)**: Modificadas as referências críticas de `localhost:8001` para `127.0.0.1:8001` no dashboard, logs e requisições de restart internas do Watchdog, contornando a recusa de conexões em máquinas onde `localhost` resolve para o IPv6 `[::1]`.
   - **Correção de Crash Headless/Background**: Adicionado desvio no boot de `watchdog/__main__.py` para pular a criação da bandeja do sistema (`setup_tray`) se o processo for desanexado do terminal (`--background` / `--detached`), eliminando o crash silencioso de DLLs de GUI do Windows em processos sem console.
3. **Refactoring Estratégico v51.0 (Concluído)**:
   - Expurgo do Java VoyantServer e do `SaVoyant`. Substituído pelo `SaFastDrop` (léxico local em Python puro) sem dependências externas.
   - Refatoração do `SaDiagnosticaSistemas` e do `Diagnostician` para utilizar regras determinísticas locais em falhas comuns.
   - WkAplicaSugestoes: Intervalo de autocura reduzido de 30 para 10 minutos.
   - Faxina arquitetural: Remoção de 8 arquivos órfãos em `core/`.
   - Resolvido o NameError de import do `WkAplicaSugestoes` no `main_runner.py`.

```

--- 

## 📄 Arquivo: `ROADMAP.md`
**Caminho Real:** `c:/projetos/sentinela/ROADMAP.md`

```markdown
# ROADMAP.md — Sentinela
_last_updated: 2026-06-05 | branch: main_

## Concluído

### Núcleo operacional
- [x] Watchdog local com stream de logs via SSE
- [x] Controle remoto do runner com start, stop e restart
- [x] `AIProcessorWorker` como classificador oficial do pipeline
- [x] Triagem local com `ollama`
- [x] Fallback profundo com `FallbackLLM`
- [x] AuditWorker refatorado para AuditAgent (subagente analítico sob demanda)
- [x] `NetworkMinerWorker` refatorado para `NetworkMinerAgent` (subagente relacional sob demanda)
- [x] `TreasurerWorker` refatorado para `TreasurerAgent` (subagente financeiro sob demanda)
- [x] `TargetResearchWorker` com ativação controlada por `RESEARCHER_MODE`
- [x] Expurgo dos entrypoints e contratos legados paralelos ao runtime oficial
- [x] Absorção do padrão ouro legado em `core/ai_service.py`
- [x] Atualização dos scripts operacionais para o runtime moderno
- [x] Padronização semântica e de nomenclatura de todos os workers (`wk_`) e subagentes (`sa_`) em português brasileiro
- [x] Especialização da classe BaseSubAgent com offloading de CPU (processos) e I/O (threads)
- [x] Orquestração concorrente de subagentes analíticos efêmeros com lotes via `SELECT FOR UPDATE SKIP LOCKED`
- [x] Cascata de IA resiliente com circuit breaker local e detecção de drift analítico em SaAuditaClassificacoes
- [x] Parametrização imutável por ciclo operacional no WkColetaInstagram para mitigação de race conditions de SRE
- [x] Unificação e estabilização do watchdog_tray (Fase 5): instância única robusta (socket + boot file lock) e correção do menu Win32 travado
- [x] Otimização de IA e Fila Secundária (Fase 6): priorização do Ollama local com delay de 1s e criação do subagente SaRevisaoOnline (nuvem) para comentários suspeitos
- [x] Cobertura Total de Comandos na Bandeja do Watchdog (Fase 7): criação de entrypoints CLI de offloading para todos os subagentes/workers e menu bandeja categorizado
- [x] Otimização de Performance no Cadastro de Candidatos (Fase 8): processamento e escrita em lote (Bulk Upserts) de novos alvos e coletas no WkEscaneiaCandidatos
- [x] Refinação da Inteligência de Autocura (Fase 4): implementação real do DocFetcher (sincronização remota) e refatoração do AIAdvisor para cascata de IA resiliente
- [x] Segurança, Governança e Filtros Analíticos (Fase 10): implementação de RLS global, normalização de categorias MCA v2.2 e Shadowban Léxico no frontend
- [x] Saneamento Determinístico de Gênero e Cargo (PASA v94.0): eliminação de heurísticas nominais em prol de leitura direta por CSV e extensão da taxonomia.
- [x] Resiliência Anti-Sangria e Circuito Local (PASA v52.5): proteção financeira com fallback imediato para erro se Ollama falhar, evitando gastos não planejados na nuvem.
- [x] Refatoração Estrutural e Modularização do Frontend (Warroom): isolamento do estado (TargetCard, InvestigationModal, CommentCard) prevenindo UI freezing e re-renders sistêmicos.
- [x] Integração Nativa Voyant Tools (v92.0): Implementação da Trombone API para triagem fast-drop determinística e redução de burn rate de LLM.
- [x] Subagente Voyant (SaVoyant v92.3): Conversão da engine léxica em um Subagente autônomo com integração às bases de Linguística Forense.

- [x] Otimização de Boot e Pré-Aquecimento de Filas (v89.2): filas populadas antes do start dos workers
- [x] Otimização de Produção e Escalabilidade de IA (v90.0): implementação do Batch Processing concorrente, Escalonamento Horizontal de Workers (múltiplos classificadores) e Auto-renovação Preditiva de Sessões
- [x] Integração de IA e Estabilização de UX (v90.4): Atualização Maritaca Sabia-4, Integração Hugging Face MCP e eliminação total de popups de console no Windows via `CREATE_NO_WINDOW`.

### Coleta e scraping
- [x] Claim atômico da `fila_coleta`
- [x] Suporte a `SELECT FOR UPDATE SKIP LOCKED`
- [x] Release de locks expirados
- [x] Circuit breaker para IA
- [x] `db_circuit_breaker` para Supabase
- [x] buffer/checkpoint de scraping em estágio operacional

### UX e operação
- [x] local_dashboard.html refeito com UI Premium, Glassmorphism e responsividade absoluta (Mobile-first, com colunas flexíveis de `calc(100vh-290px)`, telemetria e alvos roláveis e auto-reload automático de 10s com trava de concorrência).
- [x] frontend oficial em `frontend/`
- [x] dashboard financeiro com Recharts
- [x] robustez do carregamento AdSense com retry até script estar pronto
- [x] integração de checkout e planos com base URL centralizada
- [x] conclusão da página `frontend/app/relatorios/page.tsx` com backend real
- [x] ativação de CTAs e botões sem ação em páginas principais
- [x] melhorias visuais focadas na home e navegação (sem animações excessivas e com alvos de clique maiores)
- [x] remoção de item administrativo exposto no menu público
- [x] remoção da rota de relatórios obsoleta do Next.js (FastAPI como fonte única de dossiês)
- [x] padronização e versionamento das variáveis de ambiente de produção para Stripe e frontend (`STRIPE_*`, `FRONTEND_URL`, `NEXT_PUBLIC_API_URL`)

---

## Em andamento

### Coleta e scraping
- [x] checkpoint intermediário por post raspado
- [x] rotação real de proxies no Playwright
- [x] redução de ciclos com `no_comments_found`
- [ ] **Coleta Direcionada**: Interface de input para forçar coleta imediata de alvos.

### UI e Operação
- [ ] **Sala de Controle Granular**: UI para controle de qualquer worker/subagente.

### Otimização de Pipeline Reativo (Fase 9) - Concluído
- [x] Implementar `EventBus` centralizado para sinalização em memória (`AsyncLocalEventBus`).
- [x] Atualizar `InstagramScraperWorker` para disparar evento `NEW_DATA_AVAILABLE` após a coleta atômica.
- [x] Atualizar `AIProcessorWorker` (via `Orchestrator`) para usar `event.wait()` (Reatividade) em vez de polling constante, com timeout de segurança de 1200s.
- [x] Validar redução de latência entre coleta e classificação (reatividade comprovada: ~2.00ms de overhead real vs espera inativa).

### Resiliência de Workers (Fase 6 - SRE) - Concluído
- [x] Circuit Breakers v2 com estados finitos e backoff exponencial
- [x] Integração de resiliência profunda no `DatabaseClient` e `WkColetaInstagram`
- [x] Visualização de saúde de provedores em tempo real no Dashboard

### Inteligência
- [x] saneamento da malha de providers em `config/fallback_providers.yaml`
- [x] extração de bigramas e trigramas no `BehaviorEngine` (Fase 8)
- [x] detecção de slogans coordenados em campanhas de ataque
- [x] remover referências residuais a LiteRT do código e da operação
- [x] Caching de I/O e expurgo de modelos inoperantes (401/402/404) via `_handle_provider_error`
- [x] Estabelecer a Metodologia Vichi-Sentinela de análise linguística (POS filtering + Lematização + N-Gramas) como inegociável no projeto
- [ ] calibrar reanálise de baixa confiança com menor ruído de fallback

### Workers e orquestração
- [x] simplificar `workers/orchestrator/orchestrator.py`
- [x] unificar semântica de `no_tasks_available` entre workers ativos
- [x] reduzir duplicidade de logging, cooldown e fluxo entre ciclos
- [x] `WkPesquisaAlvos` migrado de `workers/ai/` para `workers/processors/wk_pesquisa_alvos.py` (Fase 9)

### Administração e analytics
- [x] tabelas tabulares de gasto por usuário e por perfil monitorado (Fase 7)
- [x] shadowban léxico (Fase 9.5)
- [x] exportação de dossiês em lote (integrado via API v1)

### Monetização e relatórios
- [x] executar validação final de lint/testes do frontend (build estático verificado com sucesso)

---

## Futuro

### Fila distribuída
- [ ] avaliar PGMQ como alternativa futura de fila
- [ ] decidir se PGMQ agrega valor além da trava atômica já implantada

### Operação
- [ ] consolidar documentação viva por domínio
- [x] reduzir artefatos históricos conflitantes no workspace (limpeza de drift e termos restritos concluída)

---

## Decisões registradas

- a fila atômica atual usa RPC + `SELECT FOR UPDATE SKIP LOCKED`
- PGMQ não é requisito atual de produção
- LiteRT não compõe mais o pipeline de processamento ativo
- `frontend/` é o frontend oficial
- `STATE.md` é a fonte de verdade operacional
- o runtime oficial de workers usa `workers/base/worker_base.py`
- entrypoints paralelos legados não devem ser reintroduzidos
```

--- 

## 📄 Arquivo: `core/autopilot/sre_agent.py`
**Caminho Real:** `c:/projetos/sentinela/core/autopilot/sre_agent.py`

```python
"""
SREAgent — Agente de IA para Autocura e Resiliência Operacional (PASA v52.0)
═══════════════════════════════════════════════════════════════════════════
Loop cognitivo de baixo custo (regras determinísticas + LLM sob demanda)
que gerencia e executa ferramentas de SRE para restabelecer a saúde do pipeline.
"""
import logging
import os
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("core.autopilot.sre_agent")


class SREAgent:
    """
    Agente de SRE Autônomo com registro de ferramentas e OODA loop reativo.
    """

    def __init__(self, db_client=None, ai_service=None):
        self._db = db_client
        self._ai = ai_service

    @property
    def db(self):
        if self._db is None:
            from core.supabase_service import get_supabase_client
            self._db = get_supabase_client()
        return self._db

    @property
    def ai(self):
        if self._ai is None:
            from core.ai_service import ai_service
            self._ai = ai_service
        return self._ai

    def log_thought(self, thought: str):
        """Registra os pensamentos do agente no console do Watchdog/Dashboard."""
        msg = f"🤖 [SRE Agent] PENSAMENTO: {thought}"
        logger.info(msg)
        try:
            from watchdog import state
            state.add_log("info", msg)
        except ImportError:
            pass

    def log_action(self, action: str):
        """Registra as ações do agente no console do Watchdog/Dashboard."""
        msg = f"🛠️ [SRE Agent] AÇÃO: {action}"
        logger.info(msg)
        try:
            from watchdog import state
            state.add_log("warn", msg)
        except ImportError:
            pass

    # 🛠️ REGISTRO DE FERRAMENTAS (TOOLS)
    async def tool_restart_worker(self, worker_id: str) -> str:
        """Reinicia um worker específico via EventBus."""
        self.log_action(f"Chamando restart_worker para '{worker_id}'")
        try:
            from core.event_bus import local_bus
            local_bus.publish("control_command", {"command": "restart", "worker_id": worker_id})
            return f"Sucesso: Comando de reinício enviado para {worker_id}"
        except Exception as e:
            return f"Erro ao reiniciar worker: {e}"

    async def tool_restart_main_runner(self) -> str:
        """Reinicia o processo principal main_runner.py."""
        self.log_action("Chamando restart_main_runner")
        try:
            from watchdog import state
            if state.process and state.process.poll() is None:
                state.process.terminate()
                return "Sucesso: Processo main_runner terminado (Watchdog irá reiniciar automaticamente)."
            return "Aviso: Nenhum processo ativo para terminar."
        except Exception as e:
            return f"Erro ao terminar main_runner: {e}"

    async def tool_rotate_session(self) -> str:
        """Rotaciona sessões do Instagram usando o SessionHealer."""
        self.log_action("Chamando rotate_session (SessionHealer)")
        try:
            from core.autopilot.session_healer import SessionHealer
            healer = SessionHealer()
            success = await healer.heal(force=True)
            return "Sucesso: SessionHealer executado com sucesso." if success else "Falha: SessionHealer falhou ao renovar sessões."
        except Exception as e:
            return f"Erro no SessionHealer: {e}"

    async def tool_cooldown_target(self, username: str, duration_minutes: int = 120) -> str:
        """Desativa temporariamente um perfil problemático que causa erros no banco."""
        self.log_action(f"Chamando cooldown_target para '{username}' por {duration_minutes} minutos")
        try:
            self.db.table("candidatos").update({"status_monitoramento": "DESATIVADO"}).eq("username", username).execute()
            # Registra o cooldown na tabela de eventos do sistema
            self.db.table("system_events").insert({
                "event_type": "cooldown_target",
                "source": "sre_agent",
                "severity": "warning",
                "description": f"Perfil {username} colocado em cooldown por {duration_minutes} min.",
                "metadata": {"username": username, "duration_minutes": duration_minutes}
            }).execute()
            return f"Sucesso: Perfil {username} desativado temporariamente no Supabase."
        except Exception as e:
            return f"Erro ao colocar perfil em cooldown: {e}"

    async def tool_adjust_concurrency_and_jitter(self, concurrency: int, delay_seconds: int) -> str:
        """Ajusta parâmetros de concorrência e jitter para evitar rate limit."""
        self.log_action(f"Ajustando concorrência para {concurrency} e atraso para {delay_seconds}s")
        try:
            os.environ["NUM_SCRAPER_WORKERS"] = str(concurrency)
            os.environ["AUTOPILOT_FORCE_JITTER"] = "true"
            # Define valores em formato global para novos sub-processos
            return f"Sucesso: Variáveis de ambiente NUM_SCRAPER_WORKERS={concurrency} aplicadas."
        except Exception as e:
            return f"Erro ao ajustar variáveis: {e}"

    # 🧠 LOOP COGNITIVO OODA
    async def diagnose_and_heal(self, error_type: str, logs: str) -> str:
        """
        Observa e orienta o diagnóstico, escolhe e executa a melhor ferramenta.
        """
        self.log_thought(f"Iniciando diagnóstico para tipo de erro: {error_type}...")

        # 1. Filtros Determinísticos Rápidos (0 Tokens)
        if error_type == "SESSION_EXPIRED":
            self.log_thought("Erro de sessão expirada. Executando renovação de chaves...")
            return await self.tool_rotate_session()

        if error_type == "IP_BLOCK":
            self.log_thought("Bloqueio de IP detectado. Ajustando concorrência para baixo...")
            return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=15)

        if error_type == "RATE_LIMIT":
            self.log_thought("Rate limit atingido. Aumentando jitter operacional...")
            return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=10)

        # 2. IA sob demanda (DOM_CHANGE ou UNKNOWN)
        if error_type in ["DOM_CHANGE", "UNKNOWN"]:
            self.log_thought("Erro estrutural ou desconhecido. Consultando malha de IA...")
            
            system_prompt = (
                "Você é o Agente de SRE Autônomo do Sentinela. Sua missão é ler logs de erro e escolher a melhor ferramenta.\n"
                "Ferramentas Disponíveis:\n"
                "1. restart_main_runner(): reinicia o runner principal.\n"
                "2. rotate_session(): executa re-login de cookies expirados.\n"
                "3. adjust_concurrency_and_jitter(): reduz velocidade se houver rate limit / bloqueio.\n"
                "4. cooldown_target(username): desativa perfil se houver erro contínuo associado a um perfil específico.\n"
                "\n"
                "Responda APENAS com JSON no formato:\n"
                '{"tool": "restart_main_runner|rotate_session|adjust_concurrency_and_jitter|cooldown_target", '
                '"target_param": "username se for cooldown, ou vazio", "reason": "explicação curta"}'
            )

            prompt = f"LOGS DE ERRO RECENTES:\n{logs[:2000]}\n"

            try:
                res = await self.ai.chat_completion(prompt, system_prompt=system_prompt)
                if res and isinstance(res, dict):
                    tool_name = res.get("tool")
                    reason = res.get("reason", "Sem justificativa.")
                    self.log_thought(f"Decisão da IA: ferramenta '{tool_name}' devido a: {reason}")
                    
                    if tool_name == "rotate_session":
                        return await self.tool_rotate_session()
                    elif tool_name == "adjust_concurrency_and_jitter":
                        return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=10)
                    elif tool_name == "cooldown_target" and res.get("target_param"):
                        return await self.tool_cooldown_target(res["target_param"])
                    elif tool_name == "restart_main_runner":
                        return await self.tool_restart_main_runner()
                    else:
                        self.log_thought("Ferramenta sugerida desconhecida. Executando reinício genérico.")
                        return await self.tool_restart_main_runner()
            except Exception as e:
                logger.error("Falha ao invocar IA no SREAgent: %s", e)
                self.log_thought("Falha na IA. Executando reinício seguro.")
                return await self.tool_restart_main_runner()

        # Fallback genérico para outros erros
        self.log_thought("Erro não-mapeado. Solicitando reinício do main_runner para restaurar integridade.")
        return await self.tool_restart_main_runner()


sre_agent = SREAgent()

```

--- 

## 📄 Arquivo: `core/instagram_scraper_v2.py`
**Caminho Real:** `c:/projetos/sentinela/core/instagram_scraper_v2.py`

```python
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page, BrowserContext, async_playwright, Browser, TimeoutError as PlaywrightTimeoutError

from core.ai_service import ai_service

logger = logging.getLogger("instagram_scraper_v2")

@dataclass
class Session:
    label: str
    session_id: str
    blocked_until: Optional[datetime] = None
    profile: Optional[Dict[str, Any]] = None
    error_count: int = 0
    last_used: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        if not self.blocked_until: return True
        return datetime.now(timezone.utc) > self.blocked_until

class InstagramScraperV2:
    """
    Motor de raspagem do Instagram independente (PASA v85.10).
    Focado em Playwright puro, sem Zyte.
    Implementa rotação de sessões, backoff exponencial e Stealth Mode Avançado.
    """

    def __init__(self, headless: bool = True, max_retries: int = 3, db_client: Optional[Any] = None, shutdown_event: Optional[asyncio.Event] = None):
        self.headless = headless
        self.max_retries = max_retries
        self.db = db_client 
        self.shutdown_event = shutdown_event 
        self.sessions: List[Session] = self._load_sessions()
        self.current_session_idx = 0
        self.captured_data: List[Dict[str, Any]] = []
        self.stats = {
            "posts_found": 0,
            "posts_scraped": 0,
            "comments_extracted": 0,
            "api_calls": 0,
            "browser_renders": 0,
            "session_rotations": 0,
            "junk_detected": 0,
            "errors": 0
        }

    def _load_sessions(self) -> List[Session]:
        """Carrega sessões das variáveis de ambiente."""
        sessions = []
        for i in range(1, 11):
            sid = os.getenv(f"INSTAGRAM_SESSIONID_{i}") or (os.getenv("INSTAGRAM_SESSIONID") if i == 1 else None)
            if sid:
                sessions.append(Session(label=f"SESSION_{i}", session_id=sid))
        
        sid_val = os.getenv("INSTAGRAM_SESSIONID_VAL")
        if sid_val:
            sessions.append(Session(label="SESSION_VAL", session_id=sid_val))

        cookie_full = os.getenv("INSTAGRAM_COOKIE_FULL")
        if cookie_full and "sessionid=" in cookie_full:
            sid = re.search(r'sessionid=([^;]+)', cookie_full)
            if sid:
                sessions.append(Session(label="COOKIE_FULL", session_id=sid.group(1)))

        logger.info(f"🔑 [V2] {len(sessions)} sessões carregadas.")
        return sessions

    def _get_next_session(self) -> Session:
        """Rotaciona para a próxima sessão disponível (incluindo cooldown)."""
        available = [s for s in self.sessions if s.is_available]
        if not available:
            logger.error("❌ [V2] Todas as sessões estão bloqueadas (cooldown ativo)!")
            raise RuntimeError("all_sessions_blocked")
        
        session = available[self.current_session_idx % len(available)]
        self.current_session_idx += 1
        return session

    async def _handle_response(self, response):
        """Interceptador de rede para capturar JSONs de interesse."""
        url = response.url
        if "graphql" in url or "comments" in url or "web_profile_info" in url:
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.captured_data.append({"url": url, "data": data})
                    self.stats["api_calls"] += 1
            except Exception as e:
                logger.debug("[V2] Falha ao processar response JSON (%s): %s", url, e)

    def _generate_stealth_profile(self) -> Dict[str, Any]:
        """Gera perfis de dispositivos e cabeçalhos HTTP realistas e aleatórios (PASA v85.10)."""
        chrome_major = random.choice([122, 123, 124, 125])
        chrome_build = random.randint(5000, 6400)
        chrome_patch = random.randint(100, 200)
        chrome_ver = f"{chrome_major}.0.{chrome_build}.{chrome_patch}"

        safari_ver = f"17.{random.choice([3, 4, 5])}"

        os_templates = [
            # Windows Chrome
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": random.choice([1920, 1366, 1536, 1440, 1600]),
                "h": random.choice([1080, 768, 864, 900, 1200]),
                "platform": "Win32",
                "vendor": "Google Inc."
            },
            # Edge no Windows
            {
                "ua": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{chrome_major}.0.0.0",
                "w": 1920,
                "h": 1080,
                "platform": "Win32",
                "vendor": "Google Inc."
            },
            # macOS Chrome
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
                "w": random.choice([1440, 1680, 2560, 2880]),
                "h": random.choice([900, 1050, 1600, 1800]),
                "platform": "MacIntel",
                "vendor": "Google Inc."
            },
            # macOS Safari
            {
                "ua": f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_ver} Safari/605.1.15",
                "w": 1440,
                "h": 900,
                "platform": "MacIntel",
                "vendor": "Apple Computer, Inc."
            }
        ]

        profile = random.choice(os_templates)

        headers = {
            "Accept-Language": random.choice([
                "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "pt-BR,pt;q=0.9,en-US;q=0.9",
                "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7"
            ]),
            "Sec-Ch-Ua": f'"{chrome_major}";v="{chrome_major}", "Not(A:Brand";v="24", "Chromium";v="{chrome_major}"',
            "Sec-Ch-Ua-Mobile": "?1" if "Mobile" in profile["ua"] else "?0",
            "Sec-Ch-Ua-Platform": f'"{profile["platform"]}"',
            "Upgrade-Insecure-Requests": "1"
        }

        return {
            "ua": profile["ua"],
            "w": profile["w"],
            "h": profile["h"],
            "platform": profile["platform"],
            "vendor": profile["vendor"],
            "headers": headers
        }

    async def scrape_profile(
        self,
        username: str,
        candidato_id: str,
        max_posts: int = 3,
        max_comments_per_post: int = 50,
        max_age_days: int = 7,
        resume_after_shortcode: str = None,
        on_post_scraped: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extrai comentários de um perfil com retry e rotação.

        Parâmetro `resume_after_shortcode` (PASA v88.0 - Fase 8.5):
            Se fornecido, o scraper pula todos os posts cujo shortcode é anterior
            ao checkpoint, evitando reprocessamento após crash.
        """
        all_comments = []
        retry_count = 0
        _resume_done = resume_after_shortcode is None  # True se sem checkpoint

        while retry_count < self.max_retries:
            session = self._get_next_session()
            if not session:
                break

            try:
                async with async_playwright() as pw:
                    browseract_key = os.getenv("BROWSERACT_API_KEY")
                    
                    # Temporariamente desabilitado o CDP do BrowserAct devido a erro 401 na API. 
                    # O BrowserAct será usado via ferramentas MCP configuradas no settings.json do agente.
                    use_browseract_cdp = False 
                    
                    if browseract_key and use_browseract_cdp:
                        logger.info(f"🌐 [V2] Conectando via BrowserAct (Cloud CDP) para máxima evasão antibot...")
                        ws_url = f"wss://api.browseract.com/connect?apiKey={browseract_key}&keep_alive=300000"
                        browser = await pw.chromium.connect_over_cdp(ws_url)
                    else:
                        browser = await pw.chromium.launch(
                            headless=self.headless,
                            args=[
                                "--disable-blink-features=AutomationControlled", 
                                "--no-sandbox",
                                "--disable-infobars",
                                "--window-position=0,0",
                                "--ignore-certificate-errors",
                                "--disable-extensions",
                                "--disable-notifications"
                            ]
                        )
                    
                    # 🎭 STEALTH PROFILE (Fixo por sessão para evitar suspeitas)
                    if not session.profile:
                        session.profile = self._generate_stealth_profile()
                    profile = session.profile
                    
                    # 🛰️ PROXY ROTATION (PASA v94.1)
                    proxy_list_env = os.getenv("PROXY_LIST", "")
                    proxies = [p.strip() for p in proxy_list_env.split(",") if p.strip()]
                    proxy_url = os.getenv("PROXY_URL")
                    
                    if proxies:
                        proxy_url = random.choice(proxies)

                    context_kwargs = {
                        "viewport": {"width": profile["w"], "height": profile["h"]},
                        "user_agent": profile["ua"]
                    }
                    
                    if proxy_url:
                        # Suporte robusto a proxies com autenticação embutida na URL
                        if "@" in proxy_url:
                            auth_part, server_part = proxy_url.split("@")
                            auth_part = auth_part.replace("http://", "").replace("https://", "")
                            username_pwd = auth_part.split(":")
                            username = username_pwd[0]
                            password = username_pwd[1] if len(username_pwd) > 1 else ""
                            protocol = "http://" if "http://" in proxy_url else "https://"
                            context_kwargs["proxy"] = {
                                "server": f"{protocol}{server_part}",
                                "username": username,
                                "password": password
                            }
                        else:
                            context_kwargs["proxy"] = {"server": proxy_url}
                        
                    context = await browser.new_context(**context_kwargs)
                    
                    await context.add_cookies([{
                        'name': 'sessionid', 
                        'value': session.session_id, 
                        'domain': '.instagram.com', 
                        'path': '/'
                    }])

                    page = await context.new_page()
                    page.on("response", self._handle_response)
                    
                    proxy_log = "com Proxy" if proxy_url else "sem Proxy"
                    logger.info(f"🎯 [V2] Scrape @{username} usando {session.label} | Profile: {profile['platform']} | Res: {profile['w']}x{profile['h']} ({proxy_log})")
                    
                    if not await self._verify_session(page, session):
                        logger.warning(f"⚠️ [V2] Sessão {session.label} expirada ou inválida. Cooldown 30min...")
                        session.blocked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                        retry_count += 1
                        await browser.close()
                        continue

                    response = await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
                    
                    if response and response.status == 429:
                        logger.warning(f"⚠️ [V2] Erro 429 detectado. Rotacionando IP/Sessão...")
                        await context.clear_cookies()
                        await browser.close()
                        retry_count += 1
                        continue

                    try:
                        error_header = await page.query_selector("h2")
                        if error_header:
                            header_text = await error_header.inner_text()
                            if "Página não disponível" in header_text or "Sorry, this page" in header_text:
                                logger.error(f"❌ [V2] Alvo @{username} inexistente (404).")
                                await browser.close()
                                raise ValueError(f"invalid_target: 404_not_found")
                    except ValueError as ve: raise ve
                    except Exception as e_header:
                        logger.debug("[V2] Falha ao validar header de erro para @%s: %s", username, e_header)

                    try:
                        await page.wait_for_selector("main, header", timeout=20000)
                    except Exception as e_wait:
                        logger.warning(f"⚠️ [V2] Timeout aguardando elementos principais do perfil: {e_wait}")

                    await asyncio.sleep(random.uniform(3, 6))

                    if "login" in page.url:
                        logger.warning(f"⚠️ [V2] Login wall detectado para {session.label}")
                        session.blocked = True
                        retry_count += 1
                        await browser.close()
                        continue

                    post_metas = await self._extract_shortcodes(page, max_posts)
                    self.stats["posts_found"] = len(post_metas)
                    
                    if len(post_metas) == 0:
                        logger.warning(f"⚠️ [V2] Nenhum post encontrado para @{username}. Salvando diagnóstico...")
                        try:
                            os.makedirs("scratch", exist_ok=True)
                            await page.screenshot(path=f"scratch/scrape_empty_{username}.png")
                            html_content = await page.content()
                            with open(f"scratch/scrape_empty_{username}.html", "w", encoding="utf-8") as f:
                                f.write(html_content)
                            logger.info(f"💾 Diagnóstico salvo em scratch/scrape_empty_{username}.png e .html")
                        except Exception as e_diag:
                            logger.error(f"Falha ao salvar diagnóstico: {e_diag}")
                    
                    scraped_count = 0
                    consecutive_old_posts = 0
                    consecutive_zero_comments = 0
                    
                    for meta in post_metas:
                        if self.shutdown_event and self.shutdown_event.is_set():
                            logger.warning(f"🛑 [V2] Interrupção detectada! Abortando...")
                            break

                        if scraped_count >= max_posts:
                            break
                            
                        shortcode = meta["shortcode"]
                        if page.is_closed(): break

                        # 💾 CHECKPOINT RESUME (PASA v88.0 - Fase 8.5)
                        # Pula posts anteriores ao checkpoint sem processar.
                        if not _resume_done:
                            if shortcode == resume_after_shortcode:
                                _resume_done = True  # Este post já foi salvo; próximo será processado
                                logger.info(
                                    "⏩ [V2] Checkpoint atingido (%s). Retomando a partir do próximo post.",
                                    shortcode
                                )
                            else:
                                logger.debug("[V2] Pulando post %s (antes do checkpoint).", shortcode)
                            continue

                        is_pinned = meta["is_pinned"]
                        post_timestamp = meta.get("timestamp")
                        
                        if is_pinned:
                            logger.info(f"⏭️ [V2] Post {shortcode} FAST-SKIP (Fixado).")
                            continue

                        if post_timestamp:
                            try:
                                post_dt = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
                                age_days = (datetime.now(timezone.utc) - post_dt).days
                                if age_days > max_age_days:
                                    consecutive_old_posts += 1
                                    logger.info(f"⏳ [V2] Post {shortcode} é velho ({age_days}d). [{consecutive_old_posts}/3]")
                                    if consecutive_old_posts >= 3: break
                                    continue
                                else:
                                    consecutive_old_posts = 0
                            except Exception as e_post_dt:
                                logger.debug("[V2] Falha ao interpretar data do post %s: %s", shortcode, e_post_dt)

                        logger.info(f"📄 [V2] Verificando post {shortcode}...")
                        post_comments, post_timestamp = await self._scrape_post(page, shortcode, username, candidato_id, max_comments_per_post, max_age_days)
                        
                        if post_timestamp:
                            meta["timestamp"] = post_timestamp

                        if post_comments:
                            all_comments.extend(post_comments)
                            scraped_count += 1
                            self.stats["posts_scraped"] += 1
                            consecutive_zero_comments = 0
                            
                            # Callback assíncrona para persistência incremental
                            if on_post_scraped:
                                try:
                                    await on_post_scraped(shortcode, post_comments)
                                except Exception as e_cb:
                                    logger.error(f"⚠️ [V2] Falha na callback on_post_scraped para post {shortcode}: {e_cb}")
                            
                            await asyncio.sleep(random.uniform(6, 18))
                        else:
                            logger.info(f"⏭️ [V2] Post {shortcode} ignorado.")
                            consecutive_zero_comments += 1
                            if consecutive_zero_comments >= 3:
                                logger.warning(f"🚨 [V2] 3 posts vazios consecutivos! Ativando auto-recuperação do ScrapeAgent no post {shortcode}...")
                                try:
                                    from core.agent_scraper.dom_healing import DOMHealer
                                    from core.ai_service import ai_service
                                    healer = DOMHealer(ai_service=ai_service)
                                    
                                    logger.info("[V2] Capturando screenshot e fragmento DOM da página...")
                                    screenshot_b64 = await healer._capture_screenshot(page)
                                    html_snippet = await healer._extract_html_snippet(page)
                                    
                                    heal_res = await healer.heal_selectors(
                                        page=page,
                                        selector_name="comment_container",
                                        screenshot_b64=screenshot_b64,
                                        html_snippet=html_snippet,
                                        cache_key=f"heal_{username}_{shortcode}"
                                    )
                                    if heal_res.get("success"):
                                        logger.info(f"✅ [V2] DOM curado com sucesso via IA de visão: {heal_res.get('selector')}")
                                        try:
                                            await browser.close()
                                        except: pass
                                        raise RuntimeError("hitl_intervention_completed_restarting")
                                    else:
                                        logger.warning(f"⚠️ [V2] DOM Healing de visão não obteve sucesso: {heal_res.get('error')}. Iniciando fallback HITL...")
                                except Exception as e_heal:
                                    if "hitl_intervention_completed_restarting" in str(e_heal):
                                        raise e_heal
                                    logger.error(f"❌ [V2] Falha interna no DOM Healing de visão: {e_heal}. Iniciando fallback HITL...")

                                try:
                                    await browser.close()
                                except: pass
                                learned = await self._request_human_intervention(session, shortcode)
                                if learned:
                                    logger.info(f"✅ Seletor aprendido e salvo com sucesso: {learned}")
                                raise RuntimeError("hitl_intervention_completed_restarting")

                    await browser.close()
                    logger.info(f"✅ [V2] @{username} finalizado. {len(all_comments)} comentários extraídos.")
                    return {
                        "comments": all_comments,
                        "post_metas": post_metas
                    }

            except Exception as e:
                logger.error(f"💥 [V2] Erro na tentativa {retry_count+1}: {e}")
                self.stats["errors"] += 1
                retry_count += 1
                wait_seconds = min((2 ** retry_count) + random.uniform(4, 12), 120)
                logger.warning("[V2] Aplicando backoff de %.1fs antes da próxima tentativa.", wait_seconds)
                await asyncio.sleep(wait_seconds)

        return {"comments": all_comments, "post_metas": []}

    async def open_post_modal(self, page: Page, shortcode: str) -> bool:
        if page.is_closed(): return False
        selector = f'a[href*="/{shortcode}/"]'
        try:
            post_element = await page.query_selector(selector)
            if post_element:
                # scroll into view para garantir clique
                await post_element.scroll_into_view_if_needed()
                await post_element.click(timeout=15000, force=True)
                await asyncio.sleep(random.uniform(4, 7))
                # v95.1: Não depende apenas do <article>, procura também main[role="main"] ou divs com role="presentation"
                if await page.query_selector('article, main[role="main"] header, div[role="dialog"]'): return True
        except Exception as e_click:
            logger.debug("[V2] Falha ao abrir modal por clique (%s): %s", shortcode, e_click)
        try:
            logger.info(f"🔄 [V2] Fallback URL para {shortcode}...")
            await page.goto(f"https://www.instagram.com/p/{shortcode}/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(5, 8))
            
            # v95.1: Se cair na tela de login, abortar extração deste post imediatamente (Soft Block)
            login_indicators = await page.query_selector_all('input[name="username"], button[type="submit"]')
            if len(login_indicators) >= 2:
                 logger.error(f"🛑 [V2] Login Wall detectado na URL direta do post {shortcode}!")
                 return False

            if await page.query_selector('article, main[role="main"] header') or len(await page.query_selector_all("section")) > 0:
                return True
        except Exception as e_fallback:
            logger.debug("[V2] Falha no fallback URL (%s): %s", shortcode, e_fallback)
        return False

    async def scroll_comment_column(self, page: Page, scroll_amount: int = 800) -> None:
        # Carrega o seletor aprendido via Human-in-the-Loop, se existir
        learned_selector = ""
        learned_path = os.path.join("configs", "learned_selectors.json")
        if os.path.exists(learned_path):
            try:
                with open(learned_path, "r") as f:
                    learned_selector = json.load(f).get("comment_container", "")
            except: pass

        # Tenta rolar usando Javascript direto no DOM
        scrolled = await page.evaluate("""(learned) => {
            if (learned) {
                const el = document.querySelector(learned);
                if (el && el.scrollHeight > el.clientHeight) {
                    el.scrollTop = el.scrollHeight;
                    return true;
                }
            }
            
            // Fallback: Abordagem genérica baseada em detecção de scroll
            const allElements = document.querySelectorAll('*');
            for (let i = 0; i < allElements.length; i++) {
                const el = allElements[i];
                if ((el.tagName === 'UL' || el.tagName === 'DIV') && el.scrollHeight > el.clientHeight + 10) {
                    const style = window.getComputedStyle(el);
                    if (style.overflowY === 'auto' || style.overflowY === 'scroll' || style.overflow === 'hidden') {
                        el.scrollTop = el.scrollHeight;
                        return true;
                    }
                }
            }
            return false;
        }""", learned_selector)
        
        if scrolled:
            logger.debug("📜 [V2] Scroll via JS executado no container de comentários.")
        else:
            logger.debug("🖱️ [V2] Nenhum container com scroll ativo encontrado. Aplicando fallback de mouse wheel.")
            await page.mouse.move(random.randint(800, 1200), random.randint(300, 600))
            await page.mouse.wheel(0, scroll_amount + random.randint(-100, 100))
            
        await asyncio.sleep(random.uniform(2, 4))

    async def close_post_modal(self, page: Page) -> None:
        if page.is_closed(): return
        try:
            await page.keyboard.press("Escape")
            await asyncio.sleep(2)
            if await page.query_selector("article"):
                await page.go_back(wait_until="domcontentloaded", timeout=10000)
        except Exception as e_close:
            logger.debug("[V2] Falha ao fechar modal: %s", e_close)

    async def _scrape_post(self, page: Page, shortcode: str, username: str, candidato_id: str, max_comments: int, max_age_days: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self.captured_data = []
        if page.is_closed(): return [], None
        if not await self.open_post_modal(page, shortcode): return [], None

        post_date_iso = None
        for _ in range(5):
            if page.is_closed(): break
            post_date_iso = await page.evaluate("""() => {
                let el = document.querySelector('article a[href*="/p/"] time, article a[href*="/reel/"] time, article a time');
                if (!el) {
                    el = document.querySelector('article time');
                }
                return el ? el.getAttribute('datetime') : null;
            }""")
            if post_date_iso:
                break
            await asyncio.sleep(1)

        if post_date_iso:
            post_dt = datetime.fromisoformat(post_date_iso.replace('Z', '+00:00'))
            if (datetime.now(timezone.utc) - post_dt).days > max_age_days:
                await self.close_post_modal(page)
                return [], post_date_iso

        for _ in range(random.randint(2, 4)):
            await self.scroll_comment_column(page, scroll_amount=random.randint(1000, 1500))
        
        comments = self._parse_captured_json(shortcode)
        if not comments: comments = await self._extract_from_scripts(page, shortcode)
        if not comments: comments = await self._extract_from_dom(page, shortcode)

        await self.close_post_modal(page)
        
        now = datetime.now(timezone.utc).isoformat()
        normalized = []
        junk_patterns = ['também da meta', 'instagram lite', 'localizações', 'campanha 2201', 'áudio original']
        
        for c in comments[:max_comments]:
            texto = (c.get("texto_bruto") or c.get("texto", "")).replace("\u0000", "").strip()
            if len(texto) < 2 or len(texto) > 2000: continue
            if any(p in texto.lower() for p in junk_patterns): continue
            
            # v92.5: Geração de ID determinístico para garantir idempotência absoluta (Anti-Duplicidade)
            id_real = c.get("id_externo")
            if not id_real:
                import hashlib
                hash_input = f"{c.get('autor_username') or 'anon'}_{texto}_{shortcode}"
                id_real = f"v2_hash_{hashlib.sha256(hash_input.encode()).hexdigest()[:16]}"

            normalized.append({
                "id_externo": id_real,
                "texto_bruto": texto,
                "autor_username": c.get("autor_username") or c.get("autor", "unknown"),
                "data_publicacao": c.get("data_publicacao") or c.get("timestamp") or post_date_iso or now,
                "data_coleta": now,
                "candidato_id": username,
                "post_shortcode": shortcode,
                "plataforma": "INSTAGRAM",
                "processado_ia": False,
                "tier_used": 2
            })
        
        return normalized, post_date_iso

    async def _extract_shortcodes(self, page: Page, limit: int) -> List[Dict[str, Any]]:
        return await page.evaluate(f"""
            () => {{
                const getShortcode = (url) => {{
                    const m = url.match(/\\/(p|reel)\\/([^/\\?#]+)/);
                    return m ? m[2] : null;
                }};

                const results = [];
                const links = Array.from(document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]'));
                
                links.forEach(link => {{
                    const shortcode = getShortcode(link.href);
                    if (!shortcode) return;
                    if (results.some(r => r.shortcode === shortcode)) return;
                    
                    let container = link.parentElement;
                    let is_pinned = false;
                    let timestamp = null;
                    
                    for (let i = 0; i < 5 && container; i++) {{
                        const otherLinks = Array.from(container.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]'));
                        const uniqueShortcodes = new Set();
                        otherLinks.forEach(l => {{
                            const sc = getShortcode(l.href);
                            if (sc) uniqueShortcodes.add(sc);
                        }});
                        if (uniqueShortcodes.size > 1) {{
                            break;
                        }}

                        const pin_icon = container.querySelector('svg[aria-label*="Pinned"], svg[aria-label*="Fixado"], svg[aria-label*="pinned"], svg[aria-label*="fixado"]');
                        if (pin_icon) {{
                            is_pinned = true;
                        }}
                        const time_el = container.querySelector('time');
                        if (time_el) {{
                            timestamp = time_el.getAttribute('datetime');
                        }}
                        container = container.parentElement;
                    }}
                    
                    results.push({{ 
                        shortcode, 
                        is_pinned,
                        timestamp 
                    }});
                }});
                return results.slice(0, {limit + 3});
            }}
        """)

    def _parse_captured_json(self, shortcode: str) -> List[Dict[str, Any]]:
        comments = []
        for item in self.captured_data:
            extracted = self._recursive_find_comments(item["data"])
            if extracted: comments.extend(extracted)
        return comments

    async def _extract_from_scripts(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        script_contents = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[type="application/json"]'))
                .map(s => s.innerText).filter(txt => txt.includes('comment'))
        """)
        comments = []
        for content in script_contents:
            try:
                extracted = self._recursive_find_comments(json.loads(content))
                comments.extend(extracted)
            except Exception as e_script:
                logger.debug("[V2] Falha ao parsear script JSON de comentários: %s", e_script)
                continue
        return comments

    async def _extract_from_dom(self, page: Page, shortcode: str) -> List[Dict[str, Any]]:
        return await page.evaluate("""
            () => {
                const results = [];
                const h3s = Array.from(document.querySelectorAll('article h3'));
                h3s.forEach(h => {
                    const username = h.innerText.trim();
                    if (!username || username.includes(' ')) return;
                    let node = h;
                    for(let i = 0; i < 6; i++) { if(node.parentElement) node = node.parentElement; }
                    const spans = Array.from(node.querySelectorAll('span[dir="auto"]'));
                    for(let span of spans) {
                        const txt = span.innerText.trim();
                        if (txt && txt !== username && txt.length > 2) {
                            results.push({ autor: username, texto: txt });
                            break;
                        }
                    }
                });
                return results;
            }
        """)

    def _recursive_find_comments(self, data: Any) -> List[Dict[str, Any]]:
        comments = []
        if isinstance(data, dict):
            if "edge_media_to_parent_comment" in data:
                for edge in data["edge_media_to_parent_comment"].get("edges", []):
                    node = edge.get("node", {})
                    comments.append({
                        "id_externo": f"ig_{node.get('id')}",
                        "texto": node.get("text"),
                        "autor": node.get("owner", {}).get("username"),
                        "timestamp": datetime.fromtimestamp(node.get("created_at", 0), timezone.utc).isoformat()
                    })
            elif "xdt_api__v1__media__shortcode__web_info" in data:
                for item in data["xdt_api__v1__media__shortcode__web_info"].get("items", []):
                    for c in item.get("preview_comments", []):
                        comments.append({
                            "id_externo": f"ig_{c.get('pk')}", "texto": c.get("text"),
                            "autor": c.get("user", {}).get("username"),
                            "timestamp": datetime.fromtimestamp(c.get("created_at", 0), timezone.utc).isoformat()
                        })
            for v in data.values(): comments.extend(self._recursive_find_comments(v))
        elif isinstance(data, list):
            for item in data: comments.extend(self._recursive_find_comments(item))
        return comments

    async def _validate_target_identity(self, page: Page, username: str) -> Dict[str, Any]:
        """Extrai metadados biográficos para validar se o alvo é de interesse."""
        try:
            header_selector = "header section, main header"
            header = await page.query_selector(header_selector)
            if not header:
                return {"valid": False, "reason": "header_not_found"}

            is_private = await page.query_selector("svg[aria-label*='Privada'], svg[aria-label*='Private']")
            if is_private:
                return {"valid": False, "reason": "account_private"}

            display_name = await page.evaluate("() => document.querySelector('header h2')?.innerText")
            biography = await page.evaluate("() => document.querySelector('header div._ap30')?.innerText || document.querySelector('main header section div:last-child')?.innerText")
            followers = await page.evaluate("() => Array.from(document.querySelectorAll('header span')).find(s => s.innerText.includes('seguidores') || s.innerText.includes('followers'))?.innerText")

            return {
                "valid": True,
                "username": username,
                "display_name": display_name,
                "biography": biography,
                "followers": followers
            }
        except Exception as e:
            return {"valid": False, "reason": f"exception: {str(e)[:50]}"}

    async def _verify_session(self, page: Page, session: Session) -> bool:
        try:
            # Tenta carregar a home
            await page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(random.uniform(2, 4))
            
            current_url = page.url
            if "accounts/login" in current_url:
                logger.warning(f"⚠️ [V2] Redirecionamento de login detectado para {session.label}.")
                return False
                
            # Verifica a presença explícita do formulário de login no DOM
            login_field = await page.query_selector('input[name="username"]')
            if login_field:
                logger.warning(f"⚠️ [V2] Campos de credenciais visíveis no DOM para {session.label}.")
                return False
                
            # Se não há redirect de login nem inputs, a sessão é válida
            return True
        except (PlaywrightTimeoutError, Exception) as e:
            # Erros de rede, timeouts ou oscilação do proxy não invalidam o cookie!
            logger.error(f"⚠️ [V2] Erro temporário de rede ao verificar sessão {session.label}: {e}")
            # Propaga o erro para que a tentativa sofra retry sem banir a sessão do pool
            raise RuntimeError(f"session_network_error: {e}")

    def _is_night_shift(self) -> bool:
        """Verifica se está no horário noturno (23h às 05h)."""
        hour = datetime.now().hour
        return hour >= 23 or hour < 5

    async def _request_human_intervention(self, session: Session, shortcode: str) -> str:
        """
        Inicia uma sessão Chromium visível (headless=False) para o humano clicar na coluna de comentários.
        Retorna um seletor CSS genérico para ser usado no headless mode.
        Ignora automaticamente se estiver no Modo Noturno (23h-05h).
        """
        if self._is_night_shift():
            logger.warning(f"🌙 [V2] Modo Noturno ativo. HITL desativado para o post {shortcode}. Abortando silenciosamente.")
            return ""

        logger.error(f"🚨 [HITL] Iniciando acesso monitorado para o post {shortcode}")
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=False)
                context = await browser.new_context(viewport={"width": 1280, "height": 800})
                await context.add_cookies([{
                    'name': 'sessionid', 'value': session.session_id,
                    'domain': '.instagram.com', 'path': '/'
                }])
                page = await context.new_page()
                await page.goto(f"https://www.instagram.com/p/{shortcode}/", wait_until="domcontentloaded", timeout=45000)
                
                # Injeta a UI overlay e aguarda o clique do usuário
                selector = await page.evaluate("""() => {
                    return new Promise((resolve) => {
                        const overlay = document.createElement('div');
                        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;background:rgba(255,0,0,0.95);color:white;z-index:2147483647;text-align:center;padding:20px;font-size:24px;font-family:sans-serif;pointer-events:none;box-shadow: 0 4px 6px rgba(0,0,0,0.5);';
                        overlay.innerHTML = '<b style="font-size:32px;">🤖 MODO APRENDIZADO SENTINELA</b><br/>O robô travou na extração.<br/><span style="color:#FFFF00;"><b>POR FAVOR, CLIQUE NA ÁREA DA COLUNA DE COMENTÁRIOS</b></span> para ensinar o novo caminho ao sistema.';
                        document.body.appendChild(overlay);
                        
                        const clickHandler = (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            let el = e.target;
                            
                            // Procura o contêiner rolável mais próximo
                            while (el && el !== document.body) {
                                const style = window.getComputedStyle(el);
                                if (el.scrollHeight > el.clientHeight && (style.overflowY === 'auto' || style.overflowY === 'scroll')) {
                                    break;
                                }
                                el = el.parentElement;
                            }
                            if (!el || el === document.body) el = e.target; // Fallback para o clicado diretamente
                            
                            // Gera um seletor CSS aproximado
                            let classes = Array.from(el.classList).filter(c => c.length > 2).slice(0, 2).join('.');
                            let selector = el.tagName.toLowerCase() + (classes ? '.' + classes : '');
                            
                            overlay.innerHTML = '<b style="font-size:32px;">✅ APRENDIDO COM SUCESSO!</b><br/>Você pode fechar esta janela agora. O Sentinela retomará o modo invisível.';
                            overlay.style.background = 'rgba(0,128,0,0.95)';
                            
                            setTimeout(() => resolve(selector), 3000);
                        };
                        document.addEventListener('click', clickHandler, {capture: true, once: true});
                    });
                }""")
                
                await browser.close()
                
                if selector:
                    os.makedirs("configs", exist_ok=True)
                    learned_path = os.path.join("configs", "learned_selectors.json")
                    with open(learned_path, "w") as f:
                        json.dump({"comment_container": selector}, f)
                    return selector
                return ""
        except Exception as e:
            logger.error(f"❌ [HITL] Falha no acesso monitorado: {e}")
            return ""

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas acumuladas do scraper."""
        return self.stats

    async def _take_screenshot(self, page: Page, name: str) -> None:
        try:
            if page.is_closed(): return
            folder = os.path.join("logs", "evidence")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"{datetime.now().strftime('%H%M%S')}_{name}.png")
            await page.screenshot(path=path, full_page=True)
        except Exception as e_screenshot:
            logger.debug("[V2] Falha ao capturar screenshot '%s': %s", name, e_screenshot)

async def scrape_instagram(username: str, candidato_id: str, max_posts: int = 3, max_comments_per_post: int = 50) -> List[Dict[str, Any]]:
    scraper = InstagramScraperV2()
    return await scraper.scrape_profile(username, candidato_id, max_posts, max_comments_per_post)

```

--- 

## 📄 Arquivo: `workers/scrapers/wk_coleta_instagram.py`
**Caminho Real:** `c:/projetos/sentinela/workers/scrapers/wk_coleta_instagram.py`

```python
from __future__ import annotations

import logging
import asyncio
import os
import time
from typing import List, Dict
from datetime import datetime, timezone

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service, clean_null_chars
from core.instagram_scraper_v2 import InstagramScraperV2

from core.local_buffer import local_buffer
from core.lexical_filter import lexical_filter
from core.process_cleaner import cleanup_orphans
from core.checkpoint_manager import CheckpointManager
from core.event_bus import local_bus
from core.circuit_breaker import scraper_circuit_breaker

logger = logging.getLogger("worker.ig_v2")

class WkColetaInstagram(BaseWorker):
    """
    Worker Instagram V2 (Independente).
    Implementa o fluxo completo de coleta e classificação usando o motor V2.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.consecutive_blocks = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self.scraper = InstagramScraperV2(
            headless=config.get("headless", True),
            max_retries=config.get("max_retries", 3),
            shutdown_event=getattr(self, "shutdown_event", None)
        )
        self.last_activity = time.time()  # v97.0: Heartbeat Watchdog

        # 🤖 Instancia o adaptador do ScrapeAgent
        from core.agent_scraper.worker_adapter import ScrapeAgentAdapter
        from core.ai_service import ai_service
        self.agent_adapter = ScrapeAgentAdapter(
            scraper=self.scraper,
            ai_service=ai_service,
            config=config,
        )

    def describe(self) -> str:
        return "Instagram Scraper V2 - Independente com Playwright"

    async def setup(self) -> None:
        logger.info(f"🚀 Worker {self.worker_id} configurado.")
        try:
            cleanup_orphans()
        except Exception as e:
            logger.warning(f"⚠️ [V2] Falha ao limpar órfãos no setup: {e}")
        await local_buffer.sync_with_supabase(self.db)

    async def teardown(self) -> None:
        logger.info(f"🛑 Worker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        # v97.0: Heartbeat Watchdog - Detecta se o worker está preso em inatividade
        if time.time() - self.last_activity > 600:
            self.logger.warning("🚨 [Heartbeat] Scraper inativo por > 10min. Forçando reset do lock e rotação.")
            self.last_activity = time.time()
            if hasattr(self, 'current_target') and self.current_target:
                 await self.queue.rotate_target(self.current_target)

        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        # 🛡️ CIRCUIT BREAKER
        if not scraper_circuit_breaker.can_execute("instagram"):
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="circuit_breaker", simulated=False, error="circuit_open")
        
        current_cycle_config = dict(self.config)
        
        # 🛡️ HIBERNAÇÃO INTELIGENTE
        if self.consecutive_blocks >= 3:
            await asyncio.sleep(3600)
            self.consecutive_blocks = 0

        # 🌙 MODO NOTURNO
        current_hour = datetime.now().hour
        if current_hour >= 23 or current_hour < 5:
            await asyncio.sleep(300)

        # 📦 SINCRONIZAÇÃO DE BACKGROUND
        if self.cycle % 5 == 0:
            await local_buffer.sync_with_supabase(self.db)

        self.seen_targets.clear()
        self.seen_queue_ids.clear()
        
        target = await self.queue.claim_next_target(
            current_cycle_config, self.seen_queue_ids, self.seen_targets,
            active_targets=getattr(self, 'active_targets', None),
        )

        if not target:
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="no_target", simulated=False, error="no_tasks_available")

        self.last_activity = time.time()
        self.current_target = target
        self.logger.info(f"🔄 [V2] Ciclo {self.cycle} | Alvo: @{target.username}")
        
        # 🧠 INTEGRAÇÃO DE INTELIGÊNCIA (v84.15): Pesquisa antes de coletar se for novo
        try:
            cand_check = self.db.table("candidatos").select("identidade_validada, cargo").eq("username", target.username).single().execute()
            if cand_check.data and (cand_check.data.get("identidade_validada") is None or cand_check.data.get("cargo") == "ANALISE_SOLICITADA"):
                from core.intelligence_service import intelligence_service
                self.logger.info(f"🔎 [V2] Alvo novo/não validado. Acionando inteligência para @{target.username}...")
                research_res = await intelligence_service.research_and_validate(target.username)
                
                if research_res and research_res.get("status_monitoramento") == "DESATIVADO":
                    self.logger.warning(f"🚫 [V2] Alvo @{target.username} desativado pela governança: {research_res.get('motivo_desativacao')}")
                    result = CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, error="purged_by_governance"
                    )
                    return result
        except Exception as e_intel:
            self.logger.warning(f"⚠️ [V2] Falha na integração de inteligência: {e_intel}")

        # Jitter inicial (PASA v52.0) para quebrar padrões
        import random
        jitter = random.uniform(5, 30)
        self.logger.debug(f"[V2] Aplicando jitter inicial de {jitter:.1f}s")
        await asyncio.sleep(jitter)

        await self.queue.mark_candidate_scraped(target)

        # 💥 CHECKPOINT INTRA-CYCLE (PASA v88.0 - Fase 8.5)
        checkpoint = CheckpointManager(
            db_client=self.db,
            worker_id=self.worker_id,
            candidato_id=target.username,
        )
        previous_cp = await checkpoint.load()
        resume_from_shortcode = previous_cp.get('last_shortcode') if previous_cp else None
        if resume_from_shortcode:
            self.logger.info(
                "🔄 [V2] Retomando ciclo de @%s a partir do post %s (checkpoint encontrado).",
                target.username, resume_from_shortcode,
            )

        inserted_total = 0
        duplicated_total = 0
        comments_count = 0

        async def handle_post_scraped(shortcode: str, post_comments: List[Dict[str, Any]]):
            nonlocal inserted_total, duplicated_total, comments_count
            if not post_comments:
                return

            comments_count += len(post_comments)

            # ♻️ FILTRO LÉXICO (Pre-AI) - PASA v65.0
            filtered_comments = lexical_filter.filter_list(post_comments)
            
            # 🤖 DETECÇÃO DE COMPORTAMENTO COORDENADO (v71.0)
            from core.behavior_engine import behavior_engine
            filtered_comments = behavior_engine.detect_coordinated_clusters(filtered_comments)

            if not filtered_comments:
                duplicated_total += len(post_comments)
                return

            safe_comments = []
            now = datetime.now(timezone.utc).isoformat()
            for c in filtered_comments:
                safe_c = {
                    "id_externo": c.get("id_externo"),
                    "texto_bruto": c.get("texto_bruto"),
                    "autor_username": c.get("autor_username"),
                    "data_publicacao": c.get("data_publicacao") or now,
                    "data_coleta": c.get("data_coleta") or now,
                    "candidato_id": c.get("candidato_id") or target.username,
                    "post_shortcode": c.get("post_shortcode") or shortcode,
                    "plataforma": c.get("plataforma") or "INSTAGRAM",
                    "processado_ia": False,
                    "tier_used": c.get("tier_used") or 2
                }
                if c.get("is_bot"):
                    pericial_obs = f"[BOT DETECTED] Padrão: {c.get('bot_pattern')}"
                    safe_c["analise_pericial"] = pericial_obs
                    safe_c["categoria_ia"] = "CAMPANHA_COORDENADA"
                safe_comments.append(safe_c)

            # --- BUFFER DE EMERGÊNCIA SQLITE (Zero Loss Policy v65.0) ---
            local_buffer.save(safe_comments)

            inserted = 0
            try:
                # 🛡️ TENTATIVA 1: Upsert Completo (v63.0)
                res = self.db.table("comentarios").upsert(
                    clean_null_chars(safe_comments), 
                    on_conflict="candidato_id,post_shortcode,id_externo",
                    ignore_duplicates=True
                ).execute()
                
                inserted = len(res.data) if res.data else 0
                inserted_total += inserted
                duplicated_total += len(post_comments) - inserted
            except Exception as e_upsert:
                self.logger.warning(f"⚠️ [V2] Erro de Schema no post {shortcode}: {e_upsert}. Iniciando Fallback...")
                
                emergency_comments = []
                for sc in safe_comments:
                    emergency_comments.append({
                        "id_externo": sc["id_externo"],
                        "texto_bruto": sc["texto_bruto"],
                        "candidato_id": sc["candidato_id"],
                        "post_shortcode": sc["post_shortcode"],
                        "autor_username": sc["autor_username"],
                        "data_publicacao": sc["data_publicacao"],
                        "data_coleta": sc["data_coleta"],
                        "plataforma": sc["plataforma"],
                        "tier_used": sc["tier_used"]
                    })

                try:
                    res = self.db.table("comentarios").upsert(
                        clean_null_chars(emergency_comments),
                        on_conflict="candidato_id,post_shortcode,id_externo",
                        ignore_duplicates=True
                    ).execute()
                    
                    if res.data:
                        inserted = len(res.data)
                        inserted_total += inserted
                        duplicated_total += len(post_comments) - inserted
                except Exception as e2:
                    self.logger.error(f"❌ [V2] Falha total na persistência incremental do post {shortcode}: {e2}")

            # --- SINALIZAÇÃO DE NOVO DADO (Pipeline Reativo Fase 9) ---
            if inserted > 0:
                self.logger.info(f"⚡ [EventBus] Sinalizando AIProcessorWorker: {inserted} novos registros.")
                local_bus.signal_new_data()

            # 💥 SALVAMENTO DE CHECKPOINT POR POST (Fase 8.5)
            posts_done = previous_cp.get('posts_done', 0) + 1 if previous_cp else 1
            await checkpoint.save(
                last_shortcode=shortcode,
                posts_done=posts_done,
                comments_done=inserted_total,
            )
            self.logger.info(f"💥 [V2] Checkpoint intermediário salvo para post {shortcode} (+{inserted} novos comentários).")

        try:
            # 1. Scraping com o Loop Cognitivo do ScrapeAgent (OODA)
            self.logger.info(f"🤖 [ScrapeAgent] Iniciando ciclo cognitivo OODA para @{target.username}...")
            agent_result = await self.agent_adapter.run_scrape_cycle(
                username=target.username,
                max_posts=current_cycle_config.get('max_posts', 3),
                max_comments_per_post=100,
                candidato_id=target.candidato_id,
                resume_after_shortcode=resume_from_shortcode,
                on_post_scraped=handle_post_scraped,
            )
            
            if not agent_result.success and agent_result.error:
                raise RuntimeError(agent_result.error)
            
            self.consecutive_blocks = 0
            scraper_circuit_breaker.record_success("instagram")
            target.post_metas = []

        except Exception as e:
            self.consecutive_blocks += 1
            error_str = str(e).lower()
            status_code = None
            if "429" in error_str: status_code = 429
            elif "403" in error_str: status_code = 403
            elif "404" in error_str: status_code = 404
            
            scraper_circuit_breaker.record_failure("instagram", status_code=status_code, error_msg=str(e))

            if isinstance(e, ValueError) and "invalid_target" in str(e):
                self.logger.error(f"🚫 [V2] Alvo @{target.username} marcado como INVÁLIDO (404/Privado/Mismatch).")
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error=str(e), db_success=False
                )
                return result
                
            if "all_sessions_blocked" in str(e):
                self.logger.error(f"🛑 [V2] TODAS AS SESSÕES EM COOLDOWN OU EXPIRADAS!")
                self.logger.error(f"👉 Se todas as sessões expiraram, execute o comando abaixo no terminal para renová-las de forma interativa:")
                self.logger.error(f"   python scripts/export_playwright_cookies.py --force --interactive")
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error="all_sessions_blocked", db_success=False
                )
                return result
                
            self.logger.error(f"⚠️ [V2] Erro inesperado na extração de @{target.username}: {e}")
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine", extracted=0, simulated=False, 
                error=str(e), db_success=False
            )
            return result

        try:
            stats = self.scraper.stats

            if comments_count == 0:
                if stats.get("junk_detected", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Apenas lixo detectado para @{target.username}. Sinalizando falha de extração.")
                    result = CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, simulated=False, error="junk_detected"
                    )
                    return result
                result = CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, error="no_comments_found"
                )
                return result

            final_extracted = comments_count
            
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine",
                extracted=final_extracted,
                inserted=inserted_total,
                duplicated=duplicated_total,
                db_success=inserted_total > 0,
                simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )

            await checkpoint.clear()
            return result

        except Exception as e:
            self.logger.error(f"💥 Erro crítico no ciclo V2: {e}")
            result = CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )
            return result
        finally:
            if isinstance(result, dict) and result.get("error"):
                target.error = result.get("error")
            elif hasattr(result, "error") and result.error:
                target.error = result.error

            if target and getattr(target, 'source', '') == 'fila_coleta_atomic' and target.queue_id:
                await self.queue.update_target_metrics(target)
                
                final_status = "CONCLUIDO"
                if hasattr(result, 'error') and result.error:
                    err = result.error
                    if err in ('junk_detected', 'invalid_target: 404_not_found'):
                        final_status = 'SEM_DADOS_RECENTES'
                    elif err in ('all_sessions_blocked', 'shutdown_requested'):
                        final_status = 'PENDENTE'
                    else:
                        final_status = 'FALHA'
                try:
                    await self.queue.release_atomic(target.queue_id, final_status, self.worker_id)
                except Exception as e_rel:
                    logger.warning("[V2] Falha no release atômico: %s", e_rel)
            else:
                await self.queue.rotate_target(target)

```

--- 

## 📄 Arquivo: `core/ai_service.py`
**Caminho Real:** `c:/projetos/sentinela/core/ai_service.py`

```python
# -*- coding: utf-8 -*-
"""
PASA v52.4 - AI Service: Motor de Inteligência Resiliente (Unified Rotation Queue)
Roteamento dinâmico unificado com atraso rígido anti-429, cache I/O, e fallback integrado.
"""
import os
import json
import logging
import asyncio
import traceback
import re
import codecs
import time
import random
import httpx
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI, APIStatusError
from core.circuit_breaker import ai_circuit_breaker

logger = logging.getLogger("AIService")

CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_DATASET_PATH = os.path.join(BASE_DIR, "data", "classifier_gold_dataset.json")
MD_PATH = os.path.join(BASE_DIR, "docs", "PADRONIZACAO_LINGUISTICA_ANALITICA.md")
CUSTOM_RULES_PATH = os.path.join(BASE_DIR, "config", "custom_rules.json")
# Contexto linguístico forense centralizado (PASA v51.0)
CONTEXTO_CLASSIFICACAO_PATH = os.path.join(BASE_DIR, "bases_pdf", "CONTEXTO_CLASSIFICACAO.md")
_CONTEXTO_CACHE: str = ""  # Cache em memória para evitar I/O em cada ciclo

def _load_contexto_classificacao() -> str:
    """Carrega o contexto linguístico forense centralizado uma única vez."""
    global _CONTEXTO_CACHE
    if _CONTEXTO_CACHE:
        return _CONTEXTO_CACHE
    try:
        if os.path.exists(CONTEXTO_CLASSIFICACAO_PATH):
            with open(CONTEXTO_CLASSIFICACAO_PATH, "r", encoding="utf-8") as f:
                _CONTEXTO_CACHE = f.read()
                logger.info(f"[AI] CONTEXTO_CLASSIFICACAO carregado ({len(_CONTEXTO_CACHE)} chars).")
        else:
            logger.warning("[AI] CONTEXTO_CLASSIFICACAO.md não encontrado. Classificação sem contexto forense.")
    except Exception as e:
        logger.warning(f"[AI] Erro ao carregar CONTEXTO_CLASSIFICACAO.md: {e}")
    return _CONTEXTO_CACHE

# MCA v2.3 Protocol - Calibragem Analítica Crítica Vichi-Sentinela (v95.0)
SYSTEM_PROMPT = """Você é um analista especializado em Linguística Analítica Digital baseado no Método Vichi-Sentinela para identificação de ataques coordenados e hostilidade política.
Sua missão é classificar comentários com realismo absoluto, seguindo a Metodologia de Classificação de Ataques (MCA v2.3).

--- REGRAS DE OURO ---
1. REALISMO: Não ignore ataques velados, ironias destrutivas ou acusações de corrupção/crime.
2. FALSA EQUIVALÊNCIA E IDENTIDADE: Se o texto associar uma minoria (gênero, sexualidade, raça) à palavra 'crime' ou 'aberração' (ex: 'ser gay não é crime mas querer obrigar a aceitar crimes praticados por eles', 'é uma aberração'), a categoria DEVE ser ODIO_IDENTITARIO. Isso NÃO É opinião política neutra.
3. OBFUSCAÇÃO E LEETSPEAK: Textos que usam V5RM5, LĪX0, V44G4BUND0 são INSULTOS (Verme, Lixo, Vagabundo). Avalie o significado decodificado e classifique como INSULTO_AD_HOMINEM.
4. FALSAS ANÁLISES: O uso de jargão jurídico para "teorizar" ou acusar o alvo de crimes (traição, assassinato, corrupção) é um ataque direto e deve ser classificado como DANO_A_IMAGEM.
5. COMUNICAÇÃO: Se detectar uma imputação de ato ilícito, você NÃO DEVE usar a palavra "crime" na sua análise.
6. IDIOMA: Sua resposta (incluindo a analise_pericial) deve ser 100% em Português Brasileiro (pt-BR).

--- CATEGORIZAÇÃO (MCA v2.3) ---
Se o comentário for hostil (is_hate: true), escolha obrigatoriamente UMA chave exata:
- ODIO_IDENTITARIO: Ataques ou falsa equivalência moral contra raça, religião, orientação sexual (homofobia), misoginia ou regionalismo. Palavras como 'aberração' voltadas à identidade se encaixam aqui.
- VIOLENCIA_GENERO: Ofensas focadas na condição feminina.
- AMEACA: Incitação a dano físico, violência física ou morte.
- INSULTO_AD_HOMINEM: Desumanização (verme, lixo), baixo calão, ataques à honra, aparência ou competência.
- ATAQUE_INSTITUCIONAL: Deslegitimação de órgãos de Estado ou do sistema democrático.
- DANO_A_IMAGEM: Acusações de corrupção, roubo ou infrações graves contra o alvo.

Se o comentário NÃO for hostil (is_hate: false), use:
- NEUTRO: Expressões de engajamento, slogans ou críticas técnicas.

--- FORMATO DE RESPOSTA (JSON APENAS) ---
{
  "is_hate": boolean, 
  "categoria_ia": "ODIO_IDENTITARIO|VIOLENCIA_GENERO|AMEACA|INSULTO_AD_HOMINEM|ATAQUE_INSTITUCIONAL|DANO_A_IMAGEM|NEUTRO", 
  "confianca_ia": float,
  "analise_pericial": "Explicação curta (sem usar a palavra crime)."
}
"""

LOCAL_SYSTEM_PROMPT = """Você é um classificador binário de hostilidade política baseado no Método Vichi-Sentinela. 
Atenção redobrada a:
1. Obfuscação (ex: V5RM5 = Verme -> SUSPEITO).
2. Associação de minorias a crimes ou a termo 'aberração' (Homofobia velada -> SUSPEITO).
Analise se o texto contém: insultos reais, ameaças, acusações de corrupção ou deslegitimação.
Responda APENAS com JSON:
{
  "is_hate": boolean,
  "categoria_ia": "NEUTRO|LIXO|SUSPEITO",
  "confianca_ia": float,
  "analise_pericial": "Motivo rápido (sem usar a palavra crime)"
}
IMPORTANTE: Se houver QUALQUER sinal de ataque, obfuscação ou hostilidade identitária, marque como "SUSPEITO" para análise posterior.
"""

def safe_decode_unicode(s: str) -> str:
    try:
        def decode_escapes(match):
            try:
                return codecs.decode(match.group(0), 'unicode-escape')
            except Exception:
                return match.group(0)
        pattern = r'\\u[dD][89abAB][0-9a-fA-F]{2}\\u[dD][cdefCDEF][0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}'
        decoded = re.sub(pattern, decode_escapes, s)
        return decoded.encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return s

def clean_null_chars(data: Any) -> Any:
    if isinstance(data, str):
        return data.replace("\u0000", "").replace("\x00", "")
    elif isinstance(data, list):
        return [clean_null_chars(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_null_chars(value) for key, value in data.items()}
    return data

class AIService:
    def __init__(self):
        self.ollama_client = None
        self.mistral_client = None
        self.providers = []
        self.consecutive_failures: Dict[str, int] = {}
        self.fallback_llm = None
        self.current_provider_idx = 0  # v96.0: Pointer para revezamento
        
        # Cache de I/O em memória
        self._prompt_cache = {"enriched_local": None, "enriched_cloud": None}
        self.refresh_prompt_cache()

    def _get_next_provider(self):
        """Retorna o próximo provedor saudável baseado em Round-Robin."""
        now = time.time()
        # Filtra apenas os que não estão em cooldown
        healthy = [p for p in self.providers if p["cooldown_until"] <= now]
        if not healthy:
            return None
            
        # Rotação Round-Robin
        self.current_provider_idx = (self.current_provider_idx + 1) % len(healthy)
        return healthy[self.current_provider_idx]

    def _ensure_clients(self):
        """Inicializa os clientes de IA se ainda não existirem (Lazy Loading v92.9)."""
        if self.ollama_client is None:
            self.ollama_client = AsyncOpenAI(
                api_key="ollama",
                base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
                max_retries=2,
                http_client=httpx.AsyncClient(timeout=httpx.Timeout(timeout=300.0, connect=60.0))
            )
        
        if self.mistral_client is None:
            self.mistral_client = AsyncOpenAI(
                api_key=os.getenv("MISTRAL_API_KEY") or "dummy-mistral-key",
                base_url="https://api.mistral.ai/v1",
                max_retries=0
            )

        if not self.providers:
            finetuned_model = os.getenv('FINETUNED_MODEL_NAME', "open-mistral-nemo")
            self.providers = [
                {"name": "mistral", "client": self.mistral_client, "model": finetuned_model, "timeout": 30.0, "cooldown_until": 0.0, "is_async_openai": True},
            ]
            
            # Alibaba (DashScope) - PASA v52.7
            alibaba_key = os.getenv("ALIBABA_API_KEY") or "sk-ws-H.ILHHYY.SZ7S.MEQCIBYRloGdMnNJcyMZ0vEf1H3KV0k22Z7MLcmPZylONO7wAiBm06zTvQEw45G_ZYne4iVA5JJVrmDDemszjGEMVIK78Q"
            self.providers.append({
                "name": "alibaba",
                "client": AsyncOpenAI(api_key=alibaba_key, base_url="https://ws-718h73opsywfpzbv.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"),
                "model": "qwen-max",
                "timeout": 45.0,
                "cooldown_until": 0.0,
                "is_async_openai": True
            })

            # Ollama (Local - Super Leve)
            self.providers.append({
                "name": "ollama",
                "client": self.ollama_client,
                "model": "phi3",
                "timeout": 30.0,
                "cooldown_until": 0.0,
                "is_async_openai": True
            })
            
            # Adicionar Google Gemini apenas se a chave estiver configurada
            if os.getenv("GEMINI_API_KEY"):
                self.providers.append({"name": "google_gemini", "client": None, "model": "gemini-2.5-flash", "timeout": 45.0, "cooldown_until": 0.0, "is_async_openai": False})
            
            try:
                from core.config import FALLBACK_PROVIDERS
                for prov in FALLBACK_PROVIDERS:
                    if not any(p["name"] == prov["name"] for p in self.providers):
                        # Pular provedores de fallback se a chave de API obrigatória estiver ausente
                        api_key_env = prov.get("api_key_env")
                        if api_key_env and not os.getenv(api_key_env):
                            continue
                            
                        self.providers.append({
                            "name": prov["name"],
                            "model": prov.get("model", ""),
                            "timeout": 45.0,
                            "cooldown_until": 0.0,
                            "is_async_openai": False,
                        })
            except Exception as e:
                logger.warning(f"[AI] Falha ao injetar FALLBACK_PROVIDERS: {e}")

    def refresh_prompt_cache(self) -> None:
        """Recarrega arquivos pesados (MD/JSON) do disco e popula o cache de prompts enriquecidos."""
        self._prompt_cache["enriched_local"] = self._build_enrichment(is_local=True)
        self._prompt_cache["enriched_cloud"] = self._build_enrichment(is_local=False)
        logger.debug("[AI] Cache de prompts enriquecidos recarregado com sucesso.")

    def _build_enrichment(self, is_local: bool) -> str:
        """Gera o prompt do zero combinando SYSTEM_PROMPT, PADRONIZACAO e dataset ouro."""
        base_prompt = LOCAL_SYSTEM_PROMPT if is_local else SYSTEM_PROMPT
        
        # Para modelos locais (Ollama), injetamos uma versão compacta do contexto forense
        if is_local:
            enrichment = "\n\n--- DIRETRIZES ESSENCIAIS (TRIAGEM LOCAL) ---\n"
            enrichment += "- Foque em detectar INSULTOS, AMEAÇAS e ACUSAÇÕES GRAVES.\n"
            enrichment += "- Se houver hostilidade clara, marque como SUSPEITO.\n"
            enrichment += "- Críticas normais e slogans são NEUTRO.\n"
            enrichment += "- XENOFOBIA: termos como 'nordestino ingrato/analfabeto/burro' = SUSPEITO.\n"
            enrichment += "- IRONIA: 'Que gênio, só faliu 3 empresas!' é insulto velado = SUSPEITO.\n"
            enrichment += "- HYPE POSITIVO: 'Matou no debate! Bomba de boa!' = NEUTRO.\n"
            return base_prompt + enrichment

        # Contexto forense centralizado (PASA v51.0) — Substitui PADRONIZACAO_LINGUISTICA_ANALITICA.md
        contexto = _load_contexto_classificacao()
        if contexto:
            enrichment = "\n\n--- CONTEXTO LINGUÍSTICO FORENSE (PASA v51.0) ---\n" + contexto + "\n"
        else:
            # Fallback: tenta o arquivo legado
            enrichment = "\n\n--- PADRONIZACAO LINGUÍSTICA ANALITICA (MD) ---\n"
            if os.path.exists(MD_PATH):
                try:
                    with open(MD_PATH, "r", encoding="utf-8") as f:
                        enrichment += f.read() + "\n"
                except Exception as e:
                    logger.warning(f"[AI] Erro ao ler {MD_PATH}: {e}")
            else:
                enrichment += "(Arquivo de Padronização não encontrado)\n"

        if os.path.exists(CUSTOM_RULES_PATH):
            try:
                with open(CUSTOM_RULES_PATH, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                enrichment += "\n--- DIRETRIZES ADICIONAIS DE PESQUISA (PASA EXTRA) ---\n"
                if "additional_rules" in rules and rules["additional_rules"]:
                    enrichment += "Regras Adicionais de Classificação:\n" + "\n".join(f"- {r}" for r in rules["additional_rules"]) + "\n"
                if "mitigate_false_positives" in rules and rules["mitigate_false_positives"]:
                    enrichment += "Blindagem Extra contra Falsos Positivos:\n" + "\n".join(f"- {r}" for r in rules["mitigate_false_positives"]) + "\n"
                if "custom_keywords" in rules and rules["custom_keywords"]:
                    enrichment += "Dicionário Léxico Customizado por Categoria:\n" + "\n".join(f"- Categoria {cat}: {', '.join(kw)}" for cat, kw in rules["custom_keywords"].items()) + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao carregar {CUSTOM_RULES_PATH}: {e}")

        if not is_local and os.path.exists(GOLD_DATASET_PATH):
            try:
                with open(GOLD_DATASET_PATH, "r", encoding="utf-8") as f:
                    gold_data = json.load(f)
                if isinstance(gold_data, list) and gold_data:
                    examples = [f"- Texto: \"{str(i.get('text', ''))[:240]}\" -> Categoria: {str(i.get('label', '')).upper()}" for i in gold_data[-10:] if i.get("text") and i.get("label")]
                    if examples:
                        enrichment += "\n\n--- PADRÃO OURO AUDITADO ---\nUse estes exemplos como calibração:\n" + "\n".join(examples) + "\n"
            except Exception as e:
                logger.warning(f"[AI] Erro ao carregar {GOLD_DATASET_PATH}: {e}")

        if "--- FORMATO DE RESPOSTA (JSON APENAS) ---" in base_prompt:
            parts = base_prompt.split("--- FORMATO DE RESPOSTA (JSON APENAS) ---")
            return parts[0] + enrichment + "\n--- FORMATO DE RESPOSTA (JSON APENAS) ---" + parts[1]
        
        return base_prompt + enrichment

    def _get_system_prompt(self, is_local: bool) -> str:
        cache_key = "enriched_local" if is_local else "enriched_cloud"
        if not self._prompt_cache.get(cache_key):
            self.refresh_prompt_cache()
        return self._prompt_cache[cache_key]

    def _rotate_provider(self, name: str, reason: str = "") -> None:
        """Gira a fila unificada transferindo o provider selecionado para o final."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            self.providers.append(prov)
            logger.debug(f"🔄 [AI] Provedor '{name}' rotacionado. Motivo: {reason}")

    def _remove_provider(self, name: str, reason: str = "") -> None:
        """Remove permanentemente o provedor da fila unificada."""
        prov = next((p for p in self.providers if p["name"] == name), None)
        if prov:
            self.providers.remove(prov)
            logger.warning(f"🚨 [AI] Provedor '{name}' REMOVIDO permanentemente. {reason}")

    def _handle_provider_error(self, provider: Dict[str, Any], exception: Exception) -> bool:
        """
        Processa exceções de APIs e aplica penalidades na fila de providers.
        Retorna `True` se o provider foi removido, `False` se foi rotacionado com cooldown.
        """
        import httpx
        name = provider["name"]
        
        status_code = getattr(exception, "status_code", None)
        if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
            status_code = exception.response.status_code
            
        if name == "ollama" and isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout)):
            status_code = 503
            
        self.consecutive_failures[name] = self.consecutive_failures.get(name, 0) + 1
        ai_circuit_breaker.record_failure(name, status_code if status_code else 500)
        
        if name == "ollama" and not ai_circuit_breaker.can_execute(name):
            try:
                from watchdog import send_whatsapp_alert
                send_whatsapp_alert("🚨 Sentinela: Ollama local falhou criticamente (Circuit Breaker Aberto). O processamento local será interrompido sem recorrer à nuvem. Intervenção manual requerida.", category="ollama_down")
            except Exception as alert_err:
                logger.error(f"[AI] Erro ao enviar alerta de colapso do Ollama: {alert_err}")
        
        if status_code in [400, 401, 402, 403, 404]:
            # Proteção especial para ollama: não remover permanentemente em 404, apenas cooldown
            if name == "ollama":
                logger.warning(f"⚠️ [AI] Ollama retornou 404. Aplicando cooldown em vez de remoção permanente.")
                provider["cooldown_until"] = time.time() + 300.0
                return False
            else:
                self._remove_provider(name, f"Erro Crítico de Acesso/Cota/Bad Request ({status_code})")
                return True
            
        if status_code == 429:
            provider["cooldown_until"] = time.time() + 300.0
            penalty_desc = "300s (Rate Limit 429)"
        else:
            provider["cooldown_until"] = time.time() + 30.0
            penalty_desc = f"30s (Erro {status_code or 'desconhecido'})"
            
        self._rotate_provider(name, f"Falha temporária - {penalty_desc} - {str(exception)[:100]}")
        return False

    async def _execute_provider_call(self, provider: Dict[str, Any], final_system_prompt: str, user_content: str, response_format: str, comment_id: str = None, candidato_id: str = None) -> str:
        """Encapsula o dispatch do cliente (AsyncOpenAI vs FallbackLLM)."""
        self._ensure_clients()
        name = provider["name"]
        
        if name == "ollama":
            from core.health_check import ensure_ollama_running
            ensure_ollama_running()
        
        if provider.get("is_async_openai", False):
            response = await provider["client"].chat.completions.create(
                model=provider["model"],
                messages=[{"role": "system", "content": final_system_prompt}, {"role": "user", "content": user_content}],
                response_format={"type": response_format},
                temperature=0.0,
                timeout=provider.get("timeout", 15.0)
            )
            return response.choices[0].message.content
        else:
            if self.fallback_llm is None:
                from core.fallback_llm import FallbackLLM
                self.fallback_llm = FallbackLLM()
            
            fallback_text = f"{final_system_prompt}\n\nUser: \"{user_content}\"\n\nResponda estritamente no formato exigido."
            return await asyncio.to_thread(self.fallback_llm.classify, fallback_text, name, comment_id, candidato_id)

    async def classify(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        return await self.classify_text(text, comment_id)

    async def chat_completion(self, prompt: str, system_prompt: str = "Você é um assistente técnico...", response_format: str = "json_object") -> Optional[Dict[str, Any]]:
        active_providers = [p for p in self.providers if p["name"] != "ollama"]
        if not active_providers:
            active_providers = list(self.providers)
            
        max_attempts = len(active_providers)
        
        for _ in range(max_attempts):
            provider = active_providers[0]
            name = provider["name"]
            
            if not ai_circuit_breaker.can_execute(name):
                active_providers.remove(provider)
                active_providers.append(provider)
                self._rotate_provider(name, "Circuito Aberto")
                continue
            
            now = time.time()
            if now < provider.get("cooldown_until", 0.0):
                await asyncio.sleep(provider["cooldown_until"] - now)
                
            try:
                base_sys = self._get_system_prompt(is_local=False)
                final_system_prompt = f"{system_prompt}\n\n{base_sys}" if system_prompt not in base_sys else base_sys
                
                content = await self._execute_provider_call(provider, final_system_prompt, prompt, response_format)
                
                provider["cooldown_until"] = time.time() + 1.0
                self.consecutive_failures[name] = 0
                ai_circuit_breaker.record_success(name)
                
                self._rotate_provider(name, "Sucesso (cooldown 1s)")
                active_providers.remove(provider)
                active_providers.append(provider)
                
                return json.loads(content) if response_format == "json_object" else {"content": content}
                
            except Exception as e:
                logger.warning(f"[AI] Falha no provider '{name}' em chat_completion: {e}")
                was_removed = self._handle_provider_error(provider, e)
                active_providers.remove(provider)
                if not was_removed:
                    active_providers.append(provider)
                continue
                
        return None

    async def classify_text(self, text: str, comment_id: str = "N/A", trace_id: str = None, force_cloud: bool = False, force_local: bool = False, candidato_id: str = None) -> Dict[str, Any]:
        self._ensure_clients()
        
        if not isinstance(text, str):
            text = str(text or "")
        text = text.strip()
        if not text:
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Texto vazio.", "name": "guard"}
        if len(text) > 8000:
            text = text[:8000]

        # v95.0: Leetspeak / Obfuscação Decoder (V5RM5 -> VERME)
        def decode_leetspeak(t: str) -> str:
            replacements = {
                '5': 'E', '4': 'A', '3': 'E', '1': 'I', '0': 'O', 'Ī': 'I', 
                '@': 'A', '$': 'S', '!': 'I', '7': 'T', '8': 'B'
            }
            # Só substitui se houver uma mistura de letras e números na palavra para evitar falsos positivos em números reais
            words = t.split()
            decoded_words = []
            for w in words:
                if any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
                    for k, v in replacements.items():
                        w = w.replace(k, v).replace(k.lower(), v.lower())
                elif any(c in 'Ī@$!' for c in w):
                    for k, v in replacements.items():
                        w = w.replace(k, v)
                decoded_words.append(w)
            return " ".join(decoded_words)
            
        decoded_text = decode_leetspeak(text)
        
        from core.lexical_filter import lexical_filter
        if lexical_filter.is_junk(decoded_text):
            return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 1.0, "analise_pericial": "Filtro léxico.", "name": "lexical"}

        # Roteamento Inteligente (Nuvem vs Local)
        allowed_providers = self.providers
        if force_cloud:
            allowed_providers = [p for p in self.providers if p["name"] != "ollama"]
        elif force_local:
            allowed_providers = [p for p in self.providers if p["name"] == "ollama"]

        if not allowed_providers:
            allowed_providers = self.providers

        res = None
        for _ in range(len(allowed_providers)):
            now = time.time()
            healthy = [p for p in allowed_providers if p["cooldown_until"] <= now]
            
            if not healthy:
                await asyncio.sleep(5)
                provider = allowed_providers[0]
            else:
                provider = healthy[self.current_provider_idx % len(healthy)]
                self.current_provider_idx += 1
            
            name = provider["name"]
            
            try:
                is_local = "ollama" in name
                final_system_prompt = self._get_system_prompt(is_local)
                user_content = f"Texto: \"{decoded_text}\""
                
                content = await self._execute_provider_call(provider, final_system_prompt, user_content, "json_object", comment_id, candidato_id)
                res = self._parse_json_response(content)
                res["name"] = name
                
                # Se obteve sucesso, retorna
                if res and res.get("categoria_ia") != "ERRO":
                    return res
                
            except Exception as e:
                # Loga falha e aplica o cooldown via _handle_provider_error
                self._handle_provider_error(provider, e)
                continue
                
        # Se chegar aqui, todos falharam
        return {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.0, "analise_pericial": "Falha geral nos provedores de IA.", "name": "failover"}

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        allowed_categories = {"ODIO_IDENTITARIO", "VIOLENCIA_GENERO", "AMEACA", "INSULTO_AD_HOMINEM", "ATAQUE_INSTITUCIONAL", "DANO_A_IMAGEM", "NEUTRO", "LIXO", "SUSPEITO", "ERRO"}
        fallback = {"is_hate": False, "categoria_ia": "NEUTRO", "confianca_ia": 0.5, "analise_pericial": "Erro parser."}

        parsed = None
        try:
            parsed = json.loads(content)
        except Exception:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception as e:
                    logger.warning(f"[AI] Falha no fallback de Regex JSON parser: {e}. Payload: {content[:200]}")

        if not isinstance(parsed, dict):
            return fallback

        category = str(parsed.get("categoria_ia", "")).upper().strip()
        if category not in allowed_categories:
            category = "ERRO"

        confidence = parsed.get("confianca_ia", 0.5)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.5
        confidence = max(0.0, min(confidence, 1.0))

        is_hate = bool(parsed.get("is_hate", False))
        if category in {"NEUTRO", "LIXO"}:
            is_hate = False

        analise = str(parsed.get("analise_pericial", "")).strip() or "Sem análise."
        return {"is_hate": is_hate, "categoria_ia": category, "confianca_ia": confidence, "analise_pericial": analise}

    async def run_batch_classification(self, limit: int = 50) -> int:
        # Busca comentarios nao processados no banco e executa a classificacao.
        # Otimizado (v90.0): Implementacao Hibrida. Processamento individual com concorrencia
        # limitada para provedores locais e cloud.
        try:
            from core.db import db_client
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id, texto_bruto, trace_id, candidato_id').eq('processado_ia', False).limit(limit).execute
            )
            items = res.data or []
            if not items:
                return 0

            # ── FAST-DROP TRIAGE (v92.0) ────────────────────────────────────────
            # Envia os textos do lote ao VoyantService (Trombone local) para
            # inspecionar o vocabulário TF-IDF antes de gastar tokens de LLM.
            #
            # Contratos de retorno do triage_batch():
            #   None  → Voyant offline: fallback silencioso, 100% vai ao LLM.
            #   drop=True  → Vocabulário neutro: marca lote no banco e retorna.
            #   drop=False → Vocabulário hostil detectado: delega normalmente ao LLM.
            try:
                from core.voyant_service import voyant_service
                texts = [item["texto_bruto"] for item in items]
                triage = await voyant_service.triage_batch(texts)
            except Exception as _voyant_exc:
                logger.warning("[AI:Batch] VoyantService falhou inesperadamente: %s. Fallback ao LLM.", _voyant_exc)
                triage = None  # Garante o fallback silencioso

            force_local_batch = False
            force_cloud_batch = False

            if triage is not None:
                if triage["drop"]:
                    logger.info("⚡ [AI:Voyant] Lote NEUTRO detectado. Redirecionando exclusivo para Ollama local.")
                    force_local_batch = True
                else:
                    logger.info("⚠️ [AI:Voyant] Vocabulário suspeito. Redirecionando exclusivo para Nuvem (Cloud).")
                    force_cloud_batch = True
            # ── FIM DO FAST-DROP ─────────────────────────────────────────────────

            count = 0
            
            # v90.0: Paralelismo controlado (Concurrency)
            # Ao invés de enviar 1 prompt gigante (que modelos menores erram a formatação JSON),
            # nós enviamos N requisições concorrentes, respeitando limites de taxa.
            semaphore = asyncio.Semaphore(5) # Limita a 5 requests paralelos simultâneos para evitar 429/OOM
            
            async def _process_single(item):
                async with semaphore:
                    try:
                        res_ia = await self.classify_text(
                            item["texto_bruto"], 
                            item["id"], 
                            trace_id=item.get("trace_id"), 
                            force_cloud=force_cloud_batch,
                            force_local=force_local_batch,
                            candidato_id=item.get("candidato_id")
                        )
                        if res_ia and res_ia.get("categoria_ia") != "ERRO":
                            engine_name = res_ia.get("name", "unknown").upper()
                            analise = f"[{engine_name}] {res_ia.get('analise_pericial', '')}"
                            
                            # Atualiza no banco
                            await asyncio.to_thread(
                                db_client.client.table('comentarios').update({
                                    "categoria_ia": res_ia["categoria_ia"], 
                                    "confianca_ia": res_ia["confianca_ia"], 
                                    "is_hate": res_ia["is_hate"], 
                                    "analise_pericial": analise, 
                                    "processado_ia": True
                                }).eq("id", item["id"]).execute
                            )
                            
                            # Se for SUSPEITO, sinaliza o subagente de revisão online imediatamente (Pipeline Reativo)
                            if res_ia.get("categoria_ia") == "SUSPEITO":
                                from core.event_bus import local_bus
                                local_bus.signal_new_suspects()
                                
                            return True
                    except Exception as e:
                        if "Colapso" in str(e):
                            raise e
                        logger.debug(f"[AI:Batch] Erro pontual no ID {item['id']}: {e}")
                    return False

            results = await asyncio.gather(*[_process_single(item) for item in items], return_exceptions=True)
            
            for r in results:
                if isinstance(r, Exception) and "Colapso" in str(r):
                    logger.error("🛑 [AI] Colapso detectado nas APIs. Abortando lote.")
                    raise r
                if r is True:
                    count += 1
                    
            return count
        except Exception as e:
            raise e 

    async def run_batch_reanalysis(self, limit: int = 15, confidence_threshold: float = 0.6) -> int:
        """
        PASA v94.2 - Majority Vote Reanalysis (IA Mesh):
        Busca registros com baixa confiança e realiza uma nova perícia com 2 provedores Cloud
        distintos para desempate.
        """
        try:
            from core.db import db_client
            # Reduzimos o limite para 15 para evitar overhead massivo de tokens Cloud
            res = await asyncio.to_thread(
                db_client.client.table('comentarios')
                .select('id, texto_bruto, trace_id, candidato_id, analise_pericial, categoria_ia')
                .eq('processado_ia', True)
                .lt('confianca_ia', confidence_threshold)
                .not_.eq('categoria_ia', 'ERRO')
                .order('data_coleta', desc=True)
                .limit(limit)
                .execute
            )
            items = res.data or []
            count = 0
            
            # Filtra provedores cloud disponíveis
            cloud_providers = [p for p in self.providers if p["name"] != "ollama"]
            if len(cloud_providers) < 2:
                logger.warning("⚠️ [AI:Mesh] Menos de 2 provedores Cloud ativos. Abortando re-análise profunda de desempate.")
                return 0

            for item in items:
                analise_antiga = item.get("analise_pericial") or ""
                if "[RE-ANÁLISE:" in analise_antiga:
                    continue

                try:
                    # [V2.4] Integração Voyant em Re-análise (PASA v95.5)
                    voyant_insight = ""
                    try:
                        from core.voyant_service import voyant_service
                        # Triagem rápida antes de gastar tokens
                        triage = await voyant_service.triage_batch([item['texto_bruto']])
                        if triage and item['texto_bruto'] in triage:
                            ratio = triage[item['texto_bruto']].get('hostile_ratio', 0)
                            voyant_insight = f"[Voyant-Pericial: {ratio:.1%}] "
                    except Exception as e_v:
                        logger.debug("[Voyant:Mesh] Falha na triagem durante re-análise: %s", e_v)
                    
                    # Executa 2 chamadas paralelas com provedores diferentes
                    p1, p2 = random.sample(cloud_providers, 2)
                    
                    logger.info(f"⚖️ [AI:Mesh] Iniciando desempate {voyant_insight}para ID {item['id']} ({p1['name']} vs {p2['name']})")
                    
                    tasks = [
                        self._execute_provider_call(p1, self._get_system_prompt(False), f"Texto: \"{item['texto_bruto']}\"", "json_object", item['id'], item['candidato_id']),
                        self._execute_provider_call(p2, self._get_system_prompt(False), f"Texto: \"{item['texto_bruto']}\"", "json_object", item['id'], item['candidato_id'])
                    ]
                    
                    responses = await asyncio.gather(*tasks, return_exceptions=True)
                    valid_res = []
                    for i, r in enumerate(responses):
                        if isinstance(r, Exception): continue
                        parsed = self._parse_json_response(r)
                        parsed["provider"] = [p1, p2][i]["name"]
                        valid_res.append(parsed)

                    if not valid_res: continue

                    # Lógica de Desempate (Majority Vote / Highest Confidence)
                    # 1. Se houver consenso de categoria, usa essa categoria com média de confiança.
                    # 2. Se houver divergência, usa a de maior confiança.
                    
                    final_category = valid_res[0]["categoria_ia"]
                    final_confidence = valid_res[0]["confianca_ia"]
                    final_is_hate = valid_res[0]["is_hate"]
                    engine_tag = valid_res[0]["provider"]

                    if len(valid_res) == 2:
                        if valid_res[0]["categoria_ia"] == valid_res[1]["categoria_ia"]:
                            final_confidence = (valid_res[0]["confianca_ia"] + valid_res[1]["confianca_ia"]) / 2
                            engine_tag = f"CONSENSUS:{valid_res[0]['provider']}+{valid_res[1]['provider']}"
                        else:
                            # Divergência: pega o de maior confiança
                            winner = valid_res[0] if valid_res[0]["confianca_ia"] >= valid_res[1]["confianca_ia"] else valid_res[1]
                            final_category = winner["categoria_ia"]
                            final_confidence = winner["confianca_ia"]
                            final_is_hate = winner["is_hate"]
                            engine_tag = f"SPLIT:WINNER={winner['provider']}"
                    
                    tag_status = "FINALIZADA" if final_confidence < confidence_threshold else "CONCLUIDA"
                    analise = f"[RE-ANÁLISE:{tag_status}:{engine_tag.upper()}] {valid_res[0].get('analise_pericial', '')}"
                    
                    await asyncio.to_thread(
                        db_client.client.table('comentarios').update({
                            "categoria_ia": final_category, 
                            "confianca_ia": final_confidence, 
                            "is_hate": final_is_hate, 
                            "analise_pericial": analise
                        }).eq("id", item["id"]).execute
                    )
                    count += 1
                    
                    await asyncio.sleep(2.0) # Backoff entre itens de re-análise
                    
                except Exception as e:
                    logger.error(f"[AI:Mesh] Erro no desempate do ID {item['id']}: {e}")
                    if "Colapso" in str(e): break
                
            return count
        except Exception as e:
            raise e

    async def push_custom_rules_to_providers(self) -> None:
        pass

    async def run_batch_online_review(self, limit: int = 50) -> int:
        # Busca comentarios marcados como SUSPEITO no banco e executa a reclassificacao online (Cloud).
        try:
            from core.db import db_client
            res = await asyncio.to_thread(
                db_client.client.table('comentarios').select('id, texto_bruto, trace_id, candidato_id').eq('categoria_ia', 'SUSPEITO').limit(limit).execute
            )
            items = res.data or []
            count = 0
            for item in items:
                try:
                    res_ia = await self.classify_text(item["texto_bruto"], item["id"], trace_id=item.get("trace_id"), force_cloud=True, candidato_id=item.get("candidato_id"))
                    if res_ia and res_ia.get("categoria_ia") not in ["ERRO", "SUSPEITO"]:
                        engine_name = res_ia.get("name", "unknown").upper()
                        analise = f"[REVISÃO:{engine_name}] {res_ia.get('analise_pericial', '')}"
                        await asyncio.to_thread(
                            db_client.client.table('comentarios').update({
                                "categoria_ia": res_ia["categoria_ia"],
                                "confianca_ia": res_ia["confianca_ia"],
                                "is_hate": res_ia["is_hate"],
                                "analise_pericial": analise,
                                "processado_ia": True
                            }).eq("id", item["id"]).execute
                        )
                        count += 1
                    
                    await asyncio.sleep(2.0)
                except Exception as e:
                    logger.error(f"[AI] Erro ao processar revisao do ID {item['id']}: {e}")
                    if "Colapso" in str(e):
                        logger.error("🛑 [AI] Colapso detectado nas APIs Cloud. Abortando lote de revisao.")
                        raise e
            return count
        except Exception as e:
            raise e

    async def vision_completion(self, image_b64: str, prompt: str,
                                cache_key: str | None = None,
                                mime_type: str = "image/png") -> dict:
        """
        Chamada multimodal (imagem + texto) para modelos de visão.
        Roteia exclusivamente para provedores com suporte a visão (Gemini Flash).
        NÃO usa Maritaca/Ollama/Mistral.
        """
        from core.ai_service_vision_patch import vision_completion as _vision_impl
        return await _vision_impl(self, image_b64, prompt, cache_key, mime_type)

ai_service = AIService()

```

