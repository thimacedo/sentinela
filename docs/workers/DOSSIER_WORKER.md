# DossierWorker - Documentação Completa

**Versão:** PASA v88.0  
**Arquivo Fonte:** `/workspace/workers/processors/dossier_worker.py`  
**Status:** ✅ Em Produção  
**Última Atualização:** Junho 2026

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Responsabilidades Funcionais](#responsabilidades-funcionais)
3. [Arquitetura e Design](#arquitetura-e-design)
4. [Ciclo de Execução](#ciclo-de-execução)
5. [Detecção de Schema](#detecção-de-schema)
6. [Geração de PDF](#geração-de-pdf)
7. [Gerenciamento de Estado](#gerenciamento-de-estado)
8. [Configuração](#configuração)
9. [Integração com Banco de Dados](#integração-com-banco-de-dados)
10. [Monitoramento e Observabilidade](#monitoramento-e-observabilidade)
11. [Troubleshooting](#troubleshooting)
12. [Métricas e KPIs](#métricas-e-kpis)
13. [Escalabilidade](#escalabilidade)
14. [Integração com Outros Componentes](#integração-com-outros-componentes)
15. [Dependências Externas](#dependências-externas)

---

## 🎯 Visão Geral

O **DossierWorker** é um sub-agente especializado em **geração automatizada de dossiês em PDF** a partir de dados estruturados.

### Responsabilidades Principais

- **Monitorar Fila de Dossiês:** Buscar registros com status "Pendente"
- **Gerar PDFs:** Converter dados de dossiê em relatório visual
- **Atualizar Status:** Marcar como "Concluído" ou "Falhou"
- **Registrar Erros:** Armazenar mensagens de falha para troubleshooting
- **Detectar Schema:** Auto-adaptar a diferentes estruturas de banco

### Necessidade de Negócio

Dossiês em PDF são entregas principais para clientes. O DossierWorker automatiza essa geração, evitando:
- Processamento manual de cada dossiê
- Erros de formatação ou dados incompletos
- Atrasos na entrega

---

## 🔄 Responsabilidades Funcionais

| Responsabilidade | Descrição |
|---|---|
| **Monitoramento de Fila** | Busca dossiês com status="Pendente" |
| **Detecção de Schema** | Identifica nomes de colunas (status, arquivo_path, error_log) |
| **Geração de PDF** | Converte dossiê via ReportGenerator |
| **Atualização de Status** | Marca como "Concluído" ou "Falhou" |
| **Registro de Erro** | Armazena mensagens de erro para debug |
| **Gestão de Shutdown** | Permite parada graceful durante processamento |

---

## 🏗️ Arquitetura e Design

### Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SETUP                                                        │
│   • Conecta ao Supabase via get_supabase_client()             │
│   • Inicializa ReportGenerator                                 │
│   • Cria diretório de reports (se não existir)                │
│   • Detecta schema da tabela 'dossies'                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. BUSCA DE DOSSIÊS PENDENTES (run_cycle)                       │
│   • Query: dossies com status="Pendente"                       │
│   • Fallback: dossies com arquivo_path IS NULL                │
│   • Limite: 25 dossiês por ciclo                               │
│   • Se vazio: retorna error="no_tasks_available"              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PROCESSAMENTO DE CADA DOSSIÊ                                 │
│   • Para cada dossiê:                                           │
│     - Marca como "Processando"                                 │
│     - Gera PDF via ReportGenerator                             │
│     - Se sucesso: atualiza para "Concluído"                   │
│     - Se erro: atualiza para "Falhou" + error_log             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. CLEANUP E FINALIZAÇÃO                                        │
│   • Conta sucessos e falhas                                    │
│   • Retorna CycleResult com métricas                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. TEARDOWN                                                     │
│   • Libera Supabase e ReportGenerator                         │
└─────────────────────────────────────────────────────────────────┘
```

### Camadas de Processamento

1. **Camada de Fila** → Busca dossiês pendentes no Supabase
2. **Camada de Adaptação** → Detecta schema automaticamente
3. **Camada de Geração** → ReportGenerator cria PDF
4. **Camada de Persistência** → Atualiza status e arquivo_path
5. **Camada de Erro** → Registra mensagens de falha

---

## ⏱️ Ciclo de Execução

### Exemplo: Ciclo Bem-Sucedido

```
[2026-06-04 14:00:00] INFO worker.dossier: 🚀 [DossierWorker] Pronto. DossierWorker — Geração de PDFs de Dossiês (dir=reports)
[2026-06-04 14:01:00] INFO worker.dossier: 📋 [DossierWorker] Ciclo #1 — buscando dossiês pendentes.
[2026-06-04 14:01:01] INFO worker.dossier: 📄 [DossierWorker] 3 dossiê(s) encontrado(s).
[2026-06-04 14:01:02] INFO worker.dossier: → [DossierWorker] Processando dossiê ID=abc123 (candidato=usuario_1)
[2026-06-04 14:01:05] INFO worker.dossier: ✅ [DossierWorker] PDF gerado: reports/usuario_1_20260604_140105.pdf
[2026-06-04 14:01:06] INFO worker.dossier: → [DossierWorker] Processando dossiê ID=def456 (candidato=usuario_2)
[2026-06-04 14:01:10] INFO worker.dossier: ✅ [DossierWorker] PDF gerado: reports/usuario_2_20260604_140110.pdf
[2026-06-04 14:01:11] INFO worker.dossier: → [DossierWorker] Processando dossiê ID=ghi789 (candidato=usuario_3)
[2026-06-04 14:01:12] ERROR worker.dossier: ❌ [DossierWorker] Erro no dossiê ID=ghi789: Dados incompletos
[2026-06-04 14:01:13] INFO worker.dossier: 📊 [DossierWorker] Ciclo #1 | Encontrados=3 | Gerados=2 | Falhas=1
```

### Sequência de Eventos

1. **t0**: Captura `start_time`
2. **t1**: Incrementa `cycle`
3. **t2**: Verifica `shutdown_event` (se set, para)
4. **t3**: Valida disponibilidade de Supabase e ReportGenerator
5. **t4**: Chama `_fetch_pending()` para buscar dossiês
6. **t5**: Para cada dossiê:
   - **t5a**: Cria payload de "Processando"
   - **t5b**: Executa ReportGenerator.generate_pdf() via executor
   - **t5c**: Se sucesso, atualiza para "Concluído" + arquivo_path
   - **t5d**: Se erro, atualiza para "Falhou" + error_log
7. **t6**: Contabiliza sucessos e falhas
8. **t7**: Retorna CycleResult com métricas

---

## 🔍 Detecção de Schema

O DossierWorker é **agnóstico de schema** — detecta automaticamente nomes de colunas:

```python
async def _detect_dossies_columns(self) -> None:
    """
    Detecta nomes de colunas na tabela 'dossies'.
    Suporta variações: status/situacao/estado, arquivo_path/report_path, error_log/erro
    """
```

### Colunas Detectadas

| Campo | Variações | Propósito |
|-------|-----------|----------|
| **Status** | status, situacao, estado | Rastreamento do estado do dossiê |
| **Path** | arquivo_path, report_path | Localização do PDF gerado |
| **Error** | error_log, erro | Mensagem de erro (opcional) |

### Exemplo: Detecção em Ação

```
[DossierWorker] Schema detectado: status=status | path=arquivo_path | error=error_log
```

### Fallback Automático

Se a coluna de status não existir:

```python
# Tenta fallback: buscar por arquivo_path nulo
if self._status_column is None:
    res = self._supabase.table("dossies").select("*").is_(self._path_column, "null").limit(25).execute()
```

---

## 📄 Geração de PDF

### ReportGenerator

```python
from processing.report_generator import ReportGenerator

self._report_gen = ReportGenerator()
# ...
gen_path = await loop.run_in_executor(None, self._report_gen.generate_pdf, [dossier], out_path, str(candidato_id))
```

**Assinatura:**
```python
ReportGenerator.generate_pdf(
    dossiers: list[dict],        # Lista com 1 dossiê
    output_path: str,            # Onde salvar o PDF
    candidato_id: str            # ID para nome do arquivo
) -> str                         # Path do arquivo gerado
```

### Nomes de Arquivo

Os PDFs são salvos com timestamp para evitar conflitos:

```python
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_name = "".join(c for c in str(candidato_id) if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
pdf_name = f"{safe_name}_{ts}.pdf"
# Exemplo: usuario_1_20260604_140105.pdf
```

### Diretório de Reports

```python
# Config padrão
self.report_dir = config.get("report_dir", "reports")

# Criação
os.makedirs(self.report_dir, exist_ok=True)
```

---

## 🔄 Gerenciamento de Estado

### Estados do Dossiê

| Estado | Significado | Quando Atribui |
|--------|-------------|----------------|
| **Pendente** | Aguardando processamento | Criação inicial |
| **Processando** | Em geração de PDF | Início do processamento |
| **Concluído** | PDF gerado com sucesso | Após sucesso |
| **Falhou** | Erro durante geração | Após exceção |

### Transições de Estado

```
Pendente
   ↓ (DossierWorker pega)
Processando
   ↓ (ReportGenerator executa)
   ├─ Sucesso → Concluído (arquivo_path preenchido)
   └─ Erro → Falhou (error_log preenchido)
```

### Payload de Update

```python
def _build_update_payload(self, status_value=None, report_path=None, error_text=None) -> dict:
    payload = {}
    if status_value and self._status_column:
        payload[self._status_column] = status_value
    if report_path:
        payload[self._path_column] = report_path
    if error_text and self._error_column:
        payload[self._error_column] = error_text[:500]  # Limita a 500 chars
    return payload
```

---

## ⚙️ Configuração

### Parâmetros de Configuração (Config Dict)

```python
config = {
    "report_dir": "reports"  # Diretório para salvar PDFs
}
```

**Padrão:** `"reports"` (relativo ao workspace)

### Variáveis de Ambiente

Nenhuma variável de ambiente obrigatória. Usa Supabase conectado via `db_client`.

### Exemplo de Inicialização

```python
from workers.processors.dossier_worker import DossierWorker

config = {"report_dir": "/path/to/reports"}

worker = DossierWorker(
    worker_id="dossier_1",
    config=config
)

await worker.setup()
for _ in range(100):
    result = await worker.run_cycle()
    print(f"Ciclo: {result.cycle}, Gerados: {result.inserted}, Falhas: {result.failed}")
await worker.teardown()
```

---

## 🗄️ Integração com Banco de Dados

### Tabelas Utilizadas

#### 1. `dossies` (Read/Write)
- **Propósito:** Armazenar metadados de dossiês
- **Operações:** SELECT (buscar pendentes), UPDATE (atualizar status)
- **Frequência:** A cada ciclo

### Schema Esperado

```sql
CREATE TABLE dossies (
    id UUID PRIMARY KEY,
    candidato_id VARCHAR,
    status VARCHAR DEFAULT 'Pendente',         -- ou 'situacao' / 'estado'
    arquivo_path VARCHAR,                       -- ou 'report_path'
    error_log TEXT,                             -- ou 'erro' (opcional)
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### Queries

```python
# BUSCA: Dossiês pendentes
res = self._supabase.table("dossies")\
    .select("*")\
    .eq(self._status_column, "Pendente")\
    .execute()

# UPDATE: Marca como processando
self._supabase.table("dossies")\
    .update({"status": "Processando"})\
    .eq("id", d_id)\
    .execute()

# UPDATE: Marca como concluído
self._supabase.table("dossies")\
    .update({"status": "Concluído", "arquivo_path": "/path/to/pdf"})\
    .eq("id", d_id)\
    .execute()
```

---

## 📊 Monitoramento e Observabilidade

### Logs Emitidos

```
✅ [DossierWorker] Conexão Supabase estabelecida.
   └─ Emitido em: setup()
   └─ Nível: INFO

❌ [DossierWorker] Falha ao conectar Supabase: {erro}
   └─ Emitido em: setup()
   └─ Nível: ERROR

✅ [DossierWorker] ReportGenerator inicializado.
   └─ Emitido em: setup()
   └─ Nível: INFO

❌ [DossierWorker] ReportGenerator não encontrado: {erro}
   └─ Emitido em: setup()
   └─ Nível: ERROR

📋 [DossierWorker] Ciclo #N — buscando dossiês pendentes.
   └─ Emitido em: run_cycle()
   └─ Nível: INFO

✅ [DossierWorker] Nenhum dossiê pendente.
   └─ Emitido em: run_cycle() [vazio]
   └─ Nível: INFO

📄 [DossierWorker] N dossiê(s) encontrado(s).
   └─ Emitido em: run_cycle() [sucesso]
   └─ Nível: INFO

→ [DossierWorker] Processando dossiê ID={id} (candidato={candidato_id})
   └─ Emitido em: _process_dossier()
   └─ Nível: INFO

✅ [DossierWorker] PDF gerado: {path}
   └─ Emitido em: _process_dossier()
   └─ Nível: INFO

❌ [DossierWorker] Erro no dossiê ID={id}: {erro}
   └─ Emitido em: _process_dossier()
   └─ Nível: ERROR

🛑 [DossierWorker] Encerrado.
   └─ Emitido em: teardown()
   └─ Nível: INFO
```

### Métricas Retornadas (CycleResult)

```python
CycleResult(
    worker_id=self.worker_id,
    cycle=self.cycle,
    source="dossier",
    extracted=len(pending),     # Total encontrado
    inserted=success,           # Total gerado com sucesso
    failed=failed,              # Total com erro
    db_success=True,            # Sempre True (se sem exceção)
    simulated=False,
    duration=elapsed_seconds,
    metadata={"success": success, "failed": failed}
)
```

---

## 🔧 Troubleshooting

### Problema 1: "Conexão Supabase Falhou"

**Sintoma:**
```
ERROR: Falha ao conectar Supabase: ...
```

**Causas Possíveis:**
- Credenciais Supabase incorretas
- Rede indisponível
- Supabase API down

**Solução:**
1. Verificar variáveis de ambiente:
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   ```

2. Testar conexão manual:
   ```python
   from core.supabase_service import get_supabase_client
   db = get_supabase_client()
   db.table("dossies").select("count", count="exact").execute()
   ```

---

### Problema 2: "ReportGenerator Não Encontrado"

**Sintoma:**
```
ERROR: ReportGenerator não encontrado: ImportError ...
```

**Causa Provável:**
Módulo `processing.report_generator` não existe ou falha ao importar.

**Solução:**
1. Verificar se arquivo existe:
   ```bash
   ls /workspace/processing/report_generator.py
   ```

2. Validar importação:
   ```python
   from processing.report_generator import ReportGenerator
   ```

3. Se faltar, criar stub mínimo ou verificar documentação do ReportGenerator

---

### Problema 3: "Schema Não Detectado"

**Sintoma:**
```
WARNING: [DossierWorker] Coluna de status inexistente em dossies.
```

**Causa Provável:**
Tabela `dossies` não tem coluna `status` (ou variações).

**Solução:**
1. Verificar schema:
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'dossies';
   ```

2. Se falta `status`, criar:
   ```sql
   ALTER TABLE dossies ADD COLUMN status VARCHAR DEFAULT 'Pendente';
   ```

3. Se usa nome diferente (ex: `situacao`), o worker vai detectar automaticamente

---

### Problema 4: PDF Gerado Mas Arquivo Não Encontrado

**Sintoma:**
```
ERROR: ReportGenerator não retornou caminho válido.
```

**Causas Possíveis:**
- Diretório `report_dir` não existe ou sem permissão
- ReportGenerator falhou silenciosamente
- Path inválido retornado

**Solução:**
1. Verificar permissões:
   ```bash
   ls -la /workspace/reports
   ```

2. Criar diretório se não existir:
   ```bash
   mkdir -p /workspace/reports
   chmod 755 /workspace/reports
   ```

3. Adicionar logs no ReportGenerator para debug

---

## 📈 Métricas e KPIs

### Métricas de Processamento

| Métrica | Definição | Target |
|---------|-----------|--------|
| Taxa de Sucesso | `inserted / (inserted + failed)` | > 95% |
| Dossiês por Ciclo | `extracted` | 1-25 |
| Tempo por PDF | `duration / inserted` | < 5s |
| Taxa de Erro | `failed / extracted` | < 5% |

### Alertas Recomendados

- 🔴 **Taxa de Sucesso < 80%:** Problema com ReportGenerator
- 🟠 **Duração > 2 minutos:** Gargalo de processamento
- 🟡 **Nenhum dossiê por 10 ciclos:** Verificar fila ou status

---

## 🚀 Escalabilidade

### Limitações Atuais

| Limitação | Valor | Impacto |
|-----------|-------|--------|
| Dossiês por ciclo | 25 | Processamento gerenciável |
| Tamanho máximo de PDF | ~50 MB (típico) | Não é gargalo |

### Estratégias de Escala

#### 1. Paralelizar Geração de PDFs
```python
# Em vez de processar sequencialmente
tasks = [self._process_dossier(d) for d in pending]
results = await asyncio.gather(*tasks)
```

#### 2. Usar Fila de Mensagens (Redis/RabbitMQ)
```python
# Publicar eventos para multiple workers
for dossier in pending:
    queue.publish("dossier_generation", dossier)
```

#### 3. Limpar PDFs Antigos
```python
# Arquivar PDFs > 90 dias
import shutil
for f in os.listdir(report_dir):
    if os.path.getmtime(f) < (time.time() - 90*86400):
        shutil.move(f, archive_dir)
```

---

## 🔗 Integração com Outros Componentes

### ReportGenerator
- **Relação:** Crítica
- **Dependência:** Gera PDFs
- **Impacto:** Se falhar, nenhum dossiê é gerado

### Supabase
- **Relação:** Crítica
- **Dependência:** Fonte de dados e persistência de status
- **Impacto:** Se desconectar, worker não funciona

### Frontend
- **Relação:** Consumidor
- **Observação:** Frontend exibe links para PDFs gerados

---

## 📦 Dependências Externas

### Bibliotecas Python

| Biblioteca | Propósito |
|-----------|----------|
| `asyncio` | Concorrência |
| `logging` | Logs |
| `pathlib` | Manipulação de paths |
| `processing.report_generator` | Geração de PDFs |

---

## 📝 Changelog

### v88.0 (Junho 2026)
- ✅ Refatoração para BaseWorker moderno
- ✅ Detecção automática de schema
- ✅ Suporte a shutdown graceful
- ✅ Tratamento robusto de erros

---

**Documento Gerado:** Junho 2026  
**Status:** ✅ Completo
