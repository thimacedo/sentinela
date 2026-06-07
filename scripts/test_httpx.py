import httpx
import asyncio

async def test():
    print("Iniciando teste async (v2)...")
    async with httpx.AsyncClient() as client:
        print("Enviando POST (string list) para 127.0.0.1...")
        # Parâmetros mistos (query + body)
        params = {
            "tool": "corpus.CorpusTerms",
            "format": "json"
        }
        data = {"string": ["teste 1", "teste 2"]}
        
        try:
            r = await client.post("http://127.0.0.1:8888/trombone", params=params, data=data)
            print(f"Status POST: {r.status_code}")
            print(f"Body POST: {r.text[:100]}...")
        except Exception as e:
            print(f"Erro capturado: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
