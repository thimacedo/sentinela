# -*- coding: utf-8 -*-
"""Reclassificação provisória dos comentários marcados como NEUTRO.

Objetivo: buscar no Supabase todos os comentários cuja `categoria_ia` está
`NEUTRO` (possível falsos negativos) e reprocessá-los com o motor de IA.
O script grava as novas classificações, mantendo o registro original
para auditoria.

Uso:
    python scripts/reclassify_neutral.py

Pré-requisitos:
- Variáveis de ambiente do Supabase configuradas (`SUPABASE_URL`,
  `SUPABASE_KEY`).
- Chave de API das IAs configurada (`OPENAI_API_KEY`, etc.).
- Opcional: `FINETUNED_MODEL_NAME` para usar o modelo já fine‑tuned.
"""

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json
# Alias to ensure any stray logger usage resolves
logger = logging.getLogger()

# Configurar logging para arquivo e console
log_file = Path(__file__).with_name("reclassify_neutral_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Serviços internos do projeto
from core.ai_service import ai_service  # instancia singleton
from core.supabase_service import supabase

# Arquivo JSON para registrar IDs já reclassificados
PROCESSED_FILE = Path(__file__).with_name("processed_neutral.json")

def load_processed_ids() -> set:
    if PROCESSED_FILE.is_file():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            logging.warning("Falha ao ler processed_neutral.json, iniciando com conjunto vazio.")
    return set()

def save_processed_ids(ids: set):
    try:
        with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Erro ao salvar processed_neutral.json: {e}")

# Conjunto em memória de IDs já processados
processed_ids = load_processed_ids()

# Configuração de logging (arquivo local para auditoria)
log_file = Path(__file__).with_name("reclassify_neutral_log.txt")
import sys



async def reclassify_comment(comment_id: int, raw_text: str) -> None:
    """Classifica novamente o texto e atualiza o registro no Supabase.

    - `comment_id`: ID do comentário na tabela `comentarios`.
    - `raw_text`: texto bruto a ser analisado.
    """
    try:
        new_result = await ai_service.classify_text(raw_text)
        # Atualiza a linha com a nova classificação
        update_payload = {
            "categoria_ia": new_result["categoria_ia"],
            "confianca_ia": new_result["confianca_ia"],
            "is_hate": new_result["is_hate"],
            "evidencia_lexical": new_result["evidencia_lexical"],
            "analise_pericial": new_result["analise_pericial"],
            # reclassificado flag removed (coluna inexistente)
            # No timestamp column to update
        }
        supabase.table("comentarios").update(update_payload).eq("id", comment_id).execute()
        logging.info(
            f"Comentário {comment_id} reclassificado: {new_result['categoria_ia']} (conf={new_result['confianca_ia']:.2f})"
        )
        # Registrar ID processado
        processed_ids.add(comment_id)
        save_processed_ids(processed_ids)
    except Exception as exc:
        logging.error(f"Erro ao reclassificar comentário {comment_id}: {exc}")

async def main(limit: int = 200) -> None:
    """Busca comentários neutros e dispara a reclassificação.

    O parâmetro `limit` evita sobrecarga em execuções de teste.
    """
    # 1. Busca comentários com categoria NEUTRO e que ainda não foram reclassificados
    resp = (
        supabase.table("comentarios")
        .select("id, texto_bruto, categoria_ia")
        .eq("categoria_ia", "NEUTRO")
        .limit(limit)
        .execute()
    )
    comments = resp.data if resp.data else []
    # Excluir já processados
    comments = [c for c in comments if c["id"] not in processed_ids]
    if not comments:
        logging.info("Nenhum comentário NEUTRO encontrado para reclassificação.")
        return

    logging.info(f"Iniciando reclassificação de {len(comments)} comentários NEUTRO.")
    tasks = [reclassify_comment(c["id"], c["texto_bruto"]) for c in comments]
    await asyncio.gather(*tasks)
    logging.info("Reclassificação concluída.")

import time

async def has_neutral_comments() -> bool:
    resp = (
        supabase.table('comentarios')
        .select('id')
        .eq('categoria_ia', 'NEUTRO')
        .limit(1)
        .execute()
    )
    return bool(resp.data)

async def run_until_done(pause_seconds: int = 60) -> None:
    while True:
        await main()
        # If no NEUTRO comments remain, exit
        if not await has_neutral_comments():
            logging.info('Todas as avaliações NEUTRO concluídas.')
            break
        logging.info(f'Aguardando {pause_seconds}s antes da próxima tentativa...')
        await asyncio.sleep(pause_seconds)

