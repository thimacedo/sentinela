"""
CORS Configuration Module
Handles secure CORS settings based on environment variables.

This replaces the insecure wildcard CORS configuration that allows
any origin to make requests to the API.
"""

import os
from typing import List


def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins from environment variable.
    
    Returns:
        List[str]: List of allowed origins
        
    Environment Variables:
        CORS_ORIGINS: Comma-separated list of allowed origins
        
    Example:
        CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com,https://admin.yourdomain.com
    """
    origins_str = os.getenv("CORS_ORIGINS", "")
    
    if not origins_str:
        # Development fallback - only localhost
        return ["http://localhost:3000", "http://localhost:8000", "http://localhost:5173"]
    
    # Parse comma-separated origins and strip whitespace
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


# CORS Configuration Dictionary
CORS_CONFIG = {
    "allow_origins": get_cors_origins(),
    "allow_credentials": os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true",
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
    "max_age": int(os.getenv("CORS_MAX_AGE", "3600")),
    "expose_headers": ["X-Total-Count", "X-Page-Number"]  # For pagination headers
}


def validate_cors_config() -> None:
    """
    Validate CORS configuration on startup.
    Warns if running with development defaults in production.
    """
    import logging
    logger = logging.getLogger("sentinela-api")
    
    origins = get_cors_origins()
    
    # Check if using development defaults
    if set(origins) == {"http://localhost:3000", "http://localhost:8000", "http://localhost:5173"}:
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment in ["production", "prod"]:
            logger.warning(
                "⚠️  WARNING: Using development CORS origins in production! "
                "Set CORS_ORIGINS environment variable with production domains."
            )
    
    logger.info(f"✅ CORS Configuration loaded: {origins}")
