# -*- coding: utf-8 -*-
"""
Script de Saneamento Lexical - Sentinela (v84.2)
Objetivo: Corrigir comentários classificados erroneamente como ódio no Supabase
que contêm apenas menções de usuários (@username) ou lixo de baixa qualidade.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Adicionar raiz do projeto ao PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.lexical_filter import lexical_filter
from core.supabase_service import supabase

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def sanear_banco():
    logging.info("🔍 [Saneamento] Buscando comentários com classificação de ódio ativa para varredura...")
    
    # Busca comentários com is_hate = True
    # Faremos paginação simples em lotes de 1000 para evitar limites de timeout ou buffers
    offset = 0
    limit = 1000
    total_corrigidos = 0
    
    while True:
        try:
            resp = (
                supabase.table("comentarios")
                .select("id, texto_bruto, categoria_ia, is_hate")
                .eq("is_hate", True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as e:
            logging.error(f"Erro ao buscar lote do Supabase: {e}")
            break
            
        comments = resp.data if resp.data else []
        if not comments:
            break
            
        logging.info(f"Processando lote de {len(comments)} comentários (Offset: {offset})...")
        
        for c in comments:
            texto = c.get("texto_bruto", "")
            if lexical_filter.is_junk(texto):
                cid = c.get("id")
                logging.info(f"♻️ [Corrigindo] Comentário ID {cid} era '{texto.strip()}' classificado como '{c.get('categoria_ia')}'")
                
                try:
                    # Correção direta
                    supabase.table("comentarios").update({
                        "is_hate": False,
                        "categoria_ia": "NEUTRO",
                        "confianca_ia": 1.0,
                        "analise_pericial": "Falso positivo de menção/lixo corrigido pelo script de saneamento lexical preventivo."
                    }).eq("id", cid).execute()
                    
                    total_corrigidos += 1
                except Exception as e:
                    logging.error(f"Erro ao atualizar comentário {cid}: {e}")
                    
        if len(comments) < limit:
            break
        offset += limit

    logging.info(f"✨ [Saneamento Concluído] Total de comentários corrigidos/saneados: {total_corrigidos}")

if __name__ == "__main__":
    asyncio.run(sanear_banco())
