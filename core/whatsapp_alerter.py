import requests
import urllib.parse
import os
import logging
from core.config import settings

logger = logging.getLogger("sentinela-whatsapp")

def send_whatsapp_summary(summary_text: str):
    """
    Envia mensagens via CallMeBot API para o WhatsApp.
    """
    phone = os.getenv("WHATSAPP_PHONE") or os.getenv("CALLMEBOT_PHONE") or "558496066876"
    apikey = os.getenv("WHATSAPP_API_KEY") or os.getenv("CALLMEBOT_APIKEY") or "8552672"
    
    if not phone or not apikey:
        logger.warning("⚠️ WHATSAPP_PHONE ou WHATSAPP_API_KEY não configurados.")
        return

    # CallMeBot exige que o texto seja URL encoded
    encoded_text = urllib.parse.quote(summary_text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_text}&apikey={apikey}"

    try:
        logger.info(f"📱 Enviando alerta WhatsApp via CallMeBot para {phone}...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Mensagem enviada com sucesso para o WhatsApp!")
            return True
        else:
            logger.error(f"❌ Erro na API CallMeBot: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Falha crítica ao enviar WhatsApp: {e}")
        return False
