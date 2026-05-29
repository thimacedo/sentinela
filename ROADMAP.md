# ROADMAP.md — Sentinela Democratica
_last_updated: 2026-05-29 | branch: main_

## Concluido

### Inteligência e Coleta Industrial (v65 - v86.0)
- [x] **Stealth Mode**: Rotação dinâmica de User-Agents, Viewports e injeção anti-fingerprint (v85.10).
- [x] **Triagem Local (Ollama)**: Integração com IA local para redução de custos em 50% (v85.11).
- [x] **Dossiês Forenses Reais**: Motor PDF v85.9 com assinatura SHA-256 e selo de integridade.
- [x] **Network Miner**: Detecção de clusters coordenados e contas multi-target (v85.13).
- [x] **Otimização de Ociosidade**: Smart Wait e Background Utility Tasks para re-análise automática (v85.12).
- [x] **Frontend v86**: Grid 2-colunas, filtros dinâmicos de UF/Partido e transparência de IA (Parecer Técnico).

### Infraestrutura e Monetização (Legado v48 - v64.0)
- [x] **Motor Scraper V2**: Playwright independente sem Zyte.
- [x] **Integridade Forense**: Validação biográfica via IA (v64.0).
- [x] **Frontend Next.js 16**: App Router + Tailwind v4 + Stripe E2E.
- [x] **Fila Inteligente**: Prioridade Dinâmica (Termômetro) e Hibernação de alvos ociosos.
- [x] **Resiliencia de Dados**: Buffer de emergência Zero-Loss e fallback de schema mismatch.

---

## Em Andamento (Fase 7.1: Governança Financeira e CI)

### Gestão de Capital (Tesoureiro)
- [ ] Implementar **`TreasurerWorker`** para auditoria de transações e ledger (PASA v86.1).
- [ ] Padronização total de nomenclatura: **STN ➔ CI** (Créditos de Inteligência).
- [ ] DRE Diário automatizado: Inflow (Stripe) vs Outflow (Burn Rate de IA).

### Expansão Analítica
- [ ] Análise de "Shadowban" léxico: detectar quando a plataforma oculta termos específicos.
- [ ] Exportação de Dossiês em lote para contas de agências.
- [ ] Dashboard Financeiro Admin para monitoramento de custos por alvo.

---

## Proximas Acoes Imediatas

1. Implementar a classe base do `TreasurerWorker` e registrar no orquestrador.
2. Refatorar `core/db.py` para suportar alias `saldo_ci` e transações atômicas de governança.
3. Testar o fluxo de cobrança de 350 CI por dossiê com o novo motor de PDF.
