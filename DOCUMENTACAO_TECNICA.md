# 📚 Documentação Técnica — Projeto Sentinela

## 1. Visão Geral

Sistema autônomo de coleta, classificação e monitoramento de conteúdo do Instagram. Arquitetura resiliente por design, com autocura ativa, filas atômicas no Supabase e scraping via Playwright.

---

## 2. Arquitetura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Daemon SRE    │────▶│ Agente Aut.  │────▶│  Supabase Queue │
│ (monitoramento) │     │ (Playwright) │     │  (claims atomic)│
└─────────────────┘     └──────────────┘     └─────────────────┘
         │                       │                       │
         └──── kill/restart ◄─────┘                       │
                                 └──────────▶ Ntfy (alerts)
```

---

## 3. Componentes

| Componente | Arquivo | Função |
|------------|---------|--------|
| **Agente Autônomo** | `sentinela_autonomous_agent.py` | Execução principal do loop autônomo e bandeja (tray) |
| **Scraper V2** | `core/instagram_scraper_v2.py` | Scraping, extração local/API/DOM e filtragem |
| **Queue Manager** | `core/agent_scraper/queue_manager.py` (ou RPCs Supabase) | Claims atômicos, releases e locks |
| **Daemon SRE** | `scripts/monitor_sre_daemon.py` | Heartbeat, autocura com tolerância de 10m/15m e telemetria |
| **Notificador** | `core/ntfy_client.py` | Alertas via Ntfy (MIME headers UTF-8, logging completo de exceções) |
| **Status Local** | `agent.status.json` | Estado, health, último diagnóstico |
| **Diretrizes** | `.agents/AGENTS.md` | Regras de SRE, encoding, graceful shutdown |

---

## 4. Fluxo de Execução

1. **Claim Atômico**: Obtém `queue_id` e `worker_id` do Supabase via RPC atômico.
2. **Modo Noturno**: Se hora local entre 23h–5h, entra em sleep de 300s (tolerado pelo daemon com threshold de 15min).
3. **Scraping**: Playwright navega no alvo. Fallback para `_extract_from_dom` se API/XHR/Scripts falharem.
4. **Filtragem**: `exact_junk` (descarte de botões) e `prefix_junk` (descarte de curtidas) evitam poluição do banco sem falsos positivos.
5. **Classificação**: Categoriza e detecta discursos impróprios ou spam via API Mistral/IA local.
6. **Persistência**: Insere comentários limpos no banco remoto. Atualiza `agent.status.json` (heartbeat).
7. **Release**: Libera lock atômico no Supabase (`release_atomic(queue_id, status, worker_id)`).
8. **Próximo ciclo**: Repete continuamente.

---

## 5. Diretrizes Críticas de SRE

### 5.1 Encoding (Windows CP1252)
Todo ponto de entrada deve reconfigurar streams no topo do arquivo:
```python
import sys
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except AttributeError:
        pass
```
FileHandlers de log e conexões de stream devem explicitar `encoding="utf-8"`.

### 5.2 Graceful Shutdown
Signal handlers (`SIGINT`, `SIGTERM`) combinados a blocos `finally` no loop `asyncio` garantem a liberação assíncrona do alvo no Supabase via `release_atomic` e salvam o estado limpo em `agent.status.json`.

### 5.3 Propagação de `worker_id`
O mesmo `worker_id` retornado no claim atômico deve ser passado obrigatoriamente no release. Caso contrário, locks persistirão órfãos em `EM_CURSO`.

### 5.4 Ntfy — MIME Headers
Cabeçalhos `Title` e `Tags` com emojis e caracteres não-ASCII devem ser codificados em formato MIME Header (`email.header.Header`) para evitar exceções de `latin-1` ao rodar sob Windows.

---

## 6. Filtro de Lixo (Comentários)

### 6.1 Camada JS (DOM)
JavaScript no `_extract_from_dom` filtra na origem spans que iniciam com metadados de curtidas (ex: *"Liked by"*) ou botões de UI antes do envio.

### 6.2 Camada Python (Normalização)
```python
exact_junk = {
    'também da meta', 'instagram lite', 'localizações', 'campanha 2201',
    'view replies', 'ver respostas', 'ver tradução', 'see translation', 'see original',
    'responder', 'reply', 'ver thread', 'view thread',
    'pinned', 'fixado', 'pinned by', 'fixado por',
    'original audio', 'áudio original', 'original sound', 'som original',
    'use template', 'usar modelo', 'remix', 'collaboration', 'colaboração'
}

prefix_junk = [
    'liked by', 'curtido por', 'others like this', 
    'pessoas curtiram', 'curtiram isto'
]
```
A verificação por prefixo e comparação exata elimina falsos positivos em comentários longos e legítimos.

---

## 7. Monitoramento SRE

| Métrica | Threshold | Ação |
|---------|-----------|------|
| Heartbeat lag (Diurno) | > 600s (10min) | Kill + Restart (Autocura) |
| Heartbeat lag (Noturno/Transição) | > 900s (15min) | Kill + Restart (Autocura) |
| Locks órfãos | > 0 | Higienização automática via cj_sre_health_check |

**Logs:** `logs/monitoramento_sre.log`  
**Status:** `agent.status.json`

---

## 8. Checklist Operacional

- [x] Commit atual carregado no runtime (compilação limpa do `15e1f0785`/`88c53208e`)
- [x] `.pyc` cache limpo recursivamente no deploy
- [x] `worker_id` propagado corretamente em claim/release
- [x] Ntfy configurado com MIME headers e log completo de exceções
- [x] Fila Supabase limpa e sem locks órfãos
- [x] `junk_patterns` ativo em todas as rotas de ingestão (API + DOM)
- [x] Daemon SRE rodando em background independente

---

## 9. Commits de Referência

| Hash | Descrição |
|------|-----------|
| `84614abc1` | Logging detalhado de erros Ntfy via `logger.exception` |
| `88c53208e` | Ajuste fino contra falsos positivos discursivos na filtragem |
| `15e1f0785` | Filtro de lixo em comentários (JS + Python) |
| `27315e35d` | Thresholds dinâmicos noturnos em daemon SRE |
| `87788a24f` | Suporte e cura de encoding UTF-8 em console Windows |
