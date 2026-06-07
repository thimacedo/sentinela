from workers.base.memory_store import MemoryStore
import asyncio

async def test():
    store = MemoryStore()
    r = await store.get_recent('ai-processor-01', n=1)
    if r:
        print(f"Ciclo: {r[0].cycle}")
    else:
        print("Nenhum dado recente.")

if __name__ == "__main__":
    asyncio.run(test())
