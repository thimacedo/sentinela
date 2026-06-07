import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv(override=True)

def test_maritaca():
    key = os.getenv("MARITACA_API_KEY")
    print(f"Testando chave: {key[:5]}...{key[-5:]}")
    url = "https://chat.maritaca.ai/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sabia-4",
        "messages": [{"role": "user", "content": "Olá!"}]
    }
    
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, json=data)
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_maritaca()
