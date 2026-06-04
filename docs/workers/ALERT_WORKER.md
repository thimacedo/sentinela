# AlertWorker - Documentação Completa

**Versão:** PASA v88.0  
**Arquivo Fonte:** `/workspace/workers/processors/alert_worker.py`  
**Status:** ✅ Em Produção  
**Última Atualização:** Junho 2026

---

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Responsabilidades Funcionais](#responsabilidades-funcionais)
3. [Arquitetura e Design](#arquitetura-e-design)
4. [Ciclo de Execução](#ciclo-de-execução)
5. [Detecção de Anomalias](#detecção-de-anomalias)
6. [Sistema de Notificações](#sistema-de-notificações)
7. [Canais de Entrega](#canais-de-entrega)
8. [Resolução de Alertas](#resolução-de-alertas)
9. [Configuração](#configuração)
10. [Integração com Banco de Dados](#integração-com-banco-de-dados)
11. [Monitoramento e Observabilidade](#monitoramento-e-observabilidade)
12. [Troubleshooting](#troubleshooting)
13. [Métricas e KPIs](#métricas-e-kpis)
14. [Escalabilidade](#escalabilidade)
15. [Integração com Outros Componentes](#integração-com-outros-componentes)
16. [Dependências Externas](#dependências-externas)

---

## 🎯 Visão Geral

O **AlertWorker** é um monitor de saúde sistêmica que **detecta anomalias** e **dispara notificações** para administradores via FCM (Firebase Cloud Messaging) e Webhooks.

### Responsabilidades Principais

- **Detectar Anomalias:** Via função RPC `detect_worker_anomalies()`
- **Criar Alertas:** Registrar na tabela `system_alerts`
- **Notificar Admins:** Via FCM (push notifications) e Webhooks (Slack/Discord)
- **Resolver Alertas:** Marcar como resolvidos quando problema se normaliza
- **Gerenciar Tokens FCM:** Limpar tokens inválidos automaticamente

### Necessidade de Negócio

A plataforma Sentinela executa múltiplos workers. Se algum falha, o admin precisa saber **rapidamente**. O AlertWorker garante:
- Alertas em tempo real sobre anomalias
- Notificações push no celular do admin
- Webhook para integração com Slack/Discord
- Histórico de alertas para análise posterior

---

## 🔄 Responsabilidades Funcionais

| Responsabilidade | Descrição |
|---|---|
| **Detecção de Anomalias** | Chama RPC `detect_worker_anomalies()` |
| **Criação de Alertas** | Insere em `system_alerts` com UPSERT |
| **Notificação FCM** | Envia push notifications via Firebase |
| **Notificação Webhook** | Envia para Slack/Discord |
| **Resolução de Alertas** | Marca alertas como resolvidos quando problema normaliza |
| **Cleanup de Tokens** | Remove push tokens inválidos |

---

## 🏗️ Arquitetura e Design

### Fluxo de Processamento

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SETUP                                                        │
│   • Inicializa Firebase Admin (se disponível)                 │
│   • Conecta ao Supabase                                        │
│   • Tenta carregar FIREBASE_SERVICE_ACCOUNT_KEY               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. DETECÇÃO DE ANOMALIAS (run_cycle)                            │
│   • Executa RPC 'detect_worker_anomalies'                      │
│   • Retorna lista de anomalias detectadas                      │
│   • Se vazio: retorna error="no_tasks_available"              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. UPSERT DE ALERTAS                                            │
│   • Para cada anomalia, insere/atualiza em system_alerts      │
│   • UNIQUE constraint: (worker_name, anomaly_type, resolved)  │
│   • Se alerta já existe: retorna ele (não cria duplicata)     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. DISPARO DE NOTIFICAÇÕES                                      │
│   • Para cada novo alerta (não_notified):                      │
│     - Se FCM ativo: envia push notification                    │
│     - Se webhook configurado: envia ao Slack/Discord           │
│   • Marca como notificado                                       │
│   • Coleta tokens inválidos do FCM                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RESOLUÇÃO DE ALERTAS ANTIGOS                                 │
│   • Busca alertas abertos (resolved=False)                     │
│   • Se anomalia não aparece na detecção atual: marca resolvido│
│   • Significa: o problema foi corrigido!                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. LIMPEZA DE TOKENS INVÁLIDOS                                  │
│   • Remove do profiles tokens que FCM reportou como inválidos │
│   • Evita tentativas repetidas para devices antigos/perdidos   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. RETORNO DE CYCLERESULT                                       │
│   • Inclui metadata com contagem de anomalias e alertas        │
└─────────────────────────────────────────────────────────────────┘
```

### Camadas de Processamento

1. **Camada de Detecção** → RPC SQL que identifica anomalias
2. **Camada de Persistência** → Armazena alertas no BD
3. **Camada de Notificação** → FCM + Webhooks
4. **Camada de Resolução** → Marca alertas como resolvidos
5. **Camada de Cleanup** → Remove tokens inválidos

---

## ⏱️ Ciclo de Execução

### Exemplo: Ciclo com Anomalia Detectada

```
[2026-06-04 14:30:00] INFO worker.alert: ✅ [AlertWorker] Inicializado. FCM=True
[2026-06-04 14:35:00] WARNING worker.alert: ⚠️ [AlertWorker] 1 anomalia(s) detectada(s).
[2026-06-04 14:35:01] WARNING worker.alert: 📣 Disparando alerta: 🚨 Sentinela — CRITICAL | [ai_processor] HIGH_ERROR_RATE: Taxa de erro > 10%
[2026-06-04 14:35:02] INFO worker.alert: FCM: 5 entregues, 0 falhas.
[2026-06-04 14:35:03] INFO worker.alert: Webhook enviado para hooks.slack.com
[2026-06-04 14:35:04] INFO worker.alert: Ciclo #1: extracted=1, inserted=1 ✅
```

### Exemplo: Ciclo com Anomalia Resolvida

```
[2026-06-04 14:40:00] INFO worker.alert: ✅ [AlertWorker] Sistema saudável. Nenhuma anomalia detectada.
[2026-06-04 14:40:01] INFO worker.alert: ✅ Alerta resolvido: [ai_processor] HIGH_ERROR_RATE
[2026-06-04 14:40:02] INFO worker.alert: Ciclo #2: extracted=0, inserted=0 (sem problemas)
```

### Sequência de Eventos Detalhada

1. **t0**: Captura `start_time`
2. **t1**: Incrementa `cycle`
3. **t2**: Verifica `shutdown_event`
4. **t3**: Executa RPC `detect_worker_anomalies()` → retorna lista
5. **t4**: Se vazio, retorna "no_tasks_available"
6. **t5**: Para cada anomalia:
   - **t5a**: Cria/recupera alerta via UPSERT
   - **t5b**: Se novo (não notificado), dispara notificações
   - **t5c**: Se FCM ativo, envia push notification multicast
   - **t5d**: Se webhook, envia POST com payload
   - **t5e**: Marca alerta como "notified"
   - **t5f**: Coleta tokens inválidos para cleanup
7. **t6**: Busca alertas abertos
8. **t7**: Para cada alerta aberto:
   - **t7a**: Se anomalia não está em anomalias_atuais, marca como resolvido
   - **t7b**: Log "Alerta resolvido"
9. **t8**: Cleanup: remove tokens inválidos do banco
10. **t9**: Retorna CycleResult com métricas

---

## 🔍 Detecção de Anomalias

### RPC: `detect_worker_anomalies()`

```python
res = self.db.rpc("detect_worker_anomalies").execute()
anomalies = res.data or []
```

**Responsabilidade:** Função SQL no Supabase que retorna anomalias do sistema.

**Retorno Esperado:**

```python
[
    {
        "worker_name": "ai_processor",
        "anomaly_type": "HIGH_ERROR_RATE",
        "severity": "critical",
        "current_value": 15,  # Taxa de erro: 15%
        "threshold": 10,
        "suggested_action": "Taxa de erro > 10%. Verificar logs do AIProcessor."
    },
    # ... outras anomalias
]
```

### Campos de Anomalia

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `worker_name` | str | Qual worker tem problema (ex: ai_processor) |
| `anomaly_type` | str | Tipo de anomalia (ex: HIGH_ERROR_RATE) |
| `severity` | str | critical, warning, info |
| `current_value` | any | Valor observado |
| `threshold` | any | Limite esperado |
| `suggested_action` | str | Sugestão de ação corretiva |

### Exemplos de Anomalias

- **HIGH_ERROR_RATE:** Taxa de erro do worker > 10%
- **SLOW_CYCLE:** Ciclo demorando > 2 minutos
- **NO_PROCESSING:** Worker não processa há > 1 hora
- **DB_TIMEOUT:** Query ao banco excedeu timeout
- **NEGATIVE_BALANCE:** Perfil com saldo CI negativo

---

## 📢 Sistema de Notificações

### Severidade e Emojis

```python
SEVERITY_EMOJI = {
    "critical": "🚨",
    "warning":  "⚠️",
    "info":     "ℹ️",
}
```

### Formato de Mensagem

```python
title = f"{emoji} Sentinela — {severity.upper()}"
body  = f"[{worker}] {anomaly}: {message}"

# Exemplo:
# title = "🚨 Sentinela — CRITICAL"
# body  = "[ai_processor] HIGH_ERROR_RATE: Taxa de erro > 10%. Verificar logs..."
```

---

## 📱 Canais de Entrega

### 1. Firebase Cloud Messaging (FCM)

#### Pré-requisitos

```bash
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
```

#### Inicialização

```python
def _init_firebase(self) -> None:
    if not _FIREBASE_AVAILABLE:
        self.fcm_enabled = False
        return
    
    if not firebase_admin._apps:
        sa_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
        if not sa_key:
            self.fcm_enabled = False
            return
        service_account = json.loads(sa_key)
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred)
    
    self.fcm_enabled = True
```

#### Envio de Notificação

```python
async def _send_fcm(self, title: str, body: str, alert: dict) -> None:
    # Busca tokens dos usuários
    tokens_res = self.db.table("profiles") \
        .select("push_token") \
        .not_.is_("push_token", "null") \
        .execute()
    
    tokens = [row["push_token"] for row in (tokens_res.data or [])]
    
    if not tokens:
        return
    
    # Envia multicast
    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={
            "alert_id": str(alert.get("id")),
            "anomaly_type": alert.get("anomaly_type"),
            "severity": alert.get("severity"),
            "worker_name": alert.get("worker_name"),
        }
    )
    
    response = messaging.send_each_for_multicast(message)
    # Cleanup de tokens inválidos
```

#### Tokens Inválidos

Se o FCM reporta token inválido:

```python
invalid = [tokens[i] for i, resp in enumerate(responses) if not resp.success]
# Limpar do banco
self.db.table("profiles").update({"push_token": None}).in_("push_token", invalid).execute()
```

### 2. Webhooks (Slack/Discord)

#### Variável de Ambiente

```bash
export ALERT_WEBHOOK_URL='https://hooks.slack.com/services/...'
```

#### Payload Compatível (Slack + Discord)

```python
slack_payload = {
    "attachments": [{
        "color": "#ef4444",  # critical
        "title": "🚨 Sentinela — CRITICAL",
        "text": "[ai_processor] HIGH_ERROR_RATE: Taxa de erro > 10%",
        "footer": "Sentinela PASA v17 | 14:35 UTC"
    }]
}
```

#### Cores por Severidade

| Severidade | Cor | Código |
|-----------|-----|--------|
| critical | Vermelho | #ef4444 |
| warning | Âmbar | #f59e0b |
| info | Azul | #3b82f6 |

---

## ✅ Resolução de Alertas

### Lógica de Resolução

```python
def _resolve_stale_alerts(self, current_anomalies: list[dict]) -> None:
    # Cria set de anomalias ATIVAS
    active_keys = {
        (a["worker_name"], a["anomaly_type"])
        for a in current_anomalies
    }
    
    # Busca alertas ABERTOS no banco
    open_alerts = self.db.table("system_alerts") \
        .select("id, worker_name, anomaly_type") \
        .eq("resolved", False) \
        .execute().data or []
    
    # Se alerta aberto NÃO está em ativas → RESOLVIDO!
    for alert in open_alerts:
        key = (alert["worker_name"], alert["anomaly_type"])
        if key not in active_keys:
            # Marca como resolvido
            self.db.table("system_alerts").update({
                "resolved": True,
                "resolved_at": datetime.now(UTC).isoformat()
            }).eq("id", alert["id"]).execute()
```

### Estados de Alerta

| Estado | Significado | Quando Ocorre |
|--------|-----------|-------------|
| **Aberto** | Problema ativo | Detectado em `detect_worker_anomalies()` |
| **Notificado** | Admin foi informado | Após envio FCM/Webhook |
| **Resolvido** | Problema corrigido | Anomalia não aparece em ciclos seguintes |

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Tipo | Obrigatória? | Descrição |
|----------|------|-------------|-----------|
| `FIREBASE_SERVICE_ACCOUNT_KEY` | JSON string | ❌ Opcional | Credenciais Firebase para FCM |
| `ALERT_WEBHOOK_URL` | str | ❌ Opcional | URL para Slack/Discord |

**Exemplos:**

```bash
# Firebase (env)
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"sentinela-prod",...}'

# Webhook (env)
export ALERT_WEBHOOK_URL='https://hooks.slack.com/services/T123/B456/XYZ'
```

### Parâmetros de Configuração (Config Dict)

```python
config = {}  # AlertWorker não requer parâmetros customizados
```

### Exemplo de Inicialização

```python
from workers.processors.alert_worker import AlertWorker

worker = AlertWorker(
    worker_id="alert_worker_1",
    config={}
)

await worker.setup()
for _ in range(100):
    result = await worker.run_cycle()
    print(f"Ciclo: {result.cycle}, Alertas: {result.metadata['anomalies']}")
await worker.teardown()
```

---

## 🗄️ Integração com Banco de Dados

### Tabelas Utilizadas

#### 1. `system_alerts` (Read/Write)
- **Propósito:** Armazenar histórico de alertas
- **Operações:** UPSERT (criar/atualizar), UPDATE (marcar resolvido)
- **Frequência:** A cada ciclo

#### 2. `profiles` (Read/Write)
- **Propósito:** Buscar push_tokens para FCM
- **Operações:** SELECT (buscar tokens), UPDATE (limpar inválidos)
- **Frequência:** A cada alerta novo, e uma vez por limpeza

### Schema Esperado

```sql
CREATE TABLE system_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_name VARCHAR,
    anomaly_type VARCHAR,
    severity VARCHAR,  -- critical, warning, info
    current_value VARCHAR,
    threshold VARCHAR,
    message TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    notified BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    UNIQUE(worker_name, anomaly_type, resolved)
);

CREATE TABLE profiles (
    id UUID PRIMARY KEY,
    push_token VARCHAR,  -- Firebase token para push notifications
    -- ... outros campos
);
```

### UPSERT Strategy

```python
res = self.db.table("system_alerts").upsert({
    "worker_name":   anomaly["worker_name"],
    "anomaly_type":  anomaly["anomaly_type"],
    "severity":      anomaly["severity"],
    "current_value": anomaly["current_value"],
    "threshold":     anomaly["threshold"],
    "message":       anomaly["suggested_action"],
    "resolved":      False,
}, on_conflict="worker_name,anomaly_type,resolved").execute()
```

---

## 📊 Monitoramento e Observabilidade

### Logs Emitidos

```
✅ Firebase Admin inicializado.
   └─ Emitido em: _init_firebase()
   └─ Nível: INFO
   └─ Quando: Firebase ativado com sucesso

Falha ao inicializar Firebase: {erro}
   └─ Emitido em: _init_firebase()
   └─ Nível: ERROR
   └─ Quando: Erro ao carregar credenciais

✅ [AlertWorker] Inicializado. FCM={True/False}
   └─ Emitido em: setup()
   └─ Nível: INFO

✅ [AlertWorker] Sistema saudável. Nenhuma anomalia detectada.
   └─ Emitido em: run_cycle() [vazio]
   └─ Nível: INFO

⚠️ [AlertWorker] N anomalia(s) detectada(s).
   └─ Emitido em: run_cycle() [anomalias]
   └─ Nível: WARNING

📣 Disparando alerta: {title} | {body}
   └─ Emitido em: _notify()
   └─ Nível: WARNING

FCM: X entregues, Y falhas.
   └─ Emitido em: _send_fcm()
   └─ Nível: INFO

Webhook enviado para {domain}
   └─ Emitido em: _send_webhook()
   └─ Nível: INFO

✅ Alerta resolvido: [{worker}] {anomaly}
   └─ Emitido em: _resolve_stale_alerts()
   └─ Nível: INFO

🧹 N tokens inválidos removidos.
   └─ Emitido em: _cleanup_invalid_tokens()
   └─ Nível: INFO

🛑 [AlertWorker] Encerrado.
   └─ Emitido em: teardown()
   └─ Nível: INFO
```

### Métricas Retornadas (CycleResult)

```python
CycleResult(
    worker_id=self.worker_id,
    cycle=self.cycle,
    source="alert",
    extracted=len(anomalies),     # Anomalias detectadas
    inserted=len(fired),          # Alertas novos disparados
    db_success=True,              # Sempre True se sem exceção
    simulated=False,
    duration=elapsed_seconds,
    metadata={
        "anomalies": len(anomalies),  # Total de anomalias
        "fired": len(fired)           # Alertas disparados
    }
)
```

---

## 🔧 Troubleshooting

### Problema 1: FCM Desativado (firebase_admin não instalado)

**Sintoma:**
```
WARNING: firebase_admin não instalado. Notificações FCM desabilitadas.
```

**Solução:**
1. Instalar:
   ```bash
   pip install firebase-admin
   ```

2. Se não deseja FCM, ignorar (webhooks funcionam)

---

### Problema 2: Firebase Não Inicializa

**Sintoma:**
```
ERROR: Falha ao inicializar Firebase: {erro}
```

**Causas Possíveis:**
- FIREBASE_SERVICE_ACCOUNT_KEY não está definida
- JSON malformado
- Firebase project não existe

**Solução:**
1. Verificar variável:
   ```bash
   echo $FIREBASE_SERVICE_ACCOUNT_KEY | jq .
   ```

2. Se vazia, definir:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_KEY=$(cat /path/to/serviceAccount.json)
   ```

3. Se JSON inválido, validar:
   ```bash
   echo $FIREBASE_SERVICE_ACCOUNT_KEY | jq . > /dev/null
   ```

---

### Problema 3: Nenhum Alerta Disparado

**Sintoma:**
```
✅ Sistema saudável. Nenhuma anomalia detectada.
fired=0
```

**Causas Possíveis:**
- RPC `detect_worker_anomalies()` retorna vazio (sistema saudável)
- Ou RPC não existe/falha

**Solução:**
1. Verificar RPC:
   ```sql
   SELECT routine_name FROM information_schema.routines 
   WHERE routine_name = 'detect_worker_anomalies';
   ```

2. Se não existe, criar a função RPC no Supabase

3. Se existe, testar manualmente:
   ```python
   res = db.rpc("detect_worker_anomalies").execute()
   print(res.data)
   ```

---

### Problema 4: Webhook Falha

**Sintoma:**
```
ERROR: Erro ao enviar webhook: ...
```

**Causas Possíveis:**
- URL inválida
- Servidor Slack/Discord down
- Timeout

**Solução:**
1. Verificar URL:
   ```bash
   curl -X POST "$ALERT_WEBHOOK_URL" -H 'Content-Type: application/json' \
     -d '{"text": "teste"}'
   ```

2. Se não funcionar, gerar nova URL no Slack/Discord

3. Se timeout, aumentar timeout em `httpx.AsyncClient(timeout=10)`

---

### Problema 5: Tokens FCM Acumulando

**Sintoma:**
Tabela `profiles` cresce indefinidamente com push_tokens antigos.

**Solução:**
O worker já limpa tokens inválidos automaticamente. Se ainda acumular:

1. Limpar manualmente:
   ```sql
   UPDATE profiles SET push_token = NULL 
   WHERE push_token IS NOT NULL 
   AND updated_at < now() - interval '90 days';
   ```

---

## 📈 Métricas e KPIs

### Métricas de Alerta

| Métrica | Definição | Target |
|---------|-----------|--------|
| Taxa de Detecção | `(extracted > 0) ? 1 : 0` | > 90% de ciclos |
| Latência de Notificação | Tempo até FCM/Webhook | < 5s |
| Taxa de Resolução | Alertas resolvidos / abertos | > 80% |
| Tempo de Resposta | Ciclo completo | < 10s |

### Alertas Recomendados

- 🔴 **Ciclo > 30s:** Gargalo de notificação
- 🟠 **Taxa de Detecção < 70%:** Problema com RPC ou dados
- 🟡 **Alertas não resolvem:** Problema pode estar ativo

---

## 🚀 Escalabilidade

### Limitações Atuais

- Busca todos os tokens de push (pode ser lento com muitos usuários)
- RPC é bloqueante (não paralelo)

### Otimizações Futuras

```python
# Paralelizar múltiplos RPC
anomalies_1, anomalies_2 = await asyncio.gather(
    db.rpc("detect_worker_anomalies").execute(),
    db.rpc("detect_db_anomalies").execute()
)

# Cache de resultados
self.anomaly_cache = {}
self.cache_ttl = 60  # 1 minuto

# Batch notifications
# Ao invés de enviar 1 alerta por vez, agrupar e enviar em batch
```

---

## 🔗 Integração com Outros Componentes

### Workers (AIProcessor, etc)
- **Relação:** Monitora
- **Dependência:** Dados de detecção_worker_anomalies()
- **Impacto:** AlertWorker reage a problemas em outros workers

### Firebase
- **Relação:** Canal de notificação
- **Dependência:** Credenciais FIREBASE_SERVICE_ACCOUNT_KEY
- **Impacto:** Sem Firebase, FCM não funciona

### Slack/Discord
- **Relação:** Canal de notificação
- **Dependência:** ALERT_WEBHOOK_URL
- **Impacto:** Sem webhook, notificações de terceiros falham

### Supabase
- **Relação:** Crítica
- **Dependência:** Leitura de RPC, escrita de alertas
- **Impacto:** Se BD cai, AlertWorker não funciona

---

## 📦 Dependências Externas

### Bibliotecas Python

| Biblioteca | Propósito |
|-----------|----------|
| `firebase_admin` | Envio de FCM |
| `httpx` | Envio de webhooks |
| `asyncio` | Concorrência |
| `logging` | Logs |

### Serviços Externos

| Serviço | Criticidade |
|---------|-------------|
| **Supabase/PostgreSQL** | CRÍTICA |
| **Firebase** | IMPORTANTE (se FCM habilitado) |
| **Slack/Discord** | IMPORTANTE (se webhook habilitado) |

---

## 📝 Changelog

### v88.0 (Junho 2026)
- ✅ Migrado para BaseWorker moderno
- ✅ FCM + Webhook compatível
- ✅ Resolução automática de alertas
- ✅ Cleanup de tokens inválidos
- ✅ Suporte a múltiplas severidades

---

**Documento Gerado:** Junho 2026  
**Status:** ✅ Completo
