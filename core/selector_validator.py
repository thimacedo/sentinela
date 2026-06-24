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
