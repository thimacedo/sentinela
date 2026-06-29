import os
import requests
import logging
from typing import Optional

logger = logging.getLogger("ntfy_client")

# Fallback para o tópico caso não exista no .env
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "sentinela")
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

def send_notification(title: str, message: str, tags: str = "robot", priority: str = "default") -> bool:
    """
    Envia uma notificação para o canal ntfy oficial.
    
    :param title: Título da notificação
    :param message: Corpo da mensagem
    :param tags: Tags/Emojis separados por vírgula (ex: 'robot', 'x', 'warning')
    :param priority: 'max', 'high', 'default', 'low', 'min'
    """
    headers = {
        "Title": title,
        "Tags": tags,
        "Priority": priority
    }
    
    # Executa de forma sincrona, idealmente em background task (to_thread) 
    # se chamado de async loop.
    try:
        response = requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar notificação ntfy para {NTFY_URL}: {e}")
        return False
