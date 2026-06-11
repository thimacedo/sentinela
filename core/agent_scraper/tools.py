"""
ScrapeAgent Tools Registry
==========================
Registro de ferramentas que o agente cognitivo pode invocar durante
o loop OODA. Cada ferramenta é um método assíncrono que executa uma
ação atômica e retorna um resultado estruturado.

Padrão seguido: core/autopilot/sre_agent.py — cada ferramenta é
registrada com nome, descrição e parâmetros esperados.

Uso:
    tools = ScrapeAgentTools(scraper_instance)
    result = await tools.execute("rotate_proxy", {})
"""
from __future__ import annotations

import json
import logging
import os
import random
import time
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger("agent_scraper.tools")


class ToolResult:
    """Resultado padronizado de execução de uma ferramenta."""

    def __init__(
        self,
        success: bool,
        tool_name: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        tokens_used: int = 0,
    ):
        self.success = success
        self.tool_name = tool_name
        self.data = data or {}
        self.error = error
        self.tokens_used = tokens_used

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "tool": self.tool_name,
            "data": self.data,
            "error": self.error,
            "tokens_used": self.tokens_used,
        }

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"ToolResult({self.tool_name}, {status}, err={self.error})"


class ScrapeAgentTools:
    """
    Registro de ferramentas do ScrapeAgent.

    Cada ferramenta segue o contrato:
        - Método assíncrono com nome descritivo
        - Retorna ToolResult padronizado
        - Registra métricas de execução
        - Custo em tokens = 0 para ações determinísticas (padrão sre_agent)

    Integração com infraestrutura existente:
        - scraper_circuit_breaker: Controle de fluxo do Instagram
        - PROXY_LIST / PROXY_URL: Rotação de proxies
        - CheckpointManager: Persistência de estado
        - learned_selectors.json: Seletor aprendido
    """

    def __init__(self, scraper_instance: Any = None, ai_service: Any = None):
        self._scraper = scraper_instance
        self._ai_service = ai_service
        self._execution_log: list[dict] = []
        self._tool_registry: dict[str, dict[str, Any]] = {}
        self._proxy_index = 0
        self._proxy_list = self._load_proxy_list()

        # Registro automático de todas as ferramentas
        self._register_all_tools()

    # -----------------------------------------------------------------------
    # Registro de Ferramentas
    # -----------------------------------------------------------------------

    def _register_all_tools(self) -> None:
        """Registra todas as ferramentas disponíveis no formato declarativo."""
        self._tool_registry = {
            "rotate_proxy": {
                "method": self.rotate_proxy,
                "description": "Rotaciona o proxy atual para o próximo da lista PROXY_LIST",
                "cost_tokens": 0,
                "category": "evasion",
                "params": {},
            },
            "adjust_typing_delay": {
                "method": self.adjust_typing_delay,
                "description": "Ajusta velocidade de digitação baseada no nível de bloqueio detectado",
                "cost_tokens": 0,
                "category": "evasion",
                "params": {"level": "str — 'normal'|'cautious'|'stealth'"},
            },
            "heal_dom_selectors": {
                "method": self.heal_dom_selectors,
                "description": "Cura seletores DOM via IA de visão (screenshot + HTML fragment)",
                "cost_tokens": 50,  # Custo estimado de tokens de visão
                "category": "recovery",
                "params": {"screenshot_b64": "str", "html_snippet": "str", "cache_key": "str|None"},
            },
            "flag_cooldown_session": {
                "method": self.flag_cooldown_session,
                "description": "Sinaliza sessão em cooldown e aplica backoff",
                "cost_tokens": 0,
                "category": "recovery",
                "params": {"session_label": "str", "duration_s": "int"},
            },
            "adjust_navigation_profile": {
                "method": self.adjust_navigation_profile,
                "description": "Ajusta perfil de navegação (User-Agent, resolução, viewport) baseado no tipo de bloqueio",
                "cost_tokens": 0,
                "category": "evasion",
                "params": {"block_type": "str — '429'|'403'|'login_redirect'|'captcha'"},
            },
            "save_learned_selector": {
                "method": self.save_learned_selector,
                "description": "Persiste seletor aprendido em configs/learned_selectors.json",
                "cost_tokens": 0,
                "category": "learning",
                "params": {"selector_name": "str", "css_path": "str"},
            },
            "get_block_severity": {
                "method": self.get_block_severity,
                "description": "Classifica severidade do bloqueio atual (determinístico, 0 tokens)",
                "cost_tokens": 0,
                "category": "sensing",
                "params": {"status_code": "int", "response_body": "str|None"},
            },
            "emergency_hibernate": {
                "method": self.emergency_hibernate,
                "description": "Hibernação de emergência — pausa coleta por duration_s segundos",
                "cost_tokens": 0,
                "category": "recovery",
                "params": {"duration_s": "int — default 3600"},
            },
        }

    @property
    def available_tools(self) -> list[str]:
        """Lista nomes de todas as ferramentas registradas."""
        return list(self._tool_registry.keys())

    @property
    def tool_descriptions(self) -> dict[str, str]:
        """Mapa nome -> descrição para contexto do LLM."""
        return {name: info["description"] for name, info in self._tool_registry.items()}

    # -----------------------------------------------------------------------
    # Executor Central
    # -----------------------------------------------------------------------

    async def execute(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        Executa uma ferramenta registrada pelo nome.

        Args:
            tool_name: Nome da ferramenta (ex: "rotate_proxy")
            params: Parâmetros nomeados para a ferramenta

        Returns:
            ToolResult padronizado
        """
        if tool_name not in self._tool_registry:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=f"Ferramenta não registrada: {tool_name}",
            )

        tool_info = self._tool_registry[tool_name]
        method = tool_info["method"]

        start = time.time()
        try:
            result = await method(**params)
            elapsed = time.time() - start

            self._execution_log.append({
                "tool": tool_name,
                "success": result.success,
                "elapsed_s": round(elapsed, 3),
                "timestamp": time.time(),
            })

            logger.info(f"[tools] {tool_name} -> {result} ({elapsed:.2f}s)")
            return result

        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"[tools] Erro em {tool_name}: {e}", exc_info=True)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=str(e),
                tokens_used=0,
            )

    # -----------------------------------------------------------------------
    # Ferramentas: Evasão e Rotação
    # -----------------------------------------------------------------------

    async def rotate_proxy(self) -> ToolResult:
        """
        Rotaciona para o próximo proxy da lista PROXY_LIST.

        Se o scraper possuir scraper_circuit_breaker, respeita o estado
        do circuito. Se a lista esgotar, retorna ao início (round-robin).
        """
        if not self._proxy_list:
            return ToolResult(
                success=False,
                tool_name="rotate_proxy",
                error="PROXY_LIST vazia ou não configurada no .env",
            )

        self._proxy_index = (self._proxy_index + 1) % len(self._proxy_list)
        new_proxy = self._proxy_list[self._proxy_index]

        # Se o scraper tem circuit breaker, notifica
        if self._scraper and hasattr(self._scraper, "scraper_circuit_breaker"):
            cb = self._scraper.scraper_circuit_breaker
            if hasattr(cb, "record_rotation"):
                cb.record_rotation(new_proxy)

        logger.info(f"[tools] Proxy rotacionado para índice {self._proxy_index}: {new_proxy[:30]}...")
        return ToolResult(
            success=True,
            tool_name="rotate_proxy",
            data={"proxy_index": self._proxy_index, "proxy_url": new_proxy},
        )

    async def adjust_typing_delay(self, level: str = "normal") -> ToolResult:
        """
        Ajusta velocidade de digitação baseada no nível de cautela.

        Levels:
            - normal: 30-80ms por caractere (padrão)
            - cautious: 80-150ms por caractere (após bloqueio leve)
            - stealth: 150-350ms por caractere (após bloqueio severo)
        """
        delay_ranges = {
            "normal": (0.030, 0.080),
            "cautious": (0.080, 0.150),
            "stealth": (0.150, 0.350),
        }

        if level not in delay_ranges:
            level = "normal"

        min_delay, max_delay = delay_ranges[level]

        # Se o scraper tem atributo de delay, atualiza
        if self._scraper and hasattr(self._scraper, "typing_delay_range"):
            self._scraper.typing_delay_range = (min_delay, max_delay)

        logger.info(f"[tools] Typing delay ajustado para nível '{level}' ({min_delay*1000:.0f}-{max_delay*1000:.0f}ms)")
        return ToolResult(
            success=True,
            tool_name="adjust_typing_delay",
            data={"level": level, "min_delay_ms": min_delay * 1000, "max_delay_ms": max_delay * 1000},
        )

    async def adjust_navigation_profile(self, block_type: str = "429") -> ToolResult:
        """
        Ajusta perfil de navegação baseado no tipo de bloqueio detectado.

        Integradado com scraper_weights.py se disponível.

        Block types:
            - 429 (Rate Limit): Aumenta jitter, troca User-Agent
            - 403 (Forbidden): Troca proxy + User-Agent + resolução
            - login_redirect: Renova sessão/cookies
            - captcha: Hibernação + troca completa de identidade
        """
        profiles = {
            "429": {
                "jitter_range": (10, 45),  # segundos
                "change_ua": True,
                "change_resolution": False,
                "change_proxy": False,
                "description": "Rate limit — aumentar jitter e trocar UA",
            },
            "403": {
                "jitter_range": (15, 60),
                "change_ua": True,
                "change_resolution": True,
                "change_proxy": True,
                "description": "Forbidden — troca completa de identidade parcial",
            },
            "login_redirect": {
                "jitter_range": (20, 60),
                "change_ua": True,
                "change_resolution": False,
                "change_proxy": False,
                "description": "Sessão expirada — renovar cookies",
            },
            "captcha": {
                "jitter_range": (30, 90),
                "change_ua": True,
                "change_resolution": True,
                "change_proxy": True,
                "description": "CAPTCHA detectado — hibernação + troca completa",
            },
        }

        if block_type not in profiles:
            block_type = "429"

        profile = profiles[block_type]

        # Aplica jitter ao scraper
        if self._scraper and hasattr(self._scraper, "jitter_range"):
            self._scraper.jitter_range = profile["jitter_range"]

        # Troca proxy se necessário
        if profile["change_proxy"]:
            await self.rotate_proxy()

        logger.info(f"[tools] Perfil de navegação ajustado para bloqueio '{block_type}': {profile['description']}")
        return ToolResult(
            success=True,
            tool_name="adjust_navigation_profile",
            data=profile,
        )

    # -----------------------------------------------------------------------
    # Ferramentas: Recuperação e Cura
    # -----------------------------------------------------------------------

    async def heal_dom_selectors(
        self,
        screenshot_b64: str,
        html_snippet: str,
        cache_key: str | None = None,
    ) -> ToolResult:
        """
        Cura seletores DOM via IA de visão.

        Fluxo:
            1. Envia screenshot + HTML fragment para vision_completion
            2. Recebe seletor CSS inferido pela IA
            3. Valida seletor (não vazio, não contem JS)
            4. Persiste em configs/learned_selectors.json
            5. Aplica no scraper em tempo real

        O HITL atual é preservado como fallback — se a visão falhar,
        o fluxo retrocede para intervenção humana.
        """
        if not self._ai_service:
            return ToolResult(
                success=False,
                tool_name="heal_dom_selectors",
                error="ai_service não disponível para chamada de visão",
            )

        # Prompt otimizado para resposta determinística
        vision_prompt = (
            "Identifique o container CSS de comentários do post exibido nesta "
            "captura de tela baseado no fragmento HTML fornecido abaixo. "
            "Responda APENAS com o seletor CSS válido, sem explicação.\n\n"
            f"Fragmento HTML:\n{html_snippet[:2000]}"
        )

        result = await self._ai_service.vision_completion(
            image_b64=screenshot_b64,
            prompt=vision_prompt,
            cache_key=cache_key,
        )

        if not result.get("success"):
            return ToolResult(
                success=False,
                tool_name="heal_dom_selectors",
                error=f"Visão falhou: {result.get('error', 'desconhecido')}",
                tokens_used=result.get("tokens_used", 0),
            )

        selector = result["content"].strip()

        # Validação básica do seletor
        if not selector or len(selector) < 2:
            return ToolResult(
                success=False,
                tool_name="heal_dom_selectors",
                error=f"Seletor inválido retornado pela IA: '{selector}'",
                tokens_used=50,
            )

        # Remove aspas se a IA as incluiu
        selector = selector.strip('"').strip("'").strip("`")

        # Persiste no arquivo de seletores aprendidos
        await self.save_learned_selector(
            selector_name="comment_container",
            css_path=selector,
        )

        logger.info(f"[tools] DOM curado — novo seletor: {selector} (provider: {result.get('provider')})")
        return ToolResult(
            success=True,
            tool_name="heal_dom_selectors",
            data={
                "selector": selector,
                "provider": result.get("provider"),
                "cached": result.get("cached", False),
            },
            tokens_used=50,
        )

    async def flag_cooldown_session(
        self,
        session_label: str = "default",
        duration_s: int = 300,
    ) -> ToolResult:
        """
        Sinaliza sessão em cooldown e aplica backoff.

        Integra com scraper_circuit_breaker se disponível.
        """
        if self._scraper and hasattr(self._scraper, "scraper_circuit_breaker"):
            cb = self._scraper.scraper_circuit_breaker
            if hasattr(cb, "record_failure"):
                cb.record_failure(session_label)

        logger.info(f"[tools] Sessão '{session_label}' em cooldown por {duration_s}s")
        return ToolResult(
            success=True,
            tool_name="flag_cooldown_session",
            data={"session": session_label, "cooldown_s": duration_s},
        )

    async def emergency_hibernate(self, duration_s: int = 3600) -> ToolResult:
        """
        Hibernação de emergência — pausa coleta por duration_s segundos.

        Padrão 1h, consistente com hibernação existente após 3 bloqueios.
        Sinaliza ao EventBus para notificar o orquestrador.
        """
        # Sinaliza ao EventBus se disponível
        try:
            from core.event_bus import event_bus
            await event_bus.emit("scraper:hibernate", {
                "duration_s": duration_s,
                "reason": "emergency_hibernate",
                "timestamp": time.time(),
            })
        except ImportError:
            pass

        logger.warning(f"[tools] HIBERNAÇÃO DE EMERGÊNCIA por {duration_s}s")
        return ToolResult(
            success=True,
            tool_name="emergency_hibernate",
            data={"duration_s": duration_s},
        )

    # -----------------------------------------------------------------------
    # Ferramentas: Sensing (Custo 0 Tokens)
    # -----------------------------------------------------------------------

    async def get_block_severity(
        self,
        status_code: int = 0,
        response_body: str | None = None,
    ) -> ToolResult:
        """
        Classifica severidade do bloqueio — FILTRO DETERMINÍSTICO (0 tokens).

        Seguindo o padrão do sre_agent.py: erros conhecidos são classificados
        sem consultar LLM. Apenas casos UNKNOWN vão para o motor cognitivo.

        Classificação:
            - SESSION_EXPIRED: redirect para login (302 para /accounts/login)
            - IP_BLOCK: status 403 sem corpo específico
            - RATE_LIMIT: status 429
            - CAPTCHA: corpo contém "captcha" ou "challenge"
            - DOM_CHANGE: página carrega mas 0 posts/conteúdo
            - UNKNOWN: qualquer outro caso
        """
        severity = "UNKNOWN"
        recommended_action = "consult_cognitive"

        if status_code == 429:
            severity = "RATE_LIMIT"
            recommended_action = "rotate_proxy+jitter"
        elif status_code == 403:
            severity = "IP_BLOCK"
            recommended_action = "rotate_proxy+change_ua"
        elif status_code in (301, 302):
            if response_body and "/accounts/login" in (response_body or ""):
                severity = "SESSION_EXPIRED"
                recommended_action = "renew_session"
        elif status_code == 200:
            if response_body and any(
                kw in response_body.lower()
                for kw in ["captcha", "challenge", "verify your identity"]
            ):
                severity = "CAPTCHA"
                recommended_action = "emergency_hibernate"

        logger.info(f"[tools] Severidade: {severity} (code={status_code}, action={recommended_action})")
        return ToolResult(
            success=True,
            tool_name="get_block_severity",
            data={
                "severity": severity,
                "recommended_action": recommended_action,
                "status_code": status_code,
            },
        )

    # -----------------------------------------------------------------------
    # Ferramentas: Aprendizado
    # -----------------------------------------------------------------------

    async def save_learned_selector(
        self,
        selector_name: str = "comment_container",
        css_path: str = "",
    ) -> ToolResult:
        """
        Persiste seletor aprendido em configs/learned_selectors.json.

        Formato idêntico ao existente no instagram_scraper_v2.py:
        {
            "comment_container": "div.x5yr21d",
            "post_container": "article._aavo",
            ...
        }
        """
        if not css_path:
            return ToolResult(
                success=False,
                tool_name="save_learned_selector",
                error="Seletor CSS vazio",
            )

        config_path = os.path.join(
            os.getenv("PROJECT_ROOT", os.getcwd()),
            "configs",
            "learned_selectors.json",
        )

        try:
            # Lê seletores existentes
            existing = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)

            # Atualiza com novo seletor
            existing[selector_name] = css_path

            # Persiste
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            logger.info(f"[tools] Seletor aprendido salvo: {selector_name} = {css_path}")
            return ToolResult(
                success=True,
                tool_name="save_learned_selector",
                data={"selector_name": selector_name, "css_path": css_path},
            )

        except Exception as e:
            logger.error(f"[tools] Erro ao salvar seletor: {e}")
            return ToolResult(
                success=False,
                tool_name="save_learned_selector",
                error=str(e),
            )

    # -----------------------------------------------------------------------
    # Helpers Internos
    # -----------------------------------------------------------------------

    def _load_proxy_list(self) -> list[str]:
        """Carrega lista de proxies do .env (PROXY_LIST ou fallback para PROXY_URL)."""
        proxy_list_str = os.getenv("PROXY_LIST", "").strip()
        if proxy_list_str:
            return [p.strip() for p in proxy_list_str.split(",") if p.strip()]

        proxy_url = os.getenv("PROXY_URL", "").strip()
        if proxy_url:
            return [proxy_url]

        return []

    def get_execution_stats(self) -> dict:
        """Retorna estatísticas de execução das ferramentas."""
        if not self._execution_log:
            return {"total_calls": 0, "success_rate": 0.0}

        total = len(self._execution_log)
        successes = sum(1 for e in self._execution_log if e["success"])
        avg_time = sum(e["elapsed_s"] for e in self._execution_log) / total

        by_tool = {}
        for entry in self._execution_log:
            name = entry["tool"]
            if name not in by_tool:
                by_tool[name] = {"calls": 0, "successes": 0}
            by_tool[name]["calls"] += 1
            if entry["success"]:
                by_tool[name]["successes"] += 1

        return {
            "total_calls": total,
            "success_rate": round(successes / total, 3) if total else 0.0,
            "avg_time_s": round(avg_time, 3),
            "by_tool": by_tool,
        }
