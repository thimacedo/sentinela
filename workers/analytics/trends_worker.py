import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from core.supabase_service import get_supabase_client

def _json_to_markdown(data: dict) -> str:
    """Convert the trends JSON structure to a simple Markdown report."""
    lines = ["# Relatório de Tendências", f"Gerado em: {data.get('generated_at', '')}\n"]
    counts = data.get('counts', {})
    lines.append("## Contagem de alertas por dia")
    for date, count in sorted(counts.items()):
        lines.append(f"- **{date}**: {count} alertas")
    return "\n".join(lines)



def generate_trends(days: int = 7) -> str:
    """Generate trend data for the last `days` days.
    Returns the path to the generated JSON file.
    """
    db = get_supabase_client()
    # Simple example: count alerts per day
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)
    # Supabase query: assuming a table `alerts` with `data_coleta` datetime field
    res = (
        db.table("alerts")
        .select("id, data_coleta")
        .gte("data_coleta", start_date.isoformat())
        .lte("data_coleta", end_date.isoformat())
        .execute()
    )
    alerts = res.data if res and hasattr(res, "data") else []
    # Aggregate counts per day
    counts = {str(start_date + timedelta(days=i)): 0 for i in range(days)}
    for a in alerts:
        try:
            dt = datetime.fromisoformat(a["data_coleta"]).date()
            if str(dt) in counts:
                counts[str(dt)] += 1
        except Exception:
            continue
    # Prepare output structure
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period_days": days,
        "counts": counts,
    }
    reports_dir = Path(__file__).resolve().parents[2] / "frontend" / "public" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"trends_{end_date.isoformat()}.json"
    out_path = reports_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    # gerar markdown
    md_content = _json_to_markdown(output)
    md_path = reports_dir / f"trends_{end_date.isoformat()}.md"
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write(md_content)
    return str(out_path)
