#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — DIAGNOSTICO DE TRAVAMENTO DO AGENTE v1.0
Identifica por que o agente parou durante a execucao de um ciclo.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_PATH = Path('.')
LOG_FILE = BASE_PATH / 'logs' / 'main_runner.json'
AGENT_STATUS = BASE_PATH / 'agent.status.json'
SCRAPER_LOG = BASE_PATH / 'logs' / 'scraper.log'

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

def check_last_logs():
    print('=' * 70)
    print('DIAGNOSTICO DE TRAVAMENTO DO AGENTE')
    print('=' * 70)
    print()

    # 1. Verificar agent.status.json
    print('[1] Verificando agent.status.json...')
    if AGENT_STATUS.exists():
        try:
            with open(AGENT_STATUS, 'r', encoding='utf-8') as f:
                status = json.load(f)
            print(f'    Status: {status.get("status", "N/A")}')
            print(f'    Ciclo: {status.get("cycle_count", "N/A")}')
            print(f'    Ultimo heartbeat: {status.get("last_heartbeat", "N/A")}')
            print(f'    Blocos consecutivos: {status.get("consecutive_blocks", "N/A")}')
        except Exception as e:
            print(f'    ERRO ao ler: {e}')
    else:
        print('    NAO ENCONTRADO')
    print()

    # 2. Verificar logs do main_runner
    print('[2] Verificando logs/main_runner.json...')
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if lines:
                # Ultimas 20 entradas
                print(f'    Total de entradas: {len(lines)}')
                print('    Ultimas 20 entradas:')
                for line in lines[-20:]:
                    try:
                        entry = json.loads(line.strip())
                        ts = entry.get('timestamp', 'N/A')
                        level = entry.get('level', 'INFO')
                        msg = entry.get('message', '')[:80]
                        print(f'      [{ts}] {level}: {msg}')
                    except:
                        print(f'      [RAW] {line.strip()[:80]}')
            else:
                print('    Arquivo vazio')
        except Exception as e:
            print(f'    ERRO: {e}')
    else:
        print('    NAO ENCONTRADO')
    print()

    # 3. Verificar se ha processo python rodando
    print('[3] Verificando processos Python...')
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        python_procs = [l for l in lines if 'python' in l.lower()]
        if python_procs:
            print(f'    {len(python_procs)} processo(s) Python encontrado(s):')
            for proc in python_procs[:5]:
                print(f'      {proc.strip()}')
        else:
            print('    NENHUM processo Python encontrado')
            print('    → O agente MORREU completamente')
    except Exception as e:
        print(f'    ERRO: {e}')
    print()

    # 4. Verificar arquivo de lock/crash
    print('[4] Verificando arquivos de crash/lock...')
    crash_files = [
        BASE_PATH / 'agent.lock',
        BASE_PATH / 'runtime_state' / 'agent.lock',
        BASE_PATH / 'data' / 'crash.log',
    ]
    for cf in crash_files:
        if cf.exists():
            print(f'    ENCONTRADO: {cf}')
            try:
                content = cf.read_text(encoding='utf-8')[:200]
                print(f'      Conteudo: {content}')
            except:
                pass
    if not any(cf.exists() for cf in crash_files):
        print('    Nenhum arquivo de crash encontrado')
    print()

    # 5. Verificar Supabase — alvo atual
    print('[5] Verificando estado do alvo no Supabase...')
    try:
        import requests
        env_path = BASE_PATH / '.env'
        env = {}
        if env_path.exists():
            for line in env_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip(chr(39)+chr(34))
        
        supabase_url = env.get('SUPABASE_URL', env.get('NEXT_PUBLIC_SUPABASE_URL', ''))
        supabase_key = env.get('SUPABASE_SERVICE_KEY', env.get('SUPABASE_KEY', ''))
        
        if supabase_url and supabase_key:
            url = f'{supabase_url}/rest/v1/fila_coleta'
            params = {'select': 'id,candidato_id,status,locked_by,locked_at', 'limit': '5', 'order': 'locked_at.desc.nullslast'}
            headers = {'apikey': supabase_key, 'Authorization': f'Bearer {supabase_key}'}
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                print(f'    Ultimos 5 itens da fila:')
                for item in data:
                    username = item.get('candidato_id', 'N/A')
                    status = item.get('status', 'N/A')
                    locked = item.get('locked_by', 'N/A')
                    print(f'      @{username} | {status} | locked_by={locked}')
            else:
                print(f'    Erro HTTP {r.status_code}')
        else:
            print('    Credenciais Supabase nao encontradas')
    except Exception as e:
        print(f'    ERRO: {e}')
    print()

    # 6. Verificar se o scraper deixou algum log
    print('[6] Verificando logs do scraper...')
    scraper_logs = [
        BASE_PATH / 'logs' / 'scraper.log',
        BASE_PATH / 'logs' / 'instagram_scraper.log',
        BASE_PATH / 'logs' / 'v2_engine.log',
    ]
    found = False
    for sl in scraper_logs:
        if sl.exists():
            found = True
            print(f'    ENCONTRADO: {sl}')
            try:
                with open(sl, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if lines:
                    print(f'      Ultimas 5 linhas:')
                    for line in lines[-5:]:
                        print(f'        {line.strip()[:100]}')
            except Exception as e:
                print(f'      ERRO ao ler: {e}')
    if not found:
        print('    Nenhum log do scraper encontrado')
    print()

    # 7. Verificar se ha erros de excecao nao tratada
    print('[7] Verificando excecoes nao tratadas nos logs...')
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            errors = []
            for line in lines:
                try:
                    entry = json.loads(line.strip())
                    msg = entry.get('message', '')
                    if 'error' in msg.lower() or 'exception' in msg.lower() or 'traceback' in msg.lower():
                        errors.append(msg[:150])
                except:
                    pass
            
            if errors:
                print(f'    {len(errors)} erro(s) encontrado(s):')
                for err in errors[-5:]:
                    print(f'      → {err}')
            else:
                print('    Nenhum erro encontrado nos logs')
        except Exception as e:
            print(f'    ERRO: {e}')
    print()

    print('=' * 70)
    print('FIM DO DIAGNOSTICO')
    print('=' * 70)

if __name__ == '__main__':
    check_last_logs()