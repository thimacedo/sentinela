# Supabase Python Client — Referência Operacional
_last_updated: 2026-05-20_

## Inicialização (singleton)
```python
from supabase import create_client, Client
import os

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client
```

## Tratamento de erros
> ⚠️ O SDK Python (>= 2.x) lança **exceções** em caso de erro. **Nunca** checar `result.error`.
```python
try:
    result = get_client().table("tabela").insert({"data": 1}).execute()
except Exception as e:
    # Capturar a exceção diretamente
    raise RuntimeError(f"Falha na operação Supabase: {e}")
```

## Operações (Boas Práticas)
- **UPSERT**: Use `upsert()` com `on_conflict` para garantir idempotência em scrapings.
- **SELECT**: Sempre especifique as colunas (`select("id, col")`) para evitar over-fetching.
- **Singleton**: Instancie apenas uma vez.
- **Índices**: Crie índices em todas as colunas usadas em `.eq()`, `.order()` ou `.gte()`.
