import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("core.lexical_filter")

class LexicalFilter:
    """
    Filtro de densidade léxica para descartar 'lixo' antes de gastar tokens de IA (PASA v65.0).
    """
    def __init__(self):
        self.junk_patterns = [
            r'^[\W_]+$', # Apenas emojis ou símbolos
            r'^.{0,2}$', # Muito curto (0-2 chars)
            r'também da meta',
            r'instagram lite',
            r'localizações',
            r'campanha 2201',
            r'áudio original',
            r'^seguido\(a\) por',
            r'^curtido por',
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.junk_patterns]

    def is_junk(self, text: str) -> bool:
        if not text: return True
        clean_text = text.strip()
        
        # 1. Checa padrões de Regex
        for pattern in self.compiled_patterns:
            if pattern.search(clean_text):
                return True
        
        # 1.5 Checa se o comentário é composto APENAS de menções a usuários (ex: @usuario)
        # Remove menções e verifica se o que sobra contém alguma letra ou número útil
        text_without_mentions = re.sub(r'@[\w\.]+', '', clean_text).strip()
        if not re.search(r'[\w\d]', text_without_mentions, re.UNICODE):
            return True
        
        # 2. Checa densidade de letras (se não tiver pelo menos uma letra ou número, é lixo)
        if not re.search(r'[\w\d]', clean_text, re.UNICODE):
            return True
            
        return False

    def filter_list(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        initial_count = len(comments)
        filtered = [c for c in comments if not self.is_junk(c.get("texto_bruto", ""))]
        diff = initial_count - len(filtered)
        if diff > 0:
            logger.info(f"♻️ [Lexical] {diff} comentários descartados por baixa qualidade léxica.")
        return filtered

lexical_filter = LexicalFilter()
