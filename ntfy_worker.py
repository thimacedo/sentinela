import os
import sys
import time
import asyncio
import sqlite3
import logging
import subprocess
from datetime import datetime

# Ajusta path para importar módulos do core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ntfy_client import _send_direct

# Configura log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/ntfy_worker.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ntfy_worker")

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

DB_PATH = "ntfy_queue.db"
SUMMARY_INTERVAL = 3 * 3600  # 3 horas
FAST_INTERVAL = 10  # 10 segundos

last_summary_time = time.time()

def invoke_healing(reason, details):
    logger.warning(f"🚨 Iniciando Auto-Cura. Motivo: {reason}")
    try:
        # Ação 1: Matar processos travados do autonomous agent para forçar um restart limpo
        kill_cmd = 'Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -match "sentinela_autonomous_agent.py" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }'
        subprocess.run(["powershell", "-Command", kill_cmd], capture_output=True)
        
        # Ação 2: Iniciar o agent diretamente de forma isolada do console
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            [sys.executable, "sentinela_autonomous_agent.py"],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        )

        # Notificar o usuário do bypass com prioridade máxima
        _send_direct(
            title="🛠️ Auto-Cura Ativada",
            message=f"Sistema interveio autonomamente.\nMotivo: {reason}\nDetalhes: {details}",
            tags="hammer_and_wrench,rotating_light",
            priority="high"
        )
    except Exception as e:
        logger.error(f"Falha ao executar rotina de auto-cura: {e}")

def process_queue():
    global last_summary_time
    if not os.path.exists(DB_PATH):
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, title, message, tags, priority FROM ntfy_messages WHERE processed = 0")
        rows = c.fetchall()
        
        if not rows:
            conn.close()
            return

        now = time.time()
        time_for_summary = (now - last_summary_time) >= SUMMARY_INTERVAL

        summary_rows = []
        critical_ids = []

        for row in rows:
            msg_id, title, msg, tags, priority = row
            tags_str = tags or ""
            title_str = title or ""
            msg_str = msg or ""
            
            # Avalia se precisa de Auto-Cura (Control Plane)
            is_critical = (
                priority in ["max", "urgent"] or 
                "PAUSA" in title_str or 
                "CRITICO" in title_str or 
                "PAUSED" in msg_str or 
                "all_sessions_blocked" in msg_str or
                "DOMHealer" in title_str
            )

            if is_critical:
                logger.error(f"Condição crítica detectada! ID: {msg_id} - {title_str}")
                invoke_healing(title_str, msg_str)
                critical_ids.append(msg_id)
            else:
                summary_rows.append(row)

        # Marca críticos como processados imediatamente
        if critical_ids:
            c.executemany("UPDATE ntfy_messages SET processed = 1 WHERE id = ?", [(i,) for i in critical_ids])
            conn.commit()

        # Envio do resumo de rotina a cada 3h
        if time_for_summary and summary_rows:
            total = len(summary_rows)
            tag_counts = {}
            for row in summary_rows:
                tags_str = row[3] or ""
                first_tag = tags_str.split(',')[0].strip() if tags_str else "outros"
                tag_counts[first_tag] = tag_counts.get(first_tag, 0) + 1

            resumo_msg = f"Resumo das últimas 3h:\n- Total de eventos rotineiros: {total}\n\n"
            for t, count in tag_counts.items():
                resumo_msg += f"[{t}]: {count} ocorrências\n"

            logger.info(f"Enviando resumo consolidado: {total} mensagens aglomeradas.")
            success = _send_direct(
                title="📊 Resumo Sentinela",
                message=resumo_msg,
                tags="bar_chart,robot",
                priority="default"
            )

            if success:
                ids = [r[0] for r in summary_rows]
                c.executemany("UPDATE ntfy_messages SET processed = 1 WHERE id = ?", [(i,) for i in ids])
                conn.commit()
                logger.info("Fila de rotina limpa e atualizada.")
                last_summary_time = now
            else:
                logger.error("Falha ao enviar o resumo. Mantendo fila.")

        conn.close()
    except Exception as e:
        logger.exception(f"Erro ao processar fila Ntfy: {e}")

async def main():
    logger.info("🚀 Ntfy Worker (Control Plane) iniciado. Loop rápido: 10s. Resumo: 3h.")
    while True:
        process_queue()
        await asyncio.sleep(FAST_INTERVAL)

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Ntfy Worker encerrado manualmente.")
