import pandas as pd
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import os
import logging
from .common import BaseWorker
from core.db import db_client
from typing import List, Dict, Any

class DataMiner(BaseWorker):
    """
    Worker para mineração temática e análise de dados (PASA v98.6).
    Transforma dados brutos processados pela IA em clusters e tendências temáticas
    usando lematização avançada do Stanza e suporte opcional a embeddings GloVe.
    """
    def __init__(self, batch_size: int = 200, poll_interval: int = 60, output_dir="visualizacoes"):
        super().__init__(name="DataMiner", batch_size=batch_size, poll_interval=poll_interval)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._glove_embeddings = None

    def _load_glove_embeddings(self) -> Dict[str, np.ndarray]:
        """Carrega os embeddings do GloVe em cache se o arquivo estiver disponível localmente."""
        if self._glove_embeddings is not None:
            return self._glove_embeddings

        glove_path = os.getenv("GLOVE_PATH") or "data/glove_s50.txt"
        embeddings = {}
        if not os.path.exists(glove_path):
            self.logger.debug(f"[GloVe] Arquivo de embeddings não encontrado em '{glove_path}'. Usando fallback para TF-IDF lematizado.")
            self._glove_embeddings = {}
            return self._glove_embeddings

        try:
            self.logger.info(f"[GloVe] Carregando embeddings do arquivo '{glove_path}'...")
            with open(glove_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts or len(parts) < 2:
                        continue
                    word = parts[0]
                    vector = np.array(parts[1:], dtype=np.float32)
                    embeddings[word] = vector
            self.logger.info(f"[GloVe] {len(embeddings)} palavras carregadas com sucesso.")
        except Exception as e:
            self.logger.warning(f"[GloVe] Falha ao carregar embeddings: {e}")
        
        self._glove_embeddings = embeddings
        return self._glove_embeddings

    async def fetch_pending_items(self, limit: int) -> List[Dict[str, Any]]:
        """Busca itens processados pela IA mas ainda não minerados."""
        return await db_client.fetch_unmined_comments(limit=limit)

    async def process_item_batch(self, items: List[Dict[str, Any]]) -> None:
        """Executa a clusterização temática no lote de itens."""
        if not items:
            return

        df = pd.DataFrame(items)
        is_hate_col = 'is_hate' if 'is_hate' in df.columns else 'is_hate_speech'

        # Garante que a coluna de ódio existe e é booleana
        if is_hate_col not in df.columns:
            df[is_hate_col] = False
        else:
            df[is_hate_col] = df[is_hate_col].fillna(False).astype(bool)

        hate_df = df[df[is_hate_col] == True].copy()

        if len(hate_df) < 5:
            self.logger.info("⚠️ Dados insuficientes no lote para clusterização temática real. Marcando apenas como minerados.")
            updates = [{"id": item['id'], "mined": True} for item in items]
            await db_client.batch_update_comments(updates)
            return

        try:
            # 1. Lematização dos textos usando Stanza para unificação morfológica
            from core.stanza_nlp import stanza_nlp
            lemmatized_texts = []
            text_col = 'texto_limpo' if 'texto_limpo' in hate_df.columns else 'text'

            for _, row in hate_df.iterrows():
                analise_ling = row.get("analise_linguistica")
                lemmas = []
                
                if isinstance(analise_ling, dict) and "lemmas" in analise_ling:
                    lemmas = analise_ling["lemmas"]
                elif isinstance(analise_ling, str):
                    try:
                        parsed_ling = json.loads(analise_ling)
                        if isinstance(parsed_ling, dict) and "lemmas" in parsed_ling:
                            lemmas = parsed_ling["lemmas"]
                    except:
                        pass

                # Se não havia análise linguística pré-calculada, processa em tempo real
                if not lemmas:
                    text_val = str(row.get(text_col, "") or row.get("texto_bruto", "")).strip()
                    res_nlp = stanza_nlp.processar_texto(text_val)
                    lemmas = res_nlp.get("lemmas", [])

                lemmatized_texts.append(" ".join(lemmas) if lemmas else str(row.get(text_col, "")))

            if not any(lemmatized_texts):
                self.logger.warning("⚠️ Textos lematizados vazios no lote. Pulando clusterização.")
                updates = [{"id": item['id'], "mined": True} for item in items]
                await db_client.batch_update_comments(updates)
                return

            # 2. Vetorização (GloVe vs TF-IDF lematizado)
            glove_embeds = self._load_glove_embeddings()
            
            if glove_embeds:
                X_list = []
                # Pega a dimensão do primeiro vetor disponível
                dim = next(iter(glove_embeds.values())).shape[0]
                
                for text in lemmatized_texts:
                    words = text.split()
                    vectors = [glove_embeds[w] for w in words if w in glove_embeds]
                    if vectors:
                        X_list.append(np.mean(vectors, axis=0))
                    else:
                        X_list.append(np.zeros(dim, dtype=np.float32))
                X = np.array(X_list)
                self.logger.debug(f"[Miner] Vetorização concluída via GloVe local (Dimensão: {dim}).")
            else:
                vectorizer = TfidfVectorizer(max_features=100, stop_words=None)
                X = vectorizer.fit_transform(lemmatized_texts)
                self.logger.debug("[Miner] Vetorização concluída via TF-IDF com lemmas.")

            # 3. Define clusters (mínimo 2, máximo 5)
            n_clusters = min(5, max(2, len(hate_df) // 3))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            hate_df['cluster'] = kmeans.fit_predict(X)

            # Prepara updates para o banco
            updates_map = {item['id']: {"id": item['id'], "mined": True, "cluster_id": None} for item in items}

            for _, row in hate_df.iterrows():
                item_id = row['id']
                if item_id in updates_map:
                    updates_map[item_id]["cluster_id"] = int(row['cluster'])

            updates = list(updates_map.values())

            if updates:
                await db_client.batch_update_comments(updates)
                self.logger.info(f"✅ {len(updates)} itens minerados ({len(hate_df)} clusterizados em {n_clusters} grupos) e atualizados no DB.")

        except Exception as e:
            self.logger.error(f"❌ Erro na mineração temática real: {e}", exc_info=True)
            # Fallback: marca como minerado para não travar a fila
            updates = [{"id": item['id'], "mined": True} for item in items]
            await db_client.batch_update_comments(updates)

    async def handle_failure(self, item: Dict[str, Any], error: Exception) -> None:
        self.logger.error(f"❌ Falha ao minerar item {item.get('id')}: {error}")

    def extrair_ngrams_periciais(self, df, coluna='bigrams', top_k=20):
        if coluna not in df.columns: 
            return []
        all_grams = [gram for lista in df[coluna] for g in lista if isinstance(lista, list)]
        return Counter(all_grams).most_common(top_k)

data_miner = DataMiner()
