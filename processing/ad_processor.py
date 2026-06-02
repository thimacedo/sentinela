import asyncio
import logging
from typing import List, Dict, Any
from core.db import db_client
from core.ai_service import AIService
from .common import BaseWorker

logger = logging.getLogger("AdProcessor")

class AdProcessor(BaseWorker):
    """
    Processador de inteligência para anúncios da Meta.
    Aplica o Protocolo PASA v16.4 para classificar o conteúdo.
    """
    
    def __init__(self, batch_size: int = 50, poll_interval: int = 10):
        super().__init__("AdProcessor", batch_size, poll_interval)
        self.ai_service = AIService()

    async def fetch_pending_items(self, limit: int) -> List[Dict[str, Any]]:
        """Busca anúncios não processados no banco de dados."""
        return await db_client.fetch_unprocessed_ads(limit=limit)

    async def process_item_batch(self, items: List[Dict[str, Any]]) -> None:
        """Processa um lote de anúncios e aplica classificação de IA em massa."""
        if not items:
            return

        self.logger.info(f"⛏️ [AdProcessor] Processando {len(items)} anúncios...")
        updates = []
        
        for ad in items:
            ad_id = ad['id']
            corpo = ad.get('corpo_anuncio') or ""
            
            if not corpo:
                # Se não tem corpo, marca como processado neutro
                updates.append({
                    "id": ad_id,
                    "processado_ia": True,
                    "categoria_ia": "NEUTRO",
                    "is_hate": False
                })
                continue

            try:
                # Classifica via PASA v16.4
                classification = await self.ai_service.classify(corpo, comment_id=ad_id)
                
                updates.append({
                    "id": ad_id,
                    "categoria_ia": classification.get('categoria_ia', 'NEUTRO'),
                    "confianca_ia": classification.get('confianca_ia', 0.0),
                    "is_hate": classification['is_hate'],
                    "processado_ia": True if classification.get('engine') != 'fail' else False
                })
                
            except Exception as e:
                await self.handle_failure(ad, e)

        if updates:
            await db_client.batch_update_ad_classification(updates)
            self.logger.info(f"✅ [AdProcessor] {len(updates)} anúncios atualizados no banco.")

    async def handle_failure(self, item: Dict[str, Any], error: Exception) -> None:
        """Lida com falhas no processamento de um anúncio específico."""
        self.logger.error(f"⚠️ Erro ao processar anúncio {item.get('ad_id')}: {error}")

ad_processor = AdProcessor()
