"""
Worker Adapter — Integração do ScrapeAgent com wk_coleta_instagram.py
======================================================================
Adaptador que injeta o ScrapeAgent no worker de coleta existente,
preservando TODA a infraestrutura atual:
    - scraper_circuit_breaker
    - CheckpointManager
    - Buffer SQLite local (local_buffer)
    - Sinalização reativa ao EventBus
    - Jitter estocástico
    - Modo noturno
    - Integração com orquestrador de filas atômico

Ponto de Integração:
    No método run_cycle() de wk_coleta_instagram.py, substituir a
    chamada direta ao scraper pelo loop cognitivo do ScrapeAgent.

    ANTES:
        result = await self.scraper.scrape_profile(username)

    DEPOIS:
        result = await self.agent_adapter.run_scrape_cycle(username)

O adaptador NÃO substitui o scraper — ele o envolve com o loop
cognitivo, adicionando capacidades de recuperação e evasão.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Optional

from core.exceptions import DOMHealerRestartSignal

logger = logging.getLogger("agent_scraper.worker_adapter")


# ---------------------------------------------------------------------------
# Resultado do Ciclo de Coleta
# ---------------------------------------------------------------------------

class ScrapeCycleResult:
    """Resultado de um ciclo de coleta processado pelo ScrapeAgent."""

    def __init__(
        self,
        success: bool,
        username: str = "",
        comments_collected: int = 0,
        posts_processed: int = 0,
        healing_triggered: bool = False,
        healing_success: bool = False,
        persona_time_s: float = 0.0,
        agent_tokens: int = 0,
        agent_decisions: list[dict] | None = None,
        error: str | None = None,
        is_control_signal: bool = False,
    ):
        self.success = success
        self.username = username
        self.comments_collected = comments_collected
        self.posts_processed = posts_processed
        self.healing_triggered = healing_triggered
        self.healing_success = healing_success
        self.persona_time_s = persona_time_s
        self.agent_tokens = agent_tokens
        self.agent_decisions = agent_decisions or []
        self.error = error
        self.is_control_signal = is_control_signal

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "username": self.username,
            "comments_collected": self.comments_collected,
            "posts_processed": self.posts_processed,
            "healing_triggered": self.healing_triggered,
            "healing_success": self.healing_success,
            "persona_time_s": round(self.persona_time_s, 2),
            "agent_tokens": self.agent_tokens,
            "agent_decisions": self.agent_decisions,
            "error": self.error,
            "is_control_signal": self.is_control_signal,
        }


# ---------------------------------------------------------------------------
# Worker Adapter
# ---------------------------------------------------------------------------

class ScrapeAgentAdapter:
    """
    Adaptador que integra o ScrapeAgent com o worker de coleta existente.

    Responsabilidades:
        1. Instanciar o ScrapeAgent com as dependências corretas
        2. Envolver o scraper existente com o loop cognitivo
        3. Interceptar erros de DOM e acionar DOM Healing
        4. Aplicar persona mode quando configurado
        5. Preservar toda infraestrutura existente (circuit breaker, checkpoint, etc.)

    Uso no worker (wk_coleta_instagram.py):
        # No __init__ do worker:
        from core.agent_scraper.worker_adapter import ScrapeAgentAdapter
        self.agent_adapter = ScrapeAgentAdapter(
            scraper=self.scraper,
            ai_service=ai_service,
        )

        # No run_cycle do worker:
        result = await self.agent_adapter.run_scrape_cycle(
            username=target,
            page=page,
        )
    """

    def __init__(
        self,
        scraper: Any = None,
        ai_service: Any = None,
        config: dict[str, Any] | None = None,
    ):
        self._scraper = scraper
        self._ai_service = ai_service
        self._config = config or {}

        # Inicializa componentes do ScrapeAgent
        from core.agent_scraper.agent import ScrapeAgent
        from core.agent_scraper.dom_healing import DOMHealer
        from core.agent_scraper.persona_mode import PersonaEngine

        self._agent = ScrapeAgent(
            scraper=scraper,
            ai_service=ai_service,
            config=config,
        )

        self._dom_healer = DOMHealer(ai_service=ai_service)

        self._persona = PersonaEngine.from_env()

        # Estatísticas
        self._stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "healing_triggers": 0,
            "healing_successes": 0,
            "hitl_fallbacks": 0,
            "total_tokens": 0,
        }

    @property
    def agent(self):
        """Acesso direto ao ScrapeAgent."""
        return self._agent

    @property
    def dom_healer(self):
        """Acesso direto ao DOMHealer."""
        return self._dom_healer

    @property
    def persona(self):
        """Acesso direto ao PersonaEngine."""
        return self._persona

    @property
    def stats(self) -> dict:
        return {**self._stats, "agent_stats": self._agent.stats}

    # -----------------------------------------------------------------------
    # Ciclo de Coleta Principal
    # -----------------------------------------------------------------------

    async def run_scrape_cycle(
        self,
        username: str,
        page: Any | None = None,
        max_posts: int = 3,
        max_comments_per_post: int = 50,
        candidato_id: str = "",
        resume_after_shortcode: str | None = None,
        on_post_scraped: Any | None = None,
    ) -> ScrapeCycleResult:
        """
        Executa um ciclo de coleta com o loop cognitivo do ScrapeAgent.

        Este método SUBSTITUI a chamada direta ao scraper no worker,
        adicionando camadas de recuperação, evasão e persona.

        Fluxo:
            1. Aplica persona mode (scroll, jitter)
            2. Executa scraping via scraper existente
            3. Se detectar problema (DOM vazio, bloqueio):
               a. O agente avalia o ambiente (OODA - Observar)
               b. Classifica severidade (OODA - Orientar)
               c. Seleciona ação (OODA - Decidir)
               d. Executa recuperação (OODA - Agir)
            4. Se DOM Healing ativado: cura seletores via IA de visão
            5. Retorna resultado estruturado
        """
        start = time.time()
        self._stats["total_cycles"] += 1
        agent_decisions = []
        total_tokens = 0

        try:
            # --- 1. Persona Mode: Preparação ---
            persona_time = 0.0
            if page and self._persona.mode != "disabled":
                # Scroll humano inicial
                scroll_result = await self._persona.human_scroll(page, target_height=500)
                persona_time += scroll_result.get("time_s", 0)

            # --- 2. Executa Scraping via Scraper Existente ---
            # O scraper existente faz todo o trabalho pesado
            # O adaptador apenas monitora e reage a problemas
            try:
                scrape_result = await self._scraper.scrape_profile(
                    username=username,
                    max_posts=max_posts,
                    max_comments_per_post=max_comments_per_post,
                    candidato_id=candidato_id,
                    resume_after_shortcode=resume_after_shortcode,
                    on_post_scraped=on_post_scraped,
                )

                # Se o scraping foi bem-sucedido, retorna direto
                if scrape_result and scrape_result.get("success", False):
                    self._stats["successful_cycles"] += 1
                    return ScrapeCycleResult(
                        success=True,
                        username=username,
                        comments_collected=scrape_result.get("comments_collected", 0),
                        posts_processed=scrape_result.get("posts_processed", 0),
                        persona_time_s=persona_time,
                    )

            except AttributeError:
                # Scraper não tem scrape_profile — usa método direto
                scrape_result = None

            # --- 3. Verifica Problemas ---
            # Lê estado do scraper para detectar problemas
            consecutive_empty = 0
            last_status_code = 0
            last_error = ""

            if self._scraper:
                if hasattr(self._scraper, "stats"):
                    stats = self._scraper.stats if isinstance(self._scraper.stats, dict) else {}
                    consecutive_empty = stats.get("consecutive_empty_posts", 0)
                    last_status_code = stats.get("last_status_code", 0)

                if hasattr(self._scraper, "last_error"):
                    last_error = str(self._scraper.last_error or "")

            # Se não há problemas, retorna sucesso
            if consecutive_empty < 3 and last_status_code < 400:
                self._stats["successful_cycles"] += 1
                return ScrapeCycleResult(
                    success=True,
                    username=username,
                    persona_time_s=persona_time,
                )

            # --- 4. Agente Avalia Ambiente (OODA) ---
            # Captura screenshot e HTML para o agente analisar
            screenshot_b64 = ""
            html_snippet = ""
            cache_key = f"heal_{username}_{int(time.time() / 300)}"  # Cache por 5 min

            if page:
                screenshot_b64 = await self._dom_healer._capture_screenshot(page)
                html_snippet = await self._dom_healer._extract_html_snippet(page)

            cycle_result = await self._agent.evaluate_environment(
                target=username,
                status_code=last_status_code,
                consecutive_empty_posts=consecutive_empty,
                screenshot_b64=screenshot_b64,
                html_snippet=html_snippet,
                cache_key=cache_key,
            )

            agent_decisions.append(cycle_result.to_dict())
            total_tokens += cycle_result.total_tokens

            # --- 5. DOM Healing (se ativado) ---
            healing_triggered = False
            healing_success = False

            if cycle_result.observation.severity.value == "DOM_CHANGE":
                healing_triggered = True
                self._stats["healing_triggers"] += 1

                heal_result = await self._dom_healer.heal_selectors(
                    page=page,
                    selector_name="comment_container",
                    screenshot_b64=screenshot_b64,
                    html_snippet=html_snippet,
                    cache_key=cache_key,
                )

                if heal_result.get("success"):
                    healing_success = True
                    self._stats["healing_successes"] += 1

                    # Aplica seletor curado ao scraper
                    new_selector = heal_result.get("selector", "")
                    if new_selector and hasattr(self._scraper, "update_selector"):
                        await self._scraper.update_selector("comment_container", new_selector)

                elif heal_result.get("source") == "hitl_fallback":
                    self._stats["hitl_fallbacks"] += 1
                    # O HITL será ativado pelo scraper existente

            # --- 6. Retorna Resultado ---
            self._stats["total_tokens"] += total_tokens
            elapsed = time.time() - start

            return ScrapeCycleResult(
                success=healing_success or cycle_result.action_result.success,
                username=username,
                healing_triggered=healing_triggered,
                healing_success=healing_success,
                persona_time_s=persona_time,
                agent_tokens=total_tokens,
                agent_decisions=agent_decisions,
                error=last_error if not healing_success else None,
            )

        except (RuntimeError, DOMHealerRestartSignal) as e:
            if isinstance(e, DOMHealerRestartSignal) or \
               (isinstance(e, RuntimeError) and "hitl_intervention_completed" in str(e)):
                username_context = username or "unknown"
                self._stats["healer_restarts"] = self._stats.get("healer_restarts", 0) + 1
                logger.warning(
                    f"🔄 [Adapter] DOM Healing restart solicitado para @{username_context}",
                    extra={
                        "username": username_context,
                        "healer_restart_count": self._stats["healer_restarts"]
                    }
                )
                return ScrapeCycleResult(
                    success=False,
                    username=username_context,
                    comments_collected=0,
                    posts_processed=0,
                    error="healer_restart_requested",
                    persona_time_s=persona_time,
                    is_control_signal=True,
                )
            
            logger.error(f"[adapter] Erro Runtime/Sinal não tratado no ciclo para {username}: {e}", exc_info=True)
            return ScrapeCycleResult(
                success=False,
                username=username,
                error=str(e),
            )
            
        except Exception as e:
            logger.error(f"[adapter] Erro no ciclo de coleta para {username}: {e}", exc_info=True)
            return ScrapeCycleResult(
                success=False,
                username=username,
                error=str(e),
            )

    # -----------------------------------------------------------------------
    # API de Conveniência para o Worker
    # -----------------------------------------------------------------------

    async def pre_cycle_evaluation(
        self,
        username: str,
        proxy_url: str = "",
        session_active: bool = True,
    ) -> dict:
        """
        Avaliação pré-ciclo — verifica se é seguro iniciar a coleta.

        Usado pelo worker ANTES de iniciar o ciclo de scraping para
        decidir se deve prosseguir ou aguardar.

        Returns:
            {"safe_to_proceed": bool, "recommendation": str, "adjusted_config": dict}
        """
        # Verifica circuit breaker
        if self._scraper and hasattr(self._scraper, "scraper_circuit_breaker"):
            cb = self._scraper.scraper_circuit_breaker
            if hasattr(cb, "is_open") and cb.is_open():
                return {
                    "safe_to_proceed": False,
                    "recommendation": "Circuit breaker aberto — aguardar",
                    "adjusted_config": {"delay_s": 60},
                }

        # Verifica sessão
        if not session_active:
            return {
                "safe_to_proceed": False,
                "recommendation": "Sessão expirada — renovar antes de coletar",
                "adjusted_config": {"renew_session": True},
            }

        return {
            "safe_to_proceed": True,
            "recommendation": "Proceder com coleta",
            "adjusted_config": {},
        }

    async def post_cycle_report(self, cycle_result: ScrapeCycleResult) -> dict:
        """
        Relatório pós-ciclo — consolida métricas e sugere ajustes.

        Usado pelo worker APÓS o ciclo para logging e ajuste de configuração.
        """
        report = {
            "username": cycle_result.username,
            "success": cycle_result.success,
            "comments_collected": cycle_result.comments_collected,
            "healing_triggered": cycle_result.healing_triggered,
            "healing_success": cycle_result.healing_success,
            "agent_tokens": cycle_result.agent_tokens,
            "persona_time_s": cycle_result.persona_time_s,
        }

        # Sugestões de ajuste baseadas no resultado
        suggestions = []
        if cycle_result.healing_triggered and not cycle_result.healing_success:
            suggestions.append("HITL fallback ativado — operador deve verificar seletor manualmente")

        if cycle_result.agent_tokens > 0:
            suggestions.append(f"Tokens de IA consumidos: {cycle_result.agent_tokens}")

        if cycle_result.persona_time_s > 10:
            suggestions.append(
                f"Persona time elevado ({cycle_result.persona_time_s:.1f}s) — "
                "considere reduzir para modo minimal"
            )

        report["suggestions"] = suggestions
        return report

    async def apply_persona_to_navigation(
        self,
        page: Any,
        action: str = "scroll",
        **kwargs,
    ) -> dict:
        """
        Aplica persona mode a uma ação de navegação específica.

        Usado pelo worker para aplicar persona mode a ações isoladas
        sem passar pelo ciclo completo do ScrapeAgent.
        """
        if action == "scroll":
            return await self._persona.human_scroll(page, **kwargs)
        elif action == "click":
            return await self._persona.human_click(page, **kwargs)
        elif action == "type":
            return await self._persona.human_type(page, **kwargs)
        elif action == "reading_pause":
            return await self._persona.reading_pause(**kwargs)
        else:
            return {"error": f"Ação de persona não reconhecida: {action}"}
