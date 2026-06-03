from __future__ import annotations
import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta, timezone
from collections import Counter
import pandas as pd
import networkx as nx
from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.db import db_client

logger = logging.getLogger("worker.network_miner")

class NetworkMinerWorker(BaseWorker):
    """
    Worker: NetworkMiner (Deteccao de Clusters e Coordenacao)
    Finalidade: Analisar o grafo de interacoes e identificar comunidades suspeitas.
    Alimenta a tabela 'redes_coordenadas' para o frontend.
    PASA v85.13
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.lookback_days = config.get("lookback_days", 7)
        self.min_similarity = config.get("min_similarity", 0.8)

    def describe(self) -> str:
        return "Motor de Analise de Redes Coordenadas e Clusters"

    async def setup(self) -> None:
        logger.info(f"🕸️ NetworkMinerWorker {self.worker_id} pronto para minerar.")

    async def teardown(self) -> None:
        logger.info(f"🛑 NetworkMinerWorker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        try:
            # 1. Busca dados recentes (7 dias) para mapeamento
            now = datetime.now(timezone.utc)
            since = (now - timedelta(days=self.lookback_days)).isoformat()
            
            # Pega amostra significativa para deteccao de clusters
            res = db_client.client.table('comentarios')\
                .select('id, autor_username, candidato_id, texto_bruto, categoria_ia, data_coleta')\
                .eq('is_hate', True)\
                .gte('data_coleta', since)\
                .limit(2000).execute()
            
            data = res.data or []
            if len(data) < 10:
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle,
                    source="network_miner", error="no_tasks_available",
                    duration=asyncio.get_event_loop().time() - start_time
                )

            # 2. Processamento via NetworkX & Pandas
            df = pd.DataFrame(data)
            
            # Identifica contas que atacam multiplos alvos (indicador de coordenacao)
            attacker_counts = df.groupby('autor_username')['candidato_id'].nunique()
            multi_attackers = attacker_counts[attacker_counts > 1].index.tolist()
            
            # Gera o Grafo de Influencia
            G = nx.Graph()
            for _, row in df.iterrows():
                u, c = row['autor_username'], row['candidato_id']
                if not u or not c: continue
                
                # Adiciona aresta entre autor e candidato atacado
                if G.has_edge(u, c):
                    G[u][c]['weight'] += 1
                else:
                    G.add_edge(u, c, weight=1, type='attack')

            # Detecta comunidades (clusters)
            # Simplificacao para MVP: Componentes conectados ou cliques
            communities = list(nx.connected_components(G))
            Suspect_Clusters = []
            
            for i, comm in enumerate(communities):
                if len(comm) < 3: continue # Ignora micro-interacoes
                
                nodes = list(comm)
                edges = []
                for u, v, d in G.edges(nodes, data=True):
                    if u in comm and v in comm:
                        edges.append({"from": u, "to": v, "weight": d['weight']})
                
                # Calcula severidade do cluster
                cluster_df = df[df['autor_username'].isin(comm) | df['candidato_id'].isin(comm)]
                hate_types = cluster_df['categoria_ia'].value_counts().to_dict()
                
                cluster_meta = {
                    "nome_rede": f"Cluster de Ataque #{i+1} ({len(comm)} nodes)",
                    "tipo_coordenacao": "MULTI_TARGET" if any(a in comm for a in multi_attackers) else "SINGLE_TARGET",
                    "nodes": nodes,
                    "edges": edges,
                    "estatisticas": {
                        "total_interacoes": len(cluster_df),
                        "principais_categorias": hate_types,
                        "contas_coordenadas": len([a for a in comm if a in multi_attackers])
                    },
                    "score_perigoso": min(100, len(comm) * 5 + len(cluster_df) // 10)
                }
                Suspect_Clusters.append(cluster_meta)

            # 3. Persiste o Top Cluster mais relevante no banco
            if Suspect_Clusters:
                top_cluster = sorted(Suspect_Clusters, key=lambda x: x['score_perigoso'], reverse=True)[0]
                
                # Gera um ID compatível com UUID v4
                raw_hash = hashlib.md5(top_cluster["nome_rede"].encode()).hexdigest()
                uuid_str = f"{raw_hash[:8]}-{raw_hash[8:12]}-4{raw_hash[13:16]}-a{raw_hash[17:20]}-{raw_hash[20:32]}"
                
                db_client.client.table('redes_coordenadas').upsert({
                    "id": uuid_str,
                    "nome_rede": top_cluster["nome_rede"],
                    "tipo_coordenacao": top_cluster["tipo_coordenacao"],
                    "nodes": top_cluster["nodes"],
                    "edges": top_cluster["edges"],
                    "estatisticas": top_cluster["estatisticas"],
                    "score_perigoso": top_cluster["score_perigoso"],
                    "created_at": now.isoformat()
                }).execute()
                
                logger.info(f"✨ [Network] Cluster detectado: {top_cluster['nome_rede']} (Score: {top_cluster['score_perigoso']})")

            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                target="global_network", source="network_miner",
                extracted=len(data), classified=len(Suspect_Clusters),
                db_success=True, classifier_success=True,
                duration=asyncio.get_event_loop().time() - start_time
            )

        except Exception as e:
            logger.error(f"💥 Erro no NetworkMinerWorker: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                failed=1, error=str(e)[:200], simulated=False,
                duration=asyncio.get_event_loop().time() - start_time
            )


def generate_network() -> str:
    """Busca o cluster de rede coordenada mais recente e gera o relatório correspondente."""
    from pathlib import Path
    db = db_client
    end_date = datetime.utcnow().date()
    
    try:
        # Pega a rede coordenada mais recente do Supabase
        res = db.client.table('redes_coordenadas')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(1).execute()
        
        network_data = res.data[0] if res.data else {}
    except Exception as e:
        print(f"❌ Erro ao buscar rede no Supabase: {e}")
        network_data = {}
        
    reports_dir = Path(__file__).resolve().parents[2] / "frontend" / "public" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"network_{end_date.isoformat()}.json"
    out_path = reports_dir / filename
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(network_data, f, ensure_ascii=False, indent=2)
        
    # Gera um markdown básico para acompanhamento
    lines = [
        "# Relatório de Redes Coordenadas",
        f"Gerado em: {datetime.utcnow().isoformat()}Z\n",
        f"## Nome da Rede: {network_data.get('nome_rede', 'N/A')}",
        f"- **Tipo de Coordenação:** {network_data.get('tipo_coordenacao', 'N/A')}",
        f"- **Score de Perigo:** {network_data.get('score_perigoso', 0)}",
        f"- **Nós envolvidos:** {len(network_data.get('nodes', []))} contas",
        f"- **Arestas (ligações):** {len(network_data.get('edges', []))} conexões"
    ]
    
    md_path = reports_dir / f"network_{end_date.isoformat()}.md"
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write("\n".join(lines))
        
    return str(out_path)

