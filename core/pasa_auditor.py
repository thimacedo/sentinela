import re
import asyncio
from typing import List, Dict, Tuple, Any
from core.ai_service import AIService 
from core.classification_service import classification_service

class PASAAuditor:
    """
    Auditor Linguístico e Analítico PASA v16.4.
    Realiza classificação de risco (IA) seguida de auditoria terminológica.
    """
    def __init__(self, ai_service_instance=None):
        if ai_service_instance is None:
            from core.ai_service import ai_service
            self.ai_service = ai_service
        else:
            self.ai_service = ai_service_instance

    async def process(self, text: str, comment_id: str = "N/A") -> Dict[str, Any]:
        """Pipeline completo: Classifica (IA) e Audita (PASA v16.4)."""
        # 1. Classificação via IA (usando AIService refatorado)
        classification = await self.ai_service.classify(text, comment_id=comment_id)
        
        # 2. Auditoria terminológica PASA (centralizada no ClassificationService)
        is_compliant, violations = classification_service.audit_terms(text)
        
        return {
            "text": text,
            "category": classification.get("category"),
            "is_hate": classification.get("is_hate"),
            "classification": classification,
            "is_compliant": is_compliant,
            "violations": violations,
            "pasa_version": classification_service.VERSION
        }

    def audit_text(self, text: str) -> Tuple[bool, List[Dict]]:
        """Proxy para compatibilidade com testes legados."""
        return classification_service.audit_terms(text)
