# Queue Manager — Gerenciador de Fila de Alvos

**File**: `/workspace/core/queue_manager.py`  
**Versão**: PASA v88.0 (Fase 8.3)  
**Última Atualização**: 2026-06-04

---

## 📋 Visão Geral

O `QueueManager` é o coração do sistema de distribuição de trabalho na Sentinela. Ele gerencia uma fila de alvos (`candidatos`) com prioridades dinâmicas, suporta múltiplos workers em paralelo, e implementa mecanismos sofisticados de fairness, backoff adaptativo e desbloqueio automático de locks.

### Responsabilidades Principais
- ✅ Reivindicar (claim) o próximo alvo disponível com resposta atômica
- ✅ Liberar (release) alvos após processamento
- ✅ Auto-repopular a fila quando está vazia
- ✅ Gerenciar locks distributivos (SKIP LOCKED) para cluster horizontal
- ✅ Implementar smart backoff baseado em "temperatura" do candidato
- ✅ Rotacionar alvos e atualizar frequência de posts

---

## 🏗️ Arquitetura

### Componentes Principais

#### 1. **Fila de Prioridade (`fila_coleta`)**
Tabela com estrutura de fila prioritária:
```sql
CREATE TABLE fila_coleta (
  id UUID PRIMARY KEY,
  candidato_id TEXT NOT NULL,
  status ENUM ('PENDENTE', 'EM_CURSO', 'CONCLUIDO', 'FALHA', 'SEM_DADOS_RECENTES'),
  prioridade INT (1=MÁXIMA, 5=MÍNIMA),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  locked_by TEXT,           -- worker_id que está processando
  locked_at TIMESTAMP,      -- timestamp do lock
  UNIQUE(candidato_id, data_agendada)
);
```

#### 2. **Tabela de Candidatos**
Armazena estado de cada alvo:
```sql
CREATE TABLE candidatos (
  id UUID PRIMARY KEY,
  username TEXT UNIQUE,
  termometro ENUM ('QUENTE', 'MORNO', 'FRIO'),
  last_scraped_at TIMESTAMP,
  posts_frequencia_semanal FLOAT,
  status_monitoramento ENUM ('Ativo', 'Inativo', 'Pausado'),
  ...
);
```

#### 3. **Prioridades na Seleção**

O `QueueManager` implementa uma cascata de prioridades:

```
1. MÁXIMA:        Alvo Manual (config["target"] ou TEST_TARGET_USERNAME)
                  ↓
2. DISTRIBUIÇÃO:  25% de chance de priorizar Rotação Global (fairness)
                  75% de chance de buscar na fila_coleta
                  ↓
3. FALLBACK:      Se fila_coleta vazia → Rotação Global de candidatos
```

---

## 🔑 Métodos Principais

### `claim_next_target(config, seen_queue_ids, seen_targets, active_targets)`

Reclama o próximo alvo disponível (versão legada/síncrona).

**Parâmetros:**
- `config` (dict): Configuração com chave `target` para alvo manual
- `seen_queue_ids` (set): IDs de fila já processados neste ciclo
- `seen_targets` (set): Usernames já vistos neste ciclo
- `active_targets` (set, opcional): Alvos em processamento no cluster

**Retorna:** `Target` ou `None`

**Fluxo:**
1. Auto-repopula a fila se necessário
2. Tenta alvo manual (se configurado)
3. Alterna entre fila_coleta e rotação global com fairness (25/75)
4. Retorna o primeiro alvo desbloqueado

**Exemplo:**
```python
queue_manager = QueueManager(db_client)
target = queue_manager.claim_next_target(
    config={"target": "bolsonaro"},  # Processamento manual
    seen_queue_ids=set(),
    seen_targets=set(),
    active_targets=active_workers
)
```

---

### `claim_next_target_atomic(worker_id, seen_targets, active_targets, max_prioridade)`

**Reclama atomicamente** o próximo alvo usando `SELECT FOR UPDATE SKIP LOCKED` no Supabase.

**Parâmetros:**
- `worker_id` (str): ID único do worker (ex: `scraper-worker-1`)
- `seen_targets` (set, opcional): Alvos já vistos
- `active_targets` (set, opcional): Alvos em processamento
- `max_prioridade` (int): Máxima prioridade a considerar (default: 10)

**Retorna:** `Target` ou `None`

**Características Críticas:**
- ✅ **100% seguro para múltiplos workers** — função SQL `fila_coleta_claim_next()` realiza tudo atomicamente
- ✅ **SKIP LOCKED** — não compete por locks, evita deadlocks
- ✅ **Fallback automático** — se função SQL não existe, usa `claim_next_target()` legado
- ✅ **Bloqueia e marca** — marca como `EM_CURSO` + `locked_by=worker_id`

**Exemplo:**
```python
# Em um worker distribuído
target = queue_manager.claim_next_target_atomic(
    worker_id="scraper-worker-1",
    seen_targets=set(),
    max_prioridade=5  # Só pega prioridade <= 5
)
if target:
    try:
        # Processar target
        scrape_and_classify(target)
    finally:
        queue_manager.release_atomic(target.queue_id, "CONCLUIDO", "scraper-worker-1")
```

---

### `release_atomic(queue_id, status, worker_id)`

Libera um item da fila após processamento (versão atômica).

**Parâmetros:**
- `queue_id` (str/UUID): ID do item na fila_coleta
- `status` (str): `CONCLUIDO`, `FALHA`, `SEM_DADOS_RECENTES`, `PENDENTE`
- `worker_id` (str): Worker que está liberando

**Comportamento:**
- Tenta chamar `fila_coleta_release()` SQL function
- Fallback: atualiza direto a tabela se função não existir
- Log de erro se ambos falharem

**Nota:** Deve ser sempre chamado após `claim_next_target_atomic()`, mesmo em caso de erro.

---

### `release_stale_locks(timeout_minutes)`

Limpa locks expirados (workers que crasharam sem liberar).

**Parâmetros:**
- `timeout_minutes` (int): Quanto tempo para considerar um lock como expirado (default: 30)

**Retorna:** Número de locks liberados

**Uso Típico:**
```python
# Chamar a cada 10 ciclos do orquestrador
if cycle_count % 10 == 0:
    released = queue_manager.release_stale_locks(timeout_minutes=30)
    if released > 0:
        logger.info(f"Liberados {released} locks expirados")
```

---

### `rotate_target(target)`

Completa o processamento de um alvo: atualiza temperatura, frequência de posts, e status.

**Parâmetros:**
- `target` (Target): Objeto com `username`, `error`, `post_metas`, `queue_id`

**Lógica de Temperatura (PASA v86.3):**

```
Erro de Sistema/Sessão? (429, captcha, login wall, etc.)
  → Manter temperatura atual + atualizar last_scraped_at
  
Junk Detectado ou 404?
  → Manter temperatura (não punis)
  
Sem comentários encontrados?
  → Manter temperatura (falta de dados)
  
Dados válidos encontrados?
  → Calcular frequência = (num_posts / dias) * 7
  → Se frequência >= 5 → QUENTE
  → Se dias_desde_ultimo_post > 7 → FRIO
  → Senão → MORNO
```

**Exemplo:**
```python
# Após scraping bem-sucedido
target.post_metas = [
    {"timestamp": "2026-06-01T10:00:00"},
    {"timestamp": "2026-06-02T14:30:00"},
    ...
]
queue_manager.rotate_target(target)
# Atualiza: last_scraped_at, termometro, posts_frequencia_semanal
```

---

### `mark_candidate_scraped(target)`

Simples atualização de `last_scraped_at` (timestamp UTC).

**Uso:**
Quando você quer apenas registrar que o candidato foi processado, sem atualizar temperatura.

---

## 🔐 Sistema de Locks Distributivos

### Problema Resolvido
Com múltiplos workers em paralelo, dois workers poderiam reivindicar o mesmo alvo simultaneamente, causando duplicação de trabalho.

### Solução: Atomic Locking com SKIP LOCKED

Implementado via **SQL functions** no Supabase:

#### `fila_coleta_claim_next(p_worker_id, p_max_prioridade)`

```sql
-- Pseudocódigo
SELECT * FROM fila_coleta
WHERE status = 'PENDENTE' AND prioridade <= p_max_prioridade
ORDER BY prioridade ASC, created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Atualiza status para EM_CURSO + locked_by
UPDATE fila_coleta
SET status = 'EM_CURSO', locked_by = p_worker_id, locked_at = NOW()
WHERE id = (... the claimed row ...);

RETURN (... claimed row ...);
```

**Garantias:**
- ✅ Um único worker consegue o lock
- ✅ Outros workers saltam (`SKIP LOCKED`) sem bloquear
- ✅ Não há deadlock
- ✅ Altamente escalável para cluster horizontal

#### `fila_coleta_release(p_queue_id, p_status, p_worker_id)`

```sql
UPDATE fila_coleta
SET status = p_status, locked_by = NULL, locked_at = NULL, updated_at = NOW()
WHERE id = p_queue_id AND locked_by = p_worker_id;
```

#### `fila_coleta_release_stale(p_timeout_minutes)`

```sql
UPDATE fila_coleta
SET locked_by = NULL, locked_at = NULL, status = 'PENDENTE'
WHERE locked_at IS NOT NULL 
  AND locked_at < NOW() - INTERVAL p_timeout_minutes MINUTE
RETURNING COUNT(*);
```

---

## 🔄 Auto-Repopulação da Fila

### Problema
A fila pode se esvaziar se todos os candidatos forem processados.

### Solução: `_ensure_queue_populated()`

Chamada automaticamente no início de `claim_next_target()`:

**Lógica:**
1. Conta itens `PENDENTE` na `fila_coleta`
2. Se `< min_pending` (default: 50), reinsere candidatos
3. Busca candidatos ativos mais antigos (`last_scraped_at ASC`)
4. Calcula prioridade baseada em `termometro`:
   - `QUENTE` → prioridade 1
   - `MORNO`/`FRIO` → prioridade 5
   - Outros → prioridade 3

**Exemplo de Resultado:**
```
🔄 [Queue] Apenas 10 itens pendentes. Repopulando fila...
✅ [Queue] 40 candidato(s) reinserido(s) na fila automaticamente.
```

---

## 🌡️ Smart Backoff — Rotação com Inteligência Térmica

### Conceito
Diferentes candidatos têm diferentes necessidades de monitoramento:
- **QUENTE** (frequência semanal >= 5): Processar a cada 2 horas
- **MORNO** (frequência semanal < 5): Processar a cada 12 horas
- **FRIO** (sem posts recentes): Processar a cada 12+ horas

### Implementação em `_get_from_global_rotation()`

```python
# ❄️ SMART BACKOFF para FRIO (< 12h desde última raspagem)
cold_threshold = now - timedelta(hours=12)

# 🔥 TURBO BACKOFF para MORNO/QUENTE (< 2h desde última raspagem)
hot_threshold = now - timedelta(hours=2)

# Query Supabase com filtro dinâmico
.or_(
    "last_scraped_at.is.null,"  # Nunca foi raspado
    "and(termometro.eq.FRIO,last_scraped_at.lt.{cold_threshold}),"
    "and(termometro.neq.FRIO,last_scraped_at.lt.{hot_threshold})"
)
```

**Resultado:**
- Alvos QUENTE são sempre processados primeiro
- Alvos FRIO são espaçados (12h entre runs)
- Carga distribuída inteligentemente

---

## 📊 Data Flow

```
┌─────────────────────────────────────────┐
│ Worker inicia ciclo (ex: scraper)      │
└──────────────┬──────────────────────────┘
               ↓
        ┌──────────────────┐
        │ claim_next_target│
        │ ou              │
        │ claim_next_target│
        │ _atomic         │
        └──────────┬───────┘
                   ↓
        ┌──────────────────────────────────┐
        │ 1. Auto-repopula fila se vazia  │
        │ 2. Tenta alvo manual             │
        │ 3. Tenta fila_coleta (75%)      │
        │ 4. Tenta rotação global (fallback)
        └──────────┬───────────────────────┘
                   ↓
        ┌──────────────────┐
        │ Recebe Target    │
        │ ou None (fila ∅) │
        └──────────┬───────┘
                   ↓
        ┌──────────────────────────────────┐
        │ Processa target (scrape/classify)│
        └──────────┬───────────────────────┘
                   ↓
        ┌──────────────────────────────────┐
        │ rotate_target(target)            │
        │ - Calcula frequência             │
        │ - Atualiza termômetro            │
        │ - Update last_scraped_at         │
        └──────────┬───────────────────────┘
                   ↓
        ┌──────────────────────────────────┐
        │ release_atomic(queue_id, status) │
        │ - Desbloqueia no banco            │
        └──────────┬───────────────────────┘
                   ↓
        ┌──────────────────┐
        │ Próximo ciclo    │
        └──────────────────┘
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Nenhuma variável específica do `QueueManager` em `.env`. A configuração é passada via:

**1. `config` dict**
```python
config = {
    "target": "bolsonaro",  # Processamento manual de um alvo
    # ... outras configs
}
```

**2. `TEST_TARGET_USERNAME`**
```bash
# Para debug — processa um único username quando configurado
TEST_TARGET_USERNAME=lula
```

### Tuning Recomendado

```python
# Em main_runner.py ou orchestrator
queue_manager.claim_next_target_atomic(
    worker_id="scraper-worker-1",
    max_prioridade=5,  # Permite até prioridade 5
    # Maiores = menos urgente
)

# Limpeza periódica de locks
if cycle % 10 == 0:
    queue_manager.release_stale_locks(timeout_minutes=30)

# Auto-repopulação (threshold padrão: 50 itens)
# Alterar em _ensure_queue_populated(min_pending=...)
```

---

## 🐛 Troubleshooting

### ❌ Problema: "Função SQL não encontrada"

**Erro:**
```
[Queue:atomic] Função SQL não encontrada. Execute 
migrations/add_queue_skip_locked.sql no Supabase.
```

**Solução:**
1. Acesse Supabase SQL Editor
2. Execute o arquivo de migração: `migrations/add_queue_skip_locked.sql`
3. Função será criada: `fila_coleta_claim_next`, `fila_coleta_release`, etc.

---

### ⚠️ Problema: Fila não está auto-repopulando

**Checklist:**
1. Candidatos na tabela com `status_monitoramento = 'Ativo'`?
2. `_ensure_queue_populated()` está sendo chamado? (É chamado em `claim_next_target()`)
3. Threshold de 50 itens pode ser muito alto? Alterar:
   ```python
   self._ensure_queue_populated(min_pending=10)  # Valores menores = mais agressivo
   ```

---

### 🔴 Problema: Workers não conseguem locks (retorna None sempre)

**Causas Possíveis:**
1. **Fila vazia completamente** → verificar `candidatos` com `status_monitoramento = 'Ativo'`
2. **Todos bloqueados** → verificar `active_targets` set (pode estar crescendo)
3. **Locks expirados** → chamar `release_stale_locks()` manualmente

**Debug:**
```python
# Check status da fila
fila_status = db.table("fila_coleta").select("status, COUNT(*)").execute()
# Check candidatos ativos
ativos = db.table("candidatos")\
    .select("username, termometro, last_scraped_at")\
    .filter("status_monitoramento", "eq", "Ativo")\
    .execute()
```

---

### 🧊 Problema: Todos os alvos viram FRIO (temperatura baixa)

**Causa:** Possível erro no cálculo de frequência.

**Verificação:**
```python
# Em rotate_target(), antes de atualizar
print(f"Valid dates: {valid_dates}")
print(f"Frequencia calculada: {frequencia}")
print(f"Days since last post: {days_since_last_post}")
```

**Reset Manual** (se necessário):
```python
db.table("candidatos").update({
    "termometro": "MORNO",
    "posts_frequencia_semanal": 0.0
}).filter("termometro", "eq", "FRIO").execute()
```

---

## 📈 Performance e Escalabilidade

### Complexidade

| Operação | Complexidade | Notas |
|----------|-------------|-------|
| `claim_next_target()` | O(1) com SELECT TOP 20 | Pequeno offset, não full-scan |
| `claim_next_target_atomic()` | O(1) via SQL function | SKIP LOCKED no banco |
| `release_atomic()` | O(1) via UPDATE | Direto no ID |
| `release_stale_locks()` | O(n) onde n=locked items | Raro, <1% dos casos |
| `rotate_target()` | O(1) | UPDATE direto |
| `_ensure_queue_populated()` | O(m) onde m=min_pending | ~50 UPSERTs, async-safe |

### Escalabilidade Horizontal

O `QueueManager` é **100% seguro para múltiplos workers**:
- ✅ Nenhum estado local (stateless)
- ✅ Todos os locks no banco (atomicidade SQL)
- ✅ SKIP LOCKED evita contentção
- ✅ Suporta centenas de workers simultaneamente

**Teste de Carga Recomendado:**
```python
# Simular 10 workers em paralelo
import threading
workers = [
    threading.Thread(
        target=worker_main,
        args=(queue_manager, f"worker-{i}")
    )
    for i in range(10)
]
for w in workers: w.start()
for w in workers: w.join()
```

---

## 🔗 Integração com Outros Módulos

### AIProcessorWorker
```python
from core.queue_manager import QueueManager

class AIProcessorWorker(BaseWorker):
    def __init__(self, db_client):
        self.queue_manager = QueueManager(db_client)
    
    def run_cycle(self):
        target = self.queue_manager.claim_next_target_atomic(
            worker_id=self.worker_id,
            seen_targets=self.seen_targets
        )
        # ... processar ...
        self.queue_manager.rotate_target(target)
```

### InstagramScraperWorker
```python
def main():
    queue_manager = QueueManager(db_client)
    
    for cycle in range(cycles_to_run):
        # Claim com config manual (debug)
        target = queue_manager.claim_next_target(
            config={"target": os.getenv("TEST_TARGET_USERNAME")},
            seen_queue_ids=seen_queue_ids,
            seen_targets=seen_targets,
            active_targets=active_targets
        )
        
        if target:
            scrape_and_extract(target)
            queue_manager.rotate_target(target)
```

---

## 📚 Referências

- **PASA Versão**: v88.0 (Fase 8.3)
- **Arquivo Principal**: `/workspace/core/queue_manager.py` (449 linhas)
- **Tabelas**: `fila_coleta`, `candidatos`
- **SQL Functions**: `fila_coleta_claim_next()`, `fila_coleta_release()`, `fila_coleta_release_stale()`
- **Relacionado**: `AIProcessorWorker`, `InstagramScraperWorker`, `Target` model

---

## ✅ Checklist de Implementação

- [ ] SQL functions criadas no Supabase (`fila_coleta_claim_next`, etc.)
- [ ] QueueManager instanciado com `db_client` válido
- [ ] Tabela `fila_coleta` com schema correto (status, prioridade, locked_by)
- [ ] Tabela `candidatos` com `termometro`, `last_scraped_at`, `status_monitoramento`
- [ ] Workers chamam `claim_next_target_atomic()` com `worker_id` único
- [ ] Sempre chamar `release_atomic()` mesmo em erro (try-finally)
- [ ] `rotate_target()` chamado após cada processamento
- [ ] `release_stale_locks()` agendado periodicamente (a cada ~10 ciclos)
- [ ] Logging verificado (ativar `DEBUG` para troubleshooting)

