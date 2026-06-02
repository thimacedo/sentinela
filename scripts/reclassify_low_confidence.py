import os
import sys
import asyncio
import argparse
import logging

# Adiciona o diretório do projeto ao path para importar 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from core.db import db_client
from core.ai_service import ai_service

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - RECLASSIFIER - %(levelname)s - %(message)s")
logger = logging.getLogger("reclassifier")

async def reclassify_comments(limit: int, cloud_only: bool, confidence_threshold: float):
    logger.info(f"Iniciando reclassificação. Threshold: {confidence_threshold}, Limit: {limit}, Cloud-Only: {cloud_only}")
    
    try:
        # Busca comentários que foram processados mas têm confianca_ia <= threshold
        res = db_client.client.table('comentarios')\
            .select('id, texto_bruto, categoria_ia, confianca_ia, is_hate, analise_pericial')\
            .eq('processado_ia', True)\
            .lte('confianca_ia', confidence_threshold)\
            .order('data_coleta', desc=True)\
            .limit(limit).execute()
        
        comments = res.data or []
    except Exception as e:
        logger.error(f"Erro ao buscar comentários do Supabase: {e}")
        return
        
    if not comments:
        logger.info("Nenhum comentário com baixa confiança encontrado para reclassificar.")
        return
        
    logger.info(f"Encontrados {len(comments)} comentários para reclassificar.")
    
    reclassified_count = 0
    changed_labels_count = 0
    
    # Guarda os provedores originais
    original_providers = list(ai_service.providers)
    if cloud_only:
        # Filtra para usar apenas provedores cloud
        ai_service.providers = [p for p in original_providers if p["name"] not in ["litert", "ollama"]]
        logger.info("Utilizando apenas provedores Cloud para reclassificação profunda.")
        
    try:
        for item in comments:
            cid = item["id"]
            text = item["texto_bruto"]
            old_cat = item["categoria_ia"]
            old_conf = item["confianca_ia"] or 0.0
            old_hate = item["is_hate"]
            
            logger.info(f"Processando comentário ID {cid} (Antigo: {old_cat} | Conf: {old_conf:.2f})")
            
            try:
                res_ia = await ai_service.classify_text(text, cid)
                
                # Se falhar e estava no modo cloud_only, tenta o fallback local
                if (not res_ia or res_ia.get("categoria_ia") == "ERRO") and cloud_only:
                    logger.warning(f"  ⚠️ Falha na perícia Cloud para {cid}. Ativando fallback local temporário...")
                    
                    # Restaura os provedores locais temporariamente para esta tentativa
                    ai_service.providers = original_providers
                    try:
                        res_ia = await ai_service.classify_text(text, cid)
                    finally:
                        # Restaura o modo cloud_only para os próximos
                        ai_service.providers = [p for p in original_providers if p["name"] not in ["litert", "ollama"]]
                        
                    if res_ia and res_ia.get("categoria_ia") != "ERRO":
                        logger.info(f"  ✅ Fallback local com sucesso (Provedor: {res_ia.get('name', 'N/A')})")
                        res_ia["is_fallback"] = True
                    else:
                        res_ia = None
                
                if res_ia and res_ia.get("categoria_ia") != "ERRO":
                    new_cat = res_ia["categoria_ia"]
                    new_conf = res_ia["confianca_ia"]
                    new_hate = res_ia["is_hate"]
                    new_analise = res_ia.get("analise_pericial", "")
                    is_fallback = res_ia.get("is_fallback", False)
                    
                    changed = (old_cat != new_cat) or (old_hate != new_hate)
                    if changed:
                        changed_labels_count += 1
                        logger.info(f"  👉 ALTERADO: '{old_cat}' -> '{new_cat}' (Nova Confiança: {new_conf:.2f})")
                    else:
                        logger.info(f"  ✅ MANTIDO: '{old_cat}' (Nova Confiança: {new_conf:.2f})")
                        
                    tag = "[RECLASSIFICADO - FALLBACK] " if is_fallback else "[RECLASSIFICADO] "
                    orig_analise = item.get("analise_pericial") or ""
                    if tag not in orig_analise:
                        analise_final = f"{tag}{new_analise}"
                    else:
                        analise_final = f"{tag}{new_analise} (Anterior: {orig_analise.replace(tag, '')})"
                        
                    db_client.client.table('comentarios').update({
                        "categoria_ia": new_cat,
                        "confianca_ia": new_conf,
                        "is_hate": new_hate,
                        "analise_pericial": analise_final,
                        "processado_ia": True
                    }).eq("id", cid).execute()
                    
                    reclassified_count += 1
                    await asyncio.sleep(0.5)
                else:
                    logger.warning(f"  ❌ Falha total ao obter reclassificação para {cid}. Aplicando backoff de 5s...")
                    await asyncio.sleep(5.0)
            except Exception as ex:
                logger.error(f"  ❌ Erro crítico ao reclassificar item {cid}: {ex}")
                await asyncio.sleep(2.0)
            
    finally:
        # Restaura os provedores originais
        ai_service.providers = original_providers
        
    if reclassified_count > 0:
        logger.info(f"Fim do processamento.")
        logger.info(f"Total processados com sucesso: {reclassified_count}/{len(comments)}")
        logger.info(f"Total com alteração de rótulo/hate: {changed_labels_count} ({changed_labels_count/reclassified_count*100:.1f}% de mudança)")
    else:
        logger.info("Nenhum comentário foi reclassificado com sucesso.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reclassificador de comentários com baixa confiança no Sentinela")
    parser.add_argument("--limit", type=int, default=50, help="Limite de comentários para processar")
    parser.add_argument("--cloud-only", action="store_true", default=True, help="Forçar uso de de modelos Cloud")
    parser.add_argument("--local-allowed", action="store_false", dest="cloud_only", help="Permitir modelos locais na reclassificação")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold de confiança máxima para reclassificar")
    
    args = parser.parse_args()
    
    asyncio.run(reclassify_comments(args.limit, args.cloud_only, args.threshold))
