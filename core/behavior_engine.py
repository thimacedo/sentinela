import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("core.behavior_engine")

class BehaviorEngine:
    """
    Módulo Solenya (v71.0) - Detecção de Comportamento Coordenado.
    Identifica clusters de similaridade para detectar bots sem descartar dados.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def simple_similarity(self, s1: str, s2: str) -> float:
        """Calcula similaridade básica baseada em interseção de palavras (fallback para Levenshtein)."""
        s1 = re.sub(r'[^\w\s]', '', s1.lower())
        s2 = re.sub(r'[^\w\s]', '', s2.lower())
        
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2: return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def detect_coordinated_clusters(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Agrupa comentários similares. 
        Retorna a lista original com marcações de cluster e bot.
        """
        if len(comments) < 2: return comments
        
        clusters = []
        processed_indices = set()

        for i, c1 in enumerate(comments):
            if i in processed_indices: continue
            
            current_cluster = [c1]
            processed_indices.add(i)
            text1 = c1.get("texto_bruto", "")

            for j, c2 in enumerate(comments):
                if j in processed_indices: continue
                
                text2 = c2.get("texto_bruto", "")
                # Ignora textos muito curtos no clustering (já tratados pelo filtro léxico)
                if len(text1) < 10 or len(text2) < 10: continue

                if self.simple_similarity(text1, text2) >= self.similarity_threshold:
                    current_cluster.append(c2)
                    processed_indices.add(j)

            # Se o grupo tem mais de 2 repetições, marcamos como suspeita coordenada
            if len(current_cluster) >= 3:
                cluster_id = f"bot_cluster_{i}_{len(current_cluster)}"
                for c in current_cluster:
                    c["is_bot"] = True
                    c["bot_pattern"] = "SIMILARIDADE_TEXTUAL_COORDENADA"
                    c["cluster_id"] = cluster_id
                    c["cluster_size"] = len(current_cluster)
                
                logger.info(f"🤖 [Solenya] Cluster Detectado: {len(current_cluster)} comentários similares (ID: {cluster_id})")
            
            clusters.extend(current_cluster)

        return clusters

behavior_engine = BehaviorEngine()
