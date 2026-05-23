# 📊 Workers Metrics Dashboard - Implementação v20.1

**Status:** ✅ Implementação Concluída  
**Data:** 6 de maio de 2026  
**Autor:** Sentinela v18.5 Architecture  

---

## 🎯 Visão Geral

O sistema de **Workers Metrics** fornece monitoramento em tempo real de latência, throughput e integridade de todos os processadores de dados (workers) da Sentinela Democrática.

**Componentes Implementados:**
1. `processing/workers_metrics.py` - Motor de coleta e agregação de métricas
2. Integração ao `BaseWorker` - Captura automática de desempenho
3. 4 endpoints de API - Exposição de dados para visualização
4. `WorkersMetricsDashboard.jsx` - Interface React com auto-refresh

---

## 🏗️ Arquitetura

### Fluxo de Dados

```
Worker (BaseWorker)
  ↓
  start_time = time.time()
  await process_item_batch()
  end_time = time.time()
  ↓
metrics_collector.record_execution()
  ↓
WorkerMetric (snapshot)
  ├─ duration_ms
  ├─ throughput
  ├─ avg_latency_per_item
  ├─ success flag
  ↓
WorkerMetricsCollector (histórico com retenção de 24h)
  ↓
/api/v1/workers/dashboard (GET)
  ↓
WorkersMetricsDashboard.jsx (auto-refresh 10s)
  ↓
Dashboard UI (tabelas, gráficos, alertas)
```

---

## 📈 Métricas Capturadas

### Por Execução (WorkerMetric)

- `duration_ms` - Tempo total (ms)
- `items_processed` - Quantidade de itens processados
- `throughput` - items/segundo
- `avg_latency_per_item` - ms/item
- `success` - Boolean
- `error_msg` - Mensagem de erro (se houver)
- `timestamp` - ISO 8601

### Agregadas (WorkerMetricsCollector)

- `total_executions` - Total de execuções
- `successful_executions` - Execuções bem-sucedidas
- `failed_executions` - Execuções falhadas
- `success_rate` - Percentual
- `avg_duration_ms` - Latência média
- `avg_throughput_items_per_sec` - Throughput médio
- `total_items_processed` - Total acumulado
- `recent_errors` - Últimas 5 falhas com timestamp

### Dashboard Summary

- `system_health` - 'green', 'yellow', ou 'red'
- `healthy_workers` - Contagem de workers saudáveis
- `degraded_workers` - Contagem de workers degradados
- `overall_success_rate` - Taxa geral de sucesso
- `avg_system_throughput_items_per_sec` - Throughput do sistema inteiro

---

## 🔌 Endpoints de API

### 1. GET `/api/v1/workers/dashboard`

Resumo consolidado para visualização no dashboard principal.

**Response:**
```json
{
  "timestamp": "2026-05-06T10:30:00Z",
  "total_workers": 3,
  "healthy_workers": 2,
  "degraded_workers": 1,
  "system_health": "yellow",
  "total_executions": 1542,
  "total_successful": 1489,
  "overall_success_rate": 96.6,
  "total_items_processed": 45821,
  "avg_system_throughput_items_per_sec": 12.5,
  "workers": [
    {
      "worker": "DataMiner",
      "status": "healthy",
      "total_executions": 542,
      "successful_executions": 530,
      "success_rate": 97.8,
      "avg_duration_ms": 2341.5,
      "avg_throughput_items_per_sec": 8.5,
      "total_items_processed": 15234,
      "last_execution": {
        "timestamp": "2026-05-06T10:29:45Z",
        "duration_ms": 2123.4,
        "items": 200,
        "success": true
      }
    }
  ]
}
```

### 2. GET `/api/v1/workers/stats`

Todos os workers com estatísticas detalhadas.

### 3. GET `/api/v1/workers/{worker_name}/stats`

Worker específico com histórico recente.

### 4. POST `/api/v1/workers/export-metrics`

Exportar métricas para arquivo JSON para análise offline.

---

## 💻 Uso no Código

### Como os Workers Capturam Automaticamente

O sistema funciona **automaticamente** para todos os workers que herdam de `BaseWorker`:

```python
from processing.common import BaseWorker

class MyCustomWorker(BaseWorker):
    async def fetch_pending_items(self, limit):
        # ...
        
    async def process_item_batch(self, items):
        # ...
        
    async def handle_failure(self, item, error):
        # ...

# Usar:
worker = MyCustomWorker(name="MyWorker", batch_size=100)
await worker.run()  # Métricas são capturadas automaticamente!
```

### Acessar Métricas Manualmente

```python
from processing.workers_metrics import metrics_collector

# Dentro do seu código
stats = await metrics_collector.get_worker_stats("DataMiner")
print(f"Success Rate: {stats['success_rate']}%")

# Dashboard summary
summary = await metrics_collector.get_dashboard_summary()
print(f"System Health: {summary['system_health']}")

# Exportar para análise
await metrics_collector.export_metrics_json("data/metrics_backup.json")
```

---

## 🎨 Componente React

### Integração no Dashboard Principal

```jsx
import WorkersMetricsDashboard from '@/components/WorkersMetricsDashboard';

export default function MainDashboard() {
  return (
    <div>
      {/* Seus outros componentes */}
      <WorkersMetricsDashboard />
    </div>
  );
}
```

### Features

- ✅ Auto-refresh a cada 10 segundos
- ✅ Toggle manual/automático
- ✅ Indicadores visuais de saúde (green/yellow/red)
- ✅ Tabela com estatísticas por worker
- ✅ Alertas de erros recentes
- ✅ Responsivo para mobile

---

## ⚙️ Configuração

### Retenção de Histórico

```python
# Default: 24 horas
metrics_collector = WorkerMetricsCollector(retention_hours=24)
```

### Batch Size e Intervalo de Polling

```python
# Cada worker tem seu próprio batch_size e poll_interval
worker = DataMiner(batch_size=200, poll_interval=60)
```

---

## 📊 Exemplo de Saída

```
📊 [DataMiner] 200 items in 2345ms (0.85 items/sec)
📊 [AdProcessor] 150 items in 1823ms (0.82 items/sec)
📊 [TextProcessor] 500 items in 3102ms (1.61 items/sec)
```

---

## 🔍 Interpretando os Dados

### Taxa de Sucesso Baixa (< 90%)

**Possíveis causas:**
- Problemas de conexão com Supabase
- Dados malformados
- Timeout em operações

**Ação:** Verificar logs e alertas recentes

### Latência Alta (> 5000ms)

**Possíveis causas:**
- Lotes muito grandes
- Recursos limitados
- Query de banco de dados lenta

**Ação:** Reduzir batch_size ou otimizar queries

### Throughput Baixo (< 1 item/sec)

**Possíveis causas:**
- Worker aguardando items pendentes
- Sistema subutilizado
- Intervalo de polling muito longo

**Ação:** Aumentar batch_size ou reduzir poll_interval

---

## 🚀 Próximos Passos

1. **Integração ao Dashboard** - Adicionar componente ao `index.html`
2. **Alertas Automáticos** - Notificar quando sistema_health ≠ 'green'
3. **Persistência** - Salvar métricas em banco para análise histórica
4. **Gráficos Temporais** - Visualizar tendências de performance
5. **SLA Tracking** - Monitorar conformidade com SLOs (Service Level Objectives)

---

## 📝 Notas Técnicas

- Métricas são thread-safe com `asyncio.Lock`
- Histórico é automaticamente limpo a cada execução
- Suporta múltiplas instâncias de workers com mesmo nome
- JSON export é UTF-8 com formatação legível

---

**Documento criado em:** 2026-05-06 (Implementação v20.1)
