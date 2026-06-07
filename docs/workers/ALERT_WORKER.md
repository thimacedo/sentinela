# WkGeraAlertas — Monitoramento e Alertas
_version: 90.8 | last_updated: 2026-06-07 | status: Ativo em Produção_

## 1. Visão Geral

**WkGeraAlertas** é o worker de monitoramento e alertas do ecossistema Sentinela. Ele **detecta anomalias** via RPC `detect_worker_anomalies()` e **dispara notificações** para administradores via FCM (Firebase Cloud Messaging) e Webhooks (Slack/Discord).

### Informações Básicas
- **ID do Worker**: Dinâmico (e.g., `alert-worker-01`)
- **Localização**: `workers/processors/wk_gera_alertas.py`
- **Classe**: `WkGeraAlertas` (herda de `BaseWorker`)
- **Status**: 🟢 Ativo em produção
- **Frequência**: Ciclo a cada ~5 minutos via bandeja do watchdog ou main_runner

---

## 2. Responsabilidades

| Responsabilidade | Descrição |
|---|---|
| **Detecção de Anomalias** | Chama RPC `detect_worker_anomalies()` no Supabase |
| **Criação de Alertas** | Insere/atualiza em `system_alerts` com UPSERT |
| **Notificação FCM** | Envia push notifications via Firebase |
| **Notificação Webhook** | Envia para Slack/Discord |
| **Resolução de Alertas** | Marca como resolvidos quando problema normaliza |
| **Cleanup de Tokens** | Remove tokens FCM inválidos automaticamente |

---

## 3. Estados de Alerta

| Estado | Significado | Quando Ocorre |
|--------|-----------|---------------|
| **Aberto** | Problema ativo | Detectado em `detect_worker_anomalies()` |
| **Notificado** | Admin informado | Após envio FCM/Webhook |
| **Resolvido** | Problema corrigido | Anomalia não aparece em ciclos seguintes |

---

## 4. Canais de Entrega

### Firebase Cloud Messaging (FCM)
```bash
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
```

### Webhooks (Slack/Discord)
```bash
export ALERT_WEBHOOK_URL='https://hooks.slack.com/services/...'
```

### Severidade e Cores
| Severidade | Emoji | Cor |
|-----------|-------|-----|
| critical | 🚨 | #ef4444 |
| warning | ⚠️ | #f59e0b |
| info | ℹ️ | #3b82f6 |

---

## 5. Execução

### Via Bandeja do Watchdog
Menu: `WORKERS (WK)` → `WkGeraAlertas`

### Via CLI
```bash
python scripts/run_gera_alertas.py
```

---

## 6. Monitoramento

```bash
tail -f logs/main_runner.json | grep "worker.alert"
```

### Dashboard Watchdog
```
Watchdog → Alertas
├─ System Alerts: N abertos
├─ Last Alert: timestamp
└─ Malha de IA: 🟢 / 🟡 / 🔴
```

---

## 7. Troubleshooting

### "FCM não funciona — firebase_admin não instalado"
```bash
pip install firebase-admin
# Se não deseja FCM, ignorar (webhooks funcionam independentemente)
```

### "Nenhum alerta disparado — sistema saudável"
- É o comportamento esperado quando não há anomalias
- Verificar RPC: `SELECT routine_name FROM information_schema.routines WHERE routine_name = 'detect_worker_anomalies'`

### "Webhook falha"
```bash
curl -X POST "$ALERT_WEBHOOK_URL" -H 'Content-Type: application/json' \
  -d '{"text": "teste"}'
```

---

## 8. Dependências

- `workers/base/worker_base.py` — Classe base
- `workers/base/cycle_result.py` — Estrutura de resultado
- `core/supabase_service.py` — Conexão com banco
- `firebase_admin` — FCM (opcional)
- `httpx` — Webhooks

---

## 9. Changelog

### v90.8 (2026-06-07)
- [x] Corrigido path: `workers/processors/wk_gera_alertas.py`
- [x] Classe renomeada: `WkGeraAlertas`
- [x] Migrado para BaseWorker moderno

---

**Última Revisão**: 2026-06-07
**PASA Version**: v88.0 → v90.8
