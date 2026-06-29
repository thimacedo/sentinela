# Variáveis de Ambiente — Sentinela
_last_updated: 2026-06-04 | version: 1.0_

## Visão Geral

Este documento descreve todas as variáveis de ambiente necessárias para configurar e executar o Sentinela em diferentes ambientes (desenvolvimento, staging, produção).

### Formato de Configuração

O projeto usa arquivo `.env` na raiz do workspace. Copiar `.env.example` para `.env` e preencher com valores reais:

```bash
cp .env.example .env
# Editar .env com seus valores
```

---

## 📋 Seções de Configuração

### 1. Database (Supabase/PostgreSQL)

#### `SUPABASE_URL` ⭐ **OBRIGATÓRIO**
- **Tipo**: URL
- **Descrição**: URL base do seu projeto Supabase
- **Exemplo**: `https://vhamejkldzxbeibqeqpk.supabase.co`
- **Onde encontrar**: Dashboard Supabase → Settings → API → Project URL
- **Usado por**: Backend (main_runner.py), API FastAPI, Workers

#### `SUPABASE_KEY` ⭐ **OBRIGATÓRIO**
- **Tipo**: JWT Token
- **Descrição**: Chave de autenticação do Supabase (service_role)
- **Segurança**: 🔴 **NÃO exposer publicamente**
- **Onde encontrar**: Dashboard Supabase → Settings → API → Service Role Secret
- **Usado por**: Backend, API, Workers para operações autenticadas

#### `SUPABASE_SERVICE_KEY` ⭐ **OBRIGATÓRIO**
- **Tipo**: JWT Token
- **Descrição**: Alias para SUPABASE_KEY (operações com privilégios totais)
- **Igual a**: `SUPABASE_KEY`
- **Usado por**: RPCs e operações administrativas

#### `DATABASE_URL` ⭐ **PARA CONEXÃO DIRETA**
- **Tipo**: PostgreSQL Connection String
- **Descrição**: URL de conexão direta ao PostgreSQL (bypassa Supabase)
- **Formato**: `postgresql://user:password@host:port/database`
- **Exemplo**: `postgresql://postgres:senha@db.vhamejkldzxbeibqeqpk.supabase.co:5432/postgres`
- **Usado por**: Scripts de migração, ferramentas de backup
- **Nota**: Usar apenas para operações administrativas

#### `NEXT_PUBLIC_SUPABASE_URL` ⭐ **PARA FRONTEND**
- **Tipo**: URL
- **Descrição**: URL pública do Supabase (seguro expor)
- **Igual a**: `SUPABASE_URL`
- **Usado por**: Frontend Next.js (cliente-side)
- **Prefixo `NEXT_PUBLIC_`**: Indica que é seguro expor no frontend

#### `NEXT_PUBLIC_SUPABASE_ANON_KEY` ⭐ **PARA FRONTEND**
- **Tipo**: JWT Token (anon)
- **Descrição**: Chave anônima do Supabase (permissões limitadas)
- **Onde encontrar**: Dashboard Supabase → Settings → API → Anon Key
- **Usado por**: Frontend Next.js
- **Segurança**: ✅ Seguro expor (permissões limitadas por RLS)

#### `VITE_SUPABASE_URL` **PARA FRONTEND (VITE)**
- **Tipo**: URL
- **Descrição**: URL Supabase para projetos Vite
- **Igual a**: `SUPABASE_URL`
- **Usado por**: Frontend Vite (se não usando Next.js)

#### `VITE_SUPABASE_ANON_KEY` **PARA FRONTEND (VITE)**
- **Tipo**: JWT Token (anon)
- **Descrição**: Chave anônima para Vite
- **Igual a**: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Usado por**: Frontend Vite

#### `SENTINELA_SUPABASE_KEY`
- **Tipo**: JWT Token
- **Descrição**: Chave customizada do Supabase (uso específico)
- **Usado por**: Pode ser vazio se usando SUPABASE_KEY

---

### 2. Instagram (Coleta)

#### `IG_USER` ⭐ **OBRIGATÓRIO**
- **Tipo**: String
- **Descrição**: Username principal da conta Instagram para scraping
- **Exemplo**: `tempareiapodcast`
- **Nota**: Deve ser uma conta com acesso ao conteúdo que será monitorado
- **Usado por**: InstagramScraperWorker (coleta principal)

#### `IG_PASS` ⭐ **OBRIGATÓRIO**
- **Tipo**: String
- **Descrição**: Senha da conta Instagram principal
- **Segurança**: 🔴 **NÃO expor publicamente**
- **Nota**: Usar senha de app ou 2FA se disponível
- **Usado por**: InstagramScraperWorker

#### `IG_USER_1` **PARA MÚLTIPLAS CONTAS**
- **Tipo**: String
- **Descrição**: Username secundária (suporte a múltiplas contas)
- **Exemplo**: `monitoramento.discurso`
- **Usado por**: Fallback de coleta se IG_USER falhar

#### `IG_PASS_1` **PARA MÚLTIPLAS CONTAS**
- **Tipo**: String
- **Descrição**: Senha da conta secundária
- **Nota**: Implementa fallback automático entre contas

#### `INSTAGRAM_SESSIONID` **PARA SESSÃO PERSISTENTE**
- **Tipo**: String (cookie)
- **Descrição**: Session ID do Instagram (evita relogin frequente)
- **Formato**: `user_id%3Asession_string`
- **Exemplo**: `53127160841%3AZmPnDmSkkaZ0uw%3A10%3AAYjogw9GikJS1WIn7...`
- **Como gerar**: Extrair de navegador autenticado via Developer Tools
- **Atualização**: Rotaciona automaticamente a cada 24h (se habilitado)
- **Usado por**: Instagram headless scraper para sessões rápidas

#### `INSTAGRAM_SESSIONID_2` **FALLBACK DE SESSÃO**
- **Tipo**: String (cookie)
- **Descrição**: Sessão secundária como fallback
- **Nota**: Permite rotação entre múltiplas sessões

#### `INSTAGRAM_SESSIONID_VAL` **VALOR TEMPORÁRIO**
- **Tipo**: String (cookie)
- **Descrição**: Sessão validada para uso imediato
- **Nota**: Gerada por `scripts/export_playwright_cookies.py`

#### `INSTAGRAM_COOKIE_FULL` **COOKIES COMPLETOS**
- **Tipo**: String
- **Descrição**: Cookies completos do Instagram (para bypass de headers)
- **Formato**: `sessionid=...; ig_did=...; csrftoken=...`
- **Usado por**: Scrapers que necessitam headers completos

#### `ENABLE_ZYTE` **PROXY DE ROTAÇÃO**
- **Tipo**: Boolean (`true` or `false`)
- **Descrição**: Ativar Zyte como proxy de rotação
- **Default**: `false`
- **Nota**: Zyte não é mais eixo principal (use Playwright)

#### `PLAYWRIGHT_HEADLESS` **MODO HEADLESS**
- **Tipo**: Boolean
- **Descrição**: Executar Playwright sem interface gráfica
- **Default**: `true`
- **Valores**: `true` (headless) ou `false` (com interface)
- **Usado por**: Instagram headless scraper

---

### 2.2. Twitter/X (Coleta)

#### `XQUIK_API_KEY` ⭐ **REQUISITO PARA TWITTER**
- **Tipo**: String
- **Descrição**: Chave de API da plataforma Xquik para busca e extração de tweets
- **Segurança**: 🔴 **NÃO expor publicamente**
- **Exemplo**: `xq_YOUR_KEY_HERE`
- **Onde encontrar**: Painel de controle em [xquik.com](https://xquik.com)
- **Usado por**: `WkColetaTwitter` (`workers/scrapers/wk_coleta_twitter.py`)

---

### 3. Inteligência Artificial (IA)

#### `IA_PROVIDER` ⭐ **OBRIGATÓRIO PARA IA**
- **Tipo**: String
- **Descrição**: Provider principal de IA
- **Valores válidos**: 
  - `hybrid`: Ollama local + cloud fallback (RECOMENDADO)
  - `ollama`: Apenas Ollama local
  - `groq`: Apenas Groq cloud
  - `mistral`: Apenas Mistral cloud
  - `gemini`: Apenas Gemini (descontinuado em produção)
- **Default**: `hybrid`
- **Usado por**: AIProcessorWorker, core/ai_service.py

#### `OLLAMA_BASE_URL` **IA LOCAL**
- **Tipo**: URL
- **Descrição**: URL do servidor Ollama local
- **Exemplo**: `http://localhost:11434`
- **Nota**: Ollama deve estar rodando localmente (`ollama serve`)
- **Usar quando**: `IA_PROVIDER=hybrid` ou `IA_PROVIDER=ollama`

#### `OLLAMA_MODEL` **MODELO LOCAL**
- **Tipo**: String
- **Descrição**: Modelo Ollama para usar localmente
- **Exemplos recomendados**:
  - `gemma:2b` — Rápido, baixa memória (DEFAULT)
  - `mistral:7b` — Melhor qualidade
  - `qwen2.5:3b` — Equilíbrio
- **Nota**: Modelo deve estar baixado em Ollama
- **Como baixar**: `ollama pull gemma:2b`

#### `MODEL_EXPERT` **MODELO ESPECIALISTA**
- **Tipo**: String
- **Descrição**: Modelo Ollama para análises mais precisas
- **Default**: `gemma:2b`
- **Nota**: Pode ser diferente de OLLAMA_MODEL

#### `ENABLE_LOCAL_AI` **ATIVAR IA LOCAL**
- **Tipo**: Boolean
- **Descrição**: Ativar uso de Ollama para IA local
- **Default**: `true`
- **Valores**: `"true"` ou `"false"` (string)

#### `GROQ_API_KEY` **GROQ CLOUD**
- **Tipo**: API Key
- **Descrição**: Chave da API Groq (cloud)
- **Obtenção**: https://console.groq.com/
- **Limite**: 90.000 tokens/minuto (tier gratuito)
- **Usado por**: Fallback cloud quando Ollama indisponível

#### `MISTRAL_API_KEY` **MISTRAL CLOUD**
- **Tipo**: API Key
- **Descrição**: Chave da API Mistral
- **Obtenção**: https://console.mistral.ai/
- **Usado por**: Fallback cloud

#### `OPENROUTER_API_KEY` **OPENROUTER (AGREGADOR)**
- **Tipo**: API Key
- **Descrição**: Chave OpenRouter (acesso a múltiplos modelos)
- **Obtenção**: https://openrouter.ai/
- **Vantagem**: Fallback automático entre providers
- **Usado por**: Fallback profundo de IA

#### `OPENAI_API_KEY` **OPENAI (DESCONTINUADO)**
- **Tipo**: API Key
- **Descrição**: ChatGPT - não recomendado para produção
- **Nota**: Mantido apenas para compatibilidade
- **Custo**: Alto, não é fallback padrão

#### `GEMINI_API_KEY` **GEMINI (DESCONTINUADO)**
- **Tipo**: API Key
- **Descrição**: Google Gemini - retirado do pipeline principal
- **Nota**: Histórico apenas, não usar

#### `ANTHROPIC_API_KEY` **CLAUDE (OPCIONAL)**
- **Tipo**: API Key
- **Descrição**: Claude API (opcional para testes)
- **Obtenção**: https://console.anthropic.com/

#### `COHERE_API_KEY` **COHERE (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: Cohere API para fallback profundo
- **Usado por**: FallbackLLM

#### `DEEPSEEK_API_KEY` **DEEPSEEK (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: DeepSeek API para fallback
- **Usado por**: FallbackLLM

#### `CEREBRAS_API_KEY` **CEREBRAS (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: Cerebras API para fallback
- **Usado por**: FallbackLLM

#### `EDENAI_API_KEY` **EDENAI (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: EdenAI (agregador de IA)
- **Usado por**: Fallback profundo

#### `REPLICATE_API_TOKEN` **REPLICATE (FALLBACK)**
- **Tipo**: API Token
- **Descrição**: Replicate para modelos open-source
- **Usado por**: FallbackLLM

#### `AI21_API_KEY` **AI21 (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: AI21 Labs para fallback
- **Usado por**: FallbackLLM

#### `FIREWORKS_API_KEY` **FIREWORKS (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: Fireworks AI para fallback
- **Usado por**: FallbackLLM

#### `ROUTELLM_API_KEY` **ROUTELLM (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: RouteLLM para roteamento dinâmico
- **Usado por**: FallbackLLM

#### `ZHIPU_API_KEY` **ZHIPU (FALLBACK)**
- **Tipo**: API Key
- **Descrição**: Zhipu AI (ChatGLM)
- **Usado por**: FallbackLLM

---

### 3.2. Explorador de Dados (Datasette)

#### `DATASETTE_URL`
- **Tipo**: URL
- **Descrição**: URL do servidor local do Datasette (explorador SQL)
- **Default**: `http://localhost:8002`
- **Usado por**: DatabaseAgent (para consultas analíticas e buscas textuais indexadas FTS5)

---

### 4. Pagamentos (Stripe)

#### `STRIPE_API_KEY` ⭐ **OBRIGATÓRIO PARA PAGAMENTOS**
- **Tipo**: API Key (começa com `sk_test_` ou `sk_live_`)
- **Descrição**: Chave secreta da Stripe
- **Segurança**: 🔴 **NUNCA expor publicamente**
- **Obtenção**: https://dashboard.stripe.com/apikeys
- **Ambientes**:
  - Dev: `sk_test_...` (teste)
  - Prod: `sk_live_...` (produção)
- **Usado por**: API FastAPI, payment_manager

#### `STRIPE_WEBHOOK_SECRET` ⭐ **OBRIGATÓRIO PARA WEBHOOKS**
- **Tipo**: Webhook Secret (começa com `whsec_`)
- **Descrição**: Secret para validar webhooks da Stripe
- **Obtenção**: https://dashboard.stripe.com/webhooks
- **Nota**: Gerar novo webhook para cada ambiente
- **Usado por**: `/api/v1/webhooks/stripe`

#### `STRIPE_STARTER_PRICE_ID`
- **Tipo**: String
- **Descrição**: Price ID do plano Starter
- **Exemplo**: `price_1Abc123defGHI456`
- **Obtenção**: Dashboard Stripe → Products → Preços
- **Usado por**: Checkout de pagamento

#### `STRIPE_SQUAD_PRICE_ID`
- **Tipo**: String
- **Descrição**: Price ID do plano Squad
- **Usado por**: Checkout de pagamento

#### `STRIPE_WARROOM_PRICE_ID`
- **Tipo**: String
- **Descrição**: Price ID do plano War Room
- **Usado por**: Checkout de pagamento

#### `STRIPE_ALLOW_MOCK_PAYMENTS` **PARA TESTES**
- **Tipo**: Boolean
- **Descrição**: Permitir pagamentos mock (não real)
- **Default**: `false`
- **Valores**: `true` ou `false`
- **⚠️ Segurança**: Usar APENAS em desenvolvimento
- **Usado por**: payment_manager para testes locais

---

### 5. APIs Externas

#### `RAPIDAPI_KEY` **PARA SCRAPING**
- **Tipo**: API Key
- **Descrição**: RapidAPI para acessar múltiplas APIs
- **Obtenção**: https://rapidapi.com/
- **Usado por**: Alguns scrapers e coletores de dados

#### `ZYTE_API_KEY` **PROXY DE ROTAÇÃO (DESCONTINUADO)**
- **Tipo**: API Key
- **Descrição**: Zyte (formerly ScrapingBee)
- **Status**: Não é mais eixo principal
- **Default**: Deixar vazio

#### `META_ACCESS_TOKEN` **META GRAPH API**
- **Tipo**: Token
- **Descrição**: Token de acesso para Meta Graph API
- **Usado por**: Coleta de anúncios da Meta Ad Library
- **Obtenção**: Facebook Developer Console

#### `META_API_VERSION` **VERSÃO META API**
- **Tipo**: String
- **Descrição**: Versão da Meta Graph API
- **Default**: `v19.0`
- **Exemplo**: `v18.0`, `v19.0`, `v20.0`

#### `CHOREO_API_URL` **CHOREO READING LIST**
- **Tipo**: URL
- **Descrição**: API Choreo para reading list
- **Usado por**: Integração com plataforma Choreo

#### `CHOREO_API_TOKEN` **CHOREO TOKEN**
- **Tipo**: JWT Token
- **Descrição**: Token de autenticação Choreo
- **Usado por**: Requests autenticados para Choreo

#### `APIFY_API_TOKEN` **APIFY (OPCIONAL)**
- **Tipo**: API Token
- **Descrição**: Apify para automação de scraping
- **Obtenção**: https://apify.com/
- **Nota**: Opcional, não implementado atualmente

---

### 6. Notificações

#### `WHATSAPP_PHONE` **PARA ALERTAS**
- **Tipo**: String (formato internacional)
- **Descrição**: Número de telefone WhatsApp para enviar alertas
- **Formato**: `55` + código de área + número
- **Exemplo**: `558496066876` (para 55 84 9 6066876)
- **Usado por**: Workers para notificações críticas
- **Nota**: Usar com API CallMeBot ou similar

#### `WHATSAPP_API_KEY` **CALLMEBOT**
- **Tipo**: API Key
- **Descrição**: Chave de autenticação CallMeBot
- **Obtenção**: https://www.callmebot.com/
- **Usado por**: Envio de mensagens WhatsApp

---

### 7. Workers & Runtime

#### `NUM_SCRAPER_WORKERS` **ROCKET MODE**
- **Tipo**: Integer
- **Descrição**: Número de InstagramScraperWorkers paralelos
- **Default**: `1`
- **Exemplo**: `2`, `4`, `8` (escalamento horizontal)
- **Nota**: Cada worker=1 conta Instagram scrapeando
- **Usado por**: main_runner.py ao registrar workers
- **⚠️ Aviso**: Aumentar gradualmente (risk de shadowban)

#### `WATCHDOG_ACTIVE` **SUPERVISÃO LOCAL**
- **Tipo**: Boolean
- **Descrição**: Ativar Watchdog para supervisionar main_runner.py
- **Default**: `true`
- **Valores**: `true` ou `false`
- **Usado por**: watchdog/__init__.py

#### `RESEARCHER_MODE` **RESEARCH WORKER**
- **Tipo**: String
- **Descrição**: Modo de operação do TargetResearchWorker
- **Valores**:
  - `disabled` — Desabilitado (default)
  - `enabled` — Habilitado
  - `lightweight` — Modo leve
- **Default**: `disabled`
- **Nota**: Research worker só sobe se houver backlog real
- **Usado por**: TargetResearchWorker

---

### 8. Frontend

#### `FRONTEND_URL` **URL DO FRONTEND**
- **Tipo**: URL
- **Descrição**: URL pública do frontend
- **Exemplo**: 
  - Dev: `http://localhost:3000`
  - Prod: `https://sentinela.ai`
- **Usado por**: 
  - Backend para CORS/redirects
  - Webhooks Stripe para retorno
  - Frontend para URLs absolutas

#### `NEXT_PUBLIC_API_URL` **API URL FRONTEND**
- **Tipo**: URL
- **Descrição**: URL da API do backend (para frontend consumir)
- **Exemplo**:
  - Dev: `http://localhost:8000`
  - Prod: `https://api.sentinela.ai`
- **Prefixo `NEXT_PUBLIC_`**: Seguro expor (incluso no bundle)
- **Usado por**: Components React para chamar `/api/v1/...`

#### `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` **STRIPE FRONTEND**
- **Tipo**: Publishable Key (começa com `pk_test_` ou `pk_live_`)
- **Descrição**: Chave pública da Stripe para frontend
- **Segurança**: ✅ Seguro expor (permissões limitadas)
- **Obtenção**: https://dashboard.stripe.com/apikeys
- **Usado por**: Stripe.js no frontend para checkout

---

### 9. Cloud & Deployment

#### `CORS_ORIGINS` **POLÍTICA CORS**
- **Tipo**: String ou Lista
- **Descrição**: Origens permitidas para CORS
- **Valores**:
  - `*` — Permitir qualquer origem (dev)
  - `https://sentinela.ai` — Específico (prod)
  - Múltiplas: `https://sentinela.ai,https://app.sentinela.ai`
- **Default**: `*`
- **Usado por**: FastAPI middleware CORS

#### `AWS_ACCESS_KEY_ID` **AWS (OPCIONAL)**
- **Tipo**: String
- **Descrição**: Chave de acesso AWS
- **Obtenção**: AWS Console → IAM
- **Nota**: Opcional, pode não estar em uso

#### `AWS_SECRET_ACCESS_KEY` **AWS (OPCIONAL)**
- **Tipo**: String
- **Descrição**: Chave secreta AWS
- **Segurança**: 🔴 Nunca expor

#### `AWS_BUCKET_NAME` **S3 BUCKET (OPCIONAL)**
- **Tipo**: String
- **Descrição**: Nome do bucket S3 para uploads
- **Exemplo**: `sentinela-uploads`

#### `AWS_REGION` **AWS REGION (OPCIONAL)**
- **Tipo**: String
- **Descrição**: Região AWS
- **Default**: `us-east-1`
- **Exemplos**: `us-west-2`, `eu-west-1`

---

### 10. Circuit Breaker & Resiliência

#### `DB_CIRCUIT_BREAKER_FAILURE_THRESHOLD`
- **Tipo**: Integer
- **Descrição**: Número de falhas antes de abrir circuit breaker
- **Default**: `5`
- **Nota**: Configurado em código, pode ser override

#### `DB_CIRCUIT_BREAKER_RECOVERY_TIMEOUT`
- **Tipo**: Integer (segundos)
- **Descrição**: Tempo para tentar recuperação após abertura
- **Default**: `60`
- **Nota**: Circuit breaker muda para "half-open" após timeout

#### `DB_CIRCUIT_BREAKER_ENABLED`
- **Tipo**: Boolean
- **Descrição**: Ativar circuit breaker para banco
- **Default**: `true`

---

## 📊 Matriz de Ambientes

### Desenvolvimento (Local)

```bash
# Database
SUPABASE_URL=https://[seu-projeto].supabase.co
SUPABASE_KEY=[service-role-key]
DATABASE_URL=postgresql://postgres:senha@localhost:5432/postgres

# Instagram
IG_USER=sua_conta
IG_PASS=sua_senha
PLAYWRIGHT_HEADLESS=false

# IA
IA_PROVIDER=hybrid
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:2b

# Stripe
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_test_...
STRIPE_ALLOW_MOCK_PAYMENTS=true

# Frontend
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Cors
CORS_ORIGINS=*

# Workers
NUM_SCRAPER_WORKERS=1
WATCHDOG_ACTIVE=true
RESEARCHER_MODE=disabled
```

### Staging

```bash
# Database
SUPABASE_URL=https://[seu-projeto].supabase.co
SUPABASE_KEY=[service-role-key-staging]

# Instagram
IG_USER=conta_staging
IG_PASS=senha_staging

# IA
IA_PROVIDER=hybrid

# Stripe
STRIPE_API_KEY=sk_test_... (continue usando teste)
STRIPE_WEBHOOK_SECRET=whsec_test_...

# Frontend
FRONTEND_URL=https://staging.sentinela.ai
NEXT_PUBLIC_API_URL=https://api-staging.sentinela.ai

# CORS
CORS_ORIGINS=https://staging.sentinela.ai

# Workers
NUM_SCRAPER_WORKERS=2
```

### Produção

```bash
# Database
SUPABASE_URL=https://[seu-projeto].supabase.co
SUPABASE_KEY=[service-role-key-prod]

# Instagram
IG_USER=conta_producao
IG_PASS=senha_producao

# IA
IA_PROVIDER=hybrid
OLLAMA_BASE_URL=http://ollama-service:11434

# Stripe
STRIPE_API_KEY=sk_live_... (chave LIVE)
STRIPE_WEBHOOK_SECRET=whsec_live_...
STRIPE_ALLOW_MOCK_PAYMENTS=false

# Frontend
FRONTEND_URL=https://sentinela.ai
NEXT_PUBLIC_API_URL=https://api.sentinela.ai

# CORS
CORS_ORIGINS=https://sentinela.ai,https://www.sentinela.ai

# Workers
NUM_SCRAPER_WORKERS=4
WATCHDOG_ACTIVE=true
RESEARCHER_MODE=disabled
```

---

## 🔐 Segurança

### Variáveis Sensíveis (NUNCA expor)
- 🔴 `SUPABASE_KEY`
- 🔴 `SUPABASE_SERVICE_KEY`
- 🔴 `DATABASE_URL`
- 🔴 `IG_PASS`, `IG_PASS_1`
- 🔴 `STRIPE_API_KEY`
- 🔴 `STRIPE_WEBHOOK_SECRET`
- 🔴 Todas as API Keys de IA
- 🔴 `AWS_SECRET_ACCESS_KEY`
- 🔴 Tokens de autenticação

### Variáveis Seguras (OK expor no frontend)
- ✅ `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- ✅ `NEXT_PUBLIC_API_URL`
- ✅ `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- ✅ URLs públicas

### Boas Práticas
1. **Nunca commitar `.env`** para Git (adicionar a `.gitignore`)
2. **Usar secrets management** (Vercel Secrets, GitHub Secrets, etc.)
3. **Rotacionar chaves regularmente** (mensal)
4. **Usar diferentes chaves** por ambiente
5. **Ativar 2FA** em plataformas externas (Stripe, Supabase, etc.)

---

## 🚀 Carregamento de Variáveis

O projeto usa `python-dotenv` para carregar variáveis:

```python
# Em main_runner.py, api/index.py, etc.
from dotenv import load_dotenv
load_dotenv(override=True)

# Depois:
import os
api_key = os.getenv("SUPABASE_KEY")
```

### Prioridade de Carregamento
1. Variáveis de ambiente do sistema (mais alta)
2. Arquivo `.env` (se `override=True`)
3. Valores padrão em código (mais baixa)

---

## ✅ Checklist de Configuração

### Antes de Iniciar em Dev
- [ ] Copiar `.env.example` para `.env`
- [ ] Preencher `SUPABASE_URL` e `SUPABASE_KEY`
- [ ] Preencher `IG_USER` e `IG_PASS`
- [ ] Preencher `GROQ_API_KEY` (mínimo para IA)
- [ ] Iniciar Ollama localmente: `ollama serve`
- [ ] Testar conexão: `python -c "from core.db import *; print('OK')"`

### Antes de Deploy em Staging
- [ ] Todas as variáveis obrigatórias preenchidas
- [ ] Chaves Stripe em modo teste
- [ ] `STRIPE_ALLOW_MOCK_PAYMENTS=false`
- [ ] `FRONTEND_URL` apontando para staging
- [ ] `CORS_ORIGINS` restritivo
- [ ] Testar webhooks Stripe

### Antes de Deploy em Produção
- [ ] Usar chaves Stripe LIVE
- [ ] `STRIPE_ALLOW_MOCK_PAYMENTS=false`
- [ ] `FRONTEND_URL` apontando para produção
- [ ] `CORS_ORIGINS` apenas produção
- [ ] `RESEARCHER_MODE=disabled`
- [ ] Aumentar `NUM_SCRAPER_WORKERS` gradualmente
- [ ] Validar com load test: `scripts/diagnose_workers.py`

---

## 📞 Troubleshooting

### Erro: "SUPABASE_URL não configurado"
```bash
# Solução: Verificar .env
cat .env | grep SUPABASE_URL

# Verificar se load_dotenv() foi chamado
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('SUPABASE_URL'))"
```

### Erro: "Ollama não está respondendo"
```bash
# Solução: Iniciar Ollama
ollama serve

# Em outro terminal:
curl http://localhost:11434/api/tags
```

### Erro: "Stripe webhook secret inválido"
```bash
# Solução: Regenerar webhook
# 1. Dashboard Stripe → Webhooks
# 2. Clicar em seu webhook
# 3. Copiar novo "Signing secret"
# 4. Atualizar STRIPE_WEBHOOK_SECRET
```

### Erro: "IG_PASS inválido ou 2FA ativado"
```bash
# Solução: Usar App Password ou desativar 2FA temporariamente
# Para 2FA: Instagram Settings → Security → Two-Factor Authentication
```

---

## 📝 Referências

- Documentação Supabase: https://supabase.com/docs
- Documentação Stripe: https://stripe.com/docs
- Documentação Ollama: https://ollama.ai
- Documentação FastAPI: https://fastapi.tiangolo.com/

---

**Status**: ✅ Completo
**Próxima atualização**: Após mudanças significativas em configuração
