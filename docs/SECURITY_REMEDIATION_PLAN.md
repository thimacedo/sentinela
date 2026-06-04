# Security & Architecture Remediation Plan — Sentinela

**Data**: 2026-06-04  
**Versão**: 1.0  
**Status**: 🔴 CRITICAL - Requer implementação imediata

---

## 📋 Sumário Executivo

Com base na revisão de código realizada, identificamos **17 vulnerabilidades** distribuídas entre:
- **3 Críticas** (exploração trivial, risco alto)
- **8 Altas** (impacto significativo em segurança)
- **6 Médias** (risco moderado)

Este plano detalha a remediação com **timeline realista, estimativas de esforço e priorização**.

---

## 🎯 Objetivos

1. ✅ Eliminar todas as vulnerabilidades críticas em **2 semanas**
2. ✅ Resolver vulnerabilidades altas em **1 mês**
3. ✅ Implementar melhorias de arquitetura em **2 meses**
4. ✅ Atingir 80%+ test coverage em **6 semanas**

---

## 🚨 FASE 1: REMEDIAÇÃO CRÍTICA (Semana 1-2)

### 1.1 **CORS Wildcard Configuration** 
**Severity**: 🔴 CRÍTICO  
**Current Risk**: CSRF attacks, credential theft, cross-origin exploitation  
**Files Affected**: `/workspace/api/index.py`, `/workspace/api/v1/admin/*.py`

#### Remediation Steps

**Step 1: Update Environment Configuration**
```bash
# Add to .env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com,https://admin.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=3600
```

**Step 2: Create CORS Configuration Module**
```python
# /workspace/api/config/cors.py
import os
from typing import List

def get_cors_origins() -> List[str]:
    """Get allowed CORS origins from environment"""
    origins_str = os.getenv("CORS_ORIGINS", "")
    if not origins_str:
        # Development fallback
        return ["http://localhost:3000", "http://localhost:8000"]
    return origins_str.split(",")

CORS_CONFIG = {
    "allow_origins": get_cors_origins(),
    "allow_credentials": os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true",
    "allow_methods": ["GET", "POST", "PUT", "DELETE"],
    "allow_headers": ["Content-Type", "Authorization"],
    "max_age": int(os.getenv("CORS_MAX_AGE", "3600"))
}
```

**Step 3: Update Main App**
```python
# /workspace/api/index.py - Line 52-57
from fastapi.middleware.cors import CORSMiddleware
from api.config.cors import CORS_CONFIG

app.add_middleware(
    CORSMiddleware,
    **CORS_CONFIG
)
```

**Effort**: 🕐 30 minutes  
**Testing**: Manual test from different origins  
**Verification**: Check response headers `Access-Control-Allow-Origin`

---

### 1.2 **Admin Endpoints Without Authentication**
**Severity**: 🔴 CRÍTICO  
**Current Risk**: Unauthorized access to financial data, user balances, system dashboard  
**Files Affected**: `/workspace/api/index.py` (Lines 219-280, 315-380, etc.)

#### Remediation Steps

**Step 1: Create Authentication Middleware**
```python
# /workspace/api/middleware/auth.py
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import logging
from api.common import verify_session_token

logger = logging.getLogger("auth")
security = HTTPBearer()

async def verify_admin_token(credentials: HTTPAuthCredentials) -> str:
    """Verify admin token and return user_id"""
    try:
        token = credentials.credentials
        user_id = verify_session_token(token)
        
        # Check if user has admin role
        from api.common import get_supa
        supa = get_supa()
        profile = supa.table('profiles').select('role').eq('id', user_id).single().execute()
        
        if profile.data.get('role') not in ['ADMIN', 'SUPER_ADMIN']:
            logger.warning(f"Non-admin user {user_id} attempted admin access")
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        return user_id
    except Exception as e:
        logger.error(f"Admin token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
```

**Step 2: Apply to Admin Endpoints**
```python
# /workspace/api/index.py - Line 219
@app.get("/api/v1/admin/finance/dashboard")
async def get_finance_dashboard(
    admin_token: str = Depends(verify_admin_token),
    supa: Client = Depends(get_supa)
):
    """Financial dashboard (Admin only)"""
    # Protected endpoint
    profiles_res = supa.table('profiles').select('id, saldo_ci, ci_limite_mensal, ci_usado_mes_atual').execute()
    return {"data": profiles_res.data}
```

**Step 3: Create Role-Based Access Control Decorator**
```python
# /workspace/api/middleware/rbac.py
from functools import wraps
from typing import List

def require_role(*roles: str):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (from Depends)
            # Check if user has required role
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.get("/api/v1/admin/users")
@require_role("ADMIN", "SUPER_ADMIN")
async def list_users(supa: Client = Depends(get_supa)):
    ...
```

**Effort**: 🕐 1-2 hours  
**Testing**: 
- ✅ Admin can access endpoint with valid token
- ✅ Non-admin cannot access endpoint
- ✅ Invalid token returns 401
- ✅ Missing token returns 401

**Affected Endpoints** (must apply authentication):
- `GET /api/v1/admin/finance/dashboard` (Line 219)
- `POST /api/v1/admin/reclassify` (Line 315)
- `POST /api/v1/admin/review` (Line 380)
- All endpoints under `/api/v1/admin/*`

---

### 1.3 **Weak Session Token Generation**
**Severity**: 🔴 CRÍTICO  
**Current Risk**: Token forgery, no token revocation, no refresh mechanism  
**Files Affected**: `/workspace/api/common.py` (Lines 52-57), `/workspace/api/v1/admin/login.py`

#### Remediation Steps

**Step 1: Install JWT Library**
```bash
pip install PyJWT python-jose[cryptography]
```

**Step 2: Create Secure Token Module**
```python
# /workspace/api/security/tokens.py
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import logging

logger = logging.getLogger("tokens")

SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET_KEY not configured")

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 120

def generate_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),  # Unique token ID for revocation
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_refresh_token(user_id: str) -> str:
    """Generate JWT refresh token (longer expiry)"""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def revoke_token(jti: str) -> None:
    """Add token JTI to revocation list"""
    # Store in Redis or database
    from api.common import get_supa
    supa = get_supa()
    supa.table("token_revocations").insert({
        "jti": jti,
        "revoked_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    logger.info(f"Token {jti} revoked")
```

**Step 3: Update Login Endpoint**
```python
# /workspace/api/v1/admin/login.py
from api.security.tokens import generate_access_token, generate_refresh_token

@app.post("/api/v1/admin/login")
async def admin_login(payload: dict = Body(...), supa: Client = Depends(get_supa)):
    """Admin login with token generation"""
    email = payload.get("email")
    totp = payload.get("totp")
    
    # Verify TOTP
    if not verify_admin_totp(totp):
        raise HTTPException(status_code=401, detail="TOTP inválido")
    
    # Get user
    user = supa.table("profiles").select("id, email").eq("email", email).single().execute()
    if not user.data:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    
    # Generate tokens
    access_token = generate_access_token(user.data["id"])
    refresh_token = generate_refresh_token(user.data["id"])
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 120 * 60  # seconds
    }

@app.post("/api/v1/admin/token/refresh")
async def refresh_access_token(refresh_token: str = Body(...)):
    """Refresh access token using refresh token"""
    from api.security.tokens import verify_token, generate_access_token
    
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        new_access_token = generate_access_token(user_id)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/v1/admin/logout")
async def admin_logout(token: str = Depends(HTTPBearer())):
    """Logout by revoking token"""
    from api.security.tokens import verify_token, revoke_token
    
    try:
        payload = verify_token(token.credentials)
        revoke_token(payload["jti"])
        return {"message": "Logout realizado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
```

**Step 4: Update Environment**
```bash
# Add to .env
SESSION_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
# Or manually generate a strong key
```

**Effort**: 🕐 2-3 hours  
**Testing**:
- ✅ Login generates access + refresh tokens
- ✅ Access token valid for 2 hours
- ✅ Refresh token valid for 7 days
- ✅ Invalid tokens rejected
- ✅ Expired tokens rejected
- ✅ Token revocation works after logout

**Migration Path**:
1. Generate new SESSION_SECRET_KEY
2. Deploy token generation code
3. Update all endpoints to use new tokens
4. Deprecate old session token method
5. Clear old sessions from database

---

## 🟠 FASE 2: REMEDIAÇÃO ALTA PRIORIDADE (Semana 2-4)

### 2.1 **No Input Validation on API Endpoints**
**Severity**: 🟠 ALTO  
**Effort**: 🕐 4-6 hours  
**Timeline**: Week 2-3

#### Implementation

**Step 1: Create Validation Models**
```python
# /workspace/api/schemas/request.py
from pydantic import BaseModel, Field, validator
from typing import Optional
import uuid

class GetTargetsRequest(BaseModel):
    """Validation for GET /api/v1/targets"""
    limit: int = Field(default=50, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    org_id: Optional[str] = Field(default=None, description="Organization ID")
    
    @validator('org_id')
    def validate_org_id(cls, v):
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid organization ID format')
        return v

class FalsePositiveRequest(BaseModel):
    """Validation for marking false positives"""
    id: str = Field(..., description="Comment ID")
    reason: str = Field(..., min_length=10, max_length=500)
    
    @validator('id')
    def validate_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid comment ID')
        return v

class ReclassifyRequest(BaseModel):
    """Batch reclassification"""
    ids: list[str] = Field(..., min_items=1, max_items=1000)
    new_sentiment: str = Field(..., regex="^(POSITIVO|NEGATIVO|NEUTRO)$")
```

**Step 2: Apply to Endpoints**
```python
# /workspace/api/index.py
from api.schemas.request import GetTargetsRequest, FalsePositiveRequest

@app.get("/api/v1/targets")
async def get_targets(
    params: GetTargetsRequest = Depends(),
    supa: Client = Depends(get_supa)
):
    """Get targets with validated parameters"""
    offset = params.offset
    limit = params.limit
    
    query = supa.table('candidatos').select('*')
    
    if params.org_id:
        query = query.eq('organization_id', params.org_id)
    
    return {
        "data": query.range(offset, offset + limit - 1).execute().data,
        "pagination": {
            "offset": offset,
            "limit": limit
        }
    }

@app.post("/api/v1/comments/false-positive")
async def mark_false_positive(
    payload: FalsePositiveRequest,
    supa: Client = Depends(get_supa)
):
    """Mark comment as false positive (validated)"""
    supa.table('comentarios').update({
        'is_hate': False,
        'flagged_as_false_positive': True
    }).eq('id', payload.id).execute()
    
    return {"success": True}
```

**Validation Coverage Required**:
- [ ] All GET endpoints with query params
- [ ] All POST endpoints with body
- [ ] UUID format validation
- [ ] Enum validation (POSITIVO/NEGATIVO/NEUTRO)
- [ ] Range validation (limit, offset)
- [ ] String length validation
- [ ] Required field validation

---

### 2.2 **Missing Rate Limiting**
**Severity**: 🟠 ALTO  
**Effort**: 🕐 3-4 hours  
**Timeline**: Week 2

#### Implementation

**Step 1: Install Rate Limiting**
```bash
pip install slowapi redis
```

**Step 2: Configure Rate Limiter**
```python
# /workspace/api/config/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
import logging

logger = logging.getLogger("rate_limit")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",  # Or in-memory for development
    default_limits=["200/day", "50/hour"]
)

RATE_LIMITS = {
    "login": "5/minute",           # Strict for auth
    "classify": "1000/hour",       # Expensive operation
    "get_targets": "100/minute",   # Read endpoint
    "webhook": "unlimited"         # Webhooks have own verification
}

def add_rate_limit_handlers(app: FastAPI):
    """Add rate limit exception handlers"""
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        logger.warning(f"Rate limit exceeded for {request.client.host}: {exc.detail}")
        return {
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please try again later."
        }
```

**Step 3: Apply to Endpoints**
```python
# /workspace/api/index.py
from api.config.rate_limit import limiter, RATE_LIMITS

@app.get("/api/v1/targets")
@limiter.limit(RATE_LIMITS["get_targets"])
async def get_targets(request: Request, supa: Client = Depends(get_supa)):
    ...

@app.post("/api/v1/admin/login")
@limiter.limit(RATE_LIMITS["login"])
async def admin_login(request: Request, payload: dict = Body(...)):
    ...

@app.post("/api/v1/classify")
@limiter.limit(RATE_LIMITS["classify"])
async def classify_text(request: Request, payload: dict = Body(...)):
    ...
```

---

### 2.3 **Sensitive Data Exposure in Error Messages**
**Severity**: 🟠 ALTO  
**Effort**: 🕐 2-3 hours  
**Timeline**: Week 1-2

#### Implementation

**Step 1: Create Error Handler Module**
```python
# /workspace/api/errors/handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger("api.errors")

class APIError(Exception):
    """Custom API error with safe message"""
    def __init__(self, status_code: int, message: str, error_code: str = None):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code

def setup_error_handlers(app: FastAPI):
    """Setup global error handlers"""
    
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """Catch all other exceptions"""
        # Log full error details for debugging
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}",
            exc_info=True,
            extra={
                "path": str(request.url),
                "method": request.method,
                "client": request.client.host
            }
        )
        
        # Return generic error to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "An internal error occurred. Please contact support.",
                "error_code": "INTERNAL_ERROR"
            }
        )
```

**Step 2: Update All Endpoints**
```python
# /workspace/api/index.py - Remove direct error exposure

# BEFORE (❌ Bad)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

# AFTER (✅ Good)
except ValueError as e:
    logger.warning(f"Validation error: {e}")
    raise APIError(400, "Invalid input provided", "VALIDATION_ERROR")
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    raise APIError(500, "Failed to process request", "DATABASE_ERROR")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise APIError(500, "An internal error occurred", "INTERNAL_ERROR")
```

---

### 2.4 **Stripe Webhook Idempotency**
**Severity**: 🟠 ALTO  
**Effort**: 🕐 2 hours  
**Timeline**: Week 2

#### Implementation

**Step 1: Create Webhook Idempotency Table**
```sql
-- migrations/add_webhook_idempotency.sql
CREATE TABLE stripe_webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id TEXT NOT NULL UNIQUE,
  event_type TEXT NOT NULL,
  processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  status ENUM('PENDING', 'PROCESSED', 'FAILED') DEFAULT 'PENDING',
  
  INDEX idx_webhook_id (webhook_id),
  INDEX idx_event_type (event_type),
  INDEX idx_processed_at (processed_at)
);

CREATE TABLE webhook_retries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id TEXT NOT NULL,
  attempt_number INT NOT NULL,
  error_message TEXT,
  retry_at TIMESTAMP,
  
  FOREIGN KEY (webhook_id) REFERENCES stripe_webhooks(webhook_id)
);
```

**Step 2: Update Webhook Handler**
```python
# /workspace/api/index.py - Stripe webhook
@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request, supa: Client = Depends(get_supa)):
    """Process Stripe webhook with idempotency"""
    
    # Get and verify signature
    sig_header = request.headers.get("stripe-signature")
    body = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    webhook_id = event.get('id')
    
    # Check if already processed
    existing = supa.table('stripe_webhooks')\
        .select('id, status')\
        .eq('webhook_id', webhook_id)\
        .single()\
        .execute()
    
    if existing.data:
        if existing.data['status'] == 'PROCESSED':
            logger.info(f"Webhook {webhook_id} already processed, returning")
            return {"status": "already_processed"}
        elif existing.data['status'] == 'FAILED':
            logger.warning(f"Webhook {webhook_id} previously failed, retrying")
    else:
        # Create webhook record
        supa.table('stripe_webhooks').insert({
            'webhook_id': webhook_id,
            'event_type': event['type'],
            'status': 'PENDING'
        }).execute()
    
    # Process webhook
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            if session.get('payment_status') == 'paid':
                # Process payment
                process_payment(session, supa)
        
        # Mark as processed
        supa.table('stripe_webhooks')\
            .update({'status': 'PROCESSED'})\
            .eq('webhook_id', webhook_id)\
            .execute()
        
        logger.info(f"Webhook {webhook_id} processed successfully")
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Webhook {webhook_id} processing failed: {e}", exc_info=True)
        supa.table('stripe_webhooks')\
            .update({'status': 'FAILED'})\
            .eq('webhook_id', webhook_id)\
            .execute()
        return {"status": "error", "detail": str(e)}
```

---

## 🟡 FASE 3: REMEDIAÇÃO MÉDIA PRIORIDADE (Semana 4-8)

### 3.1 **HTTPS Enforcement & Security Headers**
**Severity**: 🟡 MÉDIO  
**Effort**: 🕐 1-2 hours  
**Timeline**: Week 3-4

```python
# /workspace/api/middleware/security.py
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def add_security_middleware(app: FastAPI):
    """Add HTTPS and security headers"""
    
    # Redirect HTTP to HTTPS
    if not os.getenv("DEBUG"):
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trust proxy headers
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("TRUSTED_HOSTS", "").split(",")
    )
    
    # Add security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
```

---

### 3.2 **Implement Comprehensive Logging**
**Severity**: 🟡 MÉDIO  
**Effort**: 🕐 3-4 hours  
**Timeline**: Week 4-5

```python
# /workspace/api/logging/security_logger.py
import logging
import json
from datetime import datetime

security_logger = logging.getLogger("security")

class SecurityEventLogger:
    """Log security-related events for audit trail"""
    
    @staticmethod
    def log_auth_attempt(username: str, success: bool, ip: str, reason: str = None):
        event = {
            "type": "AUTH_ATTEMPT",
            "username": username,
            "success": success,
            "ip": ip,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.info(json.dumps(event))
    
    @staticmethod
    def log_unauthorized_access(user_id: str, resource: str, ip: str):
        event = {
            "type": "UNAUTHORIZED_ACCESS",
            "user_id": user_id,
            "resource": resource,
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.warning(json.dumps(event))
    
    @staticmethod
    def log_rate_limit_exceeded(ip: str, endpoint: str):
        event = {
            "type": "RATE_LIMIT_EXCEEDED",
            "ip": ip,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.warning(json.dumps(event))
```

---

### 3.3 **Content Security Policy**
**Severity**: 🟡 MÉDIO  
**Effort**: 🕐 1 hour  
**Timeline**: Week 3

```python
# /workspace/api/middleware/security.py
@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://api.supabase.co; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response
```

---

## 🎯 FASE 4: MELHORIAS DE ARQUITETURA (Semana 6-12)

### 4.1 **Database Query Optimization & Caching**
**Severity**: 💡 IMPROVEMENT  
**Effort**: 🕐 8-12 hours  
**Timeline**: Week 6-8

#### Implementation

```python
# /workspace/core/cache.py
from redis import Redis
from functools import wraps
import json
import hashlib

redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_result(expire_seconds: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__module__}.{func.__name__}:{hashlib.md5(str((args, kwargs)).encode()).hexdigest()}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, expire_seconds, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(expire_seconds=600)
async def get_active_targets(org_id: str = None):
    supa = get_supa()
    return supa.table('candidatos')\
        .select('*')\
        .filter('status_monitoramento', 'eq', 'Ativo')\
        .execute().data
```

#### Database Indexes to Create

```sql
-- Critical indexes for performance
CREATE INDEX idx_candidatos_status_org ON candidatos(status_monitoramento, organization_id);
CREATE INDEX idx_candidatos_termometro ON candidatos(termometro);
CREATE INDEX idx_comentarios_candidato_sentiment ON comentarios(candidato_id, sentimento);
CREATE INDEX idx_comentarios_is_hate ON comentarios(is_hate) WHERE is_hate = TRUE;
CREATE INDEX idx_fila_coleta_status_priority ON fila_coleta(status, prioridade);
CREATE INDEX idx_ci_transactions_profile_date ON ci_transactions(de_profile_id, created_at DESC);

-- Partial indexes for common queries
CREATE INDEX idx_comentarios_unclassified ON comentarios(candidato_id) WHERE sentimento IS NULL;
CREATE INDEX idx_fila_coleta_pending ON fila_coleta(prioridade) WHERE status = 'PENDENTE';
```

---

### 4.2 **Add Comprehensive Test Coverage**
**Severity**: 💡 IMPROVEMENT  
**Effort**: 🕐 16-20 hours  
**Timeline**: Week 7-10

#### Test Structure

```python
# tests/test_api_security.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from api.index import app
    return TestClient(app)

class TestAPISecurity:
    def test_cors_not_wildcard(self, client):
        """Verify CORS is not set to wildcard"""
        ...
    
    def test_admin_requires_auth(self, client):
        """Admin endpoints require authentication"""
        response = client.get("/api/v1/admin/finance/dashboard")
        assert response.status_code == 401
    
    def test_rate_limiting(self, client):
        """Rate limiting is enforced"""
        for i in range(101):
            response = client.get("/api/v1/summary")
            if i < 100:
                assert response.status_code == 200
            else:
                assert response.status_code == 429

# tests/test_security_headers.py
def test_https_redirect_header(client):
    """HSTS header is present"""
    response = client.get("/api/v1/summary")
    assert "Strict-Transport-Security" in response.headers

def test_csp_header(client):
    """CSP header is configured"""
    response = client.get("/api/v1/summary")
    assert "Content-Security-Policy" in response.headers
```

---

## 📅 Timeline Realista

```
SEMANA 1
├─ 🔴 CORS Wildcard Fix              [8h]  ✅ CRITICAL
├─ 🔴 Admin Auth Implementation      [8h]  ✅ CRITICAL
└─ 🔴 Session Token Redesign         [10h] ✅ CRITICAL
   Subtotal: 26h (~1 dev + 1 senior dev)

SEMANA 2
├─ 🟠 Input Validation Framework     [6h]  ✅ HIGH
├─ 🟠 Rate Limiting Implementation   [4h]  ✅ HIGH
└─ 🟠 Error Handler Refactor         [3h]  ✅ HIGH
   Subtotal: 13h

SEMANA 3
├─ 🟠 Stripe Webhook Idempotency    [3h]  ✅ HIGH
├─ 🟠 Database Injection Fix         [2h]  ✅ HIGH
├─ 🟡 HTTPS Enforcement             [2h]  ✅ MEDIUM
└─ 🟡 Security Headers              [2h]  ✅ MEDIUM
   Subtotal: 9h

SEMANA 4-5
├─ 🟡 Comprehensive Logging         [5h]  ✅ MEDIUM
├─ 🟡 CSP Headers                   [2h]  ✅ MEDIUM
└─ 🟡 Request Size Limits           [2h]  ✅ MEDIUM
   Subtotal: 9h

SEMANA 6-8
├─ 💡 Database Optimization         [12h] ✅ IMPROVEMENT
├─ 💡 Caching Layer (Redis)         [8h]  ✅ IMPROVEMENT
└─ 💡 Query Optimization            [8h]  ✅ IMPROVEMENT
   Subtotal: 28h

SEMANA 9-10
├─ 💡 Test Coverage                 [20h] ✅ IMPROVEMENT
└─ 💡 Documentation Updates         [8h]  ✅ IMPROVEMENT
   Subtotal: 28h

TOTAL: ~113 dev hours = ~3-4 weeks (2 devs) or ~2-3 months (1 dev)
```

---

## 👥 Recursos Necessários

### Equipe Recomendada
- **1 Senior Backend Dev** (lead) — 50% dedicação
- **1 Mid-level Backend Dev** — 100% dedicação
- **1 Security Specialist** — 20% dedicação (reviews)
- **1 QA Engineer** — 40% dedicação (testing)

### Ferramentas Necessárias
```bash
# Install security scanning tools
pip install safety bandit pip-audit
pip install pytest pytest-asyncio pytest-cov

# Install required dependencies
pip install PyJWT python-jose cryptography
pip install slowapi redis
pip install python-dotenv pydantic-settings

# IDE extensions
# - Security scanning plugins
# - Linting with pylint/flake8
# - Type checking with mypy
```

---

## ✅ Métricas de Sucesso

### Security Metrics
- ✅ CORS restricted to specific origins
- ✅ All admin endpoints authenticated
- ✅ No sensitive data in error messages
- ✅ HTTPS enforced
- ✅ Security headers present
- ✅ Rate limiting active
- ✅ Input validation on all endpoints

### Quality Metrics
- ✅ Test coverage >= 80%
- ✅ No CRITICAL vulnerabilities (0)
- ✅ HIGH vulnerabilities <= 2
- ✅ All bandit/safety scans pass
- ✅ Load test: 1000 req/sec without errors

### Performance Metrics
- ✅ P95 API latency < 200ms
- ✅ Database query avg < 100ms
- ✅ Cache hit rate > 60% for common queries
- ✅ Memory usage stable < 500MB

---

## 🚀 Deployment Strategy

### Phase 1: Pre-Production Testing (Week 1-3)
```bash
# Deploy to staging
git branch -b security-hardening
# Implement critical fixes
# Test thoroughly
# Get security review

# Staging deployment
docker build -t sentinela:hardened .
docker push myregistry.azurecr.io/sentinela:hardened
# Deploy to staging k8s
```

### Phase 2: Production Rollout (Week 4)
```bash
# Blue-Green Deployment
# 1. Keep current version running (Blue)
# 2. Deploy hardened version (Green)
# 3. Route 10% traffic to Green
# 4. Monitor for 24 hours
# 5. Route 50% traffic
# 6. Monitor for 24 hours
# 7. Route 100% traffic
# 8. Keep Blue running for quick rollback (7 days)
```

### Phase 3: Post-Deployment (Week 5+)
```bash
# Monitor security metrics
# Run periodic security audits
# Update dependencies monthly
# Conduct quarterly penetration testing
```

---

## 📋 Checklist de Implementação

### Semana 1
- [ ] Create CORS configuration module
- [ ] Update all endpoints with CORS config
- [ ] Implement admin authentication middleware
- [ ] Create JWT token generation module
- [ ] Update login/logout endpoints
- [ ] Deploy to staging
- [ ] Test with staging frontend
- [ ] Code review + security review

### Semana 2
- [ ] Create input validation schemas
- [ ] Apply validation to all endpoints
- [ ] Implement rate limiting
- [ ] Configure Redis for rate limits
- [ ] Update error handlers
- [ ] Remove sensitive data from logs
- [ ] Deploy to staging
- [ ] Load test rate limiting

### Semana 3
- [ ] Add webhook idempotency
- [ ] Create webhook_retries table
- [ ] Fix database query injection
- [ ] Add HTTPS enforcement
- [ ] Add security headers
- [ ] Deploy to staging
- [ ] Security scan with bandit/safety

### Semana 4+
- [ ] Setup database optimization indexes
- [ ] Implement Redis caching
- [ ] Create comprehensive tests
- [ ] Deploy to production (blue-green)
- [ ] Monitor security metrics
- [ ] Run penetration testing

---

## 🔄 Continuous Improvement

### Monthly Tasks
```bash
# Update dependencies
pip list --outdated
pip install --upgrade [packages]

# Security scanning
bandit -r /workspace/api /workspace/core
safety check
pip-audit

# Run tests
pytest --cov=. --cov-report=html
# Target: 80%+ coverage

# Performance profiling
# Identify slow endpoints
# Optimize top-5 slowest queries
```

### Quarterly Tasks
- [ ] Penetration testing (external)
- [ ] Security audit (internal)
- [ ] Dependency vulnerability scan
- [ ] Architecture review
- [ ] Update documentation

---

## 📞 Contato & Escalation

- **Security Issues**: security@sentinela.ai
- **Urgent Issues**: Slack #security-incidents
- **Code Review**: Submit PR with label `security`
- **Questions**: Refer to docs/SECURITY_REMEDIATION_PLAN.md

---

## Conclusão

Este plano é **realista, prático e focado em resultados**. Com dedicação de 2-3 devs por 4 semanas, você terá uma plataforma **production-ready e secure**.

**Próximo passo**: Começar Fase 1 (Semana 1) imediatamente com as vulnerabilidades críticas.

