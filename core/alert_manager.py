"""
PASA v18 - Alert Manager: Notificações críticas via CallMeBot (WhatsApp)
"""
import os
import httpx
import urllib.parse
from workers.core.xp_engine import XP_PENALTY_AUTH_FAIL, XP_PENALTY_TIMEOUT

# Credenciais CallMeBot (Prioriza ENV, fallback para as fornecidas)
CALLMEBOT_PHONE = os.getenv("WHATSAPP_PHONE") or os.getenv("CALLMEBOT_PHONE") or "558496066876"
CALLMEBOT_APIKEY = os.getenv("WHATSAPP_API_KEY") or os.getenv("CALLMEBOT_APIKEY") or "8552672"
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"

async def send_critical_alert(worker_id: str, run_xp: int, error_details: str):
    """
    Dispara alerta via WhatsApp usando CallMeBot se houver penalidade severa.
    """
    if run_xp not in [XP_PENALTY_AUTH_FAIL, XP_PENALTY_TIMEOUT]:
        return # Não é crítico

    if run_xp == XP_PENALTY_AUTH_FAIL:
        icon = "🚨"
        title = "FALHA DE AUTENTICAÇÃO"
        action = "Ação: Atualizar cookies/sessão do scraper imediatamente via Dashboard."
    else:
        icon = "⏱️"
        title = "TIMEOUT CRÍTICO"
        action = "Ação: Verificar estabilidade da rede ou proxy."

    message = (
        f"{icon} *{title}* {icon}\n\n"
        f"*Worker*: {worker_id}\n"
        f"*Penalidade*: {run_xp} XP\n"
        f"*Detalhes*: {error_details}\n\n"
        f"_{action}_"
    )

    params = {
        "phone": CALLMEBOT_PHONE,
        "apikey": CALLMEBOT_APIKEY,
        "text": message
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(CALLMEBOT_URL, params=params, timeout=15.0)
            if response.status_code != 200:
                print(f"[AlertManager] Erro ao enviar WhatsApp: {response.text}")
    except Exception as e:
        print(f"[AlertManager] Falha de conexão com CallMeBot: {e}")
