# API Reference — Sentinela
_version: 1.0 | last_updated: 2026-06-04 | backend: FastAPI_

## Visão Geral

A API do Sentinela é construída em **FastAPI** e fornece endpoints RESTful para:
- Monitoramento de candidatos e indicadores políticos
- Análise de sentimento e detecção de hostilidade em redes sociais
- Geração de dossiês e relatórios
- Gerenciamento de pagamentos (Stripe)
- Monitoramento de workers e telemetria

### Base URL
```
http://localhost:8000  # Development
https://api.sentinela.ai  # Production (exemplo)
```

### Autenticação

Atualmente a API **não requer autenticação por padrão**, mas suporta:
- **Headers opcionais**:
  - `X-Organization-Id`: Filtrar dados por organização
  - `Authorization`: Para endpoints futuros

### Content-Type
Todos os requests devem usar `Content-Type: application/json`

### CORS
A API permite **CORS de qualquer origem** (`allow_origins=["*"]`)

---

## 1. Health & Status

### GET `/`
**Descrição**: Root endpoint com informações de status

**Response**:
```json
{
  "status": "operational",
  "service": "Sentinela API Backend",
  "version": "50.1",
  "documentation": "/docs",
  "endpoints": {
    "health": "/api/health",
    "summary": "/api/v1/summary",
    "targets": "/api/v1/targets"
  }
}
```

### GET `/api/health`
**Descrição**: Health check simples

**Response**:
```json
{
  "status": "healthy"
}
```

---

## 2. Dashboard & Summary

### GET `/api/v1/summary`
**Descrição**: KPIs consolidados em tempo real

**Headers Opcionais**:
- `X-Organization-Id`: string (filtra por organização)

**Response**:
```json
{
  "alvo_count": 312,
  "comentarios_count": 45628,
  "alertas_criticos": 47,
  "risco_geral": "ELEVADO",
  "ultima_atualizacao": "2024-05-26T14:32:00Z"
}
```

**Status Codes**:
- `200`: Sucesso
- `500`: Erro ao conectar no banco de dados

---

## 3. Targets (Candidatos Monitorados)

### GET `/api/v1/targets`
**Descrição**: Lista candidatos monitorados com variabilidade algorítmica

**Query Parameters**:
- `limit`: int (default: 50) - Número máximo de resultados
- `X-Organization-Id`: string (header) - Filtrar por organização

**Response**:
```json
[
  {
    "id": "cand_uuid",
    "nome": "João Silva",
    "partido": "Partido X",
    "cargo": "Senador",
    "foto_url": "https://...",
    "status_monitoramento": "Ativo",
    "nota_relevancia": 85,
    "risco_nivel": "CRITICO",
    "comentarios_totais_count": 1240,
    "comentarios_odio_count": 234,
    "ultima_coleta": "2024-05-26T14:32:00Z"
  }
]
```

**Notas**:
- Top 10 candidatos (por `nota_relevancia >= 80`) são fixos
- Resto é embaralhado para evitar padrões
- Cálculo de risco baseado em: `odio_count / total_count`

---

## 4. Análise de Redes

### GET `/api/v1/networks`
**Descrição**: Análise de padrões coordenados e clusters de hostilidade

**Query Parameters**:
- `depth`: int (default: 2) - Profundidade de mineração
- `min_cluster_size`: int (default: 5) - Tamanho mínimo de cluster

**Response**:
```json
{
  "clusters": [
    {
      "cluster_id": "cluster_123",
      "size": 23,
      "centrality": 0.87,
      "hostility_avg": "CRITICO",
      "members": [
        {
          "usuario_id": "user_123",
          "username": "usuario_x",
          "posts_no_cluster": 12,
          "engagement_rate": 0.65
        }
      ],
      "patterns": [
        {
          "pattern_type": "coordinated_hate",
          "confidence": 0.92,
          "description": "Padrão de ódio coordenado detectado"
        }
      ]
    }
  ],
  "total_clusters": 7,
  "suspicious_activity": "ELEVADA"
}
```

---

## 5. Alertas

### GET `/api/v1/alerts/active`
**Descrição**: Alertas críticos ativos

**Response**:
```json
{
  "total": 47,
  "alerts": [
    {
      "id": "alert_uuid",
      "tipo": "PICO_HOSTILIDADE",
      "severity": "CRITICO",
      "candidato": "João Silva",
      "descricao": "Pico de 340% em ódio nas últimas 4h",
      "data": "2024-05-26T14:32:00Z",
      "posts_afetados": 2843
    }
  ]
}
```

### POST `/api/v1/alerts/false-positive`
**Descrição**: Marcar alerta como falso positivo

**Request Body**:
```json
{
  "id": "alert_uuid"
}
```

**Response**:
```json
{
  "status": "marked_as_false_positive",
  "id": "alert_uuid"
}
```

---

## 6. Analytics

### GET `/api/v1/analytics/marketing-kpis`
**Descrição**: KPIs de marketing e engagement

**Response**:
```json
{
  "impressoes": 1250000,
  "cliques": 45000,
  "taxa_clique": 0.036,
  "conversoes": 234,
  "custo_por_conversao": 125.50,
  "roi": 3.2,
  "periodo": "24h"
}
```

### GET `/api/v1/analytics/demographics`
**Descrição**: Dados demográficos dos alvos monitorados

**Response**:
```json
{
  "por_idade": {
    "18-25": 0.25,
    "25-35": 0.35,
    "35-50": 0.25,
    "50+": 0.15
  },
  "por_genero": {
    "masculino": 0.6,
    "feminino": 0.35,
    "outro": 0.05
  },
  "por_regiao": {
    "sudeste": 0.45,
    "nordeste": 0.25,
    "sul": 0.18,
    "norte": 0.08,
    "centro_oeste": 0.04
  }
}
```

### GET `/api/v1/analytics/resilience-ranking`
**Descrição**: Ranking de resiliência de candidatos

**Response**:
```json
[
  {
    "rank": 1,
    "nome": "João Silva",
    "resiliencia_score": 0.87,
    "ataques_recebidos": 234,
    "respostas_efetivas": 145,
    "taxa_resposta": 0.62
  }
]
```

### GET `/api/v1/analytics/temporal-series`
**Descrição**: Série temporal de hostilidade

**Query Parameters**:
- `days`: int (default: 30) - Dias para análise histórica

**Response**:
```json
{
  "data": [
    {
      "data": "2024-05-01",
      "hostilidade_media": 0.45,
      "picos": 3,
      "posts_total": 1240
    }
  ]
}
```

---

## 7. Dossiês

### POST `/api/v1/dossiers/generate`
**Descrição**: Gerar novo dossiê para candidato

**Request Body**:
```json
{
  "candidato_id": "cand_uuid",
  "user_id": "user_uuid",
  "modules": ["base", "forensics", "network"]
}
```

**Response**:
```json
{
  "dossier_id": "dossier_uuid",
  "status": "generating",
  "candidato": "João Silva",
  "modulos": ["base", "forensics", "network"],
  "criado_em": "2024-05-26T14:32:00Z"
}
```

**Status codes**:
- `201`: Dossiê criado com sucesso
- `400`: Candidato inválido ou módulos não reconhecidos
- `409`: Dossiê já existe para este candidato

### GET `/api/v1/dossiers`
**Descrição**: Listar dossiês gerados

**Query Parameters**:
- `user_id`: string - Filtrar por usuário
- `limit`: int (default: 50) - Limite de resultados

**Response**:
```json
{
  "dossiers": [
    {
      "id": "dossier_uuid",
      "candidato": "João Silva",
      "criado_em": "2024-05-26T14:32:00Z",
      "modulos": ["base", "forensics", "network"],
      "tamanho_kb": 2540,
      "status": "completed"
    }
  ],
  "total": 23
}
```

---

## 8. PASA (Padrão de Análise de Sentimento Assistido)

### GET `/api/v1/pasa/breakdown`
**Descrição**: Breakdown de classificações PASA

**Response**:
```json
{
  "ODIO_IDENTITARIO": {
    "label": "Ódio Identitário",
    "count": 234,
    "percentage": 12.5,
    "color": "#ef4444",
    "icon": "users"
  },
  "VIOLENCIA_GENERO": {
    "label": "Violência de Gênero",
    "count": 145,
    "percentage": 7.8,
    "color": "#ec4899",
    "icon": "shield-alert"
  },
  "AMEACA": {
    "label": "Ameaça",
    "count": 89,
    "percentage": 4.8,
    "color": "#f97316",
    "icon": "alert-octagon"
  },
  "INSULTO_AD_HOMINEM": {
    "label": "Insulto Ad Hominem",
    "count": 567,
    "percentage": 30.4,
    "color": "#f59e0b",
    "icon": "swords"
  },
  "ATAQUE_INSTITUCIONAL": {
    "label": "Ataque Institucional",
    "count": 234,
    "percentage": 12.5,
    "color": "#8b5cf6",
    "icon": "landmark"
  },
  "DANO_A_IMAGEM": {
    "label": "Dano à Imagem",
    "count": 298,
    "percentage": 16.0,
    "color": "#06b6d4",
    "icon": "scale"
  }
}
```

---

## 9. Trends

### GET `/api/v1/trends`
**Descrição**: Tendências em tempo real

**Response**:
```json
{
  "trending_topics": [
    {
      "topic": "#eleições2024",
      "mentions": 12450,
      "trend": "up",
      "change_percent": 23.5
    }
  ],
  "trending_candidates": [
    {
      "nome": "João Silva",
      "mentions": 2340,
      "trend": "up",
      "change_percent": 45.2
    }
  ]
}
```

---

## 10. Pagamentos (Stripe)

### POST `/api/v1/checkout/create-session`
**Descrição**: Criar sessão de checkout (Stripe)

**Request Body**:
```json
{
  "user_id": "user_uuid",
  "package_slug": "starter",
  "price_id": "price_xxxxx"
}
```

**Response**:
```json
{
  "session_id": "cs_test_xxxxx",
  "url": "https://checkout.stripe.com/pay/cs_test_xxxxx"
}
```

**Packages Disponíveis**:
- `starter`: Plano Iniciante
- `squad`: Plano Squad
- `warroom`: Plano War Room

### POST `/api/v1/webhooks/stripe`
**Descrição**: Webhook para confirmações de pagamento

**Trigger Events**:
- `checkout.session.completed` — Pagamentos imediatos (Cartão)
- `checkout.session.async_payment_succeeded` — Pagamentos atrasados (Boleto/PIX)

**Processamento**:
1. Recebe evento assinado da Stripe
2. Valida assinatura com `STRIPE_WEBHOOK_SECRET`
3. Extrai metadados (user_id, ci_amount)
4. Injeta tokens via RPC `process_ci_transaction`

**Response**:
```json
{
  "status": "success"
}
```

**Error Codes**:
- `400`: Payload ou assinatura inválida
- `500`: Erro ao processar RPC

---

## 11. Geolocalização

### GET `/api/v1/geo/uf`
**Descrição**: Estatísticas por estado

**Response**:
```json
[
  {
    "uf": "SP",
    "nome": "São Paulo",
    "candidatos": 45,
    "posts": 12450,
    "alertas": 23
  }
]
```

---

## 12. Anúncios (Meta Ad Library)

### GET `/api/v1/ads`
**Descrição**: Anúncios políticos coletados da Meta Ad Library

**Query Parameters**:
- `candidate_id`: string - Filtrar por candidato
- `date_from`: string (ISO 8601) - Data inicial
- `date_to`: string (ISO 8601) - Data final
- `limit`: int (default: 50)

**Response**:
```json
{
  "ads": [
    {
      "id": "ad_uuid",
      "titulo": "Candidato X",
      "descricao": "Vote em...",
      "candidato": "João Silva",
      "plataforma": "instagram",
      "data_publicacao": "2024-05-26T14:32:00Z",
      "impressoes": 125000,
      "custo_estimado": 5000.00,
      "link": "https://..."
    }
  ],
  "total": 234
}
```

---

## 13. Sessions (Instagram)

### GET `/api/v1/sessions/instagram/status`
**Descrição**: Status das sessões do Instagram

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "session_uuid",
      "account": "tempareiapodcast",
      "status": "active",
      "ultima_atualizacao": "2024-05-26T14:32:00Z",
      "proxima_rotacao": "2024-05-27T14:32:00Z"
    }
  ],
  "rotation_enabled": true,
  "rotation_interval_hours": 24
}
```

### GET `/api/v1/sessions/instagram`
**Descrição**: Listar todas as sessões do Instagram

**Response**: Array de sessões (mesmo schema acima)

### POST `/api/v1/sessions/instagram/cookies`
**Descrição**: Injetar cookies de Instagram

**Request Body**:
```json
{
  "cookies": "{serialized_cookies_string}"
}
```

**Response**:
```json
{
  "status": "injected",
  "session_id": "session_uuid"
}
```

### PATCH `/api/v1/sessions/instagram/{session_id}/rotation`
**Descrição**: Configurar rotação automática

**Request Body**:
```json
{
  "enabled": true,
  "intervalHours": 24
}
```

**Response**:
```json
{
  "status": "updated",
  "session_id": "session_uuid"
}
```

### POST `/api/v1/sessions/instagram/rotate`
**Descrição**: Forçar rotação de sessão

**Response**:
```json
{
  "status": "rotated"
}
```

### DELETE `/api/v1/sessions/instagram/{session_id}`
**Descrição**: Deletar sessão

**Response**:
```json
{
  "status": "deleted"
}
```

---

## 14. Workers & Telemetria

### GET `/api/v1/workers/telemetry`
**Descrição**: Telemetria geral de workers

**Response**:
```json
{
  "total_workers": 6,
  "active": 5,
  "failed": 0,
  "idle": 1,
  "metrics": {
    "total_cycles": 1542,
    "successful_cycles": 1523,
    "failed_cycles": 19,
    "average_cycle_time_seconds": 45.2
  }
}
```

### GET `/api/v1/workers/dashboard`
**Descrição**: Dashboard de workers com status individual

**Response**:
```json
{
  "workers": [
    {
      "name": "InstagramScraperWorker",
      "status": "active",
      "uptime_hours": 23.5,
      "cycles_count": 234,
      "last_cycle": "2024-05-26T14:32:00Z"
    }
  ]
}
```

### GET `/api/v1/workers/stats`
**Descrição**: Estatísticas agregadas de todos os workers

**Response**:
```json
{
  "total_processed": 1254000,
  "average_response_time_ms": 145,
  "success_rate": 0.985,
  "error_rate": 0.015
}
```

### GET `/api/v1/workers/{worker_name}/stats`
**Descrição**: Estatísticas de um worker específico

**Response**:
```json
{
  "worker_name": "InstagramScraperWorker",
  "cycles_total": 234,
  "cycles_successful": 230,
  "cycles_failed": 4,
  "average_cycle_duration_seconds": 45,
  "items_processed": 45600,
  "last_activity": "2024-05-26T14:32:00Z"
}
```

### POST `/api/v1/workers/export-metrics`
**Descrição**: Exportar métricas de workers

**Request Body**:
```json
{
  "format": "csv",
  "date_from": "2024-05-01",
  "date_to": "2024-05-26"
}
```

**Response**:
```json
{
  "status": "exported",
  "file_url": "https://...",
  "size_mb": 12.5
}
```

---

## 15. Monitor

### GET `/api/v1/monitor/status`
**Descrição**: Status geral do monitor/watchdog

**Response**:
```json
{
  "watchdog_active": true,
  "uptime_hours": 168,
  "database_connection": "ok",
  "last_health_check": "2024-05-26T14:32:00Z",
  "runtime_log_available": true
}
```

---

## 16. Autenticação & Tokens

### POST `/api/v1/auth/register-push-token`
**Descrição**: Registrar token de push notification

**Request Body**:
```json
{
  "user_id": "user_uuid",
  "token": "push_token_string",
  "platform": "web",
  "device_id": "device_uuid_optional"
}
```

**Response**:
```json
{
  "status": "registered",
  "user_id": "user_uuid"
}
```

---

## 17. Auditoria

### POST `/api/v1/audit/validate`
**Descrição**: Validar integridade de dados

**Request Body**:
```json
{
  "module": "comments",
  "period_days": 7
}
```

**Response**:
```json
{
  "status": "validated",
  "total_items": 45600,
  "invalid_items": 0,
  "integrity_score": 1.0
}
```

---

## 18. Admin Finance

### GET `/api/v1/admin/finance/dashboard`
**Descrição**: Dashboard financeiro administrativo

**Headers Requeridos**:
- `X-Admin-Key`: chave de acesso administrativo

**Response**:
```json
{
  "total_revenue": 125000.00,
  "total_ci_sold": 50000,
  "average_order_value": 157.50,
  "churn_rate": 0.08,
  "ltv": 1250.00,
  "period": "30d"
}
```

---

## Tratamento de Erros

### Códigos de Status Comuns

| Código | Descrição | Ação |
|--------|-----------|------|
| 200 | OK | Requisição bem-sucedida |
| 201 | Created | Recurso criado |
| 400 | Bad Request | Parâmetros inválidos |
| 401 | Unauthorized | Autenticação necessária |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Recurso já existe |
| 500 | Server Error | Erro interno do servidor |
| 503 | Service Unavailable | Serviço indisponível |

### Formato de Erro

```json
{
  "status": "error",
  "detail": "Descrição detalhada do erro",
  "error_code": "INVALID_PARAMETER",
  "timestamp": "2024-05-26T14:32:00Z"
}
```

---

## Rate Limiting

- **Limite**: 1000 requisições por hora por IP
- **Headers de resposta**:
  - `X-RateLimit-Limit`: Limite total
  - `X-RateLimit-Remaining`: Requisições restantes
  - `X-RateLimit-Reset`: Timestamp do reset

---

## Paginação

Endpoints que retornam listas suportam:
- `limit`: Número de resultados (default: 50, max: 500)
- `offset`: Número de resultados para pular (default: 0)

**Response com Paginação**:
```json
{
  "data": [...],
  "total": 234,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

---

## Variáveis de Ambiente Necessárias

Veja [`docs/ENVIRONMENT_VARIABLES.md`](../ENVIRONMENT_VARIABLES.md) para configuração completa da API.

**Essenciais**:
- `SUPABASE_URL`: URL do banco de dados
- `SUPABASE_KEY`: Chave do Supabase
- `STRIPE_API_KEY`: Chave da API Stripe
- `STRIPE_WEBHOOK_SECRET`: Secret para webhooks

---

## Exemplos cURL

### Obter Summary
```bash
curl -X GET http://localhost:8000/api/v1/summary \
  -H "Content-Type: application/json"
```

### Obter Targets
```bash
curl -X GET "http://localhost:8000/api/v1/targets?limit=10" \
  -H "Content-Type: application/json"
```

### Gerar Dossiê
```bash
curl -X POST http://localhost:8000/api/v1/dossiers/generate \
  -H "Content-Type: application/json" \
  -d '{
    "candidato_id": "cand_uuid",
    "user_id": "user_uuid",
    "modules": ["base", "forensics"]
  }'
```

### Criar Checkout
```bash
curl -X POST http://localhost:8000/api/v1/checkout/create-session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_uuid",
    "package_slug": "starter"
  }'
```

---

## Documentação Automática

A API fornece documentação interativa em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Acessar estes endpoints durante desenvolvimento para testar interativamente.

---

## Changelog

### Versão 1.0 (2026-06-04)
- [x] Documentação inicial
- [x] 18 grupos de endpoints documentados
- [x] Schemas de request/response
- [x] Exemplos cURL

### Pendente
- [ ] Implementar autenticação robusta
- [ ] Adicionar OpenAPI 3.0 formal em código
- [ ] Rate limiting implementado
- [ ] Logs estruturados

---

**Status**: ✅ Completo
**Próxima revisão**: Após implementação de autenticação
