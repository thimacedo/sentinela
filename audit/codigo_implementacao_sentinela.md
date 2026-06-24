# Código Corrigido e Melhorado - Sentinela v50.1
## Implementação Pronta para Produção

---

## ARQUIVO 1: `core/exceptions.py` (NOVO)

```python
"""
Hierarquia de exceções customizadas para o Sentinela.
Substitui a estratégia de string matching por type-safe handling.
"""

from typing import Optional
from datetime import datetime


class ScrapeException(Exception):
    """Exceção base para o subsistema de scraping"""
    
    def __init__(self, message: str, context: dict = None):
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)


class ScrapeControlSignal(ScrapeException):
    """
    Base para sinais de controle de fluxo (não são erros de verdade).
    Não devem ser tratados como falhas que afetam métricas ou circuit breaker.
    """
    pass


class DOMHealerRestartSignal(ScrapeControlSignal):
    """
    Sinal emitido quando DOM Healer completou com sucesso
    e o browser precisa ser reiniciado para continuar.
    
    NÃO conta como falha.
    NÃO afeta circuit breaker.
    """
    
    def __init__(
        self,
        reason: str = "dom_healer_completed",
        username: str = None,
        shortcode: str = None,
        selector_cache_key: str = None,
        healing_attempts: int = 0,
        healing_duration_s: float = 0.0,
    ):
        self.reason = reason
        self.username = username
        self.shortcode = shortcode
        self.selector_cache_key = selector_cache_key
        self.healing_attempts = healing_attempts
        self.healing_duration_s = healing_duration_s
        
        context = {
            "reason": reason,
            "username": username,
            "shortcode": shortcode,
            "selector_cache_key": selector_cache_key,
            "healing_attempts": healing_attempts,
            "healing_duration_s": healing_duration_s,
        }
        
        super().__init__(
            f"DOMHealer restart signal: {reason} "
            f"(user={username}, attempts={healing_attempts})",
            context=context
        )


class SessionExpiredError(ScrapeControlSignal):
    """
    Detectado login wall, sessão expirada ou redirecionamento para login.
    
    Semântica: A sessão de browser/cookies já não é válida.
    Ação: Fechar browser, renovar cookies, tentar novamente.
    """
    
    def __init__(self, username: str, page_url: str, reason: str = "unknown"):
        self.username = username
        self.page_url = page_url
        self.reason = reason  # "login_wall", "session_expired", "challenge", etc.
        
        context = {
            "username": username,
            "page_url": page_url,
            "reason": reason,
        }
        
        super().__init__(
            f"Session expired for @{username}: {reason} at {page_url}",
            context=context
        )


class ChallengeRequiredError(ScrapeControlSignal):
    """
    Instagram Challenge detectada (Soft Block - checkpoint de segurança).
    Requer ação humana ou espera.
    """
    
    def __init__(
        self,
        username: str,
        challenge_type: str = "unknown",
        page_url: str = None,
    ):
        self.username = username
        self.challenge_type = challenge_type
        self.page_url = page_url
        
        context = {
            "username": username,
            "challenge_type": challenge_type,
            "page_url": page_url,
        }
        
        super().__init__(
            f"Challenge required for @{username}: {challenge_type}",
            context=context
        )


class SelectorValidationError(ScrapeException):
    """Seletor CSS proposto é inválido ou não funciona"""
    
    def __init__(
        self,
        selector: str,
        reason: str,
        elements_found: int = 0,
        expected_min: int = 1,
    ):
        self.selector = selector
        self.reason = reason  # "no_elements", "too_many", "empty_content", etc.
        self.elements_found = elements_found
        self.expected_min = expected_min
        
        context = {
            "selector": selector,
            "reason": reason,
            "elements_found": elements_found,
            "expected_min": expected_min,
        }
        
        super().__init__(
            f"Selector validation failed: {reason} "
            f"({elements_found} elements, expected >={expected_min})",
            context=context
        )


class DOMHealingFailedError(ScrapeException):
    """DOM Healing completou todas as tentativas sem sucesso"""
    
    def __init__(
        self,
        username: str,
        reason: str,
        attempts: int,
        last_selector: str = None,
    ):
        self.username = username
        self.reason = reason  # "max_attempts", "repeated_selector", etc.
        self.attempts = attempts
        self.last_selector = last_selector
        
        context = {
            "username": username,
            "reason": reason,
            "attempts": attempts,
            "last_selector": last_selector,
        }
        
        super().__init__(
            f"DOM Healing failed for @{username}: {reason} "
            f"(tried {attempts} times)",
            context=context
        )


class InvalidTargetError(ScrapeException):
    """Perfil alvo não existe, é privado ou bloqueado"""
    
    def __init__(self, username: str, reason: str):
        self.username = username
        self.reason = reason  # "not_found", "private", "blocked", etc.
        
        context = {
            "username": username,
            "reason": reason,
        }
        
        super().__init__(
            f"Invalid target @{username}: {reason}",
            context=context
        )


class SessionBlockedError(ScrapeException):
    """Todas as sessões estão em cooldown ou bloqueadas"""
    
    def __init__(self, blocked_count: int, total_count: int):
        self.blocked_count = blocked_count
        self.total_count = total_count
        
        context = {
            "blocked_count": blocked_count,
            "total_count": total_count,
        }
        
        super().__init__(
            f"All sessions blocked: {blocked_count}/{total_count}",
            context=context
        )


class AIServiceError(ScrapeException):
    """Erro na comunicação com serviço de IA (Gemini, etc.)"""
    
    def __init__(self, service: str, reason: str, original_error: str = None):
        self.service = service
        self.reason = reason
        self.original_error = original_error
        
        context = {
            "service": service,
            "reason": reason,
            "original_error": original_error,
        }
        
        super().__init__(
            f"AI Service error ({service}): {reason}",
            context=context
        )
```

---

## ARQUIVO 2: `core/scrape_metrics.py` (NOVO)

```python
"""
Coleta e persistência de métricas estruturadas de scraping.
Habilitação observabilidade para diagnóstico e otimização.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapeMetrics:
    """Métricas estruturadas de um ciclo de scrape"""
    
    # Identificação
    username: str
    worker_id: str
    cycle_number: int
    
    # Timestamps
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Durações
    total_duration_s: float = 0.0
    healing_total_duration_s: float = 0.0
    extraction_duration_s: float = 0.0
    
    # Contadores de extração
    posts_found: int = 0
    posts_processed: int = 0
    comments_collected: int = 0
    
    # Healing
    healing_attempts: int = 0
    healing_successes: int = 0
    healing_failures: int = 0
    healing_repeated_selectors: int = 0
    
    # Seletores
    selectors_used: List[str] = field(default_factory=list)
    selectors_from_cache: int = 0
    selectors_from_ai: int = 0
    
    # Validação
    selectors_validated_successfully: int = 0
    selectors_validation_failed: int = 0
    
    # Resultado
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    is_control_signal: bool = False  # True se foi healer restart, etc.
    
    def end_cycle(self, success: bool, error_code: str = None, error_msg: str = None):
        """Marca o fim do ciclo de extração"""
        self.end_time = datetime.now()
        self.total_duration_s = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.error_code = error_code
        self.error_message = error_msg
    
    def to_dict(self) -> dict:
        """Converte para dicionário com timestamps serializáveis"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        return data
    
    def to_json(self, pretty: bool = True) -> str:
        """Converte para JSON"""
        data = self.to_dict()
        indent = 2 if pretty else None
        return json.dumps(data, ensure_ascii=False, indent=indent)


class MetricsCollector:
    """
    Coleta métricas durante ciclo de scrape e persiste em disco.
    """
    
    def __init__(self, metrics_dir: Path = None):
        self.metrics_dir = metrics_dir or Path("logs/metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_metrics: Optional[ScrapeMetrics] = None
        self.logger = logger
    
    def start_cycle(
        self,
        username: str,
        worker_id: str,
        cycle_number: int,
    ) -> ScrapeMetrics:
        """Inicia coleta de métricas para novo ciclo"""
        self.current_metrics = ScrapeMetrics(
            username=username,
            worker_id=worker_id,
            cycle_number=cycle_number,
            start_time=datetime.now(),
        )
        return self.current_metrics
    
    def record_healing_attempt(
        self,
        success: bool,
        duration_s: float,
        selector: str,
    ):
        """Registra tentativa de healing"""
        if not self.current_metrics:
            return
        
        self.current_metrics.healing_attempts += 1
        self.current_metrics.healing_total_duration_s += duration_s
        
        if success:
            self.current_metrics.healing_successes += 1
        else:
            self.current_metrics.healing_failures += 1
        
        if selector not in self.current_metrics.selectors_used:
            self.current_metrics.selectors_used.append(selector)
    
    def record_repeated_selector_detected(self):
        """Registra quando IA propõe seletor repetido"""
        if self.current_metrics:
            self.current_metrics.healing_repeated_selectors += 1
    
    def record_selector_validation(self, success: bool):
        """Registra resultado de validação de seletor"""
        if not self.current_metrics:
            return
        
        if success:
            self.current_metrics.selectors_validated_successfully += 1
        else:
            self.current_metrics.selectors_validation_failed += 1
    
    def record_selector_source(self, from_cache: bool):
        """Registra origem do seletor (cache ou IA)"""
        if not self.current_metrics:
            return
        
        if from_cache:
            self.current_metrics.selectors_from_cache += 1
        else:
            self.current_metrics.selectors_from_ai += 1
    
    def record_extraction_results(
        self,
        posts_found: int,
        posts_processed: int,
        comments_collected: int,
        extraction_duration_s: float,
    ):
        """Registra resultados da extração"""
        if not self.current_metrics:
            return
        
        self.current_metrics.posts_found = posts_found
        self.current_metrics.posts_processed = posts_processed
        self.current_metrics.comments_collected = comments_collected
        self.current_metrics.extraction_duration_s = extraction_duration_s
    
    def end_cycle(
        self,
        success: bool,
        error_code: str = None,
        error_message: str = None,
    ) -> Optional[ScrapeMetrics]:
        """Finaliza coleta e persiste métricas"""
        if not self.current_metrics:
            return None
        
        self.current_metrics.end_cycle(success, error_code, error_message)
        
        # Persiste em disco
        filename = self._get_metrics_filename()
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.current_metrics.to_json())
            
            self.logger.debug(f"📊 Métricas persistidas: {filename}")
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao persistir métricas: {e}")
        
        metrics = self.current_metrics
        self.current_metrics = None
        return metrics
    
    def _get_metrics_filename(self) -> Path:
        """Gera nome de arquivo para as métricas"""
        if not self.current_metrics:
            raise ValueError("Nenhum ciclo ativo")
        
        timestamp = self.current_metrics.start_time.strftime("%Y%m%d_%H%M%S")
        username = self.current_metrics.username.replace("@", "")
        worker_id = self.current_metrics.worker_id.replace(":", "_")
        
        filename = f"{timestamp}_{username}_{worker_id}_c{self.current_metrics.cycle_number}.json"
        return self.metrics_dir / filename


class MetricsAnalyzer:
    """Analisa métricas persistidas para diagnóstico e alertas"""
    
    def __init__(self, metrics_dir: Path = None):
        self.metrics_dir = metrics_dir or Path("logs/metrics")
        self.logger = logger
    
    def get_health_status(self, window_size: int = 20) -> dict:
        """
        Analisa últimas N execuções e retorna status de saúde.
        """
        metrics = self._load_recent_metrics(window_size)
        
        if len(metrics) < 5:
            return {"status": "insufficient_data", "metrics_count": len(metrics)}
        
        failures = sum(1 for m in metrics if not m.get("success"))
        failure_rate = failures / len(metrics)
        
        avg_comments = sum(m.get("comments_collected", 0) for m in metrics) / len(metrics)
        
        avg_healing_attempts = sum(
            m.get("healing_attempts", 0) for m in metrics
        ) / len(metrics)
        
        health_status = "healthy"
        if failure_rate > 0.7:
            health_status = "critical"
        elif failure_rate > 0.4:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "metrics_analyzed": len(metrics),
            "failure_rate": round(failure_rate, 2),
            "avg_comments_collected": round(avg_comments, 2),
            "avg_healing_attempts": round(avg_healing_attempts, 2),
            "critical_if_failure_rate_above": 0.7,
        }
    
    def _load_recent_metrics(self, count: int = 20) -> List[dict]:
        """Carrega últimas N métricas persistidas"""
        if not self.metrics_dir.exists():
            return []
        
        files = sorted(
            self.metrics_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:count]
        
        metrics = []
        for filepath in files:
            try:
                with open(filepath) as f:
                    metrics.append(json.load(f))
            except Exception as e:
                self.logger.warning(f"Erro lendo {filepath}: {e}")
        
        return metrics
```

---

## ARQUIVO 3: `core/healing_attempt_tracker.py` (NOVO)

```python
"""
Rastreamento de tentativas de healing para evitar loops infinitos.
"""

from typing import List, Tuple
from collections import deque
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HealingAttemptTracker:
    """
    Monitora tentativas de DOM Healing dentro de um ciclo de scrape.
    Previne loops infinitos e detecta padrões de seletores repetidos.
    """
    
    def __init__(self, max_attempts: int = 2, max_cache_size: int = 5):
        """
        Args:
            max_attempts: Máximo de tentativas de healing por ciclo
            max_cache_size: Máximo de seletores anteriores a lembrar
        """
        self.max_attempts = max_attempts
        self.max_cache_size = max_cache_size
        
        self.healing_attempts = 0
        self.proposed_selectors: deque = deque(maxlen=max_cache_size)
        self.attempt_history: List[dict] = []
    
    def can_attempt_healing(self) -> bool:
        """Verifica se ainda pode fazer tentativa de healing"""
        if self.healing_attempts >= self.max_attempts:
            logger.warning(
                f"❌ Limite de healing atingido: "
                f"{self.healing_attempts}/{self.max_attempts}"
            )
            return False
        return True
    
    def has_repeated_selector(self, new_selector: str) -> bool:
        """Detecta se seletor já foi proposto antes"""
        return new_selector in self.proposed_selectors
    
    def record_attempt(
        self,
        selector: str,
        success: bool,
        duration_s: float,
        validation_result: dict = None,
    ):
        """
        Registra uma tentativa de healing.
        
        Args:
            selector: Seletor CSS proposto
            success: Se validação foi bem-sucedida
            duration_s: Duração da tentativa
            validation_result: Resultado detalhado da validação
        """
        self.healing_attempts += 1
        self.proposed_selectors.append(selector)
        
        record = {
            "attempt_number": self.healing_attempts,
            "timestamp": datetime.now().isoformat(),
            "selector": selector,
            "success": success,
            "duration_s": duration_s,
            "validation_result": validation_result,
        }
        
        self.attempt_history.append(record)
        
        logger.info(
            f"🔧 Healing attempt {self.healing_attempts}/{self.max_attempts}: "
            f"{'✅' if success else '❌'} {selector[:50]}..."
        )
    
    def get_summary(self) -> dict:
        """Retorna resumo das tentativas"""
        return {
            "total_attempts": self.healing_attempts,
            "max_attempts": self.max_attempts,
            "can_retry": self.can_attempt_healing(),
            "selectors_proposed": list(self.proposed_selectors),
            "unique_selectors": len(set(self.proposed_selectors)),
            "history": self.attempt_history,
        }
    
    def reset(self):
        """Reseta tracker para novo ciclo"""
        self.healing_attempts = 0
        self.proposed_selectors.clear()
        self.attempt_history.clear()
```

---

## ARQUIVO 4: `core/selector_validator.py` (NOVO)

```python
"""
Validação multi-camada de seletores CSS propostos.
"""

from typing import Optional
import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class SelectorValidator:
    """Valida seletores antes de usar em extração"""
    
    def __init__(
        self,
        min_elements: int = 1,
        max_elements: int = 500,
        sample_size: int = 10,
    ):
        self.min_elements = min_elements
        self.max_elements = max_elements
        self.sample_size = sample_size
    
    async def validate_functional(
        self,
        page: Page,
        selector: str,
        selector_name: str,
    ) -> dict:
        """
        Validação multi-camada: Sintaxe → Existência → Conteúdo → Visibilidade
        """
        
        # Validação 1: Sintaxe CSS
        if not self._is_valid_syntax(selector):
            return {
                "valid": False,
                "stage": "syntax",
                "reason": "invalid_css_syntax",
                "selector": selector,
            }
        
        # Validação 2: Elementos encontrados
        try:
            elements = await page.query_selector_all(selector)
        except Exception as e:
            return {
                "valid": False,
                "stage": "query",
                "reason": f"query_failed: {type(e).__name__}",
                "error": str(e),
                "selector": selector,
            }
        
        element_count = len(elements) if elements else 0
        
        if element_count < self.min_elements:
            return {
                "valid": False,
                "stage": "existence",
                "reason": "no_elements_found",
                "element_count": element_count,
                "min_required": self.min_elements,
                "selector": selector,
            }
        
        if element_count > self.max_elements:
            return {
                "valid": False,
                "stage": "existence",
                "reason": "too_many_elements",
                "element_count": element_count,
                "max_allowed": self.max_elements,
                "selector": selector,
            }
        
        # Validação 3: Conteúdo (amostra)
        empty_count = 0
        for i, elem in enumerate(elements[:self.sample_size]):
            try:
                text = (await elem.text_content()).strip()
                if not text:
                    empty_count += 1
            except:
                pass
        
        sample_size_actual = min(self.sample_size, element_count)
        if empty_count == sample_size_actual:
            return {
                "valid": False,
                "stage": "content",
                "reason": "all_elements_empty",
                "empty_count": empty_count,
                "sample_size": sample_size_actual,
                "selector": selector,
            }
        
        # Validação 4: Visibilidade (amostra)
        visible_count = 0
        for i, elem in enumerate(elements[:5]):
            try:
                if await elem.is_visible():
                    visible_count += 1
            except:
                pass
        
        if visible_count == 0 and element_count > 0:
            logger.warning(
                f"⚠️ Seletor encontrou elementos mas nenhum é visível: {selector}"
            )
            # Não falha, apenas aviso
        
        # ✅ Passou em todas as validações
        return {
            "valid": True,
            "stage": "all_passed",
            "element_count": element_count,
            "visible_count": visible_count,
            "empty_count": empty_count,
            "sample_size": sample_size_actual,
            "selector": selector,
        }
    
    def _is_valid_syntax(self, selector: str) -> bool:
        """Validação básica de sintaxe CSS"""
        if not selector or not isinstance(selector, str):
            return False
        
        # Rejeita seletores obviamente inválidos
        if selector.startswith("(") or selector.startswith(")"):
            return False
        
        if selector.endswith("(") or selector.endswith(")"):
            return False
        
        try:
            # Tenta compilar como seletor (simples check)
            selector.count("[")  # Básico, não é perfeito
            selector.count("]")
            return True
        except:
            return False
```

---

## ARQUIVO 5: `core/login_wall_detector.py` (NOVO)

```python
"""
Detecção robusta de Login Walls, Sessions Expiradas e Challenges.
"""

import re
import logging
from typing import Tuple
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class LoginWallDetector:
    """Detecta com precisão se página é um muro de login"""
    
    # URLs que indicam login wall
    LOGIN_URL_PATTERNS = [
        r"accounts/login",
        r"accounts/account_recovery",
        r"^.*instagram\.com/accounts/",
        r"/login/?$",
        r"/signin/?$",
    ]
    
    # Títulos característicos
    LOGIN_TITLES = [
        "log in",
        "entrar",
        "login required",
        "instagram",  # Página de login fica só com "Instagram"
    ]
    
    # Textos de conteúdo que indicam login wall
    LOGIN_CONTENT_INDICATORS = [
        "log in to instagram",
        "faça login para curtir",
        "faça login para ver mais",
        "enter your login details",
        "forgot password",
        "didn't get the code?",
        "create new account",
        "sign up",
    ]
    
    CHALLENGE_INDICATORS = [
        "challenge",
        "suspicious login attempt",
        "tentativa de login suspeita",
        "verify your identity",
        "prove you're not a bot",
        "prove that you own the account",
    ]
    
    def __init__(self):
        self.logger = logger
    
    async def detect_login_wall(self, page: Page) -> Tuple[bool, dict]:
        """
        Detecta login wall com método robusto.
        
        Retorna:
            (is_login_wall, details_dict)
        """
        try:
            page_url = page.url.lower()
            page_title = (await page.title()).lower()
            page_content = (await page.content())[:10000].lower()
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao inspecionar página: {e}")
            return False, {"error": str(e)}
        
        details = {
            "url": page_url,
            "title": page_title,
            "is_login_wall": False,
            "matched_patterns": [],
        }
        
        # Check 1: URL patterns
        for pattern in self.LOGIN_URL_PATTERNS:
            if re.search(pattern, page_url, re.IGNORECASE):
                details["matched_patterns"].append(f"url_pattern:{pattern}")
                details["is_login_wall"] = True
                break
        
        # Check 2: Title
        for title_keyword in self.LOGIN_TITLES:
            if title_keyword in page_title:
                # Mas não é suficiente sozinho (muitas páginas têm "instagram" no título)
                if title_keyword != "instagram":
                    details["matched_patterns"].append(f"title:{title_keyword}")
                    details["is_login_wall"] = True
                    break
        
        # Check 3: Conteúdo (mais confiável)
        login_content_matches = sum(
            1 for indicator in self.LOGIN_CONTENT_INDICATORS
            if indicator in page_content
        )
        
        if login_content_matches >= 2:  # Pelo menos 2 indicadores
            details["matched_patterns"].append(f"content:{login_content_matches}_indicators")
            details["is_login_wall"] = True
        
        return details["is_login_wall"], details
    
    async def detect_challenge(self, page: Page) -> Tuple[bool, dict]:
        """Detecta Instagram Challenge / Soft Block"""
        try:
            page_url = page.url.lower()
            page_content = (await page.content())[:10000].lower()
        except:
            return False, {}
        
        details = {
            "url": page_url,
            "is_challenge": False,
            "challenge_type": None,
            "matched_indicators": [],
        }
        
        # Check 1: URL
        if "challenge" in page_url:
            details["is_challenge"] = True
            details["challenge_type"] = "url_based"
            details["matched_indicators"].append("challenge_in_url")
        
        # Check 2: Conteúdo
        for indicator in self.CHALLENGE_INDICATORS:
            if indicator in page_content:
                details["is_challenge"] = True
                details["challenge_type"] = "content_based"
                details["matched_indicators"].append(indicator)
                break
        
        return details["is_challenge"], details
    
    async def diagnose_page_state(self, page: Page) -> dict:
        """Diagnóstico completo do estado da página"""
        is_login, login_details = await self.detect_login_wall(page)
        is_challenge, challenge_details = await self.detect_challenge(page)
        
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "url": page.url,
            "is_login_wall": is_login,
            "login_details": login_details,
            "is_challenge": is_challenge,
            "challenge_details": challenge_details,
            "state": self._determine_state(is_login, is_challenge),
        }
        
        return diagnosis
    
    def _determine_state(self, is_login: bool, is_challenge: bool) -> str:
        """Determina estado geral da página"""
        if is_login:
            return "login_wall"
        if is_challenge:
            return "challenge_required"
        return "normal"

# Uso
from datetime import datetime
```

---

## ARQUIVO 6: Uso Integrado em `core/instagram_scraper_v2.py`

Este é um exemplo de como usar as novas exceções e validators:

```python
# No início do arquivo
from core.exceptions import (
    DOMHealerRestartSignal,
    SessionExpiredError,
    ChallengeRequiredError,
    SelectorValidationError,
    DOMHealingFailedError,
)
from core.healing_attempt_tracker import HealingAttemptTracker
from core.selector_validator import SelectorValidator
from core.login_wall_detector import LoginWallDetector
from core.scrape_metrics import MetricsCollector

# Inicialização
self.healing_tracker = HealingAttemptTracker(max_attempts=2)
self.validator = SelectorValidator()
self.detector = LoginWallDetector()
self.metrics = MetricsCollector()

# ... em scrape_profile()

# Iniciar coleta de métricas
metrics = self.metrics.start_cycle(
    username=username,
    worker_id=self.worker_id,
    cycle_number=self.cycle_count,
)

try:
    # ... lógica de scraping ...
    
    # Quando ativa o healing
    if consecutive_zero_comments >= 3:
        # Diagnóstico pré-healing
        diagnosis = await self.detector.diagnose_page_state(page)
        
        if diagnosis["is_login_wall"]:
            raise SessionExpiredError(
                username=username,
                page_url=page.url,
                reason="login_wall_detected"
            )
        
        if diagnosis["is_challenge"]:
            raise ChallengeRequiredError(
                username=username,
                challenge_type=diagnosis["challenge_details"]["challenge_type"],
                page_url=page.url,
            )
        
        # Se chegou aqui, é realmente problema de seletor
        if not self.healing_tracker.can_attempt_healing():
            raise DOMHealingFailedError(
                username=username,
                reason="max_attempts_exceeded",
                attempts=self.healing_tracker.healing_attempts,
            )
        
        # Tenta healing
        start_heal = time.time()
        heal_result = await healer.heal_selectors(...)
        heal_duration = time.time() - start_heal
        
        if heal_result.get("success"):
            new_selector = heal_result.get("selector")
            
            # Valida o seletor antes de usar
            validation = await self.validator.validate_functional(
                page,
                new_selector,
                "comment_container"
            )
            
            if not validation["valid"]:
                raise SelectorValidationError(
                    selector=new_selector,
                    reason=validation["reason"],
                    elements_found=validation.get("element_count", 0),
                )
            
            # Registra sucesso
            self.healing_tracker.record_attempt(
                new_selector,
                success=True,
                duration_s=heal_duration,
                validation_result=validation,
            )
            
            self.metrics.record_healing_attempt(True, heal_duration, new_selector)
            consecutive_zero_comments = 0
            continue
        
        else:
            self.healing_tracker.record_attempt(
                new_selector,
                success=False,
                duration_s=heal_duration,
            )
            self.metrics.record_healing_attempt(False, heal_duration, "")
            
            raise DOMHealerRestartSignal(
                reason="healing_validation_failed",
                username=username,
                shortcode=shortcode,
                healing_attempts=self.healing_tracker.healing_attempts,
                healing_duration_s=heal_duration,
            )

except DOMHealerRestartSignal as signal:
    self.logger.info(f"🔄 {signal.message}")
    self.metrics.record_healing_attempt(
        True,
        signal.healing_duration_s,
        "(restart_signal)"
    )
    # Não incrementa penalidades, não afeta circuit breaker
    raise

except SessionExpiredError as e:
    self.logger.error(f"🔐 {e.message}")
    self.metrics.end_cycle(False, "session_expired", e.message)
    raise

except ChallengeRequiredError as e:
    self.logger.error(f"⛔ {e.message}")
    self.metrics.end_cycle(False, "challenge_required", e.message)
    raise

except Exception as e:
    self.logger.error(f"❌ Erro: {e}")
    self.metrics.end_cycle(False, type(e).__name__, str(e))
    raise

# Final bem-sucedido
self.metrics.record_extraction_results(
    posts_found=len(posts),
    posts_processed=posts_processed,
    comments_collected=comments_collected,
    extraction_duration_s=time.time() - start_time,
)
self.metrics.end_cycle(True)
```

---

## Checklist de Aplicação

- [ ] Criar `core/exceptions.py` com hierarquia
- [ ] Criar `core/scrape_metrics.py` com coleta
- [ ] Criar `core/healing_attempt_tracker.py`
- [ ] Criar `core/selector_validator.py`
- [ ] Criar `core/login_wall_detector.py`
- [ ] Atualizar `instagram_scraper_v2.py` para usar novas exceções
- [ ] Atualizar `worker_adapter.py` para capturar novas exceções
- [ ] Atualizar `wk_coleta_instagram.py` para diferenciação de erros
- [ ] Adicionar testes unitários
- [ ] Executar testes de integração
- [ ] Deploy em staging
- [ ] Monitor métricas
- [ ] Deploy em produção

