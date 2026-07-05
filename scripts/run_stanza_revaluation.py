import os
import sys
import json
import time
import logging
from dotenv import load_dotenv

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass

# Neutralizador do loop do Watchdog Powershell
FLAG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runtime_state", "reval_done.flag")
if os.path.exists(FLAG_FILE):
    time.sleep(3600)
    sys.exit(0)

# Configurações agressivas contra OOM em PyTorch na inicialização
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase_client

os.environ["STANZA_RESOURCES_DIR"] = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stanza_resources")
from core.stanza_nlp import stanza_nlp
from core.ntfy import NtfyNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stanza_reval")

CHECKPOINT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "runtime_state", "stanza_reval_checkpoint.json")

def load_keywords():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "custom_rules.json")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    keywords = {}
    for cat, words in data.get("custom_keywords", {}).items():
        for w in words:
            keywords[w.lower()] = cat
    return keywords

def get_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f).get("offset", 0)
        except Exception:
            pass
    return 0

def save_checkpoint(offset: int):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"offset": offset}, f)

def is_false_positive(lemma, texto):
    texto_lower = texto.lower()
    if lemma == 'destruir':
        if any(w in texto_lower for w in ['cidade', 'família', 'familia', 'país', 'tigrinho', 'bet', 'sonho']):
            return True
    if lemma in ['matar', 'matam']:
        if any(w in texto_lower for w in ['fake', 'notícia', 'marielle', 'esquerda', 'direita', 'fome', 'saudade', 'inocente', 'pai']):
            return True
    if lemma in ['corrupção', 'corrupto', 'crime']:
        if any(w in texto_lower for w in ['chama', 'governo', 'crueldade', 'animal', 'gato', 'cachorro', 'torturado']):
            return True
    if lemma == 'raça':
        if any(w in texto_lower for w in ['jogadores', 'seleção', 'campeã', 'tem', 'com']):
            return True
    if lemma == 'kkk':
        import re
        if not re.search(r'\b(k\.?k\.?k)\b', texto_lower):
            return True
    return False

def evaluate_comment(comment, keywords):
    texto = comment.get("texto_bruto", "")
    if not texto or len(texto.strip()) == 0: return None
    
    # Limita a 1500 caracteres para evitar OOM no Stanza (alloc_cpu.cpp)
    texto = texto[:1500]
    
    res = stanza_nlp.processar_texto(texto)
    if not res.get("success"):
        return None
        
    lemmas = res.get("lemmas", [])
    for lemma in lemmas:
        if lemma in keywords:
            if not is_false_positive(lemma, texto):
                return keywords[lemma] # Retorna a categoria correta
    return None

def run_revaluation():
    client = get_supabase_client()
    keywords = load_keywords()
    notifier = NtfyNotifier("https://ntfy.sh/sentinela")
    
    batch_size = 100
    sleep_time = 27 
    
    offset = get_checkpoint()
    
    logger.info(f"Iniciando reavaliação distribuída (Stanza NLP). Offset inicial: {offset}")
    logger.info(f"Keywords carregadas: {len(keywords)} termos.")
    notifier.send_sync(title="🤖 Stanza NLP", message=f"Iniciando varredura a partir do offset {offset}", tags=["mag"])
    
    batch_count = 0
    total_falsos_negativos = 0
    
    while True:
        try:
            logger.info(f"Buscando lote (Offset: {offset}, Limite: {batch_size})...")
            response = client.table("comentarios").select("*").eq("is_hate", False).range(offset, offset + batch_size - 1).execute()
            
            data = response.data
            if not data:
                logger.info("Nenhum dado retornado. Varredura concluída!")
                break
                
            falsos_negativos = []
            for c in data:
                cat = evaluate_comment(c, keywords)
                if cat:
                    c['nova_categoria'] = cat
                    falsos_negativos.append(c)
            
            if falsos_negativos:
                logger.warning(f"Identificados {len(falsos_negativos)} falsos negativos no lote atual.")
                for fn in falsos_negativos:
                    try:
                        client.table("comentarios").update({
                            "is_hate": True,
                            "categoria_ia": fn['nova_categoria']
                        }).eq("id", fn["id"]).execute()
                    except Exception as up_err:
                        logger.error(f"Erro ao atualizar comentario {fn['id']}: {up_err}")
            
            offset += batch_size
            save_checkpoint(offset)
            
            batch_count += 1
            if falsos_negativos:
                total_falsos_negativos += len(falsos_negativos)
                
            if batch_count % 10 == 0:
                msg = f"Varredura em andamento...\nOffset atual: {offset}\nFalsos negativos encontrados ate agora: {total_falsos_negativos}"
                notifier.send_sync(title="📊 Status Stanza NLP", message=msg, tags=["bar_chart"])
                
            # Força coleta de lixo para evitar vazamento de memória nas tensores
            import gc
            gc.collect()
            
            if len(data) < batch_size:
                logger.info("Lote incompleto atingido. Fim dos registros.")
                notifier.send_sync(title="✅ Concluído", message=f"Varredura Stanza concluída. Falsos Negativos totais: {total_falsos_negativos}", tags=["tada"])
                
                # Sinaliza o fim para o orquestrador do Antigravity
                with open(FLAG_FILE, "w") as f:
                    f.write("done")
                
                break
                
            logger.info(f"Lote processado. Aguardando {sleep_time}s (Cooldown Supabase)...")
            time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Erro processando lote no offset {offset}: {e}")
            logger.info("Aplicando backoff de 60s antes de tentar novamente...")
            time.sleep(60)

if __name__ == "__main__":
    load_dotenv()
    run_revaluation()
