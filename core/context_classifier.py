# -*- coding: utf-8 -*-
"""
ContextClassifier v1.0 - Detector de Contextos Positivos
Mitigacao de falsos positivos em textos claramente benignos.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger("core.context_classifier")

# Padroes regex para detectar contextos positivos (celebracoes, aniversario, etc.)
POSITIVE_CONTEXT_PATTERNS = [
    # Aniversario / Celebracoes
    r'\bparab[eé]ns\b.*\b(?:anivers[áa]rio|amigo|irm[ãa]o|vida|felicidades?)\b',
    r'\bfeliz\s+(?:anivers[áa]rio|niver|dia|Natal|ano novo|P[áa]scoa)\b',
    r'\bmuitos\s+(?:anos\s+de\s+vida)\b',
    r'\btudo\s+de\s+bom\b',
    r'\b(?:Deus|Jesus)\s+aben[çc]oe\b',
    # Agradecimentos / Apoio
    r'\b(?:obrigad[ao]|agrade[çc]o)\b.*\b(?:Deus|aben[çc]oad[ao]|feliz)\b',
    r'\b(?:for[çc]a|apoio|estamos\s+juntos)\b.*\b(?:amigo|irm[ãa]o)\b',
    # Saudacoes positivas
    r'\b(?:bom\s+dia|boa\s+tarde|boa\s+noite)\b.*\b(?:aben[çc]oad[ao]|lindo|maravilhoso)\b',
    # Emojis de celebracao + texto positivo
    r'^[🎉🎂🎁🙌👏🥳🎊🎈✨🙏❤️💖💕]+.*\b(?:parab[eé]ns|feliz|bom|lindo)\b',
]

_compiled_positive_patterns = [re.compile(p, re.IGNORECASE) for p in POSITIVE_CONTEXT_PATTERNS]

POSITIVE_CONTEXT_KEYWORDS = {
    'aniversario', 'parabens', 'feliz_aniversario', 'niver',
    'felicidades', 'abençoe', 'realizações',
}

# Palavras que, se presentes, invalidam a classificacao de contexto benigno
NEGATIVE_INDICATORS_IN_POSITIVE = {
    'bandido', 'ladrão', 'ladráo', 'corrupto', 'verme', 'lixo',
    'vagabundo', 'idiota', 'imbecil', 'burro', 'morte', 'matar',
    'assassino', 'golpista', 'ditadura', 'fraude', 'crime',
    'odio', 'ódio', 'racista', 'homofobia', 'xenofobia',
    'preconceito', 'discriminação', 'discriminacao',
    'vergonha', 'nojo', 'asqueroso', 'repugnante',
}


class ContextClassifier:
    """
    Detector deterministico de contextos pragmaticos positivos.
    Usado ANTES do LLM para evitar falsos positivos em textos claramente benignos
    (aniversario, parabens, celebracoes, agradecimentos).
    """

    @staticmethod
    def is_positive_context(text: str) -> bool:
        """
        Retorna True se o texto esta em um contexto claramente positivo
        e NAO contem indicadores negativos (ataques).
        
        Heuristicas:
        1. Se ha palavras negativas (insultos, ameacas), retorna False
        2. Se ha padroes positivos + keywords positivas, retorna True
        3. Textos curtos (<=20 palavras) com "parabens" + "amigo" = positivo
        """
        if not text or len(text.strip()) < 3:
            return False

        text_lower = text.lower()

        # 1. Verifica se ha indicadores negativos (ataque) no texto
        for neg in NEGATIVE_INDICATORS_IN_POSITIVE:
            if neg in text_lower:
                return False

        # 2. Verifica padroes regex de contexto positivo
        positive_pattern_matches = 0
        for pattern in _compiled_positive_patterns:
            if pattern.search(text):
                positive_pattern_matches += 1

        # 3. Verifica presenca de keywords positivas
        words = set(re.findall(r'\b\w+\b', text_lower))
        keyword_matches = words & POSITIVE_CONTEXT_KEYWORDS

        # 4. Heuristica: 1+ padrao E 1+ keyword, OU 2+ padroes positivos
        if (positive_pattern_matches >= 1 and len(keyword_matches) >= 1) or positive_pattern_matches >= 2:
            logger.debug("[ContextClassifier] Contexto positivo detectado (padrao+keyword)")
            return True

        # 5. Heuristica adicional: texto curto (ate 20 palavras) com "parabens" + "amigo"
        word_count = len(words)
        if word_count <= 20 and 'parabens' in words:
            friend_words = {'amigo', 'irmão', 'irmao', 'parceiro', 'querido', 'querida', 'brother'}
            if words & friend_words:
                logger.debug("[ContextClassifier] Contexto positivo detectado (parabens+amigo)")
                return True

        return False


# Instancia singleton
context_classifier = ContextClassifier()
