# ROADMAP.md — Sentinela Democratica
_last_updated: 2026-05-24 | branch: main_

## Concluido

### Coleta Real e Inteligencia (v48 - v55.3)
- [x] **Motor Scraper V2**: Playwright independente sem Zyte (Fase 5).
- [x] **Integridade Forense**: Validação de username, 404 e conta privada no scraping.
- [x] **Filtro Inteligente**: Ignorar posts fixados (pins) e limite temporal de 7 dias (v54.4).
- [x] **AIAdvisor SRE**: Diagnóstico automático de falhas via Mistral integrado (v53.0).
- [x] **DocFetcher**: Cache local de docs técnicas com TTL de 1h para IA.
- [x] **Fila Multinível**: Prioridade Ponderada + Fairness 25% + Atomic Locking (v55.1).
- [x] **Refatoração Frontend**: Interface "War Room" profissional (Slate/Emerald) com Flexbox.
- [x] **Modularização de Dados**: Hook `useSystemInformation` isolando lógica de busca.
- [x] **Watchdog Sync**: Monitoramento unificado Supabase + Dashboard local atualizado.
- [x] **Deploy Persistente**: `render.yaml` atualizado para orquestrador persistente com Playwright.

---

## Em Andamento (Fase 7: Consolidação e Dossiês)

### Sessão e Resiliência
- [ ] Implementar renovação automática de sessões via worker dedicado.
- [ ] Rotação de User-Agents dinâmica por ciclo.

### Expansão de Coleta
- [ ] Ativar paginação de posts (atualmente max_posts=3) com teto adaptativo.
- [ ] Detecção de "Shadowban" de comentários por perfil.

### Refinamento de IA
- [ ] Fine-tuning de modelo local (Ollama) para reduzir latência e custos Cloud.
- [ ] Implementar Auditoria Cruzada (IA validando IA) para casos críticos.

### Relatórios e Visualização
- [ ] Reativar e recalibrar módulo de **Dossiês** (Exportação PDF v54).
- [ ] Reativar módulo de **Rede** (Grafos de influência com nova IA).

---

## Proximas Acoes Imediatas

1. Monitoramento de estabilidade do orquestrador no Render.
2. Fine-tuning local para redução de dependência de APIs Cloud.
3. Recalibração do motor de Dossiês para nova estrutura de dados.
