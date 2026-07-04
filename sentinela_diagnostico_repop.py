#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SENTINELA — SCRIPT DE DIAGNOSTICO DE REPOPULAÇÃO v1.0
Diagnostica e força a repopulação da fila de coleta.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ajusta encoding no Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

# Carrega ambiente
load_dotenv()

from core.supabase_client import get_supabase_client

def get_stats():
    db = get_supabase_client()
    stats = {}
    
    # 1. Total de candidatos
    try:
        res_cand = db.table("candidatos").select("id", count="exact").execute()
        stats["total_candidatos"] = res_cand.count or 0
    except Exception as e:
        stats["total_candidatos_error"] = str(e)

    # 2. Candidatos ativos
    try:
        # Tenta com ATIVO (case-insensitive via ilike)
        res_active = db.table("candidatos").select("id,username", count="exact").filter("status_monitoramento", "ilike", "Ativo").execute()
        stats["candidatos_ativos"] = res_active.count or 0
        stats["ativos_list"] = [row["username"] for row in (res_active.data or [])[:10]]
    except Exception as e:
        stats["candidatos_ativos_error"] = str(e)

    # 3. Itens na fila de coleta por status
    try:
        res_fila = db.table("fila_coleta").select("status").execute()
        fila_data = res_fila.data or []
        fila_stats = {}
        for row in fila_data:
            s = row.get("status", "desconhecido")
            fila_stats[s] = fila_stats.get(s, 0) + 1
        stats["fila_por_status"] = fila_stats
        stats["total_fila"] = len(fila_data)
    except Exception as e:
        stats["fila_error"] = str(e)

    return stats

def do_repopulate():
    db = get_supabase_client()
    print("🔄 Forçando repopulação da fila de coleta...")
    
    try:
        # Busca candidatos ativos
        res_active = db.table("candidatos").select("id,username,termometro").filter("status_monitoramento", "ilike", "Ativo").execute()
        ativos = res_active.data or []
        print(f"   - {len(ativos)} candidatos ativos encontrados.")
        
        # Busca candidatos já enfileirados que não estão concluídos
        res_fila = db.table("fila_coleta").select("candidato_id").in_("status", ["PENDENTE", "EM_CURSO", "EM ANDAMENTO"]).execute()
        in_queue = {row["candidato_id"] for row in (res_fila.data or [])}
        print(f"   - {len(in_queue)} alvos já possuem tarefas pendentes/em curso.")
        
        inserted_count = 0
        for cand in ativos:
            username = cand.get("username")
            if not username or username in in_queue:
                continue
                
            termometro = cand.get("termometro", "MORNO")
            prioridade = 2 if termometro == "QUENTE" else (1 if termometro == "MORNO" else 0)
            
            # Insere na fila tratando erros individuais
            try:
                db.table("fila_coleta").insert({
                    "candidato_id": username,
                    "status": "PENDENTE",
                    "prioridade": prioridade,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }).execute()
                inserted_count += 1
                print(f"     [+] Enfileirado: @{username} (Prioridade: {prioridade})")
            except Exception as e_row:
                # Se for erro de duplicata de chave única, apenas informa de forma limpa
                if "23505" in str(e_row) or "duplicate" in str(e_row).lower():
                    print(f"     [-] @{username} já agendado para hoje (duplicata ignorada).")
                else:
                    print(f"     [-] Erro ao enfileirar @{username}: {e_row}")
            
        print(f"✅ Repopulação concluída. {inserted_count} novos alvos inseridos na fila como PENDENTE.")
    except Exception as e:
        print(f"❌ Falha ao repopular: {e}")

def main():
    parser = argparse.ArgumentParser(description="Sentinela — Repopulation Curation Tool")
    parser.add_argument("--full", action="store_true", help="Diagnóstico completo")
    parser.add_argument("--do-repopulate", action="store_true", help="Força repopulação")
    args = parser.parse_args()

    if not (args.full or args.do_repopulate):
        parser.print_help()
        sys.exit(0)

    print("=" * 70)
    print("SENTINELA — DIAGNÓSTICO DE REPOPULAÇÃO v1.0")
    print("=" * 70)
    print()

    if args.full:
        stats = get_stats()
        print("📊 ESTATÍSTICAS DO BANCO:")
        print(f"   - Total de candidatos cadastrados: {stats.get('total_candidatos')}")
        print(f"   - Total de candidatos ATIVOS: {stats.get('candidatos_ativos')}")
        if "ativos_list" in stats:
            print(f"     Amostra de ativos: {', '.join([f'@{u}' for u in stats['ativos_list']])}")
        print(f"   - Total de registros na fila: {stats.get('total_fila')}")
        print(f"   - Distribuição na fila por status: {json.dumps(stats.get('fila_por_status'), indent=2)}")
        print()
        
        # Verifica se o método existe no queue_manager.py
        qm_path = Path("core/queue_manager.py")
        if qm_path.exists():
            content = qm_path.read_text(encoding="utf-8")
            has_method = "_ensure_queue_populated" in content
            print(f"🔍 CÓDIGO FONTE (queue_manager.py):")
            print(f"   - Possui '_ensure_queue_populated': {'Sim' if has_method else 'Não'}")
        else:
            print("   - queue_manager.py não encontrado.")
        print()

    if args.do_repopulate:
        do_repopulate()

    print("=" * 70)

if __name__ == "__main__":
    main()
