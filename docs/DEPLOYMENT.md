# Deployment Guide — Sentinela Democrática

**Purpose**: Production deployment strategies and procedures  
**Version**: 1.0  
**Last Updated**: 2026-06-04

---

## 🚀 Deployment Overview

### Environment Tiers

```
┌─────────────────────────────────────────┐
│         PRODUCTION (Live)                │
│   Full users, real data, monitored      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         STAGING (Pre-prod)               │
│   Full features, test data, monitored    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         DEVELOPMENT (Local)              │
│   Full features, dev data                │
└─────────────────────────────────────────┘
```

---

## 📋 Pre-Deployment Checklist

### Security
- [ ] CORS configured for production domains
- [ ] JWT_SECRET_KEY set to strong random value
- [ ] Database credentials stored in secure vault
- [ ] API keys for external services encrypted
- [ ] HTTPS/TLS enabled
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] Authentication middleware applied to all protected routes
- [ ] CSRF protection enabled
- [ ] Security headers configured

### Performance
- [ ] Database indexes created
- [ ] Redis cache configured
- [ ] CDN configured for static assets
- [ ] Compression enabled (gzip)
- [ ] Database connection pooling enabled
- [ ] Load balancer configured

### Testing
- [ ] Unit tests passing (80%+ coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Security tests passing
- [ ] Load testing completed
- [ ] Backup/restore tested

### Infrastructure
- [ ] Logging configured
- [ ] Monitoring/alerts configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan ready
- [ ] Database backups scheduled
- [ ] SSL certificates valid

---

## 🐳 Docker Deployment

### Backend Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations
RUN alembic upgrade head || true

# Start server
EXPOSE 8000
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Docker Setup

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build
COPY . .
RUN npm run build

# Serve with Next.js
EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  api:
    build: ./
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: production
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

  # Frontend
  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
      NEXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL}
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    ports:
      - "3000:3000"
    depends_on:
      - api

volumes:
  postgres_data:
```

### Build and Run

```bash
# Build images
docker-compose build

# Run containers
docker-compose up -d

# Check logs
docker-compose logs -f api

# Stop containers
docker-compose down
```

---

## ☁️ Cloud Deployment

### Deployment Options

#### Option 1: Vercel (Frontend) + Heroku/Railway (Backend)

**Frontend (Vercel)**:
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL
```

**Backend (Railway)**:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway up

# Set environment variables in dashboard
```

#### Option 2: AWS (Complete Stack)

**Architecture**:
```
┌─────────────────────────────┐
│   CloudFront (CDN)          │
└────────────┬────────────────┘
             │
      ┌──────┴──────┐
      │             │
  ┌───▼────┐   ┌───▼────┐
  │   ECS   │   │   S3    │
  │ (API)   │   │ (Static)│
  └───┬────┘   └────────┘
      │
  ┌───▼────────────────┐
  │   RDS (Database)   │
  │   ElastiCache      │
  └────────────────────┘
```

**Deployment Steps**:
1. Create ECR repositories for API and frontend
2. Push Docker images: `docker push <image>`
3. Create ECS task definitions
4. Create ECS services
5. Set up Application Load Balancer
6. Configure auto-scaling
7. Set up CloudFront distribution

#### Option 3: Kubernetes (Scalable)

```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinela-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentinela-api
  template:
    metadata:
      labels:
        app: sentinela-api
    spec:
      containers:
      - name: api
        image: sentinela-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 📦 Build Process

### Backend Build

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ --cov=api --cov-report=html

# Run linting
pylint api/
black --check api/

# Build package
python setup.py sdist bdist_wheel
```

### Frontend Build

```bash
# Install dependencies
npm ci

# Run tests
npm test -- --coverage

# Lint
npm run lint

# Build
npm run build

# Output in .next/ directory
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest tests/ --cov
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t sentinela-api:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.REGISTRY_USERNAME }} -p ${{ secrets.REGISTRY_PASSWORD }}
          docker push sentinela-api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deploy commands here
          kubectl set image deployment/sentinela-api \
            api=sentinela-api:${{ github.sha }}
```

---

## 🔐 Environment Management

### Production Environment Variables

```env
# Core Configuration
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://user:pass@host:6379/0
REDIS_SSL=true

# Security
JWT_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=https://sentinela.com,https://app.sentinela.com
CORS_ALLOW_CREDENTIALS=true
ENVIRONMENT=production

# Third-party Services
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=INFO
```

### Secret Management

```bash
# Using AWS Secrets Manager
aws secretsmanager create-secret \
  --name sentinela/production \
  --secret-string file://secrets.json

# Using HashiCorp Vault
vault kv put secret/sentinela/production \
  jwt_secret_key="..." \
  database_url="..."

# Using Kubernetes Secrets
kubectl create secret generic sentinela-secrets \
  --from-literal=jwt-secret=value \
  --from-literal=db-url=value
```

---

## 🚀 Deployment Strategies

### Blue-Green Deployment

```
┌──────────────────────────────────────────┐
│          Load Balancer                   │
└────────────────┬─────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
    ┌───▼────┐        ┌───▼────┐
    │ Blue   │        │ Green  │
    │ (old)  │        │ (new)  │
    │ v1.0   │        │ v1.1   │
    └────────┘        └────────┘

# 1. Deploy new version to Green
# 2. Run smoke tests on Green
# 3. Switch traffic to Green
# 4. Keep Blue for rollback
```

**Implementation**:
```bash
#!/bin/bash
# deploy-blue-green.sh

# 1. Deploy to green environment
kubectl apply -f deployment-green.yml

# 2. Wait for readiness
kubectl rollout status deployment/sentinela-api-green

# 3. Run smoke tests
./scripts/smoke-tests.sh http://green-api.internal

# 4. Switch traffic
kubectl patch service sentinela-api \
  -p '{"spec":{"selector":{"version":"green"}}}'

# 5. Keep blue for rollback
# To rollback: kubectl patch service sentinela-api -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Canary Deployment

```
            Load Balancer
            │
    ┌───────┴────────┐
    │ 95%            │ 5%
┌───▼─────┐      ┌────▼──┐
│  Stable │      │ Canary│
│  v1.0   │      │ v1.1  │
└─────────┘      └───────┘

# Gradually increase traffic to canary
# Monitor for errors before full rollout
```

---

## 📊 Database Migrations

### Running Migrations

```bash
# Using Alembic
alembic upgrade head

# Check migration status
alembic current
alembic history

# Rollback
alembic downgrade -1
```

### Migration Checklist

- [ ] Test migrations on staging first
- [ ] Create backup before migration
- [ ] Test rollback procedure
- [ ] Plan for downtime (if needed)
- [ ] Have rollback command ready
- [ ] Monitor after migration

---

## ✅ Post-Deployment

### Verification

```bash
# Check API health
curl https://api.sentinela.com/api/health

# Check database connection
curl https://api.sentinela.com/api/db-status

# Check frontend
curl https://sentinela.com

# Check logs
kubectl logs -f deployment/sentinela-api
```

### Rollback Procedure

```bash
# Quick rollback
kubectl rollout undo deployment/sentinela-api

# Specific revision
kubectl rollout undo deployment/sentinela-api --to-revision=2

# Database rollback
alembic downgrade -1
```

---

## 🔍 Monitoring & Alerts

### Key Metrics to Monitor

1. **API Health**
   - Response time (p50, p95, p99)
   - Error rate
   - Request rate

2. **Database**
   - Connection pool usage
   - Query execution time
   - Disk space
   - Replication lag

3. **Infrastructure**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network bandwidth

### Alert Thresholds

```yaml
# Prometheus alerts
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    duration: 5m
    severity: critical

  - name: HighResponseTime
    condition: p95_response_time > 1000ms
    duration: 10m
    severity: warning

  - name: LowDiskSpace
    condition: disk_available < 10%
    severity: critical
```

---

## 📚 Deployment Runbook

### Pre-deployment (1 hour before)

1. [ ] Notify team in #deployments
2. [ ] Create deployment issue tracking changes
3. [ ] Verify CI/CD pipeline status
4. [ ] Prepare rollback procedure
5. [ ] Schedule deployment window

### During Deployment (15-30 min)

1. [ ] Pull latest code
2. [ ] Run test suite
3. [ ] Build Docker image
4. [ ] Push to registry
5. [ ] Update deployment manifest
6. [ ] Apply to staging
7. [ ] Run smoke tests on staging
8. [ ] Apply to production
9. [ ] Verify health checks pass
10. [ ] Run smoke tests on production

### Post-deployment (30 min after)

1. [ ] Monitor error rate and latency
2. [ ] Check user reports
3. [ ] Verify new features working
4. [ ] Update deployment tracking
5. [ ] Document any issues
6. [ ] Notify stakeholders

### Troubleshooting

```bash
# Pod not starting
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Database connection issues
kubectl port-forward svc/postgres 5432:5432
psql postgres://user:pass@localhost:5432/db

# Out of memory
kubectl get nodes
kubectl describe node <node-name>

# Check service connectivity
kubectl exec -it <pod> -- sh
nc -zv service-name 8000
```

---

## 🔗 Resources

- **Docker Docs**: https://docs.docker.com
- **Kubernetes**: https://kubernetes.io
- **Vercel Deployment**: https://vercel.com/docs
- **AWS Deployment**: https://docs.aws.amazon.com
- **CI/CD Best Practices**: https://martinfowler.com/articles/
