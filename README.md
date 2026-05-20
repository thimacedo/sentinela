# Sentinela — PASA v50.1

Este repositório opera na arquitetura PASA v50.1 (God Mode Data Layer).

## Documentação Técnica
- [STATE.md](./STATE.md) (Fonte de verdade atual)
- [SYSTEM_CONTEXT.md](./SYSTEM_CONTEXT.md)
- [ARCHITECTURE_PASA_V50.md](./ARCHITECTURE_PASA_V50.md)
- [ROADMAP.md](./ROADMAP.md)

## Entrada oficial (Backend)
```bash
python main_runner.py
```

## Supervisão operacional
```bash
python watchdog.py
```

## Frontend Oficial
O frontend oficial está em `proposta_frontend/`. 
Configuração na Vercel:
- `Root Directory = proposta_frontend`
- Framework Preset: `Next.js`

## Legado
Componentes legados foram isolados em `archive_v17_2026/`. Não reativar sem revisão arquitetural.

## Regras Críticas
1. Não enviar SQL bruto pelo frontend.
2. Não expor `SUPABASE_SERVICE_KEY` fora do backend.
3. Não importar módulos de pastas legadas (`app/`, `core/` antigos).
