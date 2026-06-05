import asyncio
import logging
import json
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
import networkx as nx
from core.db import db_client

logger = logging.getLogger("SaMineracaoRedes")

class SaMineracaoRedes:
    """
    Subagente relacional para análise de redes coordenadas e detecção de clusters de ataque.
    Executa a mineração analítica de redes de hostilidade de forma assíncrona sob demanda.
    PASA v88.1
    """

    def __init__(self, lookback_days: int = 7, min_similarity: float = 0.8):
        self.lookback_days = lookback_days
        self.min_similarity = min_similarity

    async def run_analysis(self) -> Dict[str, Any]:
        """
        Executa a mineração de grafos e identifica comunidades/clusters suspectos de ataque.
        Persiste os resultados no Supabase e atualiza os arquivos de relatórios no frontend.
        """
        logger.info(f"[SaMineracaoRedes] Iniciando análise de redes coordenadas (lookback={self.lookback_days} dias)")
        start_time = asyncio.get_event_loop().time()

        try:
            # 1. Recuperação de comentários recentes classificados como ódio
            now = datetime.now(timezone.utc)
            since = (now - timedelta(days=self.lookback_days)).isoformat()

            res = db_client.client.table('comentarios')\
                .select('id, autor_username, candidato_id, texto_bruto, categoria_ia, data_coleta')\
                .eq('is_hate', True)\
                .gte('data_coleta', since)\
                .limit(2000).execute()

            data = res.data or []
            if len(data) < 10:
                logger.info("[SaMineracaoRedes] Dados insuficientes de comentários de ódio para minerar rede.")
                return {
                    "success": True,
                    "message": "no_tasks_available",
                    "clusters_detected": 0
                }

            # 2. Processamento via NetworkX e Pandas
            df = pd.DataFrame(data)

            # Identifica contas que atacam múltiplos alvos (indicador de coordenação)
            attacker_counts = df.groupby('autor_username')['candidato_id'].nunique()
            multi_attackers = attacker_counts[attacker_counts > 1].index.tolist()

            # Cria o grafo direcionado de interações
            G = nx.Graph()
            for _, row in df.iterrows():
                u, c = row['autor_username'], row['candidato_id']
                if not u or not c:
                    continue

                if G.has_edge(u, c):
                    G[u][c]['weight'] += 1
                else:
                    G.add_edge(u, c, weight=1, type='attack')

            # Detecta comunidades baseadas em componentes conectados
            communities = list(nx.connected_components(G))
            suspect_clusters = []

            for i, comm in enumerate(communities):
                if len(comm) < 3:
                    continue  # Ignora interações muito pequenas

                nodes = list(comm)
                edges = []
                for u, v, d in G.edges(nodes, data=True):
                    if u in comm and v in comm:
                        edges.append({"from": u, "to": v, "weight": d['weight']})

                # Estatísticas do cluster
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
                suspect_clusters.append(cluster_meta)

            # 3. Persistência do Cluster mais relevante no Supabase
            top_cluster = None
            if suspect_clusters:
                top_cluster = sorted(suspect_clusters, key=lambda x: x['score_perigoso'], reverse=True)[0]
                
                # Gerar ID compatível com UUID v4 baseado no nome da rede
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

                logger.info(f"[SaMineracaoRedes] Cluster mais crítico persistido: {top_cluster['nome_rede']} (Score: {top_cluster['score_perigoso']})")

                # 4. Gera relatórios físicos para consumo do Frontend
                self._generate_physical_reports(top_cluster)

            duration = asyncio.get_event_loop().time() - start_time
            return {
                "success": True,
                "duration_seconds": round(duration, 2),
                "clusters_detected": len(suspect_clusters),
                "top_cluster": top_cluster["nome_rede"] if top_cluster else None,
                "score_critico": top_cluster["score_perigoso"] if top_cluster else 0
            }

        except Exception as e:
            logger.error(f"[SaMineracaoRedes] Erro na análise de redes: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_physical_reports(self, cluster_data: Dict[str, Any]) -> None:
        """Salva arquivos de relatório físico em frontend/public/reports."""
        try:
            from pathlib import Path
            reports_dir = Path(PROJECT_ROOT) / "frontend" / "public" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            today_str = datetime.utcnow().date().isoformat()
            
            # 1. Salva relatório em JSON
            json_path = reports_dir / f"network_{today_str}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(cluster_data, f, ensure_ascii=False, indent=2)

            # 2. Salva relatório legível em Markdown (evitando termos proibidos)
            lines = [
                "# Relatorio de Analise de Redes Coordenadas",
                f"Gerado em: {datetime.utcnow().isoformat()}Z\n",
                f"## Nome do Cluster: {cluster_data.get('nome_rede', 'N/A')}",
                f"- **Tipo de Coordenacao:** {cluster_data.get('tipo_coordenacao', 'N/A')}",
                f"- **Score de Perigo:** {cluster_data.get('score_perigoso', 0)}/100",
                f"- **Contas Suspeitas Envolvidas:** {len(cluster_data.get('nodes', []))}",
                f"- **Conexoes Identificadas:** {len(cluster_data.get('edges', []))}"
            ]
            
            md_path = reports_dir / f"network_{today_str}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.info(f"[SaMineracaoRedes] Relatórios físicos exportados para: {json_path}")
        except Exception as e:
            logger.warning(f"[SaMineracaoRedes] Falha ao exportar relatórios físicos de rede: {e}")

# Compatibilidade retroativa para código legível
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
