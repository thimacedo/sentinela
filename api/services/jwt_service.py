"""
JWT Token Service Module
Handles secure JWT token generation and validation.

Replaces weak token generation using SUPABASE_KEY as HMAC secret.
"""

import jwt
import secrets
from datetime import datetime, timedelta, timezone
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("sentinela-api")

# Token Configuration
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
JWT_ALGORITHM = "HS256"


def get_secret_key() -> str:
    """
    Get JWT secret key from environment.
    
    Returns:
        str: JWT secret key
        
    Raises:
        ValueError: If JWT_SECRET_KEY is not configured
    """
    secret = os.getenv("JWT_SECRET_KEY")
    
    if not secret:
        # Fallback to SUPABASE_KEY if JWT_SECRET_KEY not set
        secret = os.getenv("SUPABASE_KEY")
        if secret:
            logger.warning(
                "⚠️  WARNING: Using SUPABASE_KEY for JWT signing. "
                "Set JWT_SECRET_KEY environment variable for production!"
            )
    
    if not secret:
        raise ValueError("Neither JWT_SECRET_KEY nor SUPABASE_KEY is configured")
    
    return secret


def generate_access_token(user_id: str, additional_claims: Dict[str, Any] = None) -> str:
    """
    Generate a new access token.
    
    Args:
        user_id: The user's unique identifier
        additional_claims: Optional additional claims to include in the token
        
    Returns:
        str: Encoded JWT access token
        
    Example:
        token = generate_access_token("user-123", {"role": "admin"})
    """
    try:
        secret_key = get_secret_key()
        
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),  # JWT ID for revocation tracking
            "type": "access"
        }
        
        # Add additional claims if provided
        if additional_claims:
            to_encode.update(additional_claims)
        
        token = jwt.encode(
            to_encode,
            secret_key,
            algorithm=JWT_ALGORITHM
        )
        
        logger.debug(f"✅ Access token generated for user {user_id}")
        return token
        
    except Exception as e:
        logger.error(f"Error generating access token: {e}")
        raise


def generate_refresh_token(user_id: str) -> str:
    """
    Generate a new refresh token.
    
    Args:
        user_id: The user's unique identifier
        
    Returns:
        str: Encoded JWT refresh token
    """
    try:
        secret_key = get_secret_key()
        
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "type": "refresh"
        }
        
        token = jwt.encode(
            to_encode,
            secret_key,
            algorithm=JWT_ALGORITHM
        )
        
        logger.debug(f"✅ Refresh token generated for user {user_id}")
        return token
        
    except Exception as e:
        logger.error(f"Error generating refresh token: {e}")
        raise


def generate_token_pair(user_id: str, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
    """
    Generate both access and refresh tokens.
    
    Args:
        user_id: The user's unique identifier
        additional_claims: Optional additional claims for the access token
        
    Returns:
        Dict with 'access_token' and 'refresh_token' keys
        
    Example:
        tokens = generate_token_pair("user-123")
        # Returns: {"access_token": "...", "refresh_token": "..."}
    """
    return {
        "access_token": generate_access_token(user_id, additional_claims),
        "refresh_token": generate_refresh_token(user_id),
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Dict: Decoded token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        secret_key = get_secret_key()
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[JWT_ALGORITHM]
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: token expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: {e}")
        raise


def refresh_access_token(refresh_token: str, additional_claims: Dict[str, Any] = None) -> str:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to validate
        additional_claims: Optional additional claims for the new access token
        
    Returns:
        str: New access token
        
    Raises:
        jwt.InvalidTokenError: If refresh token is invalid
    """
    try:
        payload = verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type for refresh")
        
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing user ID")
        
        return generate_access_token(user_id, additional_claims)
        
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}")
        raise
