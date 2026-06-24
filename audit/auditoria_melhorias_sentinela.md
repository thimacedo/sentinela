# Relatório de Auditoria e Melhorias - Sentinela v50.1
## Análise Crítica das Correções Propostas

**Data:** 24 de junho de 2026  
**Escopo:** Validação técnica e recomendações de boas práticas

---

## 1. PROBLEMAS IDENTIFICADOS NAS CORREÇÕES PROPOSTAS

### 1.1 🔴 CRÍTICO: Falta de Padrão de Exceções Customizadas

**Problema:**
```python
# Atual (frágil)
raise RuntimeError("hitl_intervention_completed_restarting")

# Captura em múltiplos lugares
if "hitl_intervention_completed_restarting" in str(e):
```

**Por quê é problemático:**
- Magic strings são propensas a typos
- Difícil refatorar globalmente
- Semântica imprecisa (ValueError vs RuntimeError para controle de fluxo?)
- Viola princípio SRP: RuntimeError deve ser para erros, não sinais de controle

**Recomendação:**
```python
# Criar hierarquia de exceções customizadas
class ScrapeControlSignal(Exception):
    """Base para sinais de controle (não são erros de fato)"""
    pass

class DOMHealerRestartSignal(ScrapeControlSignal):
    """Sinal de que DOM Healer completou e precisa de restart limpo"""
    def __init__(self, reason: str = "dom_healer_restart", 
                 selector_cache_key: str = None):
        self.reason = reason
        self.selector_cache_key = selector_cache_key
        super().__init__(f"DOMHealer restart signal: {reason}")

class SessionExpiredError(ScrapeControlSignal):
    """Login wall ou sessão expirada detectada"""
    def __init__(self, username: str, page_url: str):
        self.username = username
        self.page_url = page_url
        super().__init__(f"Session expired for {username} at {page_url}")

class ChallengeRequiredError(ScrapeControlSignal):
    """Challenge page detectada (Soft Block)"""
    def __init__(self, username: str, challenge_type: str = "unknown"):
        self.username = username
        self.challenge_type = challenge_type
        super().__init__(f"Challenge required for {username}: {challenge_type}")

# Uso
except DOMHealerRestartSignal as signal:
    # Tratamento semântico e type-safe
    logger.info(f"🔄 {signal}")
    return ScrapeCycleResult(..., error=signal.reason)
```

---

### 1.2 🔴 CRÍTICO: Falta de Retry Logic Inteligente

**Problema na CORREÇÃO 3:**

O código proposto faz `continue` após sucesso do DOM Healing, mas não há limite de quantas vezes isto pode acontecer no mesmo ciclo.

```python
# Risco: Loop infinito se DOMHealer sempre "cura" mas continua falhando
consecutive_zero_comments = 0  # Reset sem limite
continue  # Volta para o próximo post
```

**Cenário de Falha:**
- Seletor IA é validado (encontra elementos)
- Mas elementos estão vazios ou incorretos
- Ciclo tenta healing novamente
- Entra em loop infinito

**Recomendação:**

```python
class HealingAttemptTracker:
    """Rastreia tentativas de healing para evitar loops infinitos"""
    def __init__(self, max_healing_attempts: int = 2):
        self.max_healing_attempts = max_healing_attempts
        self.healing_attempts_this_cycle = 0
        self.last_proposed_selectors = []
    
    def can_attempt_healing(self) -> bool:
        return self.healing_attempts_this_cycle < self.max_healing_attempts
    
    def record_healing_attempt(self, selector: str, success: bool):
        self.healing_attempts_this_cycle += 1
        self.last_proposed_selectors.append((selector, success))
    
    def has_repeated_selector(self, new_selector: str) -> bool:
        """Detecta se a IA propôs o mesmo seletor novamente"""
        return any(sel == new_selector for sel, _ in self.last_proposed_selectors)
    
    def reset(self):
        self.healing_attempts_this_cycle = 0
        self.last_proposed_selectors = []

# Uso
if consecutive_zero_comments >= 3:
    if not healing_tracker.can_attempt_healing():
        logger.error(f"❌ Limite de tentativas de healing atingido. Abortar.")
        raise DOMHealerRestartSignal("max_healing_attempts_exceeded")
    
    # ... tentativa de healing ...
    
    if healing_tracker.has_repeated_selector(new_selector):
        logger.error(f"⚠️ IA propôs seletor repetido. Indicativo de problema estrutural.")
        raise DOMHealerRestartSignal("repeated_selector_detected")
    
    healing_tracker.record_healing_attempt(new_selector, success=True)
    consecutive_zero_comments = 0
    continue
```

---

### 1.3 🟡 ALTO: Validação Funcional Insuficiente

**Problema na CORREÇÃO 4:**

A validação apenas conta elementos, mas não valida **conteúdo**:

```python
# Atual - apenas verifica existência
test_elements = await page.query_selector_all(proposed_selector)
if len(test_elements) == 0:
    return {"success": False}
# Problema: E se encontrou elementos vazios ou placeholder?
```

**Recomendação:**

```python
async def _validate_selector_functionally(
    self,
    page: Page,
    selector: str,
    selector_name: str
) -> dict:
    """
    Validação multi-camada de seletores propostos.
    Retorna dict com resultado e métricas.
    """
    try:
        elements = await page.query_selector_all(selector)
        
        if not elements:
            return {
                "valid": False,
                "reason": "no_elements_found",
                "element_count": 0
            }
        
        element_count = len(elements)
        
        # Validação 1: Quantidade razoável
        if selector_name == "comment_container" and element_count > 500:
            return {
                "valid": False,
                "reason": "too_many_elements",
                "element_count": element_count,
                "expected_max": 500
            }
        
        # Validação 2: Verifica conteúdo não-vazio
        empty_elements = 0
        for elem in elements[:10]:  # Amostra dos primeiros 10
            text = (await elem.text_content()).strip()
            if not text:
                empty_elements += 1
        
        if empty_elements == len(elements[:10]):
            return {
                "valid": False,
                "reason": "all_elements_empty",
                "element_count": element_count
            }
        
        # Validação 3: Verifica visibilidade
        visible_elements = 0
        for elem in elements[:5]:
            try:
                is_visible = await elem.is_visible()
                if is_visible:
                    visible_elements += 1
            except:
                pass
        
        if visible_elements == 0:
            return {
                "valid": False,
                "reason": "no_visible_elements",
                "element_count": element_count
            }
        
        # Passou em todas as validações
        return {
            "valid": True,
            "element_count": element_count,
            "visible_count": visible_elements,
            "empty_count": empty_elements
        }
        
    except Exception as e:
        return {
            "valid": False,
            "reason": f"validation_error: {type(e).__name__}",
            "error": str(e)
        }
```

---

### 1.4 🟡 ALTO: Falta de Observabilidade Estruturada

**Problema:**

Não há rastreamento estruturado de:
- Quantas vezes cada perfil falhou por dom_healing
- Taxa de sucesso de healing da IA
- Tempo decorrido em healing vs extração normal
- Padrões de seletores que falham

**Recomendação:**

```python
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
import json

@dataclass
class ScrapeMetrics:
    """Métricas estruturadas de um ciclo de scrape"""
    username: str
    timestamp: datetime
    cycle_duration_s: float
    
    # Contadores
    posts_found: int
    posts_processed: int
    comments_collected: int
    
    # DOM Healing
    healing_attempts: int
    healing_successes: int
    healing_failures: int
    healing_total_time_s: float
    
    # Seletores
    selectors_used: list[str]
    selectors_from_cache: int
    selectors_from_ai: int
    
    # Erros
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_json(self) -> str:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return json.dumps(data, ensure_ascii=False, indent=2)

class MetricsCollector:
    """Coleta e persiste métricas estruturadas"""
    def __init__(self, metrics_dir: Path = Path("logs/metrics")):
        self.metrics_dir = metrics_dir
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.current_metrics: Optional[ScrapeMetrics] = None
    
    def start_cycle(self, username: str):
        self.current_metrics = ScrapeMetrics(
            username=username,
            timestamp=datetime.now(),
            cycle_duration_s=0,
            posts_found=0,
            posts_processed=0,
            comments_collected=0,
            healing_attempts=0,
            healing_successes=0,
            healing_failures=0,
            healing_total_time_s=0,
            selectors_used=[],
            selectors_from_cache=0,
            selectors_from_ai=0,
        )
    
    def record_healing_attempt(self, success: bool, duration_s: float, selector: str):
        if self.current_metrics:
            self.current_metrics.healing_attempts += 1
            if success:
                self.current_metrics.healing_successes += 1
            else:
                self.current_metrics.healing_failures += 1
            self.current_metrics.healing_total_time_s += duration_s
            if selector not in self.current_metrics.selectors_used:
                self.current_metrics.selectors_used.append(selector)
    
    def end_cycle(self, duration_s: float, error_code: str = None, error_msg: str = None):
        if self.current_metrics:
            self.current_metrics.cycle_duration_s = duration_s
            self.current_metrics.error_code = error_code
            self.current_metrics.error_message = error_msg
            
            # Persiste
            filename = self.metrics_dir / f"{self.current_metrics.username}_{self.current_metrics.timestamp.timestamp()}.json"
            with open(filename, "w") as f:
                f.write(self.current_metrics.to_json())
            
            return self.current_metrics

# Uso
collector = MetricsCollector()
collector.start_cycle("@capitaowagner")
# ... ciclo de extração ...
collector.record_healing_attempt(success=True, duration_s=2.5, selector=".comment-box")
metrics = collector.end_cycle(duration_s=45.2, error_code="healer_restart")
```

---

### 1.5 🟡 MÉDIO: Circuit Breaker Inadequado

**Problema:**

Não há diferenciação no tratamento de falhas:
- Uma falha de DOM Healing não deveria afetar o circuit breaker da sessão
- Todas as falhas incrementam `consecutive_blocks` igualmente

**Recomendação:**

```python
class DifferentiatedCircuitBreaker:
    """Circuit breaker que diferencia tipos de falha"""
    
    def __init__(self):
        self.failure_counts = {}  # {error_type: count}
        self.thresholds = {
            "session_expired": 1,          # 1 falha abre o circuit
            "challenge_required": 1,
            "network_error": 5,            # 5 falhas abrem
            "dom_healing_restart": float('inf'),  # Nunca abre por isto
            "invalid_target": 1,
            "generic_error": 3,
        }
    
    def record_failure(self, error_type: str) -> bool:
        """
        Registra falha. Retorna True se circuit breaker foi acionado.
        """
        self.failure_counts[error_type] = self.failure_counts.get(error_type, 0) + 1
        
        threshold = self.thresholds.get(error_type, 3)
        current_count = self.failure_counts[error_type]
        
        if current_count >= threshold:
            logger.error(f"⛔ Circuit Breaker acionado para {error_type} "
                        f"({current_count}/{threshold})")
            return True
        
        return False
    
    def record_success(self):
        """Reseta contadores após sucesso"""
        self.failure_counts.clear()
    
    def should_retry(self, error_type: str) -> bool:
        """Determina se deve fazer retry para este tipo de erro"""
        return self.failure_counts.get(error_type, 0) < self.thresholds.get(error_type, 3)
```

---

## 2. PROBLEMAS NAS CORREÇÕES PROPOSTAS

### 2.1 🔴 CORREÇÃO 1: `worker_adapter.py` — Falta de Type Hints

**Código proposto:**
```python
except RuntimeError as e:
    if "hitl_intervention_completed_restarting" in str(e):
```

**Problemas:**
- String matching é frágil
- Sem type hints, IDE não consegue autocompletar
- Sem logging de contexto (qual username, qual post)

**Melhoria:**

```python
except (RuntimeError, DOMHealerRestartSignal) as e:
    # Type-safe handling com custom exceptions
    if isinstance(e, DOMHealerRestartSignal) or \
       (isinstance(e, RuntimeError) and "hitl_intervention_completed" in str(e)):
        
        username_context = username or "unknown"
        self._stats["healer_restarts"] = self._stats.get("healer_restarts", 0) + 1
        
        logger.warning(
            f"🔄 [Adapter] DOM Healing restart solicitado",
            extra={
                "username": username_context,
                "healer_restart_count": self._stats["healer_restarts"],
                "cycle_id": getattr(self, '_current_cycle_id', 'unknown'),
            }
        )
        
        return ScrapeCycleResult(
            success=False,
            username=username_context,
            comments_collected=0,
            posts_processed=0,
            error="healer_restart_requested",
            persona_time_s=persona_time,
            is_control_signal=True,  # ✅ Flag semântico
        )
    
    # Qualquer outro erro sobe
    raise
```

---

### 2.2 🔴 CORREÇÃO 2: `wk_coleta_instagram.py` — Falta de Diferenciação

**Código proposto trata tudo igualmente:**
```python
if "healer_restart_requested" in error_str or \
   "hitl_intervention_completed_restarting" in error_str:
    # Nunca incrementa consecutive_blocks
    return result
```

**Problema:** Isto está correto, mas falta logging estruturado para diagnosticar.

**Melhoria:**

```python
except DOMHealerRestartSignal as heal_signal:
    # Tratamento explícito e semântico
    logger.info(
        f"🔄 [Worker] Ciclo de healing concluído para @{target.username}",
        extra={
            "target": target.username,
            "healing_reason": heal_signal.reason,
            "selector_cache_key": heal_signal.selector_cache_key,
            "cycle": self.cycle,
            "worker_id": self.worker_id,
        }
    )
    
    # NÃO incrementa contador punitivo
    # NÃO registra no circuit breaker
    
    result = CycleResult(
        worker_id=self.worker_id,
        cycle=self.cycle,
        target=target.username,
        source="v2_engine",
        extracted=0,
        simulated=False,
        error="healer_restart",
        db_success=False,
        is_control_signal=True,  # ✅ Semântica clara
    )
    return result
```

---

### 2.3 🔴 CORREÇÃO 3: `instagram_scraper_v2.py` — Diagnóstico Quebrado

**Problema:**

```python
is_login_wall = (
    "accounts/login" in page_url or
    "login" in page_url and "instagram" in page_url or  # ⚠️ Operador precedência errada!
    ...
)
```

**Bug:** Sem parênteses, a precedência de `and`/`or` está errada.

```python
# Isto é interpretado como:
"accounts/login" in page_url 
OR 
("login" in page_url AND "instagram" in page_url)
OR 
...

# E se URL fosse: "https://instagram.com/mylogin"
# "login" está em "mylogin"? Sim → Falso positivo!
```

**Correção:**

```python
is_login_wall = (
    "accounts/login" in page_url or
    ("/login" in page_url and "instagram" in page_url) or  # Paths específicas
    "entrar" in page_title or
    "log in to instagram" in page_content or
    "faça login para curtir" in page_content
)

# Melhor ainda: usar regex ou função dedicada
def _is_login_wall_page(page_url: str, page_title: str, page_content: str) -> bool:
    """Detecta com precisão se a página é um muro de login"""
    
    # URLs específicas
    login_url_patterns = [
        r"accounts/login",
        r"accounts/account_recovery",
        r"/login/?$",
    ]
    
    for pattern in login_url_patterns:
        if re.search(pattern, page_url):
            return True
    
    # Títulos característicos
    if any(t in page_title.lower() for t in ["log in", "entrar", "login required"]):
        return True
    
    # Conteúdo (mais robusto)
    login_indicators = [
        "log in to instagram",
        "faça login para curtir",
        "enter your login details",
        "your account has been locked",
    ]
    content_lower = page_content.lower()
    if any(ind in content_lower for ind in login_indicators):
        return True
    
    return False

# Uso
if _is_login_wall_page(page_url, page_title, page_content):
    raise SessionExpiredError(username=username, page_url=page_url)
```

---

### 2.4 🟡 MÉDIO: CORREÇÃO 5 — Script de Limpeza Incompleto

**Problema:**

```python
def clean_stale_selectors():
    # Apenas remove por timestamp
    # Não valida se seletores ainda funcionam
```

**Melhoria:**

```python
async def validate_and_clean_selectors(browser: Browser):
    """
    Valida cada seletor em cache contra a página real.
    Remove os que não funcionam mais.
    """
    CACHE_PATH = Path("configs/learned_selectors.json")
    
    with open(CACHE_PATH) as f:
        cache = json.load(f)
    
    # URL de teste (um perfil público e estável)
    test_url = "https://www.instagram.com/instagram/"
    
    page = await browser.new_page()
    try:
        await page.goto(test_url, wait_until="networkidle", timeout=15000)
        
        to_remove = []
        
        for selector_key, selector_data in cache.items():
            selector = selector_data.get("selector")
            if not selector:
                to_remove.append(selector_key)
                continue
            
            try:
                elements = await page.query_selector_all(selector)
                if not elements:
                    logger.warning(f"❌ Seletor inválido: {selector_key} → {selector}")
                    to_remove.append(selector_key)
                else:
                    logger.info(f"✅ Seletor válido: {selector_key}")
                    # Atualiza timestamp
                    cache[selector_key]["last_validated"] = datetime.now().isoformat()
            
            except Exception as e:
                logger.error(f"⚠️ Erro validando {selector_key}: {e}")
                to_remove.append(selector_key)
        
        # Remove inválidos
        for key in to_remove:
            del cache[key]
            logger.warning(f"🗑️ Removido: {key}")
        
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Validação completa: {len(to_remove)} removidos")
        
    finally:
        await page.close()
```

---

## 3. RECOMENDAÇÕES ADICIONAIS

### 3.1 Logging Estruturado (JSON)

Substituir prints/logs simples por structured logging:

```python
import logging
from pythonjsonlogger import jsonlogger

# Configurar
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)

# Uso
logger.error(
    "DOM Healing failed",
    extra={
        "username": username,
        "post_shortcode": shortcode,
        "reason": "selector_validation_failed",
        "selector": proposed_selector,
        "element_count": 0,
        "attempts": healing_attempts,
        "timestamp": datetime.now().isoformat(),
    }
)
```

---

### 3.2 Testes Unitários para Lógica Crítica

```python
# tests/test_dom_healing.py
import pytest
from core.agent_scraper.dom_healing import DOMHealer

@pytest.mark.asyncio
async def test_healing_rejects_empty_selector():
    """DOM Healer rejeita seletores que não encontram elementos"""
    healer = DOMHealer(ai_service=mock_ai)
    
    # Simula página sem elementos para o seletor
    page = await mock_browser.new_page()
    
    result = await healer.heal_selectors(
        page=page,
        selector_name="comment_container",
        screenshot_b64="fake_b64",
        html_snippet="<div>empty</div>",
    )
    
    assert not result["success"]
    assert "no elements" in result["error"].lower()

@pytest.mark.asyncio
async def test_healing_detects_repeated_selector():
    """Healing detecta quando IA propõe seletor repetido"""
    tracker = HealingAttemptTracker()
    tracker.record_healing_attempt(".selector1", success=True)
    
    assert tracker.has_repeated_selector(".selector1")
    assert not tracker.has_repeated_selector(".selector2")
```

---

### 3.3 Telemetria + Alertas

```python
# monitoring/alerts.py
class ScrapeHealthMonitor:
    """Monitora saúde do scraper e emite alertas"""
    
    def __init__(self, alert_threshold_failure_rate: float = 0.7):
        self.failure_rate_threshold = alert_threshold_failure_rate
        self.metrics_window = []  # Últimas 100 tentativas
    
    def check_health(self) -> dict:
        if len(self.metrics_window) < 20:
            return {"status": "insufficient_data"}
        
        failures = sum(1 for m in self.metrics_window if m.get("error_code"))
        failure_rate = failures / len(self.metrics_window)
        
        if failure_rate > self.failure_rate_threshold:
            return {
                "status": "critical",
                "failure_rate": failure_rate,
                "action": "STOP_SCRAPING_INVESTIGATE",
                "message": f"Taxa de falha crítica: {failure_rate*100:.1f}%"
            }
        
        return {"status": "healthy", "failure_rate": failure_rate}

# Integração
monitor = ScrapeHealthMonitor()
health = monitor.check_health()
if health["status"] == "critical":
    send_alert_to_slack(health["message"])
    pause_scraper()
```

---

## 4. CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Exceções Customizadas (CRÍTICO)
- [ ] Criar `core/exceptions.py` com hierarquia de exceções
- [ ] Refatorar todas as exceções do scraper
- [ ] Adicionar type hints

### Fase 2: Healing Inteligente (CRÍTICO)
- [ ] Implementar `HealingAttemptTracker`
- [ ] Limite de tentativas de healing
- [ ] Detecção de seletores repetidos

### Fase 3: Validação Robusta (ALTO)
- [ ] Melhorar `_validate_selector_functionally`
- [ ] Validação de conteúdo, não apenas existência
- [ ] Verificação de visibilidade

### Fase 4: Observabilidade (ALTO)
- [ ] Implementar `ScrapeMetrics` e `MetricsCollector`
- [ ] Estruturado logging (JSON)
- [ ] Dashboard de métricas

### Fase 5: Proteção (MÉDIO)
- [ ] `DifferentiatedCircuitBreaker`
- [ ] `ScrapeHealthMonitor`
- [ ] Alertas Slack/Email

### Fase 6: Testes (MÉDIO)
- [ ] Testes unitários para healing
- [ ] Testes de integração com Playwright mock
- [ ] Testes de detectores de login wall

---

## 5. ESTIMATIVA E PRIORIZAÇÃO

| Fase | Prioridade | Esforço | Risco |
|------|-----------|--------|-------|
| Exceções customizadas | 🔴 CRÍTICO | 4h | ALTO |
| Healing inteligente | 🔴 CRÍTICO | 6h | ALTO |
| Validação robusta | 🟠 ALTO | 5h | MÉDIO |
| Observabilidade | 🟠 ALTO | 8h | BAIXO |
| Proteção (Circuit Breaker) | 🟡 MÉDIO | 4h | BAIXO |
| Testes | 🟡 MÉDIO | 10h | BAIXO |

**Total estimado:** 37 horas (4-5 dias de trabalho)

---

## 6. CONCLUSÃO

As correções propostas resolvem o **sintoma** (exceção não tratada), mas não eliminam a **causa raiz** (falta de seletores robustos e validação).

A implementação de:
1. **Exceções customizadas** (em vez de strings mágicas)
2. **Healing com limite de tentativas** (evita loops infinitos)
3. **Validação multi-camada** (não apenas existência, mas funcionalidade)
4. **Observabilidade estruturada** (detecta padrões de falha)

...transformará o sistema de **frágil e reativo** para **resiliente e produtivo**.

