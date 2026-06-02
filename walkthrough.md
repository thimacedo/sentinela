# Walkthrough — Sub-Agentes, Resiliência de Reclassificação e Governança de IA (v86.8)

Esta versão consolida as entregas das rodadas de **01/06** e **02/06/2026**, elevando a capacidade de auto-melhoria da IA e a resiliência operacional do Sentinela.

---

## Rodada 02/06/2026 — Sub-Agentes e Reclassificação Resiliente

### 1. Sub-agente `reclassify_agent`

- **Definição**: Sub-agente especializado em reclassificação de comentários de baixa confiança (≤ 50%).
- **Script**: [`scripts/reclassify_low_confidence.py`](file:///c:/Projetos/sentinela/scripts/reclassify_low_confidence.py)
- **Fluxo**: Varredura do banco → Reclassificação via Cloud (Groq → OpenRouter → Mistral) → Fallback automático para LiteRT/Ollama local em caso de indisponibilidade.
- **Resiliência**: Backoff dinâmico de 5s entre tentativas para evitar sobrecarga das cotas de API.

### 2. Sub-agente `researcher_agent`

- **Definição**: Sub-agente pesquisador de critérios semânticos de classificação a partir de bases documentais.
- **Script**: [`scripts/research_pdf_criteria.py`](file:///c:/Projetos/sentinela/scripts/research_pdf_criteria.py)
- **Fluxo**: Análise de PDFs/MDs em `bases_pdf/` via `pypdf` → Extração de heurísticas semânticas → Consolidação em [`config/custom_rules.json`](file:///c:/Projetos/sentinela/config/custom_rules.json) → Injeção dinâmica no `SYSTEM_PROMPT` do [`core/ai_service.py`](file:///c:/Projetos/sentinela/core/ai_service.py).
- **Artefato vivo**: `PADRONIZACAO_LINGUISTICA_FORENSE.md` atualizado automaticamente com novas heurísticas descobertas.

---

## Rodada 01/06/2026 — Correções de IA e Infraestrutura

### 3. Restauração do Método `_call_provider`

- Método ausente em `core/ai_service.py` foi restaurado, desbloqueando o pipeline de inteligência.
- Timeouts agressivos (1.5s) e `max_retries=0` configurados nos provedores locais para resposta imediata em caso de falha.

### 4. Rotação Circular de Fallback de IA

- Provedores indisponíveis temporariamente são movidos para o **final da fila** de prioridade (rotação circular).
- Provedores locais (`litert`/`ollama`): descarte permanente apenas após **3 falhas físicas consecutivas**.
- Provedores Cloud: descarte permanente apenas em erros graves de autenticação (`401`/`403`).

### 5. Reinjeção de Credenciais Locais

- `load_dotenv(override=True)` forçado em `main_runner.py`, `watchdog/__init__.py`, `core/config.py` e scripts auxiliares.
- Elimina erros `401 Unauthorized` causados por chaves globais expiradas no Windows sobrescrevendo o `.env` correto.

### 6. Monitoramento de Saúde do Ollama e LiteRT

- **Ollama**: porta `11434`, endpoint `/api/tags`.
- **LiteRT**: porta `9379`, endpoint `/v1/models`.
- Corrigido em `watchdog/__init__.py` e [`core/health_check.py`](file:///c:/Projetos/sentinela/core/health_check.py): limpeza de aspas/paths do `.env`, status real (OK/DOWN) refletido no painel.

### 7. Saneamento de Comentários com ERRO

- Script `scripts/reset_failed_classifications.py` executado: **6.760 comentários** devolvidos à fila de classificação (3.962 + 2.798 em dois ciclos).

---

## Rodada v86.7 (anteriores) — Referência

| Entrega | Status |
|---|---|
| Dashboard DRE Financeiro (Recharts) | ✅ Entregue |
| Harmonização Tipográfica / Glassmorphism | ✅ Entregue |
| Resiliência do Watchdog (RuntimeError IG) | ✅ Entregue |
| Deduplicação de Clusters (frozenset) | ✅ Entregue |
| Grafo de Ligações Táticas (CanvasRenderingContext2D) | ✅ Entregue |
| Normalização DB de Partidos | ✅ Entregue |
| Termômetro de Candidatos (timestamp real) | ✅ Entregue |
| Signal Handler Windows (SIGTERM/SIGINT) | ✅ Entregue |
| Scanner de Candidatos com IA + DuckDuckGo | ✅ Entregue |
| Validação Manual de Sessão IG (--interactive) | ✅ Entregue |

---

## Verificação e Resultados

1. **Reclassificador Operacional**: Pipeline Groq → Mistral → Ollama funcional com fallback automático.
2. **Pesquisador de Critérios**: `custom_rules.json` alimentado com heurísticas extraídas dos PDFs de base.
3. **Infraestrutura de IA Estável**: Circuit breaker ativo, rotação circular de provedores sem descarte precoce.
4. **Commits Rastreáveis**: Todas as entregas registradas com Conventional Commits e push imediato ao `main`.
5. **Documentação Sincronizada**: STATE.md (v86.8), ROADMAP.md (Fase 8 definida), walkthrough.md e task.md atualizados.

---

## Próximos Marcos (Fase 8)

| # | Ação | Impacto Esperado |
|---|---|---|
| 8.1 | Desacoplar `IGWorkerV2` → `ScraperWorker` + `AIWorker` | Memória ↓ 40%, throughput ↑ |
| 8.2 | `asyncio.Semaphore(3)` no Orchestrator | 3x taxa de ingestão |
| 8.3 | PGMQ na `fila_coleta` | Suporte a cluster multi-servidor |
| 8.4 | Rotação de proxies no Playwright | Anti-shadowban grau Extremo |
| 8.5 | Checkpoint SQLite no IGWorker | Zero-loss em reinicializações |
| 8.6 | Circuit Breaker para Supabase + Scraping | Proteção global de infraestrutura |
