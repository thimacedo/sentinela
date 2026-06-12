"""
DOM Healing — Cura Autônoma de Seletores via IA de Visão
==========================================================
Substitui o HITL (Human-In-The-Loop) atual do instagram_scraper_v2.py
por chamadas ao modelo de visão (Gemini Flash), mantendo o HITL como
fallback em caso de falha da IA.

Fluxo Atual (instagram_scraper_v2.py, linhas 463-823):
    1. Detecta 3 posts consecutivos vazios
    2. Dispara _request_human_intervention()
    3. Abre Chromium headless=False com overlay para clique humano
    4. Salva seletor aprendido em configs/learned_selectors.json
    5. Relê o seletor no próximo ciclo

Fluxo Proposto (DOM Healing Autônomo):
    1. Detecta 3 posts consecutivos vazios (GATING INALTERADO)
    2. Tira screenshot via Playwright (já disponível)
    3. Extrai fragmento HTML da viewport
    4. Chama ai_service.vision_completion() com screenshot + HTML
    5. Recebe seletor CSS inferido pela IA
    6. Valida seletor (não vazio, sintaxe CSS válida)
    7. Persiste em configs/learned_selectors.json
    8. Aplica no scraper em tempo real
    9. Se falhar: fallback para HITL existente

GATING CRÍTICO: O DOM Healing é disparado SOMENTE após confirmar
falha de seletor (3 posts vazios consecutivos), nunca preventivamente.
Isto preserva o custo de tokens de visão apenas para quando necessário.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from typing import Any, Optional

logger = logging.getLogger("agent_scraper.dom_healing")


# ---------------------------------------------------------------------------
# Validação de Seletor CSS
# ---------------------------------------------------------------------------

def validate_css_selector(selector: str) -> bool:
    """
    Validação robusta de seletor CSS retornado pela IA.

    Critérios:
        - Não vazio
        - Não contém JavaScript (on*, javascript:)
        - Apenas caracteres válidos em seletores CSS (proíbe acentuação comum em português)
        - Sem frases longas (no máximo 5 termos separados por espaço)
        - Comprimento razoável (1-200 chars)
    """
    if not selector or len(selector) < 1 or len(selector) > 200:
        return False

    # Bloqueia JavaScript inline
    js_patterns = [r"on\w+\s*=", r"javascript:", r"<script", r"eval\("]
    for pattern in js_patterns:
        if re.search(pattern, selector, re.IGNORECASE):
            return False

    # Apenas caracteres válidos em CSS
    # Não permite acentuação comum (á, é, í, ó, ú, ç, ã, õ), comum em explicações textuais da IA
    allowed_pattern = re.compile(r"^[a-zA-Z0-9.\#\[\]:>\+,\~\*\s\-\_\(\)\'\=\^\$\|\"]+$")
    if not allowed_pattern.match(selector):
        return False

    # Evita que frases longas que contêm apenas caracteres válidos passem (ex: "Could not find comments container")
    if len(selector.split()) > 5:
        return False

    # Verifica se parece um seletor CSS válido (heurística)
    # Seletor CSS geralmente contém: ., #, >, +, [, :, div, span, etc.
    css_chars = set(".#[]:>+,~*")
    has_css_char = any(c in css_chars for c in selector)
    is_simple_tag = selector.isalpha() and selector.islower()

    return has_css_char or is_simple_tag


def extract_selector_from_response(response: str) -> str:
    """
    Extrai seletor CSS da resposta do modelo de visão.

    A IA pode retornar o seletor em vários formatos:
        - Seletor puro: "div.x5yr21d"
        - Com aspas: '"div.x5yr21d"'
        - Com explicação: "O seletor é: div.x5yr21d"
        - Em bloco de código: `div.x5yr21d`

    Esta função extrai apenas o seletor CSS válido.
    """
    # Remove blocos de código markdown
    response = re.sub(r"```[\w]*\n?", "", response)
    response = response.strip()

    # Se a resposta é curta e parece um seletor, usa diretamente
    if len(response) <= 100 and validate_css_selector(response):
        return response.strip("`'\" \n")

    # Tenta extrair de frases como "O seletor é: div.x5yr21d"
    patterns = [
        r"(?:seletor|selector|css)[:\s]+[`'\"]?([a-zA-Z.#\[\]:>+,~\s_*-]+)[`'\"]?",
        r"^[`'\"]?([a-zA-Z.#\[\]:>+,~\s_*-]+)[`'\"]?$",
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            if validate_css_selector(candidate):
                return candidate

    # Fallback: usa a primeira linha se parecer um seletor
    first_line = response.split("\n")[0].strip().strip("`'\"")
    if validate_css_selector(first_line):
        return first_line

    # Último recurso: retorna a resposta limpa (pode ser inválido)
    return response.strip("`'\" \n")


# ---------------------------------------------------------------------------
# DOM Healing Core
# ---------------------------------------------------------------------------

class DOMHealer:
    """
    Cura autônoma de seletores DOM via IA de visão.

    Integração com instagram_scraper_v2.py:
        - Substitui _request_human_intervention() por heal_selectors()
        - Preserva o gating de 3 posts vazios consecutivos
        - Fallback automático para HITL se a visão falhar
    """

    # Seletores que podem ser curados
    HEALABLE_SELECTORS = [
        "comment_container",
        "post_container",
        "comment_item",
        "load_more_button",
        "expand_replies_button",
    ]

    def __init__(
        self,
        ai_service: Any = None,
        config_path: str | None = None,
    ):
        self._ai_service = ai_service
        self._config_path = config_path or os.path.join(
            os.getenv("PROJECT_ROOT", os.getcwd()),
            "configs",
            "learned_selectors.json",
        )
        self._healing_stats = {
            "total_heals": 0,
            "successful_heals": 0,
            "fallback_to_hitl": 0,
            "vision_failures": 0,
        }

    @property
    def stats(self) -> dict:
        return self._healing_stats

    # -----------------------------------------------------------------------
    # Cura Principal
    # -----------------------------------------------------------------------

    async def heal_selectors(
        self,
        page: Any,  # Playwright Page object
        selector_name: str = "comment_container",
        screenshot_b64: str | None = None,
        html_snippet: str | None = None,
        cache_key: str | None = None,
    ) -> dict:
        """
        Executa o fluxo completo de cura de seletores DOM.

        Args:
            page: Objeto Playwright Page para capturar screenshot/HTML
            selector_name: Nome do seletor a curar
            screenshot_b64: Screenshot pré-capturado (ou None para capturar)
            html_snippet: HTML pré-extraído (ou None para extrair)
            cache_key: Chave de cache (ex: shortcode do post)

        Returns:
            {
                "success": bool,
                "selector": str | None,
                "source": "vision" | "cache" | "hitl_fallback",
                "error": str | None,
            }
        """
        self._healing_stats["total_heals"] += 1

        try:
            # --- 1. Captura de Screenshot e HTML ---
            if not screenshot_b64:
                screenshot_b64 = await self._capture_screenshot(page)

            if not html_snippet:
                html_snippet = await self._extract_html_snippet(page)

            if not screenshot_b64 or not html_snippet:
                logger.warning("[dom_healing] Falha ao capturar screenshot/HTML — ativando HITL fallback")
                self._healing_stats["fallback_to_hitl"] += 1
                return {
                    "success": False,
                    "selector": None,
                    "source": "hitl_fallback",
                    "error": "Falha na captura de screenshot ou HTML",
                }

            # --- 2. Chamada de Visão ---
            result = await self._vision_heal(
                screenshot_b64=screenshot_b64,
                html_snippet=html_snippet,
                selector_name=selector_name,
                cache_key=cache_key,
            )

            if result["success"]:
                self._healing_stats["successful_heals"] += 1
                return result

            # --- 3. Fallback HITL ---
            logger.warning(f"[dom_healing] Visão falhou: {result.get('error')} — ativando HITL fallback")
            self._healing_stats["fallback_to_hitl"] += 1
            return {
                "success": False,
                "selector": None,
                "source": "hitl_fallback",
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"[dom_healing] Erro durante cura: {e}", exc_info=True)
            self._healing_stats["fallback_to_hitl"] += 1
            return {
                "success": False,
                "selector": None,
                "source": "hitl_fallback",
                "error": str(e),
            }

    async def _vision_heal(
        self,
        screenshot_b64: str,
        html_snippet: str,
        selector_name: str,
        cache_key: str | None = None,
    ) -> dict:
        """
        Executa a cura via IA de visão.

        Returns:
            {"success": bool, "selector": str|None, "source": "vision"|"cache", "error": str|None}
        """
        if not self._ai_service:
            return {
                "success": False,
                "selector": None,
                "source": "vision",
                "error": "ai_service não disponível",
            }

        # Prompt otimizado para resposta determinística de seletor
        vision_prompt = (
            f"Identifique o container CSS de '{selector_name}' do post exibido "
            f"nesta captura de tela baseado no fragmento HTML fornecido abaixo. "
            f"Responda APENAS com o seletor CSS válido, sem explicação adicional.\n\n"
            f"Fragmento HTML:\n{html_snippet[:3000]}"
        )

        result = await self._ai_service.vision_completion(
            image_b64=screenshot_b64,
            prompt=vision_prompt,
            cache_key=cache_key,
        )

        if not result.get("success"):
            self._healing_stats["vision_failures"] += 1
            return {
                "success": False,
                "selector": None,
                "source": "vision",
                "error": f"Visão falhou: {result.get('error', 'desconhecido')}",
            }

        # Extrai e valida seletor da resposta
        raw_content = result.get("content", "")
        selector = extract_selector_from_response(raw_content)

        if not validate_css_selector(selector):
            self._healing_stats["vision_failures"] += 1
            return {
                "success": False,
                "selector": None,
                "source": "vision",
                "error": f"Seletor inválido retornado pela IA: '{selector}'",
            }

        # Persiste seletor aprendido
        await self._save_learned_selector(selector_name, selector)

        source = "cache" if result.get("cached") else "vision"
        logger.info(
            f"[dom_healing] Cura bem-sucedida: {selector_name} = {selector} "
            f"(source={source}, provider={result.get('provider')})"
        )

        return {
            "success": True,
            "selector": selector,
            "source": source,
            "error": None,
        }

    # -----------------------------------------------------------------------
    # Captura e Extração
    # -----------------------------------------------------------------------

    async def _capture_screenshot(self, page: Any) -> str:
        """
        Captura screenshot via Playwright e retorna em base64.

        Usa full_page=False para capturar apenas a viewport visível,
        reduzindo o tamanho da imagem e o custo de tokens.
        """
        try:
            screenshot_bytes = await page.screenshot(
                full_page=False,
                type="png",
            )
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"[dom_healing] Falha ao capturar screenshot: {e}")
            return ""

    async def _extract_html_snippet(self, page: Any) -> str:
        """
        Extrai fragmento HTML minimalista da área de conteúdo.

        Foco na área de comentários para reduzir tamanho do payload
        e melhorar a precisão da IA de visão.
        """
        try:
            # Tenta extrair da área de comentários primeiro
            html = await page.evaluate("""
                () => {
                    // Tenta encontrar a área de comentários
                    const commentAreas = document.querySelectorAll(
                        'main article, [role="main"], main'
                    );
                    if (commentAreas.length > 0) {
                        return commentAreas[0].innerHTML.substring(0, 5000);
                    }
                    // Fallback: body resumido
                    return document.body.innerHTML.substring(0, 5000);
                }
            """)
            return str(html)[:5000]
        except Exception as e:
            logger.error(f"[dom_healing] Falha ao extrair HTML: {e}")
            return ""

    # -----------------------------------------------------------------------
    # Persistência de Seletor Aprendido
    # -----------------------------------------------------------------------

    async def _save_learned_selector(self, selector_name: str, css_path: str) -> bool:
        """
        Persiste seletor aprendido em configs/learned_selectors.json.

        Formato idêntico ao existente no instagram_scraper_v2.py.
        """
        try:
            existing = {}
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            existing[selector_name] = css_path

            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            logger.info(f"[dom_healing] Seletor aprendido salvo: {selector_name} = {css_path}")
            return True

        except Exception as e:
            logger.error(f"[dom_healing] Erro ao salvar seletor: {e}")
            return False

    def load_learned_selectors(self) -> dict[str, str]:
        """
        Carrega seletores aprendidos do arquivo de configuração.

        Usado pelo scraper no início de cada ciclo para ler
        seletores que foram curados em ciclos anteriores.
        """
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[dom_healing] Erro ao carregar seletores: {e}")
        return {}

    # -----------------------------------------------------------------------
    # HITL Fallback
    # -----------------------------------------------------------------------

    async def hitl_fallback(
        self,
        page: Any,
        selector_name: str = "comment_container",
    ) -> dict:
        """
        Fallback para HITL (Human-In-The-Loop) quando a visão falha.

        Esta é a implementação existente do instagram_scraper_v2.py
        (linhas 463-823), preservada integralmente como fallback.

        O método _request_human_intervention() do scraper original
        deve ser chamado diretamente quando o DOM Healing falha.

        Returns:
            {"success": bool, "selector": str|None, "source": "hitl"}
        """
        logger.warning(
            f"[dom_healing] HITL fallback ativado para seletor: {selector_name}. "
            "Operador deve clicar manualmente no elemento correto."
        )
        # O HITL real é implementado no instagram_scraper_v2.py
        # Este método apenas registra a ativação do fallback
        return {
            "success": False,
            "selector": None,
            "source": "hitl",
            "error": "HITL fallback — requer intervenção humana",
        }
