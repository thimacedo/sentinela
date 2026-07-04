# Cronjob SRE Health Check (cj_sre_health_check)
# Arquivo: scripts/cj_sre_health_check.py

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Configura caminhos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

# Logger simples
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sre.health_check")

from core.supabase_client import get_supabase_client
from core.ntfy import NtfyNotifier

# Instancia notificador
ntfy_url = os.getenv("NTFY_URL") or "https://ntfy.sh/sentinela-alertas"
ntfy = NtfyNotifier(ntfy_url, enabled=True)

def check_agent_heartbeat():
    """Verifica se o arquivo agent.status.json está sendo atualizado."""
    status_file = os.path.join(PROJECT_ROOT, "agent.status.json")
    if not os.path.exists(status_file):
        logger.warning(f"⚠️ [SRE] Arquivo de status do agente não encontrado: {status_file}")
        return False
        
    try:
        mtime = os.path.getmtime(status_file)
        last_modified = datetime.fromtimestamp(mtime, timezone.utc)
        now = datetime.now(timezone.utc)
        lag = (now - last_modified).total_seconds()
        
        # Le status
        with open(status_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"[SRE] Status do agente lido. Lag: {lag:.1f}s | Fila: {data.get('queue_pending')} | Ciclos: {data.get('cycle_count')}")
        
        if lag > 600: # 10 minutos
            logger.error(f"🚨 [SRE] Heartbeat do agente autônomo está staled ({lag:.1f}s sem atualizacao)!")
            return False
        return True
    except Exception as e:
        logger.error(f"❌ [SRE] Erro ao ler agent.status.json: {e}")
        return False

def clean_orphaned_locks(db):
    """Destrava alvos presos em EM_CURSO por mais de 30 minutos."""
    try:
        now = datetime.now(timezone.utc)
        threshold = (now - timedelta(minutes=30)).isoformat()
        
        # Busca locks antigos usando rest api
        res = db.table("fila_coleta").select("id, candidato_id, locked_at").eq("status", "EM_CURSO").lt("locked_at", threshold).execute()
        orphans = res.data or []
        
        if not orphans:
            logger.info("[SRE] Nenhum lock órfão encontrado na fila_coleta.")
            return
            
        logger.warning(f"⚠️ [SRE] Encontrados {len(orphans)} locks órfãos presos há >30min. Destravando...")
        
        for item in orphans:
            queue_id = item["id"]
            username = item.get("candidato_id") or "desconhecido"
            locked_at = item["locked_at"]
            
            # Libera
            db.table("fila_coleta").update({
                "status": "PENDENTE",
                "locked_by": None,
                "locked_at": None,
                "updated_at": now.isoformat()
            }).eq("id", queue_id).execute()
            
            logger.info(f"✅ [SRE] Lock de @{username} (preso desde {locked_at}) liberado e resetado para PENDENTE.")
            
            # Alerta Ntfy leve
            ntfy.send_sync(
                title="Sentinela — Lock Órfão Destravado",
                message=f"O alvo @{username} estava preso na fila e foi liberado pelo cj_sre_health_check.",
                priority="default",
                tags=["key", "recycle"]
            )
            
    except Exception as e:
        logger.error(f"❌ [SRE] Erro ao limpar locks órfãos: {e}")

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO VARREDURA DE SAÚDE SRE (cj_sre_health_check)")
    logger.info("=" * 60)
    
    # 1. Verifica Heartbeat
    healthy = check_agent_heartbeat()
    if not healthy:
        # Tenta reiniciar o agente autônomo se o script estiver em console e falhar
        logger.error("🚨 [SRE] Agente autônomo está congelado ou inativo! Enviando alerta de urgência.")
        ntfy.send_sync(
            title="Sentinela — AGENTE INATIVO",
            message="O arquivo agent.status.json não é atualizado há mais de 10 min. Possível congelamento do Autopilot.",
            priority="urgent",
            tags=["skull", "alarm_clock"]
        )
        # O Watchdog autônomo no Windows reiniciará o script se ele cair,
        # mas esse alerta garante visibilidade imediata ao operador.
        
    # 2. Verifica Supabase e limpa locks
    try:
        db = get_supabase_client()
        clean_orphaned_locks(db)
    except Exception as e_db:
        logger.error(f"❌ [SRE] Falha ao conectar ao Supabase para verificar locks: {e_db}")

    logger.info("=" * 60)
    logger.info("VARREDURA SRE CONCLUÍDA")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
