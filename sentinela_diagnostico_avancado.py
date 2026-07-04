# Diagnosticador Avançado de Travamento do Sentinela
# Arquivo: sentinela_diagnostico_avancado.py

import os
import sys
import json
import psutil
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ajusta encoding no Windows para evitar UnicodeEncodeError em prints de emojis
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sre.diagnostico_avancado")

BASE_PATH = Path('.')
LOG_FILE = BASE_PATH / 'logs' / 'main_runner.json'

def get_python_processes():
    """Lista todos os processos Python ativos no Windows com comandos e PID."""
    print("=" * 80)
    print("🔍 [1] ANALISANDO PROCESSOS PYTHON EM EXECUÇÃO")
    print("=" * 80)
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
        try:
            name = proc.info['name']
            if 'python' in name.lower():
                found = True
                cmdline = " ".join(proc.info['cmdline'] or [])
                mem = proc.info['memory_info'].rss / (1024 * 1024) # MB
                cpu = proc.info['cpu_percent']
                print(f"   - PID: {proc.info['pid']} | Nome: {name} | CPU: {cpu}% | RAM: {mem:.1f}MB")
                print(f"     CMD: {cmdline}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if not found:
        print("   Nenhum processo Python rodando no sistema.")
    print()

def get_playwright_processes():
    """Busca navegadores e processos do Playwright zumbis (Chrome, Node, etc.)."""
    print("=" * 80)
    print("🌐 [2] ANALISANDO PROCESSOS PLAYWRIGHT / NAVEGADORES (ZUMBIS)")
    print("=" * 80)
    found = False
    browser_keywords = ['chrome', 'chromium', 'node', 'playwright']
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            name = proc.info['name'].lower()
            cmdline = " ".join(proc.info['cmdline'] or []).lower()
            
            # Verifica se pertence ao Playwright ou Chrome
            is_browser = any(kw in name for kw in browser_keywords) or any(kw in cmdline for kw in browser_keywords)
            if is_browser:
                # Omitir processos de sistema legítimos ou do VS Code
                if 'vscode' in cmdline or 'microsoft VS Code' in cmdline:
                    continue
                found = True
                mem = proc.info['memory_info'].rss / (1024 * 1024)
                print(f"   - PID: {proc.info['pid']} | Nome: {proc.info['name']} | RAM: {mem:.1f}MB")
                print(f"     CMD: {proc.info['cmdline']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if not found:
        print("   Nenhum processo do Playwright/Chrome órfão encontrado.")
    print()

def analyze_recent_logs():
    """Busca mensagens do scraper no logs/main_runner.json por volta da falha de JanjaLula."""
    print("=" * 80)
    print("📝 [3] INVESTIGANDO LOGS DE EXECUÇÃO RECENTES (ANÁLISE FORENSE)")
    print("=" * 80)
    if not LOG_FILE.exists():
        print(f"   Log de execução não encontrado em {LOG_FILE}.")
        return

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"   Total de registros de log: {len(lines)}")
        
        # Filtra registros contendo 'janjalula' ou erros críticos
        critical_entries = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                msg = entry.get("message", "")
                name = entry.get("name", "")
                
                # Foco na Janja e no Scraper
                if "janjalula" in msg.lower() or "janjalula" in name.lower() or "v2" in msg.lower() or "error" in entry.get("levelname", "").lower():
                    critical_entries.append(entry)
            except Exception:
                continue

        print(f"   Encontrados {len(critical_entries)} registros relacionados a alvos ou falhas.")
        print("   Últimos 25 logs forenses:")
        for entry in critical_entries[-25:]:
            ts = entry.get("timestamp") or entry.get("asctime") or "N/A"
            level = entry.get("levelname") or entry.get("level") or "INFO"
            name = entry.get("name") or "log"
            msg = entry.get("message", "")
            print(f"     [{ts}] [{level}] ({name}) -> {msg}")
            
    except Exception as e:
        print(f"   Erro ao analisar logs: {e}")
    print()

def analyze_autonomous_logs():
    """Analisa especificamente o log do agente autônomo (autonomous_agent.log) buscando travamentos e modo noturno."""
    print("=" * 80)
    print("📖 [4] ANALISANDO LOGS DO AGENTE AUTÔNOMO INTERATIVO (autonomous_agent.log)")
    print("=" * 80)
    log_path = Path('logs/autonomous_agent.log')
    if not log_path.exists():
        print("   Arquivo logs/autonomous_agent.log não encontrado.")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"   Total de linhas no log: {len(lines)}")
        
        # Mostra as últimas 50 linhas para contextualizar a atividade recente
        print("   Últimas 50 linhas do log do Agente Autônomo:")
        for line in lines[-50:]:
            print(f"     {line.strip()}")
    except Exception as e:
        print(f"   Erro ao ler autonomous_agent.log: {e}")
    print()

def main():
    print("=" * 80)
    print("SENTINELA — DIAGNÓSTICO AVANÇADO DE TRAVAMENTO SRE v2.0")
    print("=" * 80)
    print()
    
    get_python_processes()
    get_playwright_processes()
    analyze_recent_logs()
    analyze_autonomous_logs()
    
    print("=" * 80)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 80)

if __name__ == "__main__":
    main()
