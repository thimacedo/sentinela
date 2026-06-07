import time
import subprocess
import os
import sys
from datetime import datetime, timedelta
import asyncio

# Core imports
sys.path.append(r".")
from core.db import db_client
from core.whatsapp_alerter import send_whatsapp_summary

def get_stats():
    """Busca estatísticas reais do banco."""
    try:
        today = datetime.now().date().isoformat()
        # Contagem total de hoje
        res_total = db_client.client.table('comentarios').select('id', count='exact').filter('data_coleta', 'gte', today).execute()
        # Contagem de ódio de hoje
        from core.constants import HATE_CATEGORIES
        res_hate = db_client.client.table('comentarios').select('id', count='exact').in_('categoria_ia', HATE_CATEGORIES).filter('data_coleta', 'gte', today).execute()
        # Contagem de falhas (geral)
        res_fail = db_client.client.table('comentarios').select('id', count='exact').eq('categoria_ia', 'FALHA_IA').execute()
        
        return {
            "total": res_total.count or 0,
            "hate": res_hate.count or 0,
            "fail": res_fail.count or 0
        }
    except Exception as e:
        print(f"Erro ao buscar stats: {e}")
        return None

async def monitor_loop():
    last_wa_report = datetime.now() - timedelta(hours=1, minutes=50) # Primeiro report em 10 min
    
    print("🥒 Vigilante Pickle Iniciado! Protegendo o multiverso...")
    
    while True:
        now = datetime.now()
        print(f"[{now.strftime('%H:%M:%S')}] Auditando batimento cardíaco do sistema...")
        
        # Relatório WhatsApp (A cada 2 horas)
        if now >= last_wa_report + timedelta(hours=2):
            stats = get_stats()
            if stats:
                msg = f"*📊 RELATÓRIO SENTINELA (2h)*\n"
                msg += f"📅 Data: {now.strftime('%d/%m %H:%M')}\n"
                msg += f"📥 Coletados Hoje: {stats['total']}\n"
                msg += f"🔥 Ódio Detectado: {stats['hate']}\n"
                msg += f"⚠️ Falhas IA no Banco: {stats['fail']}\n"
                msg += f"🚀 Status: Motor Solenya em Overdrive."
                
                try:
                    send_whatsapp_summary(msg)
                    print("📱 Relatório enviado para o WhatsApp!")
                except Exception as e:
                    print(f"Erro ao enviar WhatsApp: {e}")
                last_wa_report = now
        
        await asyncio.sleep(300) # Dorme 5 minutos

if __name__ == "__main__":
    asyncio.run(monitor_loop())
