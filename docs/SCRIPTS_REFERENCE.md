# Scripts Reference — Índice Completo

**Localização**: `/workspace/scripts/`  
**Total de Scripts**: 103  
**Última Atualização**: 2026-06-04

---

## 📋 Visão Geral

Este documento cataloga **todos os 103 scripts** do projeto Sentinela, organizados por categoria funcional. Cada script tem sua descrição, parâmetros, dependências e exemplos de uso.

**Estrutura:**
- 🗂️ **Categoria** (ex: Database, Analytics, Testing)
- 📝 **Script Name** — Descrição + Uso
- ⚙️ **Parâmetros** (se aplicável)
- 🔗 **Dependências**
- 💡 **Exemplo** de execução

---

## 📚 Índice por Categoria

### Categoria: **Database & Migrations**
1. [apply_local_migrations.py](#apply_local_migrations)
2. [apply_migration.py](#apply_migration)
3. [create_anuncios_table.sql](#create_anuncios_table)
4. [db_migrate.py](#db_migrate)
5. [fix_rls_security.sql](#fix_rls_security)
6. [migration_protecao_forense.sql](#migration_protecao_forense)
7. [migration_protecao_forense_v2.sql](#migration_protecao_forense_v2)
8. [migration_v19.6_stn.sql](#migration_v19.6_stn)
9. [migration_v20.0_anuncios.sql](#migration_v20.0_anuncios)
10. [migration_v21.0_push_tokens.sql](#migration_v21.0_push_tokens)
11. [migration_v22.0_scraping_accounts.sql](#migration_v22.0_scraping_accounts)
12. [migration_v22.1_anuncios_pasa.sql](#migration_v22.1_anuncios_pasa)
13. [migration_v23.0_dossies.sql](#migration_v23.0_dossies)
14. [migration_v24.0_alertas.sql](#migration_v24.0_alertas)
15. [migration_v25.0_multitenancy.sql](#migration_v25.0_multitenancy)
16. [migration_v26.0_motor_alvos.sql](#migration_v26.0_motor_alvos)
17. [migration_v27.0_rls_kpis.sql](#migration_v27.0_rls_kpis)
18. [migration_v28.0_ci_governance.sql](#migration_v28.0_ci_governance)
19. [migration_v28.0_mining_flags.sql](#migration_v28.0_mining_flags)
20. [upgrade_schema_v7.sql](#upgrade_schema_v7)
21. [verify_anuncios_schema.sql](#verify_anuncios_schema)
22. [verify_schema.py](#verify_schema)
23. [check_tables.py](#check_tables)
24. [list_tables.py](#list_tables)

### Categoria: **Configuration & Setup**
25. [add_target.py](#add_target)
26. [add_re_pericia_flag.sql](#add_re_pericia_flag)
27. [delete_target.py](#delete_target)
28. [bundle_frontend.py](#bundle_frontend)
29. [deploy_frontend.py](#deploy_frontend)
30. [setup_stripe_catalog.py](#setup_stripe_catalog)
31. [seed_tier1_profiles.py](#seed_tier1_profiles)
32. [inject_ig_session.py](#inject_ig_session)
33. [export_instagram_storage_state.py](#export_instagram_storage_state)
34. [export_playwright_cookies.py](#export_playwright_cookies)

### Categoria: **Health Checks & Monitoring**
35. [check_drift.py](#check_drift)
36. [check_kpi_values.py](#check_kpi_values)
37. [check_stripe.py](#check_stripe)
38. [check_supabase.py](#check_supabase)
39. [diagnose_workers.py](#diagnose_workers)
40. [detect_shadowbans.py](#detect_shadowbans)
41. [generate_telemetry_report.py](#generate_telemetry_report)
42. [inspect_anuncios.py](#inspect_anuncios)
43. [inspect_metrics.py](#inspect_metrics)
44. [list_candidates.py](#list_candidates)

### Categoria: **Scraping & Data Collection**
45. [cloud_scrape_cycle.py](#cloud_scrape_cycle)
46. [test_scraper_v2.py](#test_scraper_v2)
47. [debug_scraper_v2.py](#debug_scraper_v2)
48. [test_scraper_integrity.py](#test_scraper_integrity)
49. [detect_shadowbans.py](#detect_shadowbans_scrape)
50. [research_pinned_posts.py](#research_pinned_posts)
51. [research_pdf_criteria.py](#research_pdf_criteria)
52. [run_scrapy_spider.py](#run_scrapy_spider)
53. [probe_t3_profile_html.py](#probe_t3_profile_html)
54. [probe_t3_2_storage.py](#probe_t3_2_storage)
55. [extract_pdfs.py](#extract_pdfs)
56. [purge_youtube.py](#purge_youtube)

### Categoria: **Classification & AI**
57. [cloud_classify_batch.py](#cloud_classify_batch)
58. [force_reclassify.py](#force_reclassify)
59. [mass_classify.py](#mass_classify)
60. [reclassify_csv.py](#reclassify_csv)
61. [reclassify_csv_progress.json](#reclassify_csv_progress)
62. [reclassify_low_confidence.py](#reclassify_low_confidence)
63. [reclassify_neutral.py](#reclassify_neutral)
64. [reset_failed_classifications.py](#reset_failed_classifications)
65. [test_ai_service.py](#test_ai_service)
66. [test_ai_calibration.py](#test_ai_calibration)
67. [test_fallback_classification.py](#test_fallback_classification)
68. [train_ia.py](#train_ia)

### Categoria: **Workers & Agents**
69. [run_audit_agent.py](#run_audit_agent)
70. [run_dossier_agent.py](#run_dossier_agent)
71. [run_scanner_agent.py](#run_scanner_agent)
72. [worker_classificador.py](#worker_classificador)
73. [auto_sync_daemon.py](#auto_sync_daemon)
74. [night_watch_pipeline.sh](#night_watch_pipeline)
75. [diagnose_workers.py](#diagnose_workers_worker)

### Categoria: **Data Cleanup & Maintenance**
76. [cleanup_comments.py](#cleanup_comments)
77. [cleanup_parties.py](#cleanup_parties)
78. [cleanup_scanner_noise.py](#cleanup_scanner_noise)
79. [clean_parties.py](#clean_parties)
80. [purge_garbage_comments.py](#purge_garbage_comments)
81. [saneamento_lexical.py](#saneamento_lexical)
82. [_fix_sessionid_conta1.py](#_fix_sessionid_conta1)
83. [cloud_queue_refresh.py](#cloud_queue_refresh)

### Categoria: **Analysis & Reporting**
84. [generate_audit.py](#generate_audit)
85. [generate_sentinela_monetizacao.py](#generate_sentinela_monetizacao)
86. [harvest_gold_dataset.py](#harvest_gold_dataset)
87. [report_new_targets.py](#report_new_targets)
88. [verify_cqrs_001.py](#verify_cqrs_001)
89. [query_priority.py](#query_priority)
90. [fetch_pending.py](#fetch_pending)
91. [debug_profile_manual.py](#debug_profile_manual)

### Categoria: **Testing & Validation**
92. [test_advisor.py](#test_advisor)
93. [test_scraper_v2.py](#test_scraper_v2_test)
94. [test_scraper_integrity.py](#test_scraper_integrity_test)
95. [test_ai_service.py](#test_ai_service_test)
96. [test_ai_calibration.py](#test_ai_calibration_test)
97. [test_fallback_classification.py](#test_fallback_classification_test)

### Categoria: **Utilities & Helpers**
98. [pickle_vigilante.py](#pickle_vigilante)
99. [yolo_sentinel.py](#yolo_sentinel)
100. [work_session.py](#work_session)
101. [mcp_git_helper.py](#mcp_git_helper)
102. [watchdog_fallback.py](#watchdog_fallback)
103. [watchdog_tray.py](#watchdog_tray)
104. [kill_zombies.ps1](#kill_zombies)

### Categoria: **Sync & State Management**
105. [sync_reclassified_to_supabase.py](#sync_reclassified_to_supabase)
106. [sync_reclassified_state.json](#sync_reclassified_state)
107. [training_log.txt](#training_log)
108. [update_threat_profiles.py](#update_threat_profiles)

---

## 📖 Detalhes de Scripts

### Database & Migrations

<a name="apply_local_migrations"></a>
#### `apply_local_migrations.py`
**Descrição**: Aplica migrações de banco de dados a partir do diretório local.  
**Uso**: `python scripts/apply_local_migrations.py`  
**Dependências**: Supabase client, migrations files  
**Retorno**: Status de sucesso/falha para cada migração  

<a name="apply_migration"></a>
#### `apply_migration.py`
**Descrição**: Aplica uma migração específica ao banco de dados.  
**Uso**: `python scripts/apply_migration.py <migration_name>`  
**Parâmetros**: `migration_name` — Nome do arquivo de migração  
**Exemplo**: `python scripts/apply_migration.py migration_v28.0_ci_governance.sql`

<a name="create_anuncios_table"></a>
#### `create_anuncios_table.sql`
**Descrição**: SQL para criar tabela de anúncios (v20.0+).  
**Execução**: Via Supabase SQL Editor ou `psql`  
**Schema**: `id, anuncio_text, plataforma, candidato_id, created_at, updated_at`

<a name="db_migrate"></a>
#### `db_migrate.py`
**Descrição**: Wrapper para aplicar migrações com rollback.  
**Uso**: `python scripts/db_migrate.py [--rollback]`  
**Dependências**: supabase-py, migrations/  
**Exemplo**: `python scripts/db_migrate.py --rollback migration_v28.0_ci_governance`

<a name="verify_schema"></a>
#### `verify_schema.py`
**Descrição**: Verifica integridade do schema vs. código.  
**Uso**: `python scripts/verify_schema.py`  
**Retorno**: Lista de inconsistências (colunas faltantes, tipos incomuns)

<a name="check_tables"></a>
#### `check_tables.py`
**Descrição**: Lista todas as tabelas e suas colunas.  
**Uso**: `python scripts/check_tables.py`  
**Retorno**: Dump de schema em formato tabulado

<a name="list_tables"></a>
#### `list_tables.py`
**Descrição**: Simples listagem de todas as tabelas.  
**Uso**: `python scripts/list_tables.py`  
**Retorno**: Nome das tabelas, uma por linha

---

### Configuration & Setup

<a name="add_target"></a>
#### `add_target.py`
**Descrição**: Adiciona um novo alvo (candidato) manualmente.  
**Uso**: `python scripts/add_target.py --username <username> [--termometro QUENTE|MORNO|FRIO]`  
**Parâmetros**:
- `--username` (obrigatório): Username do Instagram
- `--termometro` (opcional): QUENTE, MORNO, ou FRIO (default: MORNO)

**Exemplo**:
```bash
python scripts/add_target.py --username lula --termometro QUENTE
```

<a name="delete_target"></a>
#### `delete_target.py`
**Descrição**: Remove um alvo do monitoramento.  
**Uso**: `python scripts/delete_target.py --username <username>`  
**Parâmetros**: `--username` (obrigatório)  
**Exemplo**: `python scripts/delete_target.py --username bolsonaro`

<a name="bundle_frontend"></a>
#### `bundle_frontend.py`
**Descrição**: Empacota frontend (Next.js) para deploy.  
**Uso**: `python scripts/bundle_frontend.py`  
**Pré-requisitos**: `npm install` completo no `/workspace/frontend/`  
**Retorno**: `.next/` build directory

<a name="deploy_frontend"></a>
#### `deploy_frontend.py`
**Descrição**: Faz deploy do frontend para servidor/CDN.  
**Uso**: `python scripts/deploy_frontend.py [--env prod|staging|dev]`  
**Parâmetros**: `--env` (default: prod)  
**Dependências**: AWS S3 / Vercel / Firebase credentials  
**Exemplo**: `python scripts/deploy_frontend.py --env prod`

<a name="setup_stripe_catalog"></a>
#### `setup_stripe_catalog.py`
**Descrição**: Configura catálogo de produtos no Stripe.  
**Uso**: `python scripts/setup_stripe_catalog.py`  
**Pré-requisitos**: `STRIPE_API_KEY` em `.env`  
**Retorno**: Product IDs criados  
**Nota**: Idempotente — execuções múltiplas são seguras

<a name="seed_tier1_profiles"></a>
#### `seed_tier1_profiles.py`
**Descrição**: Popula banco de dados com perfis iniciais Tier 1.  
**Uso**: `python scripts/seed_tier1_profiles.py`  
**Dados**: ~50 perfis de políticos e personalidades conhecidas  
**Efeito**: Adiciona a `candidatos` table

<a name="inject_ig_session"></a>
#### `inject_ig_session.py`
**Descrição**: Injeta sessão do Instagram (cookies/tokens) para scraping.  
**Uso**: `python scripts/inject_ig_session.py --account <account_name> --cookies <cookies_json>`  
**Parâmetros**:
- `--account` (obrigatório): Nome da conta IG
- `--cookies` (obrigatório): JSON de cookies

**Uso Típico**: Para adicionar nova conta de scraping

<a name="export_instagram_storage_state"></a>
#### `export_instagram_storage_state.py`
**Descrição**: Exporta estado de sessão/autenticação do Instagram.  
**Uso**: `python scripts/export_instagram_storage_state.py --account <account>`  
**Retorno**: JSON com cookies e tokens  
**Uso**: Backup/migração de sessões

<a name="export_playwright_cookies"></a>
#### `export_playwright_cookies.py`
**Descrição**: Exporta cookies do Playwright (usado por scraper).  
**Uso**: `python scripts/export_playwright_cookies.py`  
**Retorno**: Arquivo JSON com estado do browser

---

### Health Checks & Monitoring

<a name="check_drift"></a>
#### `check_drift.py`
**Descrição**: Verifica drift entre código e banco de dados.  
**Uso**: `python scripts/check_drift.py`  
**Retorna**: Lista de inconsistências (colunas não documentadas, enums diferentes, etc.)

<a name="check_kpi_values"></a>
#### `check_kpi_values.py`
**Descrição**: Valida valores de KPIs no banco.  
**Uso**: `python scripts/check_kpi_values.py`  
**Checks**:
- `burn_rate > 0 AND burn_rate < 100`
- `monthly_revenue >= 0`
- `active_users_count >= 0`

<a name="check_stripe"></a>
#### `check_stripe.py`
**Descrição**: Verifica status de pagamentos no Stripe.  
**Uso**: `python scripts/check_stripe.py`  
**Retorna**: Status de últimas transações, saldo, alertas

<a name="check_supabase"></a>
#### `check_supabase.py`
**Descrição**: Verifica conectividade e health do Supabase.  
**Uso**: `python scripts/check_supabase.py`  
**Checks**:
- Connection alive?
- All tables accessible?
- Realtime working?

<a name="diagnose_workers"></a>
#### `diagnose_workers.py`
**Descrição**: Diagnostica saúde de workers ativos.  
**Uso**: `python scripts/diagnose_workers.py`  
**Retorna**: Status de cada worker (uptime, último ciclo, erros)  
**Exemplo saída**:
```
scraper-worker-1: UP, uptime=12h, last_cycle=2min ago, errors=0
ai-processor-1: UP, uptime=24h, last_cycle=30sec ago, errors=2
dossier-worker-1: DOWN, last_seen=2h ago
```

<a name="generate_telemetry_report"></a>
#### `generate_telemetry_report.py`
**Descrição**: Gera relatório de telemetria/performance.  
**Uso**: `python scripts/generate_telemetry_report.py [--days 7]`  
**Parâmetros**: `--days` (default: 7) — período de análise  
**Retorna**: PDF/JSON com métricas de performance

<a name="inspect_anuncios"></a>
#### `inspect_anuncios.py`
**Descrição**: Inspeciona tabela de anúncios (stats, distribuição).  
**Uso**: `python scripts/inspect_anuncios.py`  
**Retorna**: Count por candidato, média de sentimento, etc.

<a name="inspect_metrics"></a>
#### `inspect_metrics.py`
**Descrição**: Inspeciona métricas acumuladas no banco.  
**Uso**: `python scripts/inspect_metrics.py`  
**Retorna**: Snapshot de KPIs, estatísticas

<a name="list_candidates"></a>
#### `list_candidates.py`
**Descrição**: Lista todos os candidatos monitorados.  
**Uso**: `python scripts/list_candidates.py [--filter status=Ativo]`  
**Parâmetros**: `--filter` (opcional) — filtro SQL-like  
**Retorna**: Tabela com username, status, last_scraped_at, termometro

---

### Scraping & Data Collection

<a name="cloud_scrape_cycle"></a>
#### `cloud_scrape_cycle.py`
**Descrição**: Executa um ciclo completo de scraping na nuvem.  
**Uso**: `python scripts/cloud_scrape_cycle.py [--cycles 1] [--worker-id scraper-1]`  
**Parâmetros**:
- `--cycles` (default: 1) — quantos ciclos executar
- `--worker-id` (opcional) — ID único do worker

**Retorna**: Status de sucesso/falha para cada alvo scrapeado

<a name="test_scraper_v2"></a>
#### `test_scraper_v2.py`
**Descrição**: Testa scraper v2 com alvo específico.  
**Uso**: `python scripts/test_scraper_v2.py --target <username>`  
**Parâmetros**: `--target` (obrigatório) — username IG  
**Retorna**: JSON com dados scrapeados (posts, comentários, etc.)

<a name="debug_scraper_v2"></a>
#### `debug_scraper_v2.py`
**Descrição**: Debug detalhado do scraper (logs, screenshots, timing).  
**Uso**: `python scripts/debug_scraper_v2.py --target <username> [--verbose]`  
**Parâmetros**:
- `--target` (obrigatório)
- `--verbose` (opcional) — mais logs

**Output**: Capturas de tela do browser, timing de cada etapa

<a name="test_scraper_integrity"></a>
#### `test_scraper_integrity.py`
**Descrição**: Testa integridade dos dados scrapeados.  
**Uso**: `python scripts/test_scraper_integrity.py`  
**Checks**:
- Nenhum comentário duplicado?
- Timestamps válidos?
- Dados de usuário completos?

<a name="research_pinned_posts"></a>
#### `research_pinned_posts.py`
**Descrição**: Analisa posts fixados de candidatos (importância).  
**Uso**: `python scripts/research_pinned_posts.py`  
**Retorna**: CSV com análise de conteúdo de posts fixados

<a name="research_pdf_criteria"></a>
#### `research_pdf_criteria.py`
**Descrição**: Pesquisa critérios para geração de PDFs em dossiês.  
**Uso**: `python scripts/research_pdf_criteria.py`  
**Retorna**: Recomendações de layout, formatação

<a name="run_scrapy_spider"></a>
#### `run_scrapy_spider.py`
**Descrição**: Executa spider Scrapy (alternativa ao Playwright).  
**Uso**: `python scripts/run_scrapy_spider.py --url <url>`  
**Parâmetros**: `--url` (obrigatório)  
**Nota**: Configuração alternativa, menos usada que v2

<a name="probe_t3_profile_html"></a>
#### `probe_t3_profile_html.py`
**Descrição**: Sonda HTML de perfil no Instagram (análise estrutural).  
**Uso**: `python scripts/probe_t3_profile_html.py --username <username>`  
**Retorna**: Análise de DOM, classes CSS, estrutura

<a name="probe_t3_2_storage"></a>
#### `probe_t3_2_storage.py`
**Descrição**: Analisa storage/cache do Playwright (debug).  
**Uso**: `python scripts/probe_t3_2_storage.py`  
**Retorna**: Snapshot de estado persistido

<a name="extract_pdfs"></a>
#### `extract_pdfs.py`
**Descrição**: Extrai PDFs de perfis/documentos públicos.  
**Uso**: `python scripts/extract_pdfs.py [--candidates-csv file.csv]`  
**Parâmetros**: `--candidates-csv` (opcional)  
**Retorna**: PDFs salvos em `/workspace/pdfs/`

<a name="purge_youtube"></a>
#### `purge_youtube.py`
**Descrição**: Remove dados coletados do YouTube (limpeza de cache).  
**Uso**: `python scripts/purge_youtube.py`  
**Efeito**: Limpa tabela `youtube_videos` ou similar

---

### Classification & AI

<a name="cloud_classify_batch"></a>
#### `cloud_classify_batch.py`
**Descrição**: Classifica lote de comentários via AIService.  
**Uso**: `python scripts/cloud_classify_batch.py [--count 100]`  
**Parâmetros**: `--count` (default: 100) — quantos classificar  
**Retorna**: Estatísticas de classificação (positivo/neutro/negativo)

<a name="force_reclassify"></a>
#### `force_reclassify.py`
**Descrição**: Força reclassificação de comentários já classificados.  
**Uso**: `python scripts/force_reclassify.py --filter <sql_where>`  
**Parâmetros**: `--filter` (obrigatório) — cláusula WHERE  
**Exemplo**: `python scripts/force_reclassify.py --filter "confidence < 0.7"`

<a name="mass_classify"></a>
#### `mass_classify.py`
**Descrição**: Classifica em massa todos os comentários não classificados.  
**Uso**: `python scripts/mass_classify.py [--batch-size 50]`  
**Parâmetros**: `--batch-size` (default: 50)  
**Duração**: ~1h para 10k comentários

<a name="reclassify_csv"></a>
#### `reclassify_csv.py`
**Descrição**: Reclassifica comentários a partir de CSV com IDs.  
**Uso**: `python scripts/reclassify_csv.py --file <csv_path>`  
**CSV Format**: `comment_id, new_sentiment`  
**Exemplo**: 
```
12345,POSITIVO
12346,NEGATIVO
```

<a name="reclassify_low_confidence"></a>
#### `reclassify_low_confidence.py`
**Descrição**: Reclassifica comentários com confiança baixa.  
**Uso**: `python scripts/reclassify_low_confidence.py --threshold 0.6`  
**Parâmetros**: `--threshold` (default: 0.7) — mín confiança  
**Efeito**: Marca antigos como `needs_review`

<a name="reclassify_neutral"></a>
#### `reclassify_neutral.py`
**Descrição**: Revisa todos os comentários neutros para reclassificação.  
**Uso**: `python scripts/reclassify_neutral.py`  
**Nota**: Útil quando lógica de neutralidade muda

<a name="reset_failed_classifications"></a>
#### `reset_failed_classifications.py`
**Descrição**: Reseta classificações que falharam (error status).  
**Uso**: `python scripts/reset_failed_classifications.py`  
**Efeito**: Marca `status=PENDENTE` para retry

<a name="test_ai_service"></a>
#### `test_ai_service.py`
**Descrição**: Testa AIService com prompt de teste.  
**Uso**: `python scripts/test_ai_service.py --text <text>`  
**Parâmetros**: `--text` (obrigatório)  
**Retorna**: Classificação + confidence

<a name="test_ai_calibration"></a>
#### `test_ai_calibration.py`
**Descrição**: Calibra AIService (threshold tuning).  
**Uso**: `python scripts/test_ai_calibration.py`  
**Testa**: Diferentes temperaturas, modelos  
**Retorna**: Matriz de performance

<a name="test_fallback_classification"></a>
#### `test_fallback_classification.py`
**Descrição**: Testa fallback LLM classification.  
**Uso**: `python scripts/test_fallback_classification.py --provider <name>`  
**Parâmetros**: `--provider` (ex: openai_gpt35, groq_llama3)  
**Retorna**: Latência + resultado

<a name="train_ia"></a>
#### `train_ia.py`
**Descrição**: Treina modelo de IA custom (deprecated, usa gold_dataset.json agora).  
**Uso**: `python scripts/train_ia.py`  
**Nota**: Substituído por dynamic embedding via `custom_rules.json`

---

### Workers & Agents

<a name="run_audit_agent"></a>
#### `run_audit_agent.py`
**Descrição**: Executa worker de auditoria uma vez.  
**Uso**: `python scripts/run_audit_agent.py [--cycles 1]`  
**Parâmetros**: `--cycles` (default: 1)  
**Retorna**: Relatório de inconsistências encontradas

<a name="run_dossier_agent"></a>
#### `run_dossier_agent.py`
**Descrição**: Executa worker de dossiês (gera PDFs).  
**Uso**: `python scripts/run_dossier_agent.py --target <username>`  
**Parâmetros**: `--target` (obrigatório)  
**Retorna**: Caminho para PDF gerado

<a name="run_scanner_agent"></a>
#### `run_scanner_agent.py`
**Descrição**: Executa worker de scanning (candidatos).  
**Uso**: `python scripts/run_scanner_agent.py [--cycles 1]`  
**Parâmetros**: `--cycles` (default: 1)  
**Retorna**: Novos candidatos descobertos

<a name="worker_classificador"></a>
#### `worker_classificador.py`
**Descrição**: Worker de classificação em loop (daemon).  
**Uso**: `python scripts/worker_classificador.py [--worker-id clf-1]`  
**Parâmetros**: `--worker-id` (opcional, default: auto)  
**Comportamento**: Loop infinito, processa ciclos até SIGTERM  
**Logs**: `/logs/worker_classificador.log`

<a name="auto_sync_daemon"></a>
#### `auto_sync_daemon.py`
**Descrição**: Daemon de sincronização automática (CQRS).  
**Uso**: `python scripts/auto_sync_daemon.py [--interval 60]`  
**Parâmetros**: `--interval` (default: 60s)  
**Retorna**: Estado de sincronização periódico  
**Nota**: Roda em background continuamente

<a name="night_watch_pipeline"></a>
#### `night_watch_pipeline.sh`
**Descrição**: Pipeline de trabalhos noturnos (bash script).  
**Uso**: `bash scripts/night_watch_pipeline.sh`  
**Tarefas**:
1. Limpeza de lixo
2. Análise de logs
3. Backup de dados
4. Relatório de saúde

**Agendado**: Cron job às 23:00

---

### Data Cleanup & Maintenance

<a name="cleanup_comments"></a>
#### `cleanup_comments.py`
**Descrição**: Remove comentários duplicados ou spam.  
**Uso**: `python scripts/cleanup_comments.py [--dry-run]`  
**Parâmetros**: `--dry-run` (opcional) — simular sem deletar  
**Retorna**: Count de comentários removidos

<a name="cleanup_parties"></a>
#### `cleanup_parties.py`
**Descrição**: Limpa dados de partidos inválidos.  
**Uso**: `python scripts/cleanup_parties.py`  
**Efeito**: Remove referências órfãs, normaliza nomes

<a name="cleanup_scanner_noise"></a>
#### `cleanup_scanner_noise.py`
**Descrição**: Remove falsos positivos do scanner de candidatos.  
**Uso**: `python scripts/cleanup_scanner_noise.py`  
**Filtro**: Perfis < 1000 seguidores (spam)

<a name="clean_parties"></a>
#### `clean_parties.py`
**Descrição**: Alias para cleanup_parties.py (versão alternativa).  
**Uso**: Idem cleanup_parties.py

<a name="purge_garbage_comments"></a>
#### `purge_garbage_comments.py`
**Descrição**: Remove comentários identificados como lixo/bot.  
**Uso**: `python scripts/purge_garbage_comments.py [--confidence 0.8]`  
**Parâmetros**: `--confidence` (default: 0.95) — min score para deletar  
**Nota**: Irreversível, usar com cuidado

<a name="saneamento_lexical"></a>
#### `saneamento_lexical.py`
**Descrição**: Normaliza texto de comentários (acentos, unicode, spam).  
**Uso**: `python scripts/saneamento_lexical.py`  
**Efeito**: Atualiza coluna `text_normalized` em comentários  
**Nota**: Idempotente, seguro executar múltiplas vezes

<a name="_fix_sessionid_conta1"></a>
#### `_fix_sessionid_conta1.py`
**Descrição**: Fix específico para bug de session ID da conta 1.  
**Uso**: `python scripts/_fix_sessionid_conta1.py`  
**Escopo**: Apenas conta 1  
**Status**: Legacy, raramente necessário

<a name="cloud_queue_refresh"></a>
#### `cloud_queue_refresh.py`
**Descrição**: Refresca/repopula fila de coleta automática.  
**Uso**: `python scripts/cloud_queue_refresh.py [--min-pending 50]`  
**Parâmetros**: `--min-pending` (default: 50)  
**Efeito**: Auto-insere candidatos antigos se fila baixa

---

### Analysis & Reporting

<a name="generate_audit"></a>
#### `generate_audit.py`
**Descrição**: Gera auditoria de integridade de dados.  
**Uso**: `python scripts/generate_audit.py [--output report.json]`  
**Parâmetros**: `--output` (default: audit_TIMESTAMP.json)  
**Retorna**: Relatório JSON com status de cada tabela

<a name="generate_sentinela_monetizacao"></a>
#### `generate_sentinela_monetizacao.py`
**Descrição**: Gera relatório de monetização da Sentinela.  
**Uso**: `python scripts/generate_sentinela_monetizacao.py`  
**Retorna**: Dashboard JSON: revenue, burn_rate, MRR, etc.

<a name="harvest_gold_dataset"></a>
#### `harvest_gold_dataset.py`
**Descrição**: Coleta exemplos de qualidade alta para gold dataset (treino de IA).  
**Uso**: `python scripts/harvest_gold_dataset.py [--count 100]`  
**Parâmetros**: `--count` (default: 1000)  
**Retorna**: JSON lines com comentários + labels  
**Saída**: `/workspace/data/gold_dataset.json`

<a name="report_new_targets"></a>
#### `report_new_targets.py`
**Descrição**: Relata novos alvos descobertos recentemente.  
**Uso**: `python scripts/report_new_targets.py [--days 7]`  
**Parâmetros**: `--days` (default: 7)  
**Retorna**: Lista de novos candidatos + fonte de descoberta

<a name="verify_cqrs_001"></a>
#### `verify_cqrs_001.py`
**Descrição**: Verifica integridade de dados entre read model (cache) e write model (DB).  
**Uso**: `python scripts/verify_cqrs_001.py`  
**Retorna**: Inconsistências encontradas  
**Nota**: CQRS = Command Query Responsibility Segregation

<a name="query_priority"></a>
#### `query_priority.py`
**Descrição**: Consulta prioridade de candidatos (ordem de processamento).  
**Uso**: `python scripts/query_priority.py`  
**Retorna**: Ranking de próximos a processar

<a name="fetch_pending"></a>
#### `fetch_pending.py`
**Descrição**: Busca tarefas pendentes não processadas.  
**Uso**: `python scripts/fetch_pending.py [--type comment]`  
**Parâmetros**: `--type` (ex: comment, classification)  
**Retorna**: JSON array de itens pendentes

<a name="debug_profile_manual"></a>
#### `debug_profile_manual.py`
**Descrição**: Debug manual de perfil específico.  
**Uso**: `python scripts/debug_profile_manual.py --username <username>`  
**Parâmetros**: `--username` (obrigatório)  
**Retorna**: Snapshot completo do perfil + logs de processamento

---

### Testing & Validation

<a name="test_advisor"></a>
#### `test_advisor.py`
**Descrição**: Testa AI Advisor (recomendações de ações).  
**Uso**: `python scripts/test_advisor.py --scenario <name>`  
**Parâmetros**: `--scenario` (ex: "threat_detected", "user_paused")  
**Retorna**: Recomendações de ação

---

### Utilities & Helpers

<a name="pickle_vigilante"></a>
#### `pickle_vigilante.py`
**Descrição**: Serializa/deserializa vigilantes de dados (debug).  
**Uso**: `python scripts/pickle_vigilante.py [--action dump|load]`  
**Parâmetros**: `--action` (dump = serializar, load = carregar)

<a name="yolo_sentinel"></a>
#### `yolo_sentinel.py`
**Descrição**: "You Only Look Once" — detector rápido de anomalias.  
**Uso**: `python scripts/yolo_sentinel.py`  
**Nota**: Experimental, alertas em tempo real

<a name="work_session"></a>
#### `work_session.py`
**Descrição**: Gerencia sessão de trabalho (state, resumption).  
**Uso**: `python scripts/work_session.py [--action start|stop|status]`  
**Parâmetros**: `--action` (default: status)

<a name="mcp_git_helper"></a>
#### `mcp_git_helper.py`
**Descrição**: Helper para integração com Git (MCP — Model Control Protocol).  
**Uso**: `python scripts/mcp_git_helper.py [--command <cmd>]`  
**Nota**: Interno, para CI/CD

<a name="watchdog_fallback"></a>
#### `watchdog_fallback.py`
**Descrição**: Watchdog que monitora fallback LLM providers.  
**Uso**: `python scripts/watchdog_fallback.py`  
**Comportamento**: Loop, verifica saúde a cada 60s

<a name="watchdog_tray"></a>
#### `watchdog_tray.py`
**Descrição**: Watchdog com interface de system tray.  
**Uso**: `python scripts/watchdog_tray.py`  
**GUI**: Notificações de status no tray

<a name="kill_zombies"></a>
#### `kill_zombies.ps1`
**Descrição**: PowerShell script para matar processos zumbis (Windows).  
**Uso**: `powershell -ExecutionPolicy Bypass -File scripts/kill_zombies.ps1`  
**Plataforma**: Windows only

---

### Sync & State Management

<a name="sync_reclassified_to_supabase"></a>
#### `sync_reclassified_to_supabase.py`
**Descrição**: Sincroniza comentários reclassificados localmente para Supabase.  
**Uso**: `python scripts/sync_reclassified_to_supabase.py`  
**Pré-requisito**: `sync_reclassified_state.json` populado  
**Efeito**: Atualiza `sentimentos` coluna

<a name="sync_reclassified_state"></a>
#### `sync_reclassified_state.json`
**Descrição**: Arquivo de estado (JSON) com histórico de reclassificações.  
**Localização**: `/workspace/scripts/`  
**Estrutura**: Array de {comment_id, old_sentiment, new_sentiment, timestamp}

<a name="update_threat_profiles"></a>
#### `update_threat_profiles.py`
**Descrição**: Atualiza perfis de ameaça baseado em análise recente.  
**Uso**: `python scripts/update_threat_profiles.py`  
**Efeito**: Recalcula score de risco para cada candidato

---

## 🔗 Execução Rápida

### Database
```bash
python scripts/verify_schema.py          # Validar schema
python scripts/apply_migration.py <name> # Aplicar migração
python scripts/check_tables.py            # Listar tabelas
```

### Monitoring
```bash
python scripts/diagnose_workers.py       # Status de workers
python scripts/check_supabase.py         # Saúde Supabase
python scripts/generate_telemetry_report.py # Performance report
```

### Scraping
```bash
python scripts/cloud_scrape_cycle.py     # Um ciclo de scraping
python scripts/test_scraper_v2.py --target <user> # Teste alvo
```

### Classification
```bash
python scripts/cloud_classify_batch.py   # Classifica lote
python scripts/test_ai_service.py --text "<text>" # Testa IA
```

### Cleanup
```bash
python scripts/cleanup_comments.py --dry-run  # Simular limpeza
python scripts/saneamento_lexical.py          # Normaliza texto
```

---

## ⚠️ Scripts Críticos

**🔴 Cuidado ao executar:**
- `delete_target.py` — Irreversível
- `purge_garbage_comments.py` — Irreversível
- `migration_*.sql` — Alteram schema
- `reset_failed_classifications.py` — Marca para reprocessamento em massa

**✅ Sempre teste com `--dry-run` primeiro** (se aplicável)

---

## 📞 Suporte

- Script não listado? Procure em `/workspace/scripts/`
- Dúvida sobre uso? Consulte shebangs/docstrings do script
- Erro ao executar? Verifique variáveis de ambiente em `.env`

---

## ✅ Checklist para Novo Script

Ao criar novo script:
- [ ] Adicionar ao `/workspace/scripts/`
- [ ] Incluir docstring em português
- [ ] Adicionar suporte a `--help` ou argparse
- [ ] Documentar aqui neste arquivo
- [ ] Incluir exemplos de uso
- [ ] Considerar `--dry-run` para operações destrutivas

