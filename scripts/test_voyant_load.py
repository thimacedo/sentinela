import httpx
import asyncio

async def test():
    print("Iniciando teste de carga grande...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        text = "Este é um comentário longo. " * 200 # ~5KB
        texts = [f"Comentário {i}: {text}" for i in range(100)] # ~500KB total
        
        data = {"string": texts}
        params = {"tool": "corpus.CorpusTerms", "format": "json"}
        
        try:
            r = await client.post("http://127.0.0.1:8888/trombone", params=params, data=data)
            print(f"Status: {r.status_code}")
            if r.status_code != 200:
                print(f"Erro: {r.text[:500]}")
        except Exception as e:
            print(f"Exceção: {e}")

if __name__ == "__main__":
    asyncio.run(test())
