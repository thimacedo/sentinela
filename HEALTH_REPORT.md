# Sentinela Democrática: HEALTH REPORT (PASA v50.0)

## Status Operacional
O projeto passou por uma auditoria Solenya e purgação de lixo legado em 19/05/2026. A infraestrutura central foi preservada e o diretório raiz foi limpo.

### 🏛️ Infraestrutura (Base)
- **Database**: Supabase integrado. Schema `pgmq` operacional para filas.
- **Orquestrador**: `watchdog.py` gerencia o monitoramento e o dashboard.
- **Pipeline**: `main_runner.py` centraliza a execução de workers.

### ⛏️ Coleta de Dados (Scrapers)
- **Instagram (Tier 2/4)**: `scraper_headless.py` operacional via Playwright.
- **Instagram (Tier 3)**: `scraper_zyte.py` configurado como fallback.
- **Scrapy**: Projetos ativos nas pastas `sentinela_novo` e `sentinela_scrapy`.

### 🧹 Higiene do Repositório
- **Diretório Root**: Limpo de scripts de teste e legados.
- **Archive**: Todos os arquivos legados (`main.py`, `run_worker.py`, etc.) foram movidos para a pasta `archive/`.
- **Logs**: Centralizados na pasta `logs/`.

## Conclusão
O sistema está **OPERACIONAL** e **ESTÁVEL**. A dívida técnica superficial foi removida e o pipeline PASA v50.0 está pronto para escala total.

---
🥒 *Gerado por Pickle Rick Manager*
