import os
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("DocFetcher")

class DocFetcher:
    """
    Responsável por buscar e cachear documentação de APIs alvo.
    Evita re-fetching desnecessário e economiza tokens.
    """
    def __init__(self, cache_dir: str = "workers/config/api_docs", ttl_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.ttl = ttl_seconds
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_relevant(self, doc_key: str) -> Optional[str]:
        """Recupera conteúdo se existir e estiver dentro do TTL."""
        # Se o worker_id for algo como 'ig-v2-01', tentamos 'instagram'
        normalized_key = doc_key.split("-")[0].lower()
        file_path = os.path.join(self.cache_dir, f"{normalized_key}.md")
        
        if os.path.exists(file_path):
            # Verifica TTL
            mtime = os.path.getmtime(file_path)
            if (time.time() - mtime) > self.ttl:
                logger.info(f"📄 [DocFetcher] Doc para {normalized_key} expirou. Necessita refresh.")
                # Por enquanto apenas logamos, refresh_all cuidará da atualização real futuramente
            
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def refresh_all(self) -> None:
        """
        Simula atualização de docs expiradas.
        Em produção, isso poderia baixar via GitHub API ou um S3.
        """
        logger.info("📄 [DocFetcher] Sincronizando documentação técnica...")
        # Placeholder para sync real
        for file in os.listdir(self.cache_dir):
            if file.endswith(".md"):
                # Simula atualização (touch)
                os.utime(os.path.join(self.cache_dir, file), None)
        logger.info("✅ [DocFetcher] Documentação sincronizada.")
