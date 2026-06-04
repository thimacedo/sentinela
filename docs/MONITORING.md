# Monitoring & Observability Guide — Sentinela Democrática

**Purpose**: System monitoring, logging, metrics, and alerting setup  
**Version**: 1.0  
**Last Updated**: 2026-06-04

---

## 🔍 Observability Stack

### Architecture

```
┌─────────────────────────────────────────┐
│       Application Layer                  │
│  (API, Frontend, Workers)                │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
  ┌───▼────┐  ┌───▼────┐  ┌──────────┐
  │ Logs   │  │Metrics │  │ Traces   │
  │(ELK)   │  │(Prom)  │  │(Jaeger)  │
  └────────┘  └────────┘  └──────────┘
      │            │            │
      │   ┌────────┴────────┐   │
      └───┤ Visualization   ├───┘
          │  (Grafana)      │
          └─────────────────┘
                  │
           ┌──────▼──────┐
           │  Alerting   │
           │ (AlertManager)
           └─────────────┘
```

---

## 📝 Logging

### Application Logging

#### Python Logging Configuration

```python
# core/logging_config.py
import logging
import logging.handlers
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure JSON logging for production"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # JSON Handler (stdout)
    json_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter()
    json_handler.setFormatter(json_formatter)
    logger.addHandler(json_handler)
    
    # File Handler (rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger
```

#### Log Levels

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed diagnostic info")           # Development only
logger.info("General informational messages")       # Important events
logger.warning("Warning about potential issues")    # Recoverable issues
logger.error("Error that prevented operation")      # Errors
logger.critical("Critical system failure")          # System down
```

#### Structured Logging

```python
logger.info("Target created", extra={
    "event": "target_created",
    "target_id": target.id,
    "user_id": user_id,
    "risk_level": target.risk_level,
    "timestamp": datetime.utcnow().isoformat()
})

logger.error("API call failed", extra={
    "event": "api_error",
    "endpoint": "/api/v1/targets",
    "status_code": 500,
    "error": str(exception),
    "duration_ms": 1500
})
```

### Log Aggregation (ELK Stack)

#### Elasticsearch Setup

```yaml
# docker-compose.yml - Elasticsearch
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
```

#### Logstash Configuration

```conf
# pipeline/logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse timestamp
  date {
    match => ["timestamp", "ISO8601"]
  }
  
  # Add metadata
  mutate {
    add_field => { "[@metadata][index_name]" => "sentinela-%{+YYYY.MM.dd}" }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
}
```

#### Kibana Dashboards

```typescript
// Access Kibana
// URL: http://localhost:5601
// Default credentials: elastic / changeme

// Create index pattern: sentinela-*
// Create visualizations for:
// - Request volume over time
// - Error rate by endpoint
// - Response time distribution
// - Top errors
// - User activity
```

### Log Rotation

```python
# logs/logrotate.conf
/workspace/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        # Restart application to use new log file
        systemctl restart sentinela-api
    endscript
}
```

---

## 📊 Metrics & Monitoring

### Prometheus Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sentinela-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'database'
    static_configs:
      - targets: ['localhost:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

#### Application Metrics

```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Business metrics
targets_created = Counter(
    'targets_created_total',
    'Total targets created'
)

alerts_triggered = Counter(
    'alerts_triggered_total',
    'Total alerts triggered',
    ['severity']
)

active_targets = Gauge(
    'targets_active_total',
    'Number of active targets'
)

# Usage example
@app.middleware("http")
async def add_metrics(request, call_next):
    method = request.method
    path = request.url.path
    
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    request_count.labels(method, path, response.status_code).inc()
    request_duration.labels(method, path).observe(duration)
    
    return response
```

#### Custom Metrics

```python
# Track business logic
def create_target(data):
    target = Target(**data)
    db.save(target)
    
    # Increment counter
    targets_created.inc()
    
    # Update gauge
    active_targets.set(Target.query.filter_by(status='active').count())
    
    return target

# Track alerts
def trigger_alert(target_id, severity):
    alert = Alert(target_id=target_id, severity=severity)
    db.save(alert)
    
    # Track alert
    alerts_triggered.labels(severity).inc()
```

### Grafana Dashboards

#### Dashboard Setup

```bash
# Access Grafana
# URL: http://localhost:3000
# Default: admin / admin
```

#### Key Dashboards

**1. API Performance**
```
- Requests per second (gauge)
- Error rate % (gauge)
- P95 response time (gauge)
- Requests by endpoint (stacked bar)
- Response time distribution (heatmap)
```

**2. Database Health**
```
- Connection pool usage (gauge)
- Query execution time (histogram)
- Slow queries (table)
- Replication lag (gauge)
- Disk usage (gauge)
```

**3. Business Metrics**
```
- New targets created (counter)
- Alerts triggered by severity (stacked area)
- Active targets (gauge)
- Average risk distribution (pie)
- Top targets by mentions (table)
```

**4. Infrastructure**
```
- CPU usage by pod (multiline graph)
- Memory usage by pod (multiline graph)
- Network I/O (stacked area)
- Disk I/O (stacked area)
- Pod restarts (table)
```

#### Example Dashboard JSON

```json
{
  "dashboard": {
    "title": "Sentinela API Performance",
    "panels": [
      {
        "title": "Requests per Second",
        "type": "gauge",
        "targets": [{
          "expr": "rate(api_requests_total[1m])"
        }]
      },
      {
        "title": "Error Rate",
        "type": "gauge",
        "targets": [{
          "expr": "rate(api_requests_total{status=~'5..'}[5m]) / rate(api_requests_total[5m])"
        }]
      }
    ]
  }
}
```

---

## 🚨 Alerting

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: sentinela
    rules:
      # API Alerts
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~'5..'}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: SlowApiResponse
        expr: histogram_quantile(0.95, api_request_duration_seconds) > 1
        for: 10m
        annotations:
          summary: "API response time is slow"
          description: "P95 response time is {{ $value }}s"
      
      # Database Alerts
      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count > 80
        annotations:
          summary: "High database connection usage"
          description: "{{ $value }}/100 connections in use"
      
      - alert: DatabaseReplicationLag
        expr: pg_replication_lag_seconds > 30
        annotations:
          summary: "Database replication is lagging"
          description: "Lag is {{ $value }}s"
      
      - alert: DiskSpaceRunningOut
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        annotations:
          summary: "Disk space is running out"
          description: "{{ $value | humanizePercentage }} free"
      
      # Application Alerts
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes > 1073741824  # 1GB
        for: 5m
        annotations:
          summary: "High memory usage"
          description: "{{ $value | humanize }}B"
      
      - alert: PodRestartingTooOften
        expr: rate(kube_pod_container_status_restarts_total[1h]) > 5
        annotations:
          summary: "Pod is restarting too frequently"
          description: "{{ $value }} restarts in last hour"
```

### Alert Manager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: $SLACK_WEBHOOK_URL

route:
  receiver: 'slack-notifications'
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    
    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
  
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: $PAGERDUTY_KEY
        description: '{{ .GroupLabels.alertname }}'
```

---

## 🔍 Distributed Tracing

### Jaeger Setup

```yaml
# docker-compose.yml
jaeger:
  image: jaegertracing/all-in-one:latest
  ports:
    - "16686:16686"  # UI
    - "6831:6831/udp"  # Jaeger agent
```

### Application Instrumentation

```python
# core/tracing.py
from jaeger_client import Config

def init_jaeger_tracer(service_name):
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },
        service_name=service_name,
        validate=True,
    )
    return config.initialize_tracer()

# In FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

tracer = init_jaeger_tracer("sentinela-api")

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
```

### Trace Queries

```python
# Example: Trace a user request
# 1. User logs in
# 2. API validates credentials (span)
# 3. Database query (span)
# 4. JWT token generation (span)
# 5. Response sent (span)

# View in Jaeger UI: http://localhost:16686
```

---

## 🐛 Error Tracking

### Sentry Setup

```python
# core/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    environment=os.getenv("ENVIRONMENT"),
)
```

### Error Context

```python
with sentry_sdk.push_scope() as scope:
    scope.set_tag("target_id", target.id)
    scope.set_context("user", {
        "id": user.id,
        "email": user.email,
        "role": user.role
    })
    
    try:
        # Some operation
    except Exception as e:
        sentry_sdk.capture_exception(e)
```

---

## 📈 Performance Profiling

### Database Query Profiling

```python
# core/db_profiler.py
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.INFO)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log slow queries > 1s
        logger.warning(f"SLOW QUERY ({total:.2f}s): {statement[:100]}...")
```

### Python Profiling

```bash
# Profile endpoint
python -m cProfile -o profile.prof api/index.py

# Analyze results
python -c "import pstats; p = pstats.Stats('profile.prof'); p.sort_stats('cumulative'); p.print_stats(20)"
```

---

## 📋 Health Checks

### API Health Endpoint

```python
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        checks["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        checks["checks"]["database"] = {"status": "error", "error": str(e)}
        checks["status"] = "unhealthy"
    
    # Redis check
    try:
        redis.ping()
        checks["checks"]["redis"] = {"status": "ok"}
    except Exception as e:
        checks["checks"]["redis"] = {"status": "error", "error": str(e)}
    
    # API check
    checks["checks"]["api"] = {"status": "ok", "version": "52.4.5"}
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(checks, status_code=status_code)
```

### Readiness & Liveness Probes

```yaml
# kubernetes deployment
spec:
  containers:
  - name: api
    livenessProbe:
      httpGet:
        path: /api/health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
      failureThreshold: 3
    
    readinessProbe:
      httpGet:
        path: /api/health/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 1
```

---

## 📊 Dashboard Queries

### Useful Prometheus Queries

```promql
# Request rate
rate(api_requests_total[5m])

# Error rate percentage
rate(api_requests_total{status=~'5..'}[5m]) / rate(api_requests_total[5m])

# P95 response time
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))

# Database connection pool usage
pg_stat_activity_count / pg_settings_max_connections

# Target creation rate (per hour)
rate(targets_created_total[1h])

# Active targets
targets_active_total

# Alert trigger distribution by severity
rate(alerts_triggered_total[1h]) by (severity)
```

---

## 🔔 Notification Channels

### Slack Integration

```python
# core/notifications.py
import slack_sdk

def send_slack_notification(channel, message):
    client = slack_sdk.WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    client.chat_postMessage(
        channel=channel,
        text=message,
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ {message}"
            }
        }]
    )
```

### Email Notifications

```python
# For critical alerts
def send_alert_email(alert_name, description):
    from email.mime.text import MIMEText
    import smtplib
    
    msg = MIMEText(description)
    msg['Subject'] = f"🚨 CRITICAL: {alert_name}"
    msg['From'] = "alerts@sentinela.com"
    msg['To'] = ",".join(ALERT_RECIPIENTS)
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.send_message(msg)
    server.quit()
```

---

## 📚 Monitoring Checklist

- [ ] Logging configured (JSON, structured, rotated)
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards created
- [ ] Alert rules configured
- [ ] AlertManager notifications set up
- [ ] Health check endpoints working
- [ ] Database query profiling enabled
- [ ] Error tracking (Sentry) configured
- [ ] Distributed tracing (Jaeger) running
- [ ] Slack/Email notifications working
- [ ] Regular monitoring review scheduled
- [ ] On-call rotation established

---

## 📚 Resources

- **Prometheus**: https://prometheus.io
- **Grafana**: https://grafana.com
- **Elasticsearch**: https://elastic.co
- **Jaeger**: https://jaegertracing.io
- **Sentry**: https://sentry.io
