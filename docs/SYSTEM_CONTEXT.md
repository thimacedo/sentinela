# Sentinela - Referência Arquitetural de Engenharia (PASA v50.1)

## 1. Visão de Sistema & Missão
O Sentinela é um ecossistema de análise linguística automatizada e monitoramento em larga escala. Sua missão é a **extração, normalização, classificação semântica e auditoria** de discursos em plataformas Meta, operando sob requisitos rigorosos de resiliência anti-bot, integridade de dados e conformidade legal.

## 2. Topologia de Infraestrutura (Asynchronous-Hybrid)
* **Node Local (Orquestrador):** `local_server.py` executado via `watchdog.py`. Gerencia filas, cooldowns, orquestração de workers e persistência local.
* **Workers (Processos Assíncronos):** `InstagramWorker` (e outros) processam alvos em paralelo, utilizando `asyncio` para I/O-bound tasks.
* **Motor de Ingestão (Zyte Integration):** Sistema híbrido `Zyte API` (Primário) + `Playwright` (Fallback). O motor decide dinamicamente a estratégia de extração (API JSON -> Renderização DOM -> Regex/Scraping).
* **Camada de Persistência (Supabase):** PostgreSQL configurado com Row Level Security (RLS). Estrutura relacional densa (`candidatos`, `comentarios`, `anuncios_pasa`, `fila_coleta`, `worker_sessions`).
* **Front-end:** SPA React, desacoplada, servida via Vercel, consumindo snapshots JSON/CSV gerados pelo pipeline de backend para evitar query load excessivo no Supabase.

## 3. Protocolo PASA (Metodologia de Análise Léxica)
O núcleo de inteligência é o **PASA v50.1**. Todo dado coletado passa por este pipeline de transformação:
1. **Sanitização (InstagramWorker):** Remoção de ruído, normalização de caracteres e limpeza de URLs (Regex + Hash-mapping para ID_EXTERNO).
2. **Normalização (core.normalizer):** Ajuste léxico para entrada nos modelos de IA.
3. **Classificação (IA Gateway):** Utiliza motor `Gemini 1.5 Flash` para classificação de risco e detecção de padrões de ódio.
4. **Auditoria (PASA Auditor):** Cross-check via `Groq/Llama 3` para validação de falsos positivos.
5. **Persistência de Dados:** Registro com data/hora UTC e rastreabilidade total da origem. Termos proibidos: "forense", "prova", "evidência" — usar "indício", "informação", "análise analítica".

## 4. Resiliência Operacional (The Guardian Logic)
O sistema possui mecanismos de auto-cura:
* **Circuit Breaker:** `InstagramWorker` verifica limites de requisições e falhas consecutivas antes de prosseguir.
* **Watchdog Guardião:** `watchdog.py` monitora o ciclo de vida do servidor. Se `local_server.py` travar, o watchdog realiza:
    1. Reinicialização do processo.
    2. Validação de dependências (`pip install -r requirements.txt`).
    3. Alerta crítico via WhatsApp (CallMeBot).
* **Zyte Health Check:** Rotina de ping (`zyte_checker.py`) a cada 30 min para garantir que o motor de scraping não está bloqueado.

## 5. Estratégia de Coleta Equalitária
O sistema evita o gasto predatório de créditos Zyte através de:
* **Priority-Based Batching:** Apenas alvos com `prioridade_coleta = 10` (Elite) são processados intensivamente.
* **Temporal Sharding:** Cooldown fixo de 12 horas entre raspagens do mesmo alvo.
* **Batch Limiting:** Máximo de 3 perfis por ciclo, com pausa de 60 segundos entre cada, suavizando a carga no Instagram e evitando detecção.

## 6. Governança e Compliance
* **Filtros Jurídicos:** Perfis marcados como `status_monitoramento = 'Pausado'` são saltados pelo orquestrador.
* **Audit Trail:** Logs de divergência de username em `divergent_usernames.log` para recalibragem humana.
* **Credenciais:** Uso de `.env` para gestão de segredos. Proibição absoluta de hardcoding. `SERVICE_KEY` exclusiva para backend — nunca exposta no frontend.
* **Terminologia:** Seguir estritamente as restrições de `GEMINI.md` — seção Proteção Jurídica.

## 7. SOP de Troubleshooting (Procedimento Padrão)
| Sintoma | Ação Técnica |
| :--- | :--- |
| `[ALERTA USERNAME]` | Verificar username em `divergent_usernames.log` e atualizar banco. |
| `Supabase 🔴 OFFLINE` | Verificar RLS Policies e conexão em `core/supabase_service.py`. |
| `Falha Zyte API` | Verificar `ZYTE_API_KEY` no `.env` e rodar `core/zyte_checker.py`. |
| Drift de KPIs | Executar `scripts/check_drift.py` e forçar `scripts/update_kpis.py`. |