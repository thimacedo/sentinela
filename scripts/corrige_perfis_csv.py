import sys
import os
import asyncio

# Corrige encoding de saída no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Garante o path para imports locais
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ground_truth import ground_truth
from core.db import db_client

async def fix_database():
    print("==================================================")
    print("  SANITIZAÇÃO DETERMINÍSTICA DE PERFIS (PASA v94.0) ")
    print("==================================================")
    
    atualizados = 0
    erros = 0

    total_alvos = len(ground_truth._db)
    if total_alvos == 0:
        print("❌ O GroundTruthDB não carregou nenhum alvo. Verifique se o arquivo alvos_sanitizacao.csv está na raiz e tem o formato correto.")
        return

    print(f"Iniciando correção de {total_alvos} perfis no banco de dados local...")

    for username, dados in ground_truth._db.items():
        try:
            # Tenta executar update no Supabase (execução bloqueante em I/O convertida pra asyncio para segurança se no loop, ou sincrona se fora)
            # Como esse script roda solto, usar await to_thread
            res = await asyncio.to_thread(
                db_client.client.table('candidatos')
                .update({
                    "nome_completo": dados["nome_completo"],
                    "cargo": dados["cargo"],
                    "sexo": dados["sexo"],
                    "identidade_validada": True # Marca como validado para o WkPesquisaAlvos pular a IA
                })
                .eq('username', username)
                .execute
            )
            
            if res.data:
                atualizados += 1
                print(f"✅ @{username:<20} corrigido: {dados['cargo']:<25} ({dados['sexo']})")
        except Exception as e:
            erros += 1
            print(f"❌ Erro ao corrigir @{username}: {e}")

    print("==================================================")
    print(f"Concluído! {atualizados} perfis corrigidos com sucesso.")
    if erros > 0:
        print(f"{erros} erros detectados (perfis podem não existir no banco).")

if __name__ == "__main__":
    asyncio.run(fix_database())
