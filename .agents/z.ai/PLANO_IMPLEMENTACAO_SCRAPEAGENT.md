# Plano de Implementação Completo — ScrapeAgent
**Sentinela | v1.0 | 12 de Junho de 2026**

---

## Sumário Executivo

Este documento consolida o plano de implementação do ScrapeAgent, validado contra o estado real do repositório `github.com/thimacedo/sentinela` (branch `main`). O plano segue a ordem de fases recomendada pela validação arquitetural, com o acréscimo do pré-requisito ausente (Fase 2: `vision_completion`).

**Veredito global: PROPOSTA VIÁVEL — com 2 ressalvas técnicas endereçadas neste plano.**

---

## Estrutura de Arquivos Gerados

```
core/
├── ai_service_vision_patch.py           # Fase 2: Patch cirúrgico no ai_service
└── agent_scraper/
    ├── __init__.py                       # Módulo de isolamento (GEMINI.md compliant)
    ├── agent.py                          # Fase 3: Loop OODA principal
    ├── tools.py                          # Fase 1: Registro de ferramentas
    ├── dom_healing.py                    # Fase 4: Cura autônoma de seletores DOM
    ├── cognitive_prioritizer.py          # Fase 5: Priorização cognitiva de alvos
    ├── persona_mode.py                   # Fase 6: Simulação de comportamento humano
    └── worker_adapter.py                 # Fase 7: Adaptador para wk_coleta_instagram.py
```

---

## Fase 1: Registro de Ferramentas (`tools.py`)

**Prioridade:** Alta  
**Dependências:** Nenhuma  
**Custo em tokens:** 0 (apenas determinístico)  
**Arquivo:** `core/agent_scraper/tools.py`

### O que foi implementado

A classe `ScrapeAgentTools` registra 8 ferramentas organizadas por categoria:

| Ferramenta | Categoria | Custo Tokens | Descrição |
|---|---|---|---|
| `rotate_proxy` | evasion | 0 | Rotação round-robin da PROXY_LIST |
| `adjust_typing_delay` | evasion | 0 | Ajuste de velocidade de digitação (normal/cautious/stealth) |
| `adjust_navigation_profile` | evasion | 0 | Ajuste de perfil de navegação baseado no tipo de bloqueio (429/403/login_redirect/captcha) |
| `heal_dom_selectors` | recovery | 50 | Cura de seletores DOM via IA de visão |
| `flag_cooldown_session` | recovery | 0 | Sinalização de sessão em cooldown + backoff |
| `emergency_hibernate` | recovery | 0 | Hibernação de emergência com sinalização ao EventBus |
| `save_learned_selector` | learning | 0 | Persistência em `configs/learned_selectors.json` |
| `get_block_severity` | sensing | 0 | Classificação determinística de severidade (SESSION_EXPIRED/IP_BLOCK/RATE_LIMIT/CAPTCHA/DOM_CHANGE/UNKNOWN) |

### Padrão seguido

Cada ferramenta:
- É um método assíncrono que retorna `ToolResult` padronizado
- Registra métricas de execução (tempo, sucesso/falha)
- Custo em tokens declarado no registro (0 para ações determinísticas)
- Integra com infraestrutura existente (`scraper_circuit_breaker`, `PROXY_LIST`, `learned_selectors.json`)

### Integração com código existente

- `rotate_proxy`: Respeita `scraper_circuit_breaker.record_rotation()` se disponível
- `adjust_navigation_profile`: Aplica perfis de `scraper_weights.py` se disponível
- `get_block_severity`: Mapeamento idêntico ao `sre_agent.py` (SESSION_EXPIRED, IP_BLOCK, RATE_LIMIT, CAPTCHA, DOM_CHANGE, UNKNOWN)
- `save_learned_selector`: Formato idêntico ao `instagram_scraper_v2.py`

---

## Fase 2: `vision_completion` no ai_service (PRÉ-REQUISITO BLOQUEADOR)

**Prioridade:** Alta (bloqueia Fase 4)  
**Dependências:** Nenhuma  
**Arquivo:** `core/ai_service_vision_patch.py`

### O gap identificado

O `ai_service.chat_completion()` é **somente texto** — assinatura `(prompt: str, system_prompt: str, response_format: str)`. O DOM Healing requer conteúdo multimodal (imagem base64 + texto).

### O que foi implementado

A função `vision_completion()` com as seguintes características:

1. **Roteamento exclusivo para Gemini Flash** — provedor com suporte nativo a visão. Maritaca/Ollama/Mistral **não são usados** para visão.

2. **Cache de sessão** — respostas cacheadas por 5 minutos com chave (ex: shortcode do post). Evita chamadas repetidas ao mesmo seletor.

3. **Payload no formato Gemini API** — `contents` com `parts` contendo texto e `inline_data` (imagem base64).

4. **Tratamento de rate limit** — se status 429, aplica cooldown de 60s no provedor.

5. **Validação de provedor disponível** — verifica cooldown e circuit breaker antes de chamar.

6. **Timeout de 30s** — evita bloqueio do worker em caso de lentidão.

### Como aplicar o patch

Adicionar o método abaixo à classe `AIService` em `core/ai_service.py`:

```python
async def vision_completion(self, image_b64: str, prompt: str,
                            cache_key: str | None = None,
                            mime_type: str = "image/png") -> dict:
    from core.ai_service_vision_patch import vision_completion as _vision_impl
    return await _vision_impl(self, image_b64, prompt, cache_key, mime_type)
```

### Risco de regressão: NENHUM

O novo método é aditivo. O `chat_completion()` existente não é alterado. O HITL atual pode funcionar como fallback se a IA de visão falhar.

---

## Fase 3: Loop OODA Principal (`agent.py`)

**Prioridade:** Alta  
**Dependências:** Fase 1 (tools.py)  
**Arquivo:** `core/agent_scraper/agent.py`

### O que foi implementado

A classe `ScrapeAgent` implementa o loop OODA com:

#### Data Classes

- `Observation`: Sinal coletado do ambiente (tipo, severidade, status_code, dados)
- `Severity`: Enum com SESSION_EXPIRED, IP_BLOCK, RATE_LIMIT, CAPTCHA, DOM_CHANGE, UNKNOWN, HEALTHY
- `Decision`: Decisão do agente (ferramenta, parâmetros, tipo, raciocínio)
- `ActionResult`: Resultado da execução (sucesso, dados, erro, tokens)
- `CycleResult`: Resultado completo do ciclo (observação + decisão + ação + métricas)

#### Roteamento Determinístico vs Cognitivo

Seguindo o padrão do `sre_agent.py`:

| Severidade | Roteamento | Tokens | Ação |
|---|---|---|---|
| SESSION_EXPIRED | Determinístico | 0 | `flag_cooldown_session` (300s) |
| IP_BLOCK | Determinístico | 0 | `adjust_navigation_profile` (403) |
| RATE_LIMIT | Determinístico | 0 | `adjust_navigation_profile` (429) |
| CAPTCHA | Determinístico | 0 | `emergency_hibernate` (3600s) |
| HEALTHY | Determinístico | 0 | Nenhuma ação |
| DOM_CHANGE | Cognitivo (visão) | ~50 | `heal_dom_selectors` |
| UNKNOWN | Cognitivo (LLM) | Variável | Consulta ao LLM |

#### API de Conveniência

```python
result = await agent.evaluate_environment(
    target="username",
    status_code=429,
    consecutive_empty_posts=0,
    screenshot_b64="...",
    html_snippet="...",
    cache_key="shortcode_abc123",
)
```

#### Fallback para HITL

Se a ação falhar e a severidade for DOM_CHANGE ou UNKNOWN, o agente sinaliza `fallback_to_hitl=True` no `CycleResult`, permitindo que o worker ative a intervenção humana existente.

---

## Fase 4: DOM Healing Autônomo (`dom_healing.py`)

**Prioridade:** Alta  
**Dependências:** Fase 2 (vision_completion)  
**Arquivo:** `core/agent_scraper/dom_healing.py`

### O que foi implementado

A classe `DOMHealer` substitui o HITL atual com:

1. **Captura de screenshot via Playwright** — `full_page=False` para reduzir tamanho e custo de tokens

2. **Extração de fragmento HTML** — foco na área de comentários, máximo 5000 chars

3. **Prompt otimizado** — instrui a IA a retornar APENAS o seletor CSS, sem explicação

4. **Validação de seletor** — bloqueia JavaScript inline, valida sintaxe CSS, comprimento 1-200 chars

5. **Extração robusta** — lida com respostas da IA em vários formatos (puro, com aspas, com explicação, em bloco de código)

6. **Persistência idêntica** — mesmo formato de `configs/learned_selectors.json` usado pelo scraper atual

7. **Fallback HITL** — se a visão falhar, retorna `source: "hitl_fallback"` e o worker ativa o fluxo de intervenção humana existente

### GATING PRESERVADO

O DOM Healing é disparado **SOMENTE** após confirmar falha de seletor (3 posts vazios consecutivos), nunca preventivamente. Isto é consistente com o gating atual do HITL e protege contra custo desnecessário de tokens de visão.

### Risco de latência

A chamada à IA de visão adiciona ~2-5s por evento de healing. O HITL atual bloqueia o worker até o operador clicar (potencialmente minutos). A IA de visão é estritamente superior. O cache por sessão evita chamadas repetidas ao mesmo shortcode.

---

## Fase 5: Priorização Cognitiva de Alvos (`cognitive_prioritizer.py`)

**Prioridade:** Alta  
**Dependências:** Supabase client  
**Custo em tokens:** 0 (apenas SQL)  
**Arquivo:** `core/agent_scraper/cognitive_prioritizer.py`

### O que foi implementado

A classe `CognitivePrioritizer` calcula scores de prioridade baseados em 4 métricas:

| Métrica | Peso | Fonte | Normalização |
|---|---|---|---|
| Volume de comentários (24h) | 40% | SQL COUNT sobre `comentarios` | Logarítmica (0-100) |
| Proporção de ódio | 30% | SQL COUNT com HATE_CATEGORIES | Não-linear (0-100) |
| Tempo desde última coleta | 20% | SQL MAX(data_coleta) | Logarítmica (0-100) |
| Nota de relevância | 10% | `candidatos.nota_relevancia` | Linear (0-100) |

### Integração com QueueManager

```python
# Extensão de claim_next_target():
prioritizer = CognitivePrioritizer(supabase_client)
username, priority = await prioritizer.get_next_priority(active_usernames)
await queue_manager.add_target_to_queue(username, priority=priority)
```

### Por que esta é a capacidade de menor risco

- Não requer LLM — apenas SQL agregado
- Não altera o scraper — apenas reordena a fila
- Implementável como patch no `claim_next_target()` do QueueManager
- ROI imediato: perfis com picos de ódio são coletados primeiro

---

## Fase 6: Modo Persona Experimental (`persona_mode.py`)

**Prioridade:** Baixa (validar custo/benefício primeiro)  
**Dependências:** Playwright  
**Arquivo:** `core/agent_scraper/persona_mode.py`

### O que foi implementado

A classe `PersonaEngine` com 3 níveis configuráveis via `.env`:

| Modo | SCRAPER_PERSONA_MODE | Funcionalidades | Impacto no Ciclo |
|---|---|---|---|
| Full | `full` | Mouse estocástico + leitura + scroll + digitação variável | ALTO (~+8-15s/alvo) |
| Minimal | `minimal` | Apenas jitter de scroll | BAIXO (~+1-3s/alvo) |
| Disabled | `disabled` | Nenhum (comportamento original) | Nenhum |

### Recomendação

Ativar por padrão apenas o modo `minimal` (jitter de scroll), que é o item de **maior impacto com menor custo**. O modo `full` deve ser validado quantitativamente antes de ativar em produção.

### Funcionalidades por modo

- **Scroll humano** (minimal + full): Jitter estocástico de distância e pausa, 5% chance de "voltar"
- **Mouse estocástico** (full only): Trajetória Bézier com ruído gaussiano
- **Digitação variável** (full only): Delay por caractere + pausa entre palavras
- **Tempo de leitura** (full only): Proporcional ao volume de comentários visíveis

---

## Fase 7: Adaptador do Worker (`worker_adapter.py`)

**Prioridade:** Alta  
**Dependências:** Todas as fases anteriores  
**Arquivo:** `core/agent_scraper/worker_adapter.py`

### O que foi implementado

A classe `ScrapeAgentAdapter` é o ponto de integração final que:

1. **Instancia o ScrapeAgent** com as dependências corretas (scraper + ai_service)
2. **Envolve o scraper existente** com o loop cognitivo
3. **Intercepta erros de DOM** e aciona DOM Healing
4. **Aplica persona mode** quando configurado
5. **Preserva toda infraestrutura existente** (circuit breaker, checkpoint, buffer, EventBus)

### Ponto de Integração no Worker

No método `run_cycle()` de `wk_coleta_instagram.py`:

```python
# No __init__ do worker:
from core.agent_scraper.worker_adapter import ScrapeAgentAdapter
self.agent_adapter = ScrapeAgentAdapter(
    scraper=self.scraper,
    ai_service=ai_service,
)

# No run_cycle do worker:
result = await self.agent_adapter.run_scrape_cycle(
    username=target,
    page=page,
)
```

### Fluxo de Execução

```
1. Persona Mode: Scroll/jitter inicial
2. Scraping via scraper existente (scrape_profile)
3. Se sucesso → retorna direto
4. Se problema (DOM vazio, bloqueio):
   a. Agente avalia ambiente (OODA - Observar)
   b. Classifica severidade (OODA - Orientar)
   c. Seleciona ação (OODA - Decidir)
   d. Executa recuperação (OODA - Agir)
5. Se DOM_CHANGE: DOM Healing via IA de visão
6. Se visão falhar: fallback para HITL existente
7. Retorna ScrapeCycleResult estruturado
```

---

## Ordem de Implementação Recomendada

| Ordem | Fase | Arquivo | Prioridade | Bloqueado Por |
|---|---|---|---|---|
| 1 | Registro de Ferramentas | `tools.py` | Alta | Nada |
| 2 | `vision_completion` no ai_service | `ai_service_vision_patch.py` | Alta | Nada |
| 3 | Loop OODA Principal | `agent.py` | Alta | Fase 1 |
| 4 | DOM Healing Autônomo | `dom_healing.py` | Alta | Fase 2 |
| 5 | Priorização Cognitiva | `cognitive_prioritizer.py` | Alta | Nada |
| 6 | Modo Persona (Experimental) | `persona_mode.py` | Baixa | Nada |
| 7 | Adaptador do Worker | `worker_adapter.py` | Alta | Fases 1-5 |

**Fases 1, 2 e 5 podem ser implementadas em paralelo** — não têm dependências entre si.

---

## Riscos Técnicos Endereçados

### Risco 1: Latência do DOM Healing em produção
**Mitigação:** Cache de sessão por shortcode (TTL 5 min). O HITL atual bloqueia por minutos; a IA de visão bloqueia por ~2-5s.

### Risco 2: Custo de tokens de visão
**Mitigação:** DOM Healing disparado SOMENTE após 3 posts vazios consecutivos (gating inalterado). Nunca preventivamente.

### Risco 3: Compatibilidade com AGENTS_SYNC.md
**Mitigação:** Isolamento em `core/agent_scraper/` está alinhado com GEMINI.md. A proposta é expansão orgânica que não conflita com restrições existentes.

### Risco 4: Modo Persona aumentando tempo de ciclo
**Mitigação:** Default `SCRAPER_PERSONA_MODE=minimal`. Validação quantitativa antes de ativar `full`.

---

## Variáveis de Ambiente (.env)

```env
# ScrapeAgent
SCRAPER_PERSONA_MODE=minimal          # full|minimal|disabled
PERSONA_SCROLL_PAUSE_MIN=0.3          # Segundos
PERSONA_SCROLL_PAUSE_MAX=1.2          # Segundos
PERSONA_TYPING_DELAY_MIN=0.030        # Segundos por caractere
PERSONA_TYPING_DELAY_MAX=0.080        # Segundos por caractere

# Visão (pré-requisito)
GEMINI_API_KEY=AIza...               # Obrigatório para DOM Healing

# Proxy
PROXY_LIST=http://proxy1:8080,http://proxy2:8080
PROXY_URL=http://proxy1:8080          # Fallback se PROXY_LIST vazio
```

---

## Próximo Passo Imediato

**Antes de criar qualquer arquivo em `core/agent_scraper/`**, implementar o método `vision_completion` no `ai_service.py` como patch cirúrgico. Este é o **único pré-requisito ausente** que bloqueia a capacidade mais valiosa da proposta (DOM Healing).

Após aplicar o patch, as fases 1, 3, 5 e 6 podem avançar em paralelo, com a Fase 4 (DOM Healing) desbloqueada e a Fase 7 (Worker Adapter) como ponto de integração final.
