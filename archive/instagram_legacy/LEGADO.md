# Instagram Workers Legados

Arquivados em: 2026-05-20
Razão: Substituídos por `ig_headless.py` e `ig_zyte.py` (v50.1)

## Arquivos

### workers_instagram_worker.py
- Herança: `BaseWorker` (correto)
- Tamanho: ~8kb
- Motivo do arquivamento: Lógica consolidada em `ig_headless.py`

### app_workers_instagram_worker.py
- Herança: Nenhuma (quebrado)
- Tamanho: ~12kb
- Motivo do arquivamento: Não segue padrão v50.1

### workers_scrapers_instagram_worker.py
- Herança: `BaseWorker` (correto)
- Tamanho: ~18kb
- Motivo do arquivamento: Lógica de sessão migrada para `ig_headless.py`

## Workers ativos (v50.1)

```python
from workers.scrapers.ig_headless import IGHeadlessWorker
from workers.scrapers.ig_zyte import IGZyteWorker
```

Ambos herdam de `BaseWorker` e seguem o protocolo de recompensas.
