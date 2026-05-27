"""
diagnose_workers.py — Script de Diagnóstico e Auditoria Operacional do Sentinela (v83.0)
Lê logs locais, consulta a telemetria remota do Supabase e consolida o status em logs/diagnostico_recente.md.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

# --- Auto-Anchoring ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

# Ajusta encodings
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass

def parse_local_logs(log_path: str, max_lines: int = 300) -> dict:
    """Busca exceções e erros importantes no log local do main_runner."""
    result = {
        "found": False,
        "errors": [],
        "warnings": [],
        "last_lines": []
    }
    if not os.path.exists(log_path):
        return result

    result["found"] = True
    critical_keywords = [
        "error", "exception", "traceback", "429", "timeout", 
        "rate limit", "sessionid", "fail", "bloque", "solenya"
    ]

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    last_subset = lines[-max_lines:]
    result["last_lines"] = [line.strip() for line in last_subset[-10:]]

    for line in last_subset:
        line_lower = line.lower()
        if any(kw in line_lower for kw in critical_keywords):
            if "error" in line_lower or "exception" in line_lower or "traceback" in line_lower or "429" in line_lower:
                result["errors"].append(line.strip())
            else:
                result["warnings"].append(line.strip())

    return result

def get_db_metrics() -> dict:
    """Busca a telemetria no Supabase remoto."""
    metrics = {
        "connected": False,
        "heartbeats": [],
        "queue_status": {},
        "recent_fails": [],
        "error_msg": ""
    }
    
    try:
        from core.supabase_service import get_supabase_client
        db = get_supabase_client()
        metrics["connected"] = True
        
        # 1. Heartbeats
        hb_res = db.table("system_heartbeat").select("*").execute()
        metrics["heartbeats"] = hb_res.data or []
        
        # 2. Status da Fila
        queue_res = db.table("fila_coleta").select("status").execute()
        for row in (queue_res.data or []):
            st = row.get("status", "UNKNOWN")
            metrics["queue_status"][st] = metrics["queue_status"].get(st, 0) + 1
            
        # 3. Alvos que falharam recentemente
        fails_res = db.table("fila_coleta")\
            .select("username, candidato_id, updated_at")\
            .eq("status", "FALHOU")\
            .order("updated_at", desc=True)\
            .limit(5)\
            .execute()
        metrics["recent_fails"] = fails_res.data or []

    except Exception as e:
        metrics["error_msg"] = str(e)
        
    return metrics

def write_report(log_analysis: dict, db_metrics: dict, output_path: str):
    """Gera o arquivo markdown final consolidando o diagnóstico."""
    now_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S (%Z)")
    
    lines = []
    lines.append(f"# Relatório de Diagnóstico Sentinela Democratica (v83.0)")
    lines.append(f"_Gerado em: {now_str}_\n")
    
    # Seção 1: Status da Fila e Banco Remoto
    lines.append("## 📊 Telemetria Remota (Supabase)")
    if not db_metrics["connected"]:
        lines.append(f"❌ **Falha de Conexão com o Supabase:** `{db_metrics['error_msg']}`\n")
    else:
        lines.append("✅ Conexão com Supabase estabelecida com sucesso.")
        
        # Status de Heartbeats
        lines.append("\n### 💓 Heartbeats Recentes")
        if not db_metrics["heartbeats"]:
            lines.append("⚠️ Nenhum heartbeat registrado no sistema.")
        else:
            lines.append("| Origem | Status | Última Atividade | Metadados |")
            lines.append("|---|---|---|---|")
            for hb in db_metrics["heartbeats"]:
                src = hb.get("source")
                st = hb.get("status")
                upd = hb.get("updated_at")
                meta = hb.get("metadata", {})
                lines.append(f"| `{src}` | **{st}** | {upd} | `{meta}` |")
        
        # Resumo da Fila
        lines.append("\n### 📦 Status da Fila de Coleta")
        qs = db_metrics["queue_status"]
        if not qs:
            lines.append("⚠️ A fila de coleta está vazia ou sem itens registrados.")
        else:
            for k, v in qs.items():
                lines.append(f"- **{k}**: {v} alvos")
                
        # Falhas Recentes
        if db_metrics["recent_fails"]:
            lines.append("\n### ⚠️ Falhas de Coleta Recentes na Fila")
            for f in db_metrics["recent_fails"]:
                usr = f.get("username") or f.get("candidato_id")
                t_str = f.get("updated_at")
                lines.append(f"- Alvo `@{usr}` falhou na última tentativa às `{t_str}`")
        lines.append("")

    # Seção 2: Logs Locais
    lines.append("## 📁 Logs Locais do Runner (`main_runner.log`)")
    if not log_analysis["found"]:
        lines.append("⚠️ Arquivo de log `logs/main_runner.log` não foi encontrado localmente.\n")
    else:
        lines.append("✅ Arquivo de log localizado.")
        
        # Erros Críticos
        lines.append(f"\n### 💥 Erros Críticos Detectados (últimas linhas)")
        errs = log_analysis["errors"]
        if not errs:
            lines.append("✅ Nenhum erro crítico de execução ou exceção encontrado no bloco analisado.")
        else:
            lines.append(f"Foram encontrados **{len(errs)}** alertas de erros nos logs recentes:")
            for e in errs[-15:]: # mostra no máximo os últimos 15 erros
                lines.append(f"- `{e}`")
                
        # Warnings e Jitters
        lines.append(f"\n### ⚠️ Alertas e Avisos Operacionais")
        warns = log_analysis["warnings"]
        if not warns:
            lines.append("✅ Nenhum aviso operacional pendente.")
        else:
            lines.append(f"Existem **{len(warns)}** avisos recentes. Últimas ocorrências:")
            for w in warns[-8:]:
                lines.append(f"- `{w}`")

        # Fim de Arquivo
        lines.append("\n### 📄 Últimas Linhas Gravadas no Log:")
        lines.append("```text")
        for line in log_analysis["last_lines"]:
            lines.append(line)
        lines.append("```\n")
        
    # Recomendações Automáticas de Melhoria
    lines.append("## 💡 Recomendações Automáticas do Diagnóstico")
    recs = []
    
    # Analisa falhas no supabase
    if not db_metrics["connected"]:
        recs.append("- **Ação Corretiva**: Verifique as variáveis de ambiente locais `.env` (chaves do Supabase expiradas ou inválidas).")
    
    # Analisa quantidade de erros e bloqueio de sessões
    errors_str = " ".join(log_analysis.get("errors", [])).lower()
    if "sess" in errors_str or "bloqueada" in errors_str or "429" in errors_str:
        recs.append("- **🚨 AÇÃO CRÍTICA**: Bloqueio de sessão detectado! O scraper reportou `'Todas as sessões estão bloqueadas!'`. Recomenda-se renovar as cookies e o `INSTAGRAM_SESSIONID` no seu arquivo `.env` local e nos Repository Secrets do GitHub.")
    elif len(log_analysis.get("errors", [])) > 5:
        recs.append("- **Ação Corretiva**: Taxa de falha elevada detectada no runner local (mais de 5 erros recentes). Recomenda-se analisar se há problemas de conexão ou rate limit temporário.")
        
    # Analisa fila vazia
    if db_metrics.get("connected") and not db_metrics["queue_status"].get("PENDENTE"):
        recs.append("- **Ação Operacional**: Fila sem alvos PENDENTES. Execute o script de repopulação `scripts/cloud_queue_refresh.py` para alimentar o sistema.")

    if not recs:
        recs.append("- ✨ **Tudo saudável**: Todos os subsistemas e conexões locais/remotas operam sob parâmetros normais.")
        
    for r in recs:
        lines.append(r)
        
    lines.append("\n---")
    lines.append("_Sentinela Autopilot Diagnostic Tool_")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    log_file = "logs/main_runner.log"
    report_file = "logs/diagnostico_recente.md"
    
    print("🤖 Iniciando consolidação do diagnóstico dos workers...")
    logs = parse_local_logs(log_file)
    db_data = get_db_metrics()
    write_report(logs, db_data, report_file)
    print(f"✅ Diagnóstico consolidado com sucesso em: {report_file}")
