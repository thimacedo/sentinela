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
