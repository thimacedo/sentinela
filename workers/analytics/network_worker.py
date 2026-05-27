import os
import json
from datetime import datetime
from pathlib import Path
import networkx as nx

from core.supabase_service import get_supabase_client

def generate_network() -> str:
    """Generate a coordinated network graph based on interactions.
    Returns the path to the generated JSON file (node-link format).
    """
    db = get_supabase_client()
    # Example: table `interactions` with columns `source`, `target`
    res = db.table("interactions").select("source, target").execute()
    rows = res.data if res and hasattr(res, "data") else []
    G = nx.DiGraph()
    for row in rows:
        src = row.get("source")
        tgt = row.get("target")
        if src and tgt:
            G.add_edge(src, tgt)
    # Export to node-link JSON (compatible with d3)
    data = nx.node_link_data(G)
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "graph": data,
    }
    reports_dir = Path(__file__).resolve().parents[3] / "frontend" / "public" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"network_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    out_path = reports_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return str(out_path)
