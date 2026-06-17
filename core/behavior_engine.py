import logging
import json
import random
from typing import List, Dict, Any

from core.ai_service import ai_service

logger = logging.getLogger("core.behavior_engine")

class BehaviorEngine:
    """
    Módulo Solenya (v95.0) - Agente de Inteligência e Disinformation Analysis.
    Substituiu a contagem burra de N-Gramas (SpaCy) por Avaliação Semântica Larga
    via LLMs para detectar campanhas coordenadas de desinformação através do contexto.
    """
    
    def __init__(self):
        pass

    async def detect_coordinated_clusters(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Análise OODA Híbrida:
        Observe: Coleta lote de comentários curtos em intervalo curto de tempo.
        Orient: Reúne textos para análise de lote.
        Decide: Consulta à IA de triagem rápida se os discursos possuem mesma intenção sintática dissimulada.
        Act: Etiqueta o cluster.
        """
        if len(comments) < 3: 
            return comments

        # Prepara Lote Textual
        batch_text = ""
        index_map = {}
        for idx, c in enumerate(comments):
            txt = c.get("texto_bruto", "").strip()
            if len(txt) > 5:
                batch_text += f"[{idx}] {txt}\n"
                index_map[str(idx)] = c
                
        if not batch_text:
            return comments

        prompt = f"""
        Você é o "Solenya", o Analista Chefe de Desinformação do Sentinela.
        Sua missão é ler um lote de comentários de redes sociais extraídos no mesmo minuto e determinar se há um Ataque Coordenado (Swarm/Milícia Digital).
        
        As campanhas coordenadas modernas não copiam e colam o mesmo texto exato; eles usam sinônimos para o mesmo núcleo argumentativo ou narrativa estrutural.
        Leia os comentários abaixo e agrupe pelo Índice (IDs entre colchetes) aqueles que compartilham EXATAMENTE a mesma métrica argumentativa estruturada, não apenas a mesma opinião política.
        
        LOTE DE COMENTÁRIOS:
        {batch_text}
        
        Retorne um JSON estrito no seguinte formato:
        {{
            "clusters": [
                {{
                    "ids": ["0", "2", "5"],
                    "narrative_core": "Narrativa identificada que une os textos",
                    "confidence": 0.9
                }}
            ]
        }}
        Se não houver coordenação de no mínimo 3 IDs no mesmo cluster, retorne "clusters": [].
        """
        try:
            # Invoca modelo de triagem veloz (Mistral/Flash)
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)
            
            clusters = data.get("clusters", [])
            for cl in clusters:
                ids = cl.get("ids", [])
                if len(ids) >= 3:
                    cluster_id = f"solenya_cog_{random.randint(1000, 9999)}"
                    logger.info(f"🤖 [Solenya] Swarm Semântico Detectado! IDs: {ids} | Núcleo: {cl.get('narrative_core')}")
                    
                    for string_id in ids:
                        if string_id in index_map:
                            ref = index_map[string_id]
                            ref["is_bot"] = True
                            ref["bot_pattern"] = "COORDENACAO_SEMANTICA"
                            ref["cluster_id"] = cluster_id
                            ref["cluster_size"] = len(ids)
                            ref["slogans_detectados"] = [cl.get("narrative_core")]
                            
        except Exception as e:
            logger.error(f"[Solenya] Erro na inferência cognitiva de clusters: {e}")

        return comments

behavior_engine = BehaviorEngine()
