import os, time, requests, json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def classify_pasa(text):
    try:
        r = requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": "llama3.2",
            "prompt": f"Classifique PASA v16.4. Categorias: NEUTRO, ODIO_IDENTITARIO, VIOLENCIA_GENERO, AMEACA, INSULTO_AD_HOMINEM, ATAQUE_INSTITUCIONAL, RIGOR_CRIMINAL. Críticas políticas são NEUTRO. Texto: {text}\nResponda APENAS JSON: {{\"categoria\": \"CATEGORIA\", \"confianza\": 0.9}}",
            "stream": False,
            "format": "json"
        }, timeout=60)
        r.raise_for_status()
        res = json.loads(r.json().get("response", "{}"))
        cat = res.get("categoria", "FALHA_IA")
        conf = float(res.get("confianza", 0.0))
        # Aplicar limiar de confiança unificado\r\n        confidence_threshold = CONFIDENCE_THRESHOLD\r\n        if conf < confidence_threshold:\r\n            cat = "INDEFINIDO"\r\n        return cat, conf, cat not in ["NEUTRO", "FALHA_IA", "INDEFINIDO"]
    except Exception as e:
        # print(f"Erro: {e}") # Silencioso conforme instrução de alto sinal
        return "FALHA_IA", 0.0, False

def run():
    print("🧠 [Ollama] Iniciando processamento com Llama 3.2...")
    res = supa.table('comentarios').select('id, texto_bruto').neq('processado_ia', True).limit(100).execute()
    if not res.data: 
        print("✅ 0 pendentes")
        return
        
    total = len(res.data)
    print(f"📦 Processando lote de {total} comentários...")
    
    for i, c in enumerate(res.data, 1):
        if not c['texto_bruto'] or len(c['texto_bruto']) < 3: 
            supa.table('comentarios').update({"processado_ia": True, "categoria_ia": "NEUTRO"}).eq('id', c['id']).execute()
            continue
            
        cat, conf, is_hate = classify_pasa(c['texto_bruto'])
        supa.table('comentarios').update({
            "categoria_ia": cat, 
            "confianza_ia": conf, 
            "is_hate": is_hate, 
            "processado_ia": True
        }).eq('id', c['id']).execute()
        
        status = "💀" if is_hate else "🛡️"
        print(f"  [{i}/{total}] {status} {cat}")
        time.sleep(0.2)
        
    print(f"🏁 {total} processados")

if __name__ == "__main__": 
    run()
