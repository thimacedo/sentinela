import httpx
import json
import sys

def get_live_status():
    try:
        resp = httpx.get("http://localhost:8001/api/ai_health", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            providers = data.get("providers", {})
            
            print("# RELATÓRIO DE ESTADO REAL DA MALHA DE IA")
            print(f"Gerado em: {data.get('timestamp')}")
            print("\n| Provedor | Status | Detalhe |")
            print("| :--- | :--- | :--- |")
            
            for name, status in providers.items():
                print(f"| {name} | {status['icon']} {status['status']} | {status['detail']} |")
            
            return True
    except Exception as e:
        print(f"Erro ao conectar ao Watchdog: {e}")
    return False

if __name__ == "__main__":
    get_live_status()
