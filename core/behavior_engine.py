import logging
import re
import random
from typing import List, Dict, Any, Tuple
from collections import Counter

logger = logging.getLogger("core.behavior_engine")

class BehaviorEngine:
    """
    Módulo Solenya (v94.4) - Detecção de Comportamento Coordenado.
    Identifica clusters de similaridade e slogans (N-Gramas) para detectar 
    campanhas coordenadas de desinformação ou ataque.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._nlp = None
        self._stopwords = set()
        
        # Slogan patterns to ignore (common noisy bigrams)
        self.ignore_ngrams = {
            "o de", "a de", "e a", "o que", "e o", "do que", "da de", "é o", "é a",
            "que o", "que a", "um de", "uma de", "de um", "de uma", "com o", "com a"
        }

    def _get_nlp(self):
        """Lazy load do spacy para evitar overhead no boot se não for usado."""
        if self._nlp is None:
            try:
                import spacy
                # Tenta carregar o modelo de português
                try:
                    self._nlp = spacy.load("pt_core_news_sm")
                except:
                    logger.warning("⚠️ [Solenya] Modelo spacy 'pt_core_news_sm' não encontrado. Usando split básico.")
                    self._nlp = False # Sinaliza falha
            except ImportError:
                logger.warning("⚠️ [Solenya] Biblioteca 'spacy' não instalada.")
                self._nlp = False
        return self._nlp

    def extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Extrai n-gramas (bigramas/trigramas) do texto."""
        text = re.sub(r'[^\w\s]', ' ', text.lower()).strip()
        words = [w for w in text.split() if len(w) > 1]
        
        if len(words) < n: return []
        
        grams = []
        for i in range(len(words) - n + 1):
            gram = " ".join(words[i : i + n])
            if gram not in self.ignore_ngrams:
                grams.append(gram)
        return grams

    def simple_similarity(self, s1: str, s2: str) -> float:
        """Calcula similaridade baseada em interseção de palavras."""
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
        Análise Híbrida: Similaridade Semântica + N-Gramas (Slogans).
        Retorna a lista enriquecida com metadados de coordenação.
        """
        if len(comments) < 2: return comments
        
        # 1. Extração de Slogans (N-Gramas frequentes)
        all_bigrams = []
        all_trigrams = []
        
        for c in comments:
            text = c.get("texto_bruto", "")
            if len(text) > 10:
                all_bigrams.extend(self.extract_ngrams(text, 2))
                all_trigrams.extend(self.extract_ngrams(text, 3))
        
        # Identifica slogans (trigramas que repetem > 3x)
        trigram_counts = Counter(all_trigrams)
        slogans = {gram for gram, count in trigram_counts.items() if count >= 3}
        
        # 2. Clustering por Similaridade e Slogan
        processed_indices = set()
        final_list = []

        for i, c1 in enumerate(comments):
            if i in processed_indices: continue
            
            current_cluster = [c1]
            processed_indices.add(i)
            text1 = c1.get("texto_bruto", "").lower()
            
            # Verifica se o comentário contém algum slogan global
            found_slogans = [s for s in slogans if s in text1]

            for j, c2 in enumerate(comments):
                if j in processed_indices: continue
                
                text2 = c2.get("texto_bruto", "").lower()
                if len(text1) < 10 or len(text2) < 10: continue

                # Critério A: Similaridade Global
                is_similar = self.simple_similarity(text1, text2) >= self.similarity_threshold
                
                # Critério B: Compartilhamento de Slogan
                shares_slogan = any(s in text2 for s in found_slogans)

                if is_similar or shares_slogan:
                    current_cluster.append(c2)
                    processed_indices.add(j)

            # 3. Marcação de Resultado
            if len(current_cluster) >= 3:
                cluster_id = f"solenya_{random.randint(1000, 9999)}_{len(current_cluster)}"
                pattern = "SLOGAN_REPETITIVO" if found_slogans else "COPY_PASTE_COORDENADO"
                
                for c in current_cluster:
                    c["is_bot"] = True
                    c["bot_pattern"] = pattern
                    c["cluster_id"] = cluster_id
                    c["cluster_size"] = len(current_cluster)
                    if found_slogans:
                        c["slogans_detectados"] = list(set(found_slogans))
                
                logger.info(f"🤖 [Solenya] Coordenação Detectada: {len(current_cluster)} itens | Padrão: {pattern}")
            
            final_list.extend(current_cluster)

        return final_list

behavior_engine = BehaviorEngine()
