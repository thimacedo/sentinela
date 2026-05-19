"""
PASA v49 - Worker Runner: Executa workers isoladamente para testes e automação.
"""
import sys
import os
import argparse
import subprocess
from datetime import datetime

# Garante que o diretório raiz esteja no PATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_test_worker(target: str):
    print(f"🚀 [Runner] Disparando InstagramWorker para @{target}...")
    
    try:
        from app.workers.instagram_worker import InstagramWorker
        worker = InstagramWorker()
        success = worker.run(target)
        
        if success:
            print(f"✅ [Runner] Execução concluída com sucesso para @{target}.")
        else:
            print(f"⚠️ [Runner] Worker reportou falha ou nenhum dado para @{target}.")
            
    except Exception as e:
        print(f"💥 [Runner] Erro crítico ao instanciar/rodar worker: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PASA Worker Test Runner")
    parser.add_argument("--target", type=str, help="Username ou URL do alvo")
    parser.add_argument("--force", action="store_true", help="Ignora circuit breaker (não implementado neste runner simples)")
    
    args = parser.parse_args()
    
    if args.target:
        run_test_worker(args.target)
    else:
        print("❌ Informe um alvo: python run_worker.py --target lulaoficial")
