import time
import datetime
import os

log_file = "runtime_state/night_monitor.log"

def monitor():
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"\n[{datetime.datetime.now()}] Iniciando monitoramento noturno (10-min pulse)...\n")
        
    while True:
        try:
            # Pega as últimas 20 linhas do watchdog_bg
            bg_log = "runtime_state/watchdog_bg.log"
            tail = ""
            if os.path.exists(bg_log):
                with open(bg_log, "r", encoding="utf-8", errors="replace") as bl:
                    lines = bl.readlines()
                    tail = "".join(lines[-20:])
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n--- Check-in: {datetime.datetime.now()} ---\n")
                f.write(tail)
                f.write("\n-------------------------------------------------\n")
                
            time.sleep(600)  # 10 minutes
        except Exception as e:
            time.sleep(60)

if __name__ == "__main__":
    monitor()
