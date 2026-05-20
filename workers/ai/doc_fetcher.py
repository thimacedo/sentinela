import os
import time
from typing import Dict, Optional

class DocFetcher:
    """
    Responsável por buscar e cachear documentação de APIs alvo.
    Evita re-fetching desnecessário e economiza tokens.
    """
    def __init__(self, cache_dir: str = "workers/config/api_docs"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_relevant(self, doc_key: str) -> Optional[str]:
        file_path = os.path.join(self.cache_dir, f"{doc_key}.md")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def refresh_all(self) -> None:
        """Simula atualização de docs expiradas."""
        # Implementação futura de sync remoto
        pass
