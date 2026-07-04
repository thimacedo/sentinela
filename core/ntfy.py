# Ntfy Notification Client with MIME Header Encoding
# Arquivo: core/ntfy.py

import logging
import asyncio
import requests
from email.header import Header
from typing import Optional, List

logger = logging.getLogger("core.ntfy")

def encode_header(text: str) -> str:
    """Codifica texto no formato MIME Header para evitar falhas de codificação HTTP no Windows."""
    try:
        return Header(text, 'utf-8').encode()
    except Exception:
        return text

class NtfyNotifier:
    """
    Cliente robusto para envio de notificações Ntfy.
    Suporta chamadas síncronas e assíncronas e codifica headers em MIME.
    """
    def __init__(self, url: str, enabled: bool = True):
        self.url = url
        self.enabled = enabled

    async def send(self, title: str, message: str, priority: str = "default",
                    tags: Optional[List[str]] = None) -> bool:
        """Envia uma notificação de forma assíncrona."""
        if not self.enabled:
            return True
            
        try:
            import aiohttp
            headers = {
                "Title": encode_header(title),
                "Priority": priority
            }
            if tags:
                headers["Tags"] = ",".join(tags)
                
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, data=message.encode("utf-8")) as resp:
                    return resp.status == 200
        except ImportError:
            # Fallback para síncrono se aiohttp não estiver disponível
            return self.send_sync(title, message, priority, tags)
        except Exception as e:
            logger.error(f"[Ntfy] Erro no envio assincrono: {e}")
            return False

    def send_sync(self, title: str, message: str, priority: str = "default",
                  tags: Optional[List[str]] = None) -> bool:
        """Envia uma notificação de forma síncrona (adequado para cronjobs)."""
        if not self.enabled:
            return True
            
        try:
            headers = {
                "Title": encode_header(title),
                "Priority": priority
            }
            if tags:
                headers["Tags"] = ",".join(tags)
                
            resp = requests.post(self.url, headers=headers, data=message.encode("utf-8"), timeout=15)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"[Ntfy] Erro no envio sincrono: {e}")
            return False
