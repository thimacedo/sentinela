"""
Authentication Middleware Module
Handles JWT token verification and role-based access control.

This module provides middleware and decorators for protecting endpoints
that require authentication and specific user roles.
"""

import logging
from typing import Optional
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt
from datetime import datetime, timezone
import os

logger = logging.getLogger("sentinela-api")
security = HTTPBearer()


async def verify_admin_token(credentials: HTTPAuthCredentials) -> str:
    """
    Verify admin token and return user_id.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: Verified user_id
        
    Raises:
        HTTPException: If token is invalid or user doesn't have admin role
    """
    try:
        token = credentials.credentials
        
        # Verify token signature and expiration
        SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SUPABASE_KEY")
        if not SECRET_KEY:
            logger.error("JWT_SECRET_KEY not configured in environment")
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing user ID")
        
        token_type = payload.get("type", "access")
        if token_type != "access":
            raise ValueError("Invalid token type")
        
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError("Token expired")
        
        # Check if user has admin role in the database
        from api.common import get_supa
        supa = get_supa()
        
        try:
            profile = supa.table('profiles').select('role').eq('id', user_id).single().execute()
            
            if not profile.data or profile.data.get('role') not in ['ADMIN', 'SUPER_ADMIN']:
                logger.warning(f"Non-admin user {user_id} attempted admin access")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado: permissão de administrador requerida"
                )
            
            logger.info(f"✅ Admin access granted to user {user_id}")
            return user_id
            
        except Exception as db_error:
            logger.error(f"Database error checking admin role: {db_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao verificar permissões"
            )
        
    except jwt.ExpiredSignatureError:
        logger.warning("Admin token verification failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Admin token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    except Exception as e:
        logger.error(f"Unexpected error in token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao verificar autenticação"
        )


async def verify_user_token(credentials: Optional[HTTPAuthCredentials] = Depends(security)) -> str:
    """
    Verify user token and return user_id.
    
    Less strict than admin verification - any authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        str: Verified user_id
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        token = credentials.credentials
        
        SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SUPABASE_KEY")
        if not SECRET_KEY:
            raise HTTPException(status_code=500, detail="Server configuration error")
        
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing user ID")
        
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao verificar autenticação"
        )
