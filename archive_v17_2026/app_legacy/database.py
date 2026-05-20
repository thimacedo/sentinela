"""
PASA v22 - Database Proxy
Encaminha as chamadas para o serviço centralizado do core.
"""
from core.supabase_service import supabase

# Apenas re-exporta o singleton do core
__all__ = ["supabase"]
