import hashlib
import hmac
import os
import time
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import Header, HTTPException

# SECURITY FIX: Fase 1 - Import new JWT service
try:
    from api.services.jwt_service import generate_token_pair, verify_token
except ImportError:
    from services.jwt_service import generate_token_pair, verify_token

load_dotenv()


SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SENTINELA_SUPABASE_KEY") or ""
TOTP_SECRET = os.getenv("SENTINELA_ADMIN_TOTP_SECRET") or ""
APP_ENV = os.getenv("APP_ENV", "development")
CORS_ORIGINS = [origin.strip() for origin in (os.getenv("CORS_ORIGINS") or "*").split(",") if origin.strip()]


def require_env(name: str, value: str) -> str:
    if value:
        return value
    raise HTTPException(status_code=500, detail=f"Variavel obrigatoria ausente: {name}")


def supabase_headers(prefer: Optional[str] = None) -> dict:
    key = require_env("SUPABASE_KEY", SUPABASE_KEY)
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


async def fetch_json(path: str, *, method: str = "GET", params: Optional[dict] = None, json: Optional[dict] = None,
                     prefer: Optional[str] = None, timeout: float = 20.0) -> tuple[object, httpx.Response]:
    base_url = require_env("SUPABASE_URL", SUPABASE_URL)
    url = f"{base_url}/rest/v1/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, url, params=params, json=json, headers=supabase_headers(prefer))
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    if response.content:
        return response.json(), response
    return None, response


def generate_session_token(user_id: str = None) -> str:
    """
    SECURITY FIX: Fase 1 - Generate secure JWT token instead of weak HMAC token.
    
    This replaces the insecure HMAC-based token generation that used SUPABASE_KEY
    as the secret. Now uses PyJWT with proper secret key management.
    
    Args:
        user_id: Optional user ID. If provided, returns full token pair.
        
    Returns:
        str: Access token (or access token from token pair if user_id provided)
    """
    if user_id:
        # Return only the access token for backwards compatibility
        tokens = generate_token_pair(user_id)
        return tokens["access_token"]
    
    # Fallback for backwards compatibility (no user_id provided)
    # This is deprecated and should not be used in new code
    import logging
    logger = logging.getLogger("sentinela-api")
    logger.warning("generate_session_token() called without user_id. Use generate_token_pair(user_id) instead.")
    
    # Old implementation as fallback (kept for backwards compatibility only)
    key = require_env("SUPABASE_KEY", SUPABASE_KEY)
    exp = int(time.time()) + (2 * 3600)
    payload = str(exp).encode()
    sig = hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def verify_session_token(token: Optional[str]) -> Optional[str]:
    """
    Verify JWT token and return user_id.
    
    SECURITY FIX: Fase 1 - Now properly validates JWT tokens with signature
    and expiration verification.
    
    Args:
        token: JWT token to verify
        
    Returns:
        str: User ID from token
        
    Raises:
        HTTPException: If token is invalid, expired, or missing
    """
    if not token:
        raise HTTPException(status_code=401, detail="Sessao ausente")
    
    try:
        # Try new JWT verification first
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido: user ID ausente")
        
        return user_id
        
    except Exception as e:
        # Fallback to old token format for backwards compatibility during migration
        try:
            exp_str, sig = token.split(".")
            key = require_env("SUPABASE_KEY", SUPABASE_KEY)
            expected_sig = hmac.new(key.encode(), exp_str.encode(), hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(sig, expected_sig):
                raise HTTPException(status_code=401, detail="Sessao invalida")
            
            if int(exp_str) < int(time.time()):
                raise HTTPException(status_code=401, detail="Sessao expirada")
            
            # Old token format - no user_id available
            return None
            
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Erro de autenticacao") from e


def get_admin_token(authorization: Optional[str] = Header(None)) -> str:
    token = authorization
    if token and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]
    verify_session_token(token)
    return token or ""


def sanitize_username(username: str) -> str:
    return (username or "").strip().replace("@", "").lower()


def safe_origin_list() -> list[str]:
    if CORS_ORIGINS == ["*"]:
        return ["*"]
    return CORS_ORIGINS
