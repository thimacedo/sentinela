# ROADMAP.md — Sentinela Democratica
_last_updated: 2026-05-24 | branch: main_

## Concluido

### Coleta Real e Inteligencia (v48 - v64.0)
- [x] **Motor Scraper V2**: Playwright independente sem Zyte (Fase 5).
- [x] **Integridade Forense**: Validação biográfica via IA para detecção de perfis inautênticos (v64.0).
- [x] **Otimização de Performance**: Fast-Skip de posts fixados e velhos diretamente no grid (v62.1).
- [x] **Inteligencia Robusta**: Detecção de Bots por densidade léxica e categoria CAMPANHA_COORDENADA.
- [x] **Refinamento MCA**: IA calibrada anti-falsos positivos e temperatura determinística.
- [x] **Fila Inteligente**: Prioridade Dinâmica (Termômetro) e Hibernação de alvos ociosos.
- [x] **Resiliencia de Dados**: Buffer de emergência Zero-Loss e fallback de schema mismatch.
- [x] **Infraestrutura**: Watchdog modernizado com 'uv' e Auto-Ancoragem global de diretórios.
- [x] **Frontend Moderno**: Interface SAAS Premium Multitema (Light/Dark) v60.2.
- [x] **Documentacao**: Mapa de dados v58, Mapa funcional e Índice de onboarding.

---

## Em Andamento (Fase 7: Consolidação e Relatórios)

### Sessão e Escala
- [ ] Implementar rotação de User-Agents dinâmica por ciclo para evitar detecção.
- [x] **Worker de Renovação Automática**: Implementado (`export_playwright_cookies.py`), mas enfrentando bloqueios de CAPTCHA/2FA que requerem intervenção manual periódica.

### Expansão Analítica
- [x] **Fase 4 Ativa**: Módulo `AIAdvisor` e `DocFetcher` integrados ao fluxo de erro dos workers para diagnóstico automático (v84.5).
- [ ] Ativar paginação de posts adaptativa (max_posts dinâmico baseado no Termômetro).
- [ ] Análise de "Shadowban" léxico: detectar quando a plataforma oculta termos específicos.

### Relatórios Premium
- [ ] Recalibrar motor de **Dossiês** para nova estrutura de dados (Exportação PDF v54).
- [ ] Reativar módulo de **Rede** (Grafos de influência baseados na nova categorização).
- [ ] API Gateway comercial para venda de créditos e integração externa.

---

## Proximas Acoes Imediatas

1. Monitoramento da estabilidade do Scraper V2 sob a nova validação biográfica.
2. Fine-tuning local (Ollama) para categorias específicas de hostilidade velada.
3. Teste do módulo de Dossiês com os novos dados normalizados.
