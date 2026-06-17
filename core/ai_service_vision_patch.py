"""
Patch Cirúrgico: Extensão de Visão para o ai_service
=====================================================
Adiciona o método `vision_completion()` ao ai_service existente,
permitindo chamadas multimodais (imagem + texto) para DOM Healing.

PRÉ-REQUISITO BLOQUEADOR — Deve ser integrado ao core/ai_service.py
antes de qualquer componente do ScrapeAgent.

Roteamento: Exclusivamente para provedores com suporte a visão
(Gemini Flash). Maritaca/Ollama/Mistral não são usados aqui.

Uso:
    from core.ai_service import ai_service
    result = await ai_service.vision_completion(
        image_b64="iVBORw0KGgo...",
        prompt="Identifique o container CSS de comentários...",
    )
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("core.ai_service.vision")

# ---------------------------------------------------------------------------
# Constantes de Roteamento de Visão
# ---------------------------------------------------------------------------
# Apenas provedores com suporte nativo a multimodalidade são elegíveis.
# Ordem de preferência: Gemini Flash (mais rápido/barato) > Claude 3.5 Sonnet > outros.
VISION_PROVIDERS_PRIORITY = [
    "gemini-2.5-flash",
    "gemini-flash",
    "claude-3-5-sonnet",
    "gemini",
]

# Cache de sessão para evitar chamadas repetidas ao mesmo shortcode
_vision_cache: dict[str, dict[str, Any]] = {}
_VISION_CACHE_TTL = 300  # 5 minutos


def _select_vision_provider(providers: list[dict]) -> Optional[dict]:
    """
    Seleciona o provedor de visão elegível com base na prioridade
    e no estado do circuit breaker.

    Args:
        providers: Lista de provedores do ai_service (formato: [{"name": ..., "cooldown_until": ...}])

    Returns:
        Provedor elegível ou None se nenhum estiver disponível.
    """
    now = time.time()

    # Constrói mapa de provedores ativos (não em cooldown, não removidos)
    available = {}
    for p in providers:
        name = p.get("name", "")
        cooldown = p.get("cooldown_until", 0)
        if cooldown > now:
            continue  # Em cooldown, pular
        available[name] = p

    # Tenta na ordem de prioridade
    for preferred_name in VISION_PROVIDERS_PRIORITY:
        if preferred_name in available:
            logger.info(f"[vision] Provedor selecionado: {preferred_name}")
            return available[preferred_name]

    logger.warning("[vision] Nenhum provedor de visão disponível.")
    return None


def _build_gemini_vision_payload(
    image_b64: str,
    prompt: str,
    mime_type: str = "image/png",
) -> dict:
    """
    Constrói o payload no formato Gemini API para chamada multimodal.
    """
    return {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,  # Baixa temperatura para respostas determinísticas
            "maxOutputTokens": 256,  # Seletor CSS é curto
            "topP": 0.8,
        },
    }

def _build_claude_vision_payload(
    image_b64: str,
    prompt: str,
    mime_type: str = "image/png",
) -> dict:
    """
    Constrói o payload no formato Anthropic API (Messages) para chamada multimodal.
    """
    # Mapeia mime types se necessário. A API espera "image/jpeg", "image/png", "image/gif", or "image/webp"
    media_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/png"
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 256,
        "temperature": 0.1
    }


async def vision_completion(
    ai_service_instance: Any,
    image_b64: str,
    prompt: str,
    cache_key: Optional[str] = None,
    mime_type: str = "image/png",
) -> dict:
    """
    Método de extensão para chamadas multimodais (imagem + texto).

    Este método deve ser adicionado como método de instância na classe
    AIService em core/ai_service.py. A implementação aqui serve como
    spec funcional completa.

    Args:
        ai_service_instance: Instância do AIService (self)
        image_b64: Imagem codificada em base64 (screenshot)
        prompt: Instrução textual para o modelo de visão
        cache_key: Chave de cache (ex: shortcode do post). Se fornecida,
                   respostas são cacheadas por TTL para evitar chamadas repetidas.
        mime_type: MIME type da imagem (default: image/png)

    Returns:
        {"success": bool, "content": str, "provider": str, "cached": bool, "error": str|None}

    Comportamento:
        1. Verifica cache se cache_key fornecida
        2. Seleciona provedor de visão elegível (Gemini Flash preferencial)
        3. Constrói payload multimodal
        4. Faz chamada HTTP com timeout e retry
        5. Caches a resposta se cache_key fornecida
        6. Fallback: se visão falhar, retorna erro (não roteia para texto)
    """
    global _vision_cache

    if hasattr(ai_service_instance, "_ensure_clients"):
        ai_service_instance._ensure_clients()

    # --- 1. Verificação de Cache ---
    if cache_key:
        cached = _vision_cache.get(cache_key)
        if cached and (time.time() - cached.get("ts", 0)) < _VISION_CACHE_TTL:
            logger.info(f"[vision] Cache hit para chave: {cache_key}")
            return {
                "success": True,
                "content": cached["content"],
                "provider": cached["provider"],
                "cached": True,
                "error": None,
            }

    # --- 2. Seleção de Provedor ---
    provider = _select_vision_provider(ai_service_instance.providers)
    if not provider:
        return {
            "success": False,
            "content": "",
            "provider": "none",
            "cached": False,
            "error": "Nenhum provedor de visão disponível. Verifique GEMINI_API_KEY no .env",
        }

    provider_name = provider.get("name", "unknown")
    api_key = provider.get("api_key", "") or os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        return {
            "success": False,
            "content": "",
            "provider": provider_name,
            "cached": False,
            "error": f"API key não configurada para provedor de visão: {provider_name}",
        }

    # --- 3. Construção do Payload e 4. Chamada HTTP ---
    try:
        import httpx

        if "claude" in provider_name.lower():
            payload = _build_claude_vision_payload(image_b64, prompt, mime_type)
            api_key = provider.get("api_key", "") or os.getenv("ANTHROPIC_API_KEY", "")
            
            if not api_key:
                 return {
                    "success": False,
                    "content": "",
                    "provider": provider_name,
                    "cached": False,
                    "error": f"API key não configurada para provedor Claude: {provider_name}",
                 }
            
            url = "https://api.anthropic.com/v1/messages"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                )
        else:
            # Fallback natural (Gemini)
            payload = _build_gemini_vision_payload(image_b64, prompt, mime_type)
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/"
                f"models/{provider_name}:generateContent?key={api_key}"
            )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

        if response.status_code == 429:
            # Rate limit — aplica cooldown
            logger.warning(f"[vision] Rate limit no provedor {provider_name}")
            provider["cooldown_until"] = time.time() + 60
            return {
                "success": False,
                "content": "",
                "provider": provider_name,
                "cached": False,
                "error": f"Rate limit no provedor {provider_name}. Cooldown 60s.",
            }

        if response.status_code >= 400:
            error_detail = response.text[:500]
            logger.error(f"[vision] Erro HTTP {response.status_code}: {error_detail}")
            return {
                "success": False,
                "content": "",
                "provider": provider_name,
                "cached": False,
                "error": f"HTTP {response.status_code}: {error_detail}",
            }

        result = response.json()

        # Extrai conteúdo da resposta baseada no provedor
        if "claude" in provider_name.lower():
            if not result.get("content") or len(result["content"]) == 0:
                return {
                    "success": False,
                    "content": "",
                    "provider": provider_name,
                    "cached": False,
                    "error": "Resposta sem content do modelo de visão (Claude).",
                }
            content = result["content"][0].get("text", "")
        else:
            candidates = result.get("candidates", [])
            if not candidates:
                return {
                    "success": False,
                    "content": "",
                    "provider": provider_name,
                    "cached": False,
                    "error": "Resposta sem candidates do modelo de visão (Gemini).",
                }
            content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        if not content:
            return {
                "success": False,
                "content": "",
                "provider": provider_name,
                "cached": False,
                "error": "Conteúdo vazio na resposta do modelo de visão.",
            }

        # --- TELEMETRIA DE VISÃO (PASA v98.5) ---
        try:
            from core.supabase_service import get_supabase_client
            db = get_supabase_client()
            db.table("telemetry_events").insert({
                "event_type": "vision_resolved",
                "source_module": "ai_service_vision_patch",
                "provider_name": provider_name,
                "status": "success",
                "metadata": {
                    "is_fallback": provider_name != VISION_PROVIDERS_PRIORITY[0]
                }
            }).execute()
        except Exception as e:
            logger.error(f"[vision] Falha ao registrar telemetria: {e}")

        # --- 5. Cache da Resposta ---
        if cache_key:
            _vision_cache[cache_key] = {
                "content": content,
                "provider": provider_name,
                "ts": time.time(),
            }
            # Limpa entradas expiradas
            _vision_cache = {
                k: v for k, v in _vision_cache.items()
                if (time.time() - v.get("ts", 0)) < _VISION_CACHE_TTL
            }

        logger.info(f"[vision] Resposta recebida do provedor {provider_name} ({len(content)} chars)")
        return {
            "success": True,
            "content": content,
            "provider": provider_name,
            "cached": False,
            "error": None,
        }

    except httpx.TimeoutException:
        logger.error(f"[vision] Timeout na chamada ao provedor {provider_name}")
        return {
            "success": False,
            "content": "",
            "provider": provider_name,
            "cached": False,
            "error": f"Timeout (30s) na chamada ao provedor {provider_name}",
        }

    except Exception as e:
        logger.error(f"[vision] Erro inesperado: {e}", exc_info=True)
        return {
            "success": False,
            "content": "",
            "provider": provider_name,
            "cached": False,
            "error": f"Erro inesperado: {str(e)}",
        }


# ---------------------------------------------------------------------------
# Patch de Integração — Instruções para aplicar no ai_service.py
# ---------------------------------------------------------------------------
INTEGRATION_PATCH = """
# === PATCH: Adicionar à classe AIService em core/ai_service.py ===

async def vision_completion(self, image_b64: str, prompt: str,
                            cache_key: str | None = None,
                            mime_type: str = "image/png") -> dict:
    \"\"\"
    Chamada multimodal (imagem + texto) para modelos de visão.
    Roteia exclusivamente para provedores com suporte a visão (Gemini Flash).
    NÃO usa Maritaca/Ollama/Mistral.

    Args:
        image_b64: Imagem em base64 (screenshot)
        prompt: Instrução textual para o modelo
        cache_key: Chave de cache (ex: shortcode). Respostas cacheadas por 5 min.
        mime_type: MIME type da imagem

    Returns:
        {"success": bool, "content": str, "provider": str, "cached": bool, "error": str|None}
    \"\"\"
    from core.ai_service_vision_patch import vision_completion as _vision_impl
    return await _vision_impl(self, image_b64, prompt, cache_key, mime_type)
"""
