#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — SCRIPT DE EMERGENCIA v1.0
Diagnostica e corrige agente em VERMELHO sem editar código fonte.

USO:
    python sentinela_emergency.py [--env .env] [--fix-all]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def load_env(env_path: Path):
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"\'')


def check_supabase_queue():
    """Verifica estado da fila no Supabase."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            return {"error": "SUPABASE_URL ou SUPABASE_KEY nao configurados"}

        supabase = create_client(url, key)
        result = supabase.table("fila_coleta").select("*", count="exact").execute()

        rows = result.data if hasattr(result, "data") else []
        stats = {"total": len(rows), "concluido": 0, "em_curso": 0, "falhado": 0, "pendente": 0, "locked": 0}

        for row in rows:
            status = row.get("status", "")
            if status == "CONCLUIDO":
                stats["concluido"] += 1
            elif status == "EM_CURSO":
                stats["em_curso"] += 1
                if row.get("locked_by"):
                    stats["locked"] += 1
            elif status in ("FALHADO", "ERRO"):
                stats["falhado"] += 1
            else:
                stats["pendente"] += 1

        return stats
    except Exception as e:
        return {"error": str(e)}


def release_stale_locks():
    """Libera locks orfaos na fila."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        supabase = create_client(url, key)

        result = supabase.rpc("fila_coleta_release_stale", {"stale_minutes": 30}).execute()
        return {"released": getattr(result, "count", 0) or 0}
    except Exception as e:
        return {"error": str(e)}


def reset_circuit_breaker():
    """Reseta o circuit breaker."""
    try:
        import importlib.util
        cb_path = Path(r"C:\projetos\sentinela\core\circuit_breaker.py")
        if not cb_path.exists():
            return {"error": "circuit_breaker.py nao encontrado"}

        spec = importlib.util.spec_from_file_location("circuit_breaker", cb_path)
        cb_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cb_module)

        if hasattr(cb_module, "scraper_circuit_breaker"):
            cb_module.scraper_circuit_breaker.reset()
            return {"success": True, "message": "Circuit breaker resetado"}
        else:
            return {"error": "scraper_circuit_breaker nao encontrado no modulo"}
    except Exception as e:
        return {"error": str(e)}


def reset_agent_status(base_path: Path):
    """Reseta o arquivo agent.status.json."""
    try:
        status_file = base_path / "agent.status.json"
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)

            # Reseta estados problemáticos
            if "smart_queue" in status:
                status["smart_queue"]["global_empty_cycles"] = 0
                if "target_states" in status["smart_queue"]:
                    for username, state in status["smart_queue"]["target_states"].items():
                        if state.get("status") in ("EXHAUSTED", "BLOCKED", "BACKOFF"):
                            state["status"] = "ACTIVE"
                            state["consecutive_empty_cycles"] = 0
                            state["backoff_until"] = None

            status["heartbeat"] = {
                "last_heartbeat": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat_age_seconds": 0,
            }

            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)

            return {"success": True, "message": "agent.status.json resetado"}
        else:
            return {"error": "agent.status.json nao encontrado"}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Sentinela — Script de Emergencia")
    parser.add_argument("--env", default=".env", help="Arquivo .env")
    parser.add_argument("--path", default=r"C:\projetos\sentinela", help="Caminho base")
    parser.add_argument("--fix-all", action="store_true", help="Aplica TODAS as correcoes")
    parser.add_argument("--release-locks", action="store_true", help="Libera locks orfaos")
    parser.add_argument("--reset-cb", action="store_true", help="Reseta circuit breaker")
    parser.add_argument("--reset-status", action="store_true", help="Reseta agent.status.json")
    parser.add_argument("--check-queue", action="store_true", help="Verifica fila Supabase")
    args = parser.parse_args()

    base_path = Path(args.path)
    env_path = base_path / args.env

    print("=" * 70)
    print("SENTINELA — SCRIPT DE EMERGENCIA v1.0")
    print("=" * 70)
    print()

    load_env(env_path)

    # Se --fix-all, aplica tudo
    if args.fix_all:
        args.release_locks = True
        args.reset_cb = True
        args.reset_status = True
        args.check_queue = True

    results = {}

    if args.check_queue:
        print("[1] Verificando fila Supabase...")
        results["queue"] = check_supabase_queue()
        print(f"    Resultado: {json.dumps(results['queue'], indent=2, ensure_ascii=False)}")
        print()

    if args.release_locks:
        print("[2] Liberando locks orfaos...")
        results["locks"] = release_stale_locks()
        print(f"    Resultado: {json.dumps(results['locks'], indent=2, ensure_ascii=False)}")
        print()

    if args.reset_cb:
        print("[3] Resetando circuit breaker...")
        results["circuit_breaker"] = reset_circuit_breaker()
        print(f"    Resultado: {json.dumps(results['circuit_breaker'], indent=2, ensure_ascii=False)}")
        print()

    if args.reset_status:
        print("[4] Resetando agent.status.json...")
        results["status"] = reset_agent_status(base_path)
        print(f"    Resultado: {json.dumps(results['status'], indent=2, ensure_ascii=False)}")
        print()

    print("=" * 70)
    print("RESUMO:")
    for key, val in results.items():
        status = "OK" if val.get("success") else ("INFO" if "error" not in val else "ERRO")
        print(f"  [{status}] {key}: {val}")
    print()

    if args.fix_all:
        print("TODAS AS CORRECOES APLICADAS.")
        print("Reinicie o agente: python sentinela_autonomous_agent.py")

    print("=" * 70)


if __name__ == "__main__":
    main()
