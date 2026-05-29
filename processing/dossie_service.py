import hashlib
import json
import os
import asyncio
from datetime import datetime
from processing.report_generator import ReportGenerator
from core.db import db_client

class DossieService:
    """
    Serviço para geração de dossiês forenses com persistência estruturada.
    PASA v85.9 (Otimizado para integridade e performance)
    """
    def __init__(self):
        self.generator = ReportGenerator()

    async def generate_dossie(self, data, path, candidato_id: str):
        """
        Gera o PDF e persiste os metadados no banco de dados.
        """
        if not data:
            print(f"⚠️ [DossieService] Nenhum dado para gerar dossiê de @{candidato_id}.")
            return None

        # 1. Calcula Metadados Forenses para o Selo de Integridade
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        total_comentarios = len(data)
        total_hate = len([item for item in data if item.get('is_hate')])

        # 2. Gera o PDF físico (Executa em thread para não bloquear o loop de eventos)
        # FPDF é síncrono e intensivo em CPU
        loop = asyncio.get_event_loop()
        pdf_path = await loop.run_in_executor(
            None, 
            self.generator.generate_pdf, 
            data, path, candidato_id
        )
        
        if pdf_path:
            # 3. Persistência Estruturada no Supabase
            dossie_meta = {
                "candidato_id": candidato_id,
                "hash_integridade": data_hash,
                "total_comentarios": total_comentarios,
                "total_hate": total_hate,
                "arquivo_path": pdf_path,
                "versao_pasa": "v85.9",
                "data_geracao": datetime.now().isoformat()
            }
            await db_client.persist_dossier(dossie_meta)
            print(f"✨ [DossieService] Inteligência do dossiê {data_hash[:10]} persistida no repositório.")
            
        return pdf_path

dossie_service = DossieService()
