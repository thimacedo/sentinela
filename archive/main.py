
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import os
import ollama
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Busca o nome do modelo no .env
MODELO = os.getenv("MODEL_NAME")

# --- ADICIONE ESTE BLOCO DE VERIFICAÇÃO ---
if MODELO is None:
    print("\n❌ ERRO: A variável MODEL_NAME não foi encontrada no arquivo .env!")
    print("Certifique-se de que o arquivo se chama exatamente '.env' e contém 'MODEL_NAME=gemma:2b'")
    exit() # Para o programa aqui para você corrigir
# ------------------------------------------

def sentinela_chat(mensagem):
    try:
        response = ollama.chat(model=MODELO, messages=[
            {
                'role': 'system',
                'content': 'Você é o Sentinela Democrática, um assistente focado em análise de dados democráticos e cidadania.',
            },
            {
                'role': 'user',
                'content': mensagem,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"Erro ao conectar com o Gemma: {e}"

if __name__ == "__main__":
    print("--- Sentinela Democrática Iniciada ---")
    print(f"Usando o modelo: {MODELO}") # Agora sabemos qual modelo ele tentou usar
    print("Digite 'sair' para encerrar.\n")
    
    while True:
        pergunta = input("Você: ")
        if pergunta.lower() == 'sair':
            break
            
        resposta = sentinela_chat(pergunta)
        print(f"\nGemma: {resposta}\n")
