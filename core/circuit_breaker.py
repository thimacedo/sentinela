"""
PASA v49 - Circuit Breaker
Impede loops infinitos em falhas de API (Rate Limit, Auth, Server Error).
"""
import time
import logging
from typing import Dict

logger = logging.getLogger("CircuitBreaker")

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures: Dict[str, int] = {}
        self.open_until: Dict[str, float] = {}

    def can_execute(self, service_name: str) -> bool:
        """Verifica se o circuito está aberto (bloqueado) para o serviço."""
        if service_name in self.open_until:
            if time.time() < self.open_until[service_name]:
                logger.debug(f"CIRCUITO ABERTO para {service_name}. Bloqueado até {time.ctime(self.open_until[service_name])}")
                return False
            else:
                del self.open_until[service_name]
                self.failures[service_name] = 0
                logger.info(f"🔄 [CB] Circuito HALF-OPEN para {service_name}. Tentando novamente...")
        return True

    def record_success(self, service_name: str):
        """Registra sucesso e reseta contadores."""
        if service_name in self.failures:
            self.failures.pop(service_name, None)
            self.open_until.pop(service_name, None)
            logger.info(f"✅ [CB] Circuito FECHADO para {service_name}. Operação normal.")

    def record_failure(self, service_name: str, status_code: int = None):
        """Registra falha e abre o circuito se o limite for atingido."""
        self.failures[service_name] = self.failures.get(service_name, 0) + 1
        count = self.failures[service_name]

        # Falhas fatais (Auth) abrem o circuito por 1 hora
        if status_code in [401, 403]:
            logger.error(f"[CB] Falha FATAL ({status_code}) em {service_name}. Circuito ABERTO por 1 hora.")
            self.open_until[service_name] = time.time() + 3600
            return

        # Falhas de Rate Limit ou indisponibilidade temporária abrem por 5 minutos
        if status_code in [429, 503]:
            cooldown = 300
            logger.warning(f"[CB] {service_name} indisponível ({status_code}). Circuito ABERTO por {cooldown}s.")
            self.open_until[service_name] = time.time() + cooldown
            return

        # Outras falhas acumulam
        if count >= self.failure_threshold:
            logger.warning(f"[CB] {service_name} falhou {count}x seguidas. Circuito ABERTO por {self.cooldown_seconds}s.")
            self.open_until[service_name] = time.time() + self.cooldown_seconds

# --- Instâncias Globais dos Circuit Breakers ---

# Para os serviços de Inteligência Artificial
ai_circuit_breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=300)

# Para o serviço de Scraping da Zyte
zyte_circuit_breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=600) # 10 min de cooldown

# Para o serviço de Banco de Dados (Supabase)
db_circuit_breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=60)
