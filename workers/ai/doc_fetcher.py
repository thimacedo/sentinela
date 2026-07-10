import os
import time
import logging
import httpx
from typing import Dict, Optional

logger = logging.getLogger("DocFetcher")

class DocFetcher:
    """
    Responsável por buscar e cachear documentação de APIs alvo.
    Evita re-fetching desnecessário e economiza tokens.
    """
    def __init__(self, cache_dir: str = "workers/config/api_docs", ttl_seconds: int = 86400):
        self.cache_dir = cache_dir
        self.ttl = ttl_seconds
        # URL corrigida para o repositório oficial de documentação do Sentinela
        self.remote_url = os.getenv("REMOTE_DOCS_URL", "https://raw.githubusercontent.com/thimacedo/sentinela/main/workers/config/api_docs")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_relevant(self, doc_key: str) -> Optional[str]:
        """Recupera conteúdo se existir e estiver dentro do TTL."""
        # Se o worker_id for algo como 'ig-v2-01', tentamos 'instagram'
        normalized_key = doc_key.split("-")[0].lower()
        if "instagram" in normalized_key or "ig" == normalized_key:
            normalized_key = "instagram"
            
        file_path = os.path.join(self.cache_dir, f"{normalized_key}.md")
        
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            if (time.time() - mtime) > self.ttl:
                logger.info(f"📄 [DocFetcher] Doc para {normalized_key} expirou. Tentando atualização em background...")
                # Em um sistema real, poderíamos disparar o refresh aqui. 
                # Por simplicidade, refresh_all() deve ser chamado pelo orquestrador.
            
            base_real = os.path.realpath(self.cache_dir)
            target_real = os.path.realpath(file_path)
            if os.path.commonpath([base_real, target_real]) != base_real:
                raise Exception("Invalid file path")
            with open(target_real, "r", encoding="utf-8") as f:
                return f.read()
        return None

    async def refresh_all(self) -> None:
        """
        Sincroniza documentação técnica do repositório remoto.
        """
        logger.info("📄 [DocFetcher] Sincronizando documentação técnica...")
        
        targets = ["instagram.md", "meta_ads.md", "pasa_protocol.md"]
        async with httpx.AsyncClient(timeout=10.0) as client:
            for target in targets:
                url = f"{self.remote_url}/{target}"
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        file_path = os.path.join(self.cache_dir, target)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(response.text)
                        logger.info(f"✅ [DocFetcher] Atualizado: {target}")
                    else:
                        logger.warning(f"⚠️ [DocFetcher] Falha ao baixar {target} ({response.status_code})")
                except Exception as e:
                    logger.error(f"❌ [DocFetcher] Erro ao sincronizar {target}: {e}")
                    
        logger.info("✅ [DocFetcher] Ciclo de sincronização finalizado.")
