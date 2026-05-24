import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Add root to pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.supabase_service import get_supabase_client
from core.ai_service import AIService

async def reprocess_comments():
    print("[*] Iniciando reprocessamento de comentários NEUTRO/INDEFINIDO...")
    db = get_supabase_client()
    ai = AIService()
    
    # Buscar comentários que precisam de revisão (os que podem ser falsos negativos)
    print("[*] Buscando falsos negativos potenciais na base...")
    res = db.table("comentarios") \
        .select("id, texto_bruto, categoria_ia, is_hate") \
        .in_("categoria_ia", ["NEUTRO", "INDEFINIDO"]) \
        .execute()
        
    comentarios = res.data
    total = len(comentarios)
    print(f"[*] Encontrados {total} comentários para revisão.")
    
    reclassificados = 0
    lixos = 0
    
    for i, c in enumerate(comentarios):
        cid = c["id"]
        texto = c["texto_bruto"]
        antiga_cat = c["categoria_ia"]
        
        print(f"\n--- [{i+1}/{total}] Analisando ---")
        print(f"Texto: {texto}")
        
        try:
            result = await ai.classify_text(texto)
            nova_cat = result.get("categoria_ia")
            
            if nova_cat == "LIXO":
                print(f"🗑️ Reclassificado como LIXO. Apagando...")
                db.table("comentarios").delete().eq("id", cid).execute()
                lixos += 1
            else:
                if nova_cat != antiga_cat:
                    print(f"🔄 Mudança: {antiga_cat} -> {nova_cat} (is_hate: {result.get('is_hate')})")
                    db.table("comentarios").update({
                        "processado_ia": True,
                        "is_hate": result.get("is_hate", False),
                        "categoria_ia": nova_cat,
                        "confianca_ia": result.get("confianca_ia", 0.0),
                        "evidence_extracted": result.get("evidencia_lexical", []),
                        "analise_pericial": result.get("analise_pericial", "")
                    }).eq("id", cid).execute()
                    reclassificados += 1
                else:
                    print(f"Mantido como {antiga_cat}.")
                    
            # Respeitando rate limits do Groq/Llama
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Erro ao classificar: {e}")
            await asyncio.sleep(5)
            
    print(f"\n[*] Concluído! {reclassificados} reclassificados de fato, {lixos} lixos deletados.")

if __name__ == "__main__":
    asyncio.run(reprocess_comments())
