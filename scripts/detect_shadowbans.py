"""
PASA v46.2 - Shadowban Detector: Auto-Cure Edition
Detecta o silêncio, alerta uma vez, e REMOVE a flag se a conta se recuperar.
"""
import os
import requests
from datetime import datetime, timezone
from core.supabase_service import get_supabase_client

CALLMEBOT_PHONE = os.getenv("WHATSAPP_PHONE") or os.getenv("CALLMEBOT_PHONE") or "558496066876"
CALLMEBOT_APIKEY = os.getenv("WHATSAPP_API_KEY") or os.getenv("CALLMEBOT_APIKEY") or "8552672"
CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"

def detect_shadowbans():
    db = get_supabase_client()
    
    # 1. Busca todos os alvos de alto escalão
    targets = db.table('candidatos')\
        .select('username, seguidores, comentarios_totais_count, shadowban_suspect, shadowban_detected_at')\
        .gt('seguidores', 100000)\
        .execute()
    
    if not targets.data:
        return

    for t in targets.data:
        username = t['username']
        followers = t.get('seguidores', 0)
        total_comments = t.get('comentarios_totais_count', 0)
        is_suspect = t.get('shadowban_suspect', False)
        
        # LÓGICA DE DETECÇÃO: Sem comentários + Alto seguidor = Ban
        if total_comments == 0 and not is_suspect:
            print(f"[ShadowbanDetector] 🚨 NOVO SUSPEITO: @{username} ({followers} seg, 0 comms)")
            db.table('candidatos').update({
                'shadowban_suspect': True,
                'shadowban_detected_at': datetime.now(timezone.utc).isoformat()
            }).eq('username', username).execute()
            send_shadowban_alert(username, followers)
        
        # LÓGICA DE CURA: Se tinha ban mas agora tem comentários, o ban acabou
        elif total_comments > 0 and is_suspect:
            print(f"[ShadowbanDetector] ✅ BAN ENCERRADO: @{username} voltou a render ({total_comments} comms)")
            db.table('candidatos').update({
                'shadowban_suspect': False,
                'shadowban_detected_at': None
            }).eq('username', username).execute()
        
        # LÓGICA DE PERSISTÊNCIA: Ainda está banido (Não spamma WhatsApp de novo)
        elif total_comments == 0 and is_suspect:
            print(f"[ShadowbanDetector] ⏳ AINDA BANIDO: @{username} (Silêncio persiste)")

def send_shadowban_alert(username, followers):
    message = f"🚨 *SHADOWBAN SUSPEITO* 🚨\n\nO perfil *@{username}* ({followers} seg) rendeu *0 comentários*.\nAlertarei novamente apenas quando o ban for levantado."
    
    params = {
        "phone": CALLMEBOT_PHONE,
        "apikey": CALLMEBOT_APIKEY,
        "text": message
    }
    try:
        requests.get(CALLMEBOT_URL, params=params, timeout=10)
    except Exception as e:
        print(f"[ShadowbanDetector] Falha ao enviar alerta: {e}")

if __name__ == "__main__":
    detect_shadowbans()