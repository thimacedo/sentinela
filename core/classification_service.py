import json
import logging
import time
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("sentinela-classification")

# --- Matriz Taxonômica PASA v42 (MTAD) ---
VALID_CATEGORIES = [
    "ODIO_IDENTITARIO",
    "VIOLENCIA_GENERO",
    "AMEACA",
    "ATAQUE_INSTITUCIONAL",
    "RIGOR_CRIMINAL",
    "INSULTO_AD_HOMINEM",
    "NEUTRO"
]

class PasaClassificationService:
    """
    Serviço Centralizado de Auditoria Analítica PASA v42.
    Gerencia prompts baseados no MCA v2.0, parsing e auditoria CCF.
    """

    VERSION = "42.1.0"

    def __init__(self):
        self.manual_path = "docs/classification/MANUAL_CLASSIFICACAO_ANALITICA_v2.md"
        self.forbidden_terms = {
            re.compile(r'\bperícia(?:s)?\b', re.IGNORECASE): "análise / relatório",
            re.compile(r'\bperito(?:s|as|a)?\b', re.IGNORECASE): "analista",
            re.compile(r'\bpericial\b', re.IGNORECASE): "analítica",
            re.compile(r'\bforense(?:s)?\b', re.IGNORECASE): "estratégica",
            re.compile(r'\bprova(?:s)?\b', re.IGNORECASE): "indícios situacionais",
            re.compile(r'\blaudo(?:s)?\b', re.IGNORECASE): "dossiê"
        }

    def _load_manual(self) -> str:
        """Carrega o manual MCA v2.0 do disco."""
        try:
            # Tenta caminhos relativos diferentes dependendo de onde o processo é iniciado
            paths = [self.manual_path, f"../{self.manual_path}", f"E:/Projetos/sentinela-democratica/{self.manual_path}"]
            for p in paths:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        return f.read()
            return "AVISO: Manual MCA v2.0 não encontrado. Use a taxonomia MTAD e o CCF Framework."
        except Exception as e:
            logger.error(f"Erro ao carregar manual: {e}")
            return "ERRO ao carregar Manual MCA v2.0."

    def get_system_prompt(self) -> str:
        """Retorna o System Prompt baseado no MCA v2.0 definitivo."""
        manual = self._load_manual()
        return f"""
Você é um Analista de Linguística Analítica do Sistema Sentinela Democrática.
Siga RIGOROSAMENTE o manual abaixo para classificar os comentários.

{manual}

IMPORTANTE: Toda resposta DEVE ser um JSON válido contendo obrigatoriamente as chaves:
- "is_hate" (boolean)
- "categoria_ia" (string, usar "NEUTRO" se não houver risco)
- "confidence_score" (int de 0 a 100)
- "evidence_extracted" (string com o trecho exato que justifica a classificação, ou vazio)
"""

    def parse_verdict(self, raw_text: str) -> Dict[str, Any]:
        """Parser resiliente para respostas de IA (MCA v2.0 Pattern)."""
        try:
            # Limpeza de markdown
            clean = raw_text.strip()
            if "```json" in clean:
                clean = clean.split("```json")[1].split("```")[0]
            elif "```" in clean:
                clean = clean.split("```")[1].split("```")[0]

            clean = clean.strip()
            data = json.loads(clean)

            # Mapeamento do JSON da IA para o Schema do Supabase
            cat = str(data.get("categoria_ia", data.get("category", "NEUTRO"))).upper().strip()
            if cat not in VALID_CATEGORIES:
                cat = "NEUTRO"

            # Determina o rotulo (is_hate)
            rotulo = data.get("rotulo", "not_hate")
            is_hate = True if rotulo == "hate" else False
            if cat != "NEUTRO": 
                is_hate = True # Garantia analítica

            return {
                "id": data.get("id"),
                "category": cat,
                "categoria_ia": cat,
                "is_hate": is_hate,
                "rotulo": "hate" if is_hate else "not_hate",
                "direcao_odio": data.get("direcao_odio"),
                "ccf_density": float(data.get("ccf_density", 0.0)),
                "ccf_sync": float(data.get("ccf_sync", 0.0)),
                "ccf_performativity": float(data.get("ccf_performativity", 0.0)),
                "confidence": float(data.get("confidence_score", data.get("confianca_ia", 0))),
                "confianca_ia": float(data.get("confidence_score", data.get("confianca_ia", 0))),
                "confidence_score": int(data.get("confidence_score", 0)),
                "evidence_extracted": str(data.get("evidence_extracted", data.get("reason", ""))),
                "reason": str(data.get("evidence_extracted", data.get("reason", "Análise PASA v42"))),
                "pasa_version": self.VERSION
            }
        except Exception as e:
            logger.error(f"[Classification] Erro de parsing MCA v2.0: {e}")
            return {
                "categoria_ia": "NEUTRO",
                "is_hate": False,
                "rotulo": "not_hate",
                "confianca_ia": 0.0,
                "reason": f"Erro de parser: {str(e)}"
            }

    def audit_terms(self, text: str) -> Tuple[bool, List[Dict]]:
        """Auditoria terminológica para conformidade jurídica PASA."""
        violations = []
        for pattern, replacement in self.forbidden_terms.items():
            for match in pattern.finditer(text):
                violations.append({
                    'found_term': match.group(),
                    'replacement': replacement
                })
        return len(violations) == 0, violations

    def log_audit(self, text: str, verdict: Dict[str, Any], engine: str, latency: float):
        """Registra o evento de classificação para auditoria futura."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "engine": engine,
            "latency": latency,
            "category": verdict.get("categoria_ia", "NEUTRO"),
            "is_hate": verdict.get("is_hate", False),
            "confidence": verdict.get("confianca_ia", 0.0),
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "reason": verdict.get("reason", ""),
            "pasa_version": verdict.get("pasa_version", self.VERSION)
        }
        logger.info(f"[PASA AUDIT] {engine.upper()} | {verdict.get('categoria_ia', 'NEUTRO')} | {latency:.2f}s | {verdict.get('reason', '')}")
        return log_entry

# Singleton para acesso fácil
classification_service = PasaClassificationService()
