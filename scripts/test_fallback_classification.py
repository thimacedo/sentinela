#!/usr/bin/env python
"""Teste rápido de classificação usando todos os provedores de IA configurados.
Este script carrega as credenciais do .env, instancia o wrapper fallback
(FallbackLLM) e envia um prompt de classificação simples para cada provedor.
"""
import os
from pathlib import Path
import json

# Carrega variáveis de ambiente do .env (se necessário)
from dotenv import load_dotenv
load_dotenv()

# Importa o wrapper (presumindo que core/fallback_llm.py existe)
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from core.fallback_llm import FallbackLLM
except ImportError as e:
    print("Erro ao importar FallbackLLM:", e)
    raise

# Texto de exemplo para classificação
samples = [
    "Este produto é excelente e recomendo a todos!",
    "O serviço foi péssimo, nunca mais comprarei aqui.",
    "A reunião foi produtiva, mas precisamos melhorar a comunicação."
]

llm = FallbackLLM()

print("=== Teste de classificação por provedor ===")
for provider in llm.providers_order:
    try:
        print(f"\n>>> Provedor: {provider['name']}")
        for txt in samples:
            # Utiliza um método genérico do wrapper para obter resposta
            resp = llm.classify(text=txt, provider_name=provider['name'])
            print(f"Texto: {txt}\nResposta: {resp}\n")
    except Exception as exc:
        print(f"Falha ao usar {provider['name']}: {exc}")

print("Teste concluído.")
