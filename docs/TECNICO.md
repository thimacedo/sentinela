# Sentinela - Documentacao Tecnica

Data: 05 de Julho de 2026
Autor: Thiago Macedo
Versao: 1.0

---

## Melhorias TypeScript

### Tipos Centralizados
- Arquivo: frontend/types/index.ts
- Tipos: Alert, DashboardStats, TimelineEvent, Candidate, Comment, ApiResponse, PaginatedResponse, FilterParams
- Beneficios: Consistencia, manutencao, seguranca de tipos

### Remocao de any Types
- Arquivo: frontend/app/page.tsx
- Acao: Removido eslint disable, substituido any por interfaces
- Impacto: Erros em tempo de compilacao, melhor IDE support

---

## Otimizacoes de Queries

### N+1 Query Problem
- Arquivo: core/queue_manager.py
- Antes: 4+ queries + N upserts individuais
- Depois: 3 queries + 1 batch insert
- Melhoria: -60-70% queries, -99% upserts

### Indices Banco de Dados
- Arquivo: migrations/add_performance_indexes.sql
- Indices: 8 indices para fila_coleta e candidatos
- Funcoes: get_candidates_for_scraping(), repopulate_queue_if_needed()

---

## Performance Impact

### Benchmark
- Antes: ~230ms + 20 conexoes
- Depois: ~75ms + 4 conexoes
- Melhoria: 67% mais rapido, 80% menos conexoes

---

## Arquivos Modificados

| Arquivo | Mudanca | Commit |
|---------|---------|---------|
| price.env | DELETADO | - |
| .gitignore | Atualizado | 965fadc9 |
| core/queue_manager.py | Otimizado | 21a3e1eb, c306c1d7 |
| frontend/types/index.ts | Criado | existente |
| frontend/app/page.tsx | Atualizado | existente |
| migrations/add_performance_indexes.sql | Criado | bfe4efef |
| CHANGES.md | Criado | bc27b91e |