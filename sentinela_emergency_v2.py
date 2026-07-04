#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — SCRIPT DE EMERGENCIA v2.0
Recuperaçao operacional sem dependencias do projeto.

USO:
    python sentinela_emergency_v2.py --check-all
    python sentinela_emergency_v2.py --fix-all
    python sentinela_emergency_v2.py --status
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# CONFIGURACAO — le do .env automaticamente
# ============================================================

def load_env():
    env = {}
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'""")
    return env

ENV = load_env()
SUPABASE_URL = ENV.get("SUPABASE_URL", ENV.get("NEXT_PUBLIC_SUPABASE_URL", ""))
SUPABASE_KEY = ENV.get("SUPABASE_SERVICE_KEY", ENV.get("SUPABASE_KEY", ENV.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")))
NTFY_URL = ENV.get("NTFY_URL", "")

# ============================================================
# SUPABASE REST DIRETO (sem create_client)
# ============================================================

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def supabase_request(method, path, data=None, params=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "SUPABASE_URL ou SUPABASE_KEY nao encontrados no .env"}

    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    try:
        if HAS_REQUESTS:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                r = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PATCH":
                r = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=30)
            else:
                return {"error": f"Metodo {method} nao suportado"}
            return {"status": r.status_code, "data": r.json() if r.text else None}
        elif HAS_URLLIB:
            req = urllib.request.Request(url, method=method)
            for k, v in headers.items():
                req.add_header(k, v)
            if data and method in ("POST", "PATCH"):
                req.data = json.dumps(data).encode("utf-8")
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return {"status": resp.status, "data": json.loads(body) if body else None}
        else:
            return {"error": "Ni requests ni urllib disponivel. Instale: pip install requests"}
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# DIAGNOSTICO DA FILA
# ============================================================

def check_queue():
    print("[1] Verificando fila Supabase (REST direto)...")

    # Itens presos com lock
    result_locked = supabase_request(
        "GET", "fila_coleta",
        params={"locked_by": "not.is.null", "limit": "100"}
    )

    # Contagem por status
    result_count = supabase_request(
        "GET", "fila_coleta",
        params={"select": "status", "limit": "1"}
    )

    # Tentar RPC se disponivel
    result_rpc = supabase_request(
        "POST", "rpc/fila_coleta_release_stale",
        data={}
    )

    locked = result_locked.get("data", [])

    print(f"    Itens com lock ativo: {len(locked)}")
    if locked:
        for item in locked[:5]:
            locked_at = item.get("locked_at", "N/A")
            username = item.get("username", "N/A")
            print(f"      - @{username} | locked_at: {locked_at}")

    print(f"    RPC release_stale: {result_rpc.get('status', 'ERRO')} — {result_rpc.get('data', result_rpc.get('error', 'N/A'))}")

    return {
        "locked_count": len(locked),
        "locked_items": locked[:10],
        "rpc_result": result_rpc
    }

# ============================================================
# DIAGNOSTICO DO CIRCUIT BREAKER (via logs)
# ============================================================

def check_circuit_breaker():
    print("[2] Verificando circuit breaker (via logs)...")

    log_path = Path("logs/main_runner.json")
    if not log_path.exists():
        print("    Log nao encontrado. Criando diretorio logs/...")
        Path("logs").mkdir(exist_ok=True)
        return {"status": "no_logs", "last_circuit_open": None}

    try:
        lines = log_path.read_text(encoding="utf-8").strip().split("
")
        last_circuit = None
        last_entries = []

        for line in lines[-200:]:
            try:
                entry = json.loads(line)
                last_entries.append(entry)
                if "circuit_open" in str(entry) or "Circuit breaker" in str(entry):
                    last_circuit = entry
            except:
                pass

        if last_circuit:
            print(f"    ULTIMO CIRCUIT OPEN: {json.dumps(last_circuit, indent=2, ensure_ascii=False)[:300]}")
        else:
            print("    Nenhum circuit_open encontrado nos ultimos 200 logs.")

        # Verificar se ha erros recentes de ExtractionFailure
        extractions = [e for e in last_entries if "ExtractionFailure" in str(e) or "Falha estrutural" in str(e)]
        print(f"    ExtractionFailure nos ultimos logs: {len(extractions)}")

        return {
            "status": "checked",
            "last_circuit_open": last_circuit,
            "extraction_failures": len(extractions),
            "total_recent_logs": len(last_entries)
        }
    except Exception as e:
        print(f"    ERRO ao ler logs: {e}")
        return {"status": "error", "error": str(e)}

# ============================================================
# DIAGNOSTICO DO AGENTE STATUS
# ============================================================

def check_agent_status():
    print("[3] Verificando agent.status.json...")

    status_path = Path("agent.status.json")
    if not status_path.exists():
        print("    agent.status.json NAO ENCONTRADO — criando...")
        default_status = {
            "version": "1.2",
            "status": "UNKNOWN",
            "cycle_count": 0,
            "consecutive_blocks": 0,
            "last_cycle_time": None,
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "targets_tracked": 0,
            "queue_status": "unknown"
        }
        status_path.write_text(json.dumps(default_status, indent=2, ensure_ascii=False), encoding="utf-8")
        print("    agent.status.json criado com estado UNKNOWN.")
        return {"status": "created", "data": default_status}

    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
        print(f"    Status atual: {data.get('status', 'N/A')}")
        print(f"    Ciclos: {data.get('cycle_count', 0)}")
        print(f"    Blocos consecutivos: {data.get('consecutive_blocks', 0)}")
        print(f"    Ultimo ciclo: {data.get('last_cycle_time', 'N/A')}")

        # Verificar se esta stale (mais de 10 min sem heartbeat)
        last_hb = data.get("last_heartbeat")
        if last_hb:
            try:
                last_dt = datetime.fromisoformat(last_hb.replace("Z", "+00:00"))
                idle_minutes = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60
                print(f"    Tempo desde ultimo heartbeat: {idle_minutes:.1f} minutos")
                if idle_minutes > 10:
                    print("    ⚠️  AGENTE PARECE ESTAR PARADO (heartbeat > 10 min)")
            except:
                pass

        return {"status": "ok", "data": data}
    except Exception as e:
        print(f"    ERRO ao ler status: {e}")
        return {"status": "error", "error": str(e)}

# ============================================================
# DIAGNOSTICO DE SESSOES
# ============================================================

def check_sessions():
    print("[4] Verificando sessoes Instagram...")

    env_path = Path(".env")
    if not env_path.exists():
        print("    .env nao encontrado")
        return {"status": "no_env"}

    sessions = []
    for k, v in ENV.items():
        if "SESSIONID" in k and v:
            masked = v[:10] + "..." + v[-5:] if len(v) > 15 else "***"
            sessions.append({"key": k, "value": masked, "full": v})

    print(f"    Sessoes IG encontradas: {len(sessions)}")
    for s in sessions:
        print(f"      - {s['key']}: {s['value']}")

    return {"status": "ok", "sessions": sessions}

# ============================================================
# FIX ALL — CORRECOES OPERACIONAIS
# ============================================================

def fix_all():
    print("="*70)
    print("SENTINELA — CORRECAO OPERACIONAL v2.0")
    print("="*70)

    results = {}

    # 1. Liberar locks orfaos via RPC
    print("\n[FIX 1] Liberando locks orfaos...")
    result = supabase_request("POST", "rpc/fila_coleta_release_stale", data={})
    if "error" in result:
        print(f"    ERRO RPC: {result['error']}")
        # Fallback: PATCH manual nos itens presos
        locked = supabase_request("GET", "fila_coleta", params={"locked_by": "not.is.null", "limit": "50"})
        if locked.get("data"):
            for item in locked["data"]:
                item_id = item.get("id")
                if item_id:
                    supabase_request("PATCH", f"fila_coleta?id=eq.{item_id}", data={"locked_by": None, "locked_at": None, "status": "PENDENTE"})
            print(f"    Liberados manualmente: {len(locked['data'])} itens")
        results["locks"] = "manual_release"
    else:
        print(f"    OK: RPC executado (status {result.get('status', 'N/A')})")
        results["locks"] = "rpc_release"

    # 2. Resetar status do agente
    print("\n[FIX 2] Resetando agent.status.json...")
    status_path = Path("agent.status.json")
    reset_status = {
        "version": "1.2",
        "status": "RUNNING",
        "cycle_count": 0,
        "consecutive_blocks": 0,
        "last_cycle_time": datetime.now(timezone.utc).isoformat(),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "targets_tracked": 0,
        "queue_status": "reset_by_emergency"
    }
    status_path.write_text(json.dumps(reset_status, indent=2, ensure_ascii=False), encoding="utf-8")
    print("    OK: agent.status.json resetado para RUNNING")
    results["status"] = "reset"

    # 3. Verificar circuit breaker (apenas log, nao podemos resetar sem a classe)
    print("\n[FIX 3] Verificando circuit breaker...")
    cb_result = check_circuit_breaker()
    if cb_result.get("extraction_failures", 0) > 5:
        print("    ⚠️  Muitas falhas de extracao detectadas. O circuit breaker pode estar aberto.")
        print("    → Reinicie o agente para forcar reset do circuit breaker (ele e reiniciado em memoria).")
    results["circuit"] = cb_result

    # 4. Notificar Ntfy
    print("\n[FIX 4] Notificando Ntfy...")
    if NTFY_URL:
        try:
            msg = {
                "topic": NTFY_URL.split("/")[-1] if "/" in NTFY_URL else "sentinela",
                "title": "Sentinela — Recuperacao Operacional",
                "message": f"Correcoes aplicadas em {datetime.now().strftime('%H:%M')}. Locks liberados, status resetado. Reinicie o agente.",
                "tags": ["warning", "tools"],
                "priority": 4
            }
            if HAS_REQUESTS:
                requests.post(NTFY_URL, json=msg, timeout=10)
            elif HAS_URLLIB:
                req = urllib.request.Request(NTFY_URL, method="POST")
                req.add_header("Content-Type", "application/json")
                req.data = json.dumps(msg).encode("utf-8")
                urllib.request.urlopen(req, timeout=10)
            print("    OK: Notificacao enviada")
            results["ntfy"] = "sent"
        except Exception as e:
            print(f"    ERRO Ntfy: {e}")
            results["ntfy"] = f"error: {e}"
    else:
        print("    NTFY_URL nao configurado, pulando notificacao.")
        results["ntfy"] = "skipped"

    print("\n" + "="*70)
    print("RESUMO:")
    for k, v in results.items():
        print(f"  [{k.upper()}] {v}")
    print("="*70)
    print("\nPROXIMO PASSO: Reinicie o agente com:")
    print("  python sentinela_autonomous_agent.py --env .env")
    print("="*70)

    return results

# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Sentinela — Script de Emergencia v2.0")
    parser.add_argument("--check-all", action="store_true", help="Diagnostico completo")
    parser.add_argument("--fix-all", action="store_true", help="Aplicar todas as correcoes")
    parser.add_argument("--status", action="store_true", help="Status rapido do agente")
    args = parser.parse_args()

    if not any([args.check_all, args.fix_all, args.status]):
        print("Uso: python sentinela_emergency_v2.py --check-all | --fix-all | --status")
        sys.exit(1)

    if args.status:
        check_agent_status()
        check_circuit_breaker()
        return

    if args.check_all:
        print("="*70)
        print("SENTINELA — DIAGNOSTICO COMPLETO v2.0")
        print("="*70)
        check_queue()
        print()
        check_circuit_breaker()
        print()
        check_agent_status()
        print()
        check_sessions()
        print("="*70)
        return

    if args.fix_all:
        fix_all()
        return

if __name__ == "__main__":
    main()
