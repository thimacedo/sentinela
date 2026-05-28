# Sentinela — PASA v84.11

Este repositório opera na arquitetura PASA v84.11 (God Mode Data Layer & Frontend Premium).

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
O frontend oficial está em `frontend/` operando sob Next.js 16 (App Router) + TailwindCSS.
Configuração na Vercel:
- `Root Directory = frontend`
- Framework Preset: `Next.js`
- Comandos de Build: `npm run build`

## Legado
Componentes legados foram isolados em `archive_v17_2026/`. Não reativar sem revisão arquitetural.

## Regras Críticas
1. Não enviar SQL bruto pelo frontend.
2. Não expor `SUPABASE_SERVICE_KEY` fora do backend.
3. Não importar módulos de pastas legadas (`app/`, `core/` antigos).
