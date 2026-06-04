import os
import httpx
import pyotp
import logging
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# SECURITY FIX: Fase 1 - Import new JWT service and CORS config
from api.config.cors import CORS_CONFIG, validate_cors_config
from api.services.jwt_service import generate_token_pair

load_dotenv()

logger = logging.getLogger("sentinela-api")

app = FastAPI()

# SECURITY FIX: Fase 1 - Use secure CORS configuration
validate_cors_config()
app.add_middleware(
    CORSMiddleware,
    **CORS_CONFIG
)

TOTP_SECRET = os.getenv("SENTINELA_ADMIN_TOTP_SECRET")


@app.post("/api/v1/admin/login")
async def admin_login(payload: dict = Body(...)):
    """
    Admin login endpoint with TOTP verification.
    
    SECURITY FIX: Fase 1 - Now returns secure JWT tokens instead of weak HMAC tokens.
    
    Request:
        {
            "code": "123456"  # 6-digit TOTP code
        }
    
    Response:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "bearer",
            "expires_in": 3600
        }
    """
    code = payload.get("code")
    if not TOTP_SECRET:
        logger.error("Admin auth not configured - TOTP_SECRET missing")
        raise HTTPException(status_code=500, detail="Auth not configured")
    
    try:
        totp = pyotp.TOTP(TOTP_SECRET)
        if totp.verify(code):
            # SECURITY FIX: Use new JWT token generation
            # For admin login, we use a hardcoded admin user ID
            # In production, this should be replaced with actual user ID from database
            tokens = generate_token_pair(
                user_id="admin-user",
                additional_claims={"role": "ADMIN"}
            )
            
            logger.info("✅ Admin login successful")
            return tokens
        else:
            logger.warning(f"Failed admin login attempt with invalid TOTP code")
            raise HTTPException(status_code=401, detail="Código inválido")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during admin login: {e}")
        raise HTTPException(status_code=500, detail="Login error")
