"""
Modo Persona — Simulação de Comportamento Humano (Experimental)
================================================================
Implementa trajetórias de mouse estocásticas, tempo de leitura
variável e jitter de scroll para tornar o scraping mais difícil
de detectar por sistemas antibot.

CONFIGURÁVEL VIA .ENV:
    SCRAPER_PERSONA_MODE=full|minimal|disabled (default: minimal)

    - full:    Mouse estocástico + leitura + scroll + digitação variável
    - minimal: Apenas jitter de scroll (maior impacto, menor custo)
    - disabled: Comportamento original (sem alteração)

AVISO DE CUSTO/BENEFÍCIO:
    O modo "full" eleva o tempo médio de ciclo por alvo, impactando
    diretamente o throughput da backlog_ia. Precisa de validação
    quantitativa antes de ativar em produção.

RECOMENDAÇÃO DA VALIDAÇÃO:
    Ativar por padrão apenas o jitter de scroll (minimal), que é o
    item de maior impacto com menor custo de ciclo.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from enum import Enum
from typing import Any, Optional, Tuple

logger = logging.getLogger("agent_scraper.persona_mode")


class PersonaMode(str, Enum):
    """Níveis de simulação de persona."""
    FULL = "full"
    MINIMAL = "minimal"
    DISABLED = "disabled"


# ---------------------------------------------------------------------------
# Configuração de Persona
# ---------------------------------------------------------------------------

class PersonaConfig:
    """Configuração do modo persona."""

    # Jitter de scroll (minimal mode)
    SCROLL_PAUSE_RANGE: Tuple[float, float] = (0.3, 1.2)  # segundos entre scrolls
    SCROLL_DISTANCE_RANGE: Tuple[int, int] = (200, 600)    # pixels por scroll

    # Mouse estocástico (full mode)
    MOUSE_STEP_SIZE_RANGE: Tuple[int, int] = (5, 25)       # pixels por passo
    MOUSE_STEP_PAUSE_RANGE: Tuple[float, float] = (0.005, 0.025)  # segundos entre passos
    MOUSE_CURVATURE: float = 0.3                             # curvatura da trajetória

    # Tempo de leitura (full mode)
    READING_TIME_BASE: float = 1.5                          # segundos base
    READING_TIME_PER_COMMENT: float = 0.3                   # segundos por comentário visível
    READING_TIME_JITTER: Tuple[float, float] = (0.5, 2.0)  # jitter adicional

    # Digitação variável (full mode)
    TYPING_DELAY_RANGE: Tuple[float, float] = (0.030, 0.080)   # segundos por caractere
    TYPING_PAUSE_WORD: Tuple[float, float] = (0.100, 0.300)     # pausa entre palavras

    # Velocidade de navegação
    NAVIGATION_DELAY_RANGE: Tuple[float, float] = (1.0, 3.0)    # delay antes de clicar

    @classmethod
    def from_env(cls) -> "PersonaConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        config = cls()

        # Override do .env se definido
        env_overrides = {
            "PERSONA_SCROLL_PAUSE_MIN": ("SCROLL_PAUSE_RANGE", 0, float),
            "PERSONA_SCROLL_PAUSE_MAX": ("SCROLL_PAUSE_RANGE", 1, float),
            "PERSONA_TYPING_DELAY_MIN": ("TYPING_DELAY_RANGE", 0, float),
            "PERSONA_TYPING_DELAY_MAX": ("TYPING_DELAY_RANGE", 1, float),
        }

        for env_var, (attr, index, converter) in env_overrides.items():
            value = os.getenv(env_var)
            if value:
                current = getattr(config, attr)
                current_list = list(current)
                current_list[index] = converter(value)
                setattr(config, attr, tuple(current_list))

        return config


# ---------------------------------------------------------------------------
# Persona Engine
# ---------------------------------------------------------------------------

class PersonaEngine:
    """
    Motor de simulação de comportamento humano para Playwright.

    Uso:
        engine = PersonaEngine(mode=PersonaMode.MINIMAL)
        await engine.human_scroll(page, target_height=3000)
        await engine.human_click(page, selector="button.load-more")
    """

    def __init__(
        self,
        mode: PersonaMode = PersonaMode.MINIMAL,
        config: PersonaConfig | None = None,
    ):
        self._mode = mode
        self._config = config or PersonaConfig()
        self._stats = {
            "scrolls_performed": 0,
            "clicks_performed": 0,
            "mouse_movements": 0,
            "total_persona_time_s": 0.0,
        }

    @property
    def mode(self) -> PersonaMode:
        return self._mode

    @property
    def stats(self) -> dict:
        return self._stats

    @classmethod
    def from_env(cls) -> "PersonaEngine":
        """Cria engine a partir da variável SCRAPER_PERSONA_MODE do .env."""
        mode_str = os.getenv("SCRAPER_PERSONA_MODE", "minimal").strip().lower()
        try:
            mode = PersonaMode(mode_str)
        except ValueError:
            logger.warning(f"[persona] Modo inválido '{mode_str}', usando 'minimal'")
            mode = PersonaMode.MINIMAL

        logger.info(f"[persona] Modo de persona: {mode.value}")
        return cls(mode=mode)

    # -----------------------------------------------------------------------
    # Scroll Humano (Disponível em MINIMAL e FULL)
    # -----------------------------------------------------------------------

    async def human_scroll(
        self,
        page: Any,
        target_height: int | None = None,
        incremental: bool = True,
    ) -> dict:
        """
        Scroll com jitter estocástico — simula navegação humana.

        Este é o item de MAIOR IMPACTO com MENOR CUSTO de ciclo.
        Disponível mesmo no modo minimal.

        Args:
            page: Playwright Page object
            target_height: Altura alvo em pixels (ou None para scroll incremental)
            incremental: Se True, rola incrementalmente com pausas

        Returns:
            {"scrolled_pixels": int, "scroll_count": int, "time_s": float}
        """
        if self._mode == PersonaMode.DISABLED:
            # Modo desabilitado — scroll instantâneo
            if target_height:
                await page.evaluate(f"window.scrollTo(0, {target_height})")
            return {"scrolled_pixels": target_height or 0, "scroll_count": 1, "time_s": 0}

        start = time.time()
        total_scrolled = 0
        scroll_count = 0

        current_position = await page.evaluate("window.scrollY")

        if target_height and incremental:
            # Scroll incremental com pausas
            while current_position < target_height:
                scroll_dist = random.randint(*self._config.SCROLL_DISTANCE_RANGE)
                scroll_dist = min(scroll_dist, target_height - current_position)

                await page.evaluate(
                    f"window.scrollBy(0, {scroll_dist})"
                )
                total_scrolled += scroll_dist
                scroll_count += 1

                # Pausa estocástica entre scrolls
                pause = random.uniform(*self._config.SCROLL_PAUSE_RANGE)
                await asyncio.sleep(pause)

                current_position = await page.evaluate("window.scrollY")

                # Pequena chance de "voltar" (comportamento humano)
                if random.random() < 0.05:  # 5% chance
                    back_dist = random.randint(50, 150)
                    await page.evaluate(f"window.scrollBy(0, -{back_dist})")
                    current_position = await page.evaluate("window.scrollY")
                    await asyncio.sleep(random.uniform(0.2, 0.5))

        elif target_height:
            # Scroll direto com jitter
            await page.evaluate(f"window.scrollTo(0, {target_height})")
            total_scrolled = target_height
            scroll_count = 1

        elapsed = time.time() - start
        self._stats["scrolls_performed"] += scroll_count
        self._stats["total_persona_time_s"] += elapsed

        return {
            "scrolled_pixels": total_scrolled,
            "scroll_count": scroll_count,
            "time_s": round(elapsed, 2),
        }

    # -----------------------------------------------------------------------
    # Mouse Estocástico (Apenas FULL mode)
    # -----------------------------------------------------------------------

    async def human_click(
        self,
        page: Any,
        selector: str,
        offset_x: int | None = None,
        offset_y: int | None = None,
    ) -> dict:
        """
        Clique com trajetória de mouse estocástica.

        No modo minimal, usa page.click() direto.
        No modo full, move o mouse gradualmente até o elemento.
        """
        start = time.time()

        if self._mode == PersonaMode.MINIMAL or self._mode == PersonaMode.DISABLED:
            # Click direto com pequeno offset aleatório
            try:
                element = await page.query_selector(selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        cx = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                        cy = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
                        await page.mouse.click(cx, cy)
                    else:
                        await page.click(selector)
                else:
                    await page.click(selector)
            except Exception:
                await page.click(selector)

            self._stats["clicks_performed"] += 1
            return {"click": selector, "mode": "direct", "time_s": round(time.time() - start, 2)}

        # Full mode: trajetória de mouse estocástica
        try:
            element = await page.query_selector(selector)
            if not element:
                await page.click(selector)
                return {"click": selector, "mode": "fallback_direct", "time_s": 0}

            box = await element.bounding_box()
            if not box:
                await page.click(selector)
                return {"click": selector, "mode": "fallback_direct", "time_s": 0}

            # Centro do elemento com offset
            target_x = box["x"] + box["width"] / 2 + (offset_x or random.uniform(-10, 10))
            target_y = box["y"] + box["height"] / 2 + (offset_y or random.uniform(-5, 5))

            # Posição atual do mouse
            current_pos = await page.evaluate("({x: window._mouseX || 0, y: window._mouseY || 0})")
            start_x = current_pos.get("x", random.uniform(100, 500))
            start_y = current_pos.get("y", random.uniform(100, 500))

            # Gera trajetória estocástica
            waypoints = self._generate_mouse_path(
                start_x, start_y, target_x, target_y
            )

            # Move o mouse pelos waypoints
            for wx, wy in waypoints:
                await page.mouse.move(wx, wy)
                await asyncio.sleep(random.uniform(*self._config.MOUSE_STEP_PAUSE_RANGE))
                self._stats["mouse_movements"] += 1

            # Pausa antes do clique (tempo de "decisão")
            await asyncio.sleep(random.uniform(*self._config.NAVIGATION_DELAY_RANGE))

            # Clique
            await page.mouse.click(target_x, target_y)

            # Atualiza posição virtual
            await page.evaluate(
                f"window._mouseX = {target_x}; window._mouseY = {target_y}"
            )

            self._stats["clicks_performed"] += 1

        except Exception as e:
            logger.warning(f"[persona] Erro no click estocástico: {e} — fallback direto")
            try:
                await page.click(selector)
            except Exception:
                pass

        elapsed = time.time() - start
        self._stats["total_persona_time_s"] += elapsed
        return {"click": selector, "mode": "stochastic", "time_s": round(elapsed, 2)}

    async def human_type(
        self,
        page: Any,
        selector: str,
        text: str,
    ) -> dict:
        """
        Digitação com delay variável por caractere e pausa entre palavras.

        No modo minimal, usa page.fill() direto.
        No modo full, digita caractere por caractere.
        """
        start = time.time()

        if self._mode == PersonaMode.MINIMAL or self._mode == PersonaMode.DISABLED:
            await page.fill(selector, text)
            return {"type": selector, "mode": "direct", "time_s": 0}

        # Full mode: digitação caractere por caractere
        try:
            await page.click(selector)
            await asyncio.sleep(random.uniform(0.1, 0.3))

            for i, char in enumerate(text):
                await page.keyboard.type(char)
                # Delay variável por caractere
                delay = random.uniform(*self._config.TYPING_DELAY_RANGE)
                await asyncio.sleep(delay)

                # Pausa extra entre palavras
                if char == " ":
                    word_pause = random.uniform(*self._config.TYPING_PAUSE_WORD)
                    await asyncio.sleep(word_pause)

        except Exception as e:
            logger.warning(f"[persona] Erro na digitação estocástica: {e} — fallback direto")
            try:
                await page.fill(selector, text)
            except Exception:
                pass

        elapsed = time.time() - start
        return {"type": selector, "mode": "stochastic", "time_s": round(elapsed, 2)}

    # -----------------------------------------------------------------------
    # Tempo de Leitura (Apenas FULL mode)
    # -----------------------------------------------------------------------

    async def reading_pause(
        self,
        visible_comments: int = 0,
    ) -> dict:
        """
        Pausa de leitura simulada antes de expandir comentários.

        No modo minimal, aplica pausa curta fixa.
        No modo full, calcula tempo baseado no volume de comentários.
        """
        if self._mode == PersonaMode.DISABLED:
            return {"pause_s": 0}

        if self._mode == PersonaMode.MINIMAL:
            # Pausa curta variável
            pause = random.uniform(0.5, 1.5)
            await asyncio.sleep(pause)
            return {"pause_s": round(pause, 2)}

        # Full mode: tempo proporcional ao conteúdo
        base = self._config.READING_TIME_BASE
        per_comment = self._config.READING_TIME_PER_COMMENT
        jitter = random.uniform(*self._config.READING_TIME_JITTER)

        pause = base + (visible_comments * per_comment) + jitter
        pause = min(pause, 8.0)  # Cap em 8 segundos

        await asyncio.sleep(pause)
        self._stats["total_persona_time_s"] += pause

        return {"pause_s": round(pause, 2), "visible_comments": visible_comments}

    # -----------------------------------------------------------------------
    # Geração de Trajetória de Mouse
    # -----------------------------------------------------------------------

    def _generate_mouse_path(
        self,
        start_x: float,
        start_y: float,
        target_x: float,
        target_y: float,
    ) -> list[tuple[float, float]]:
        """
        Gera trajetória de mouse estocástica entre dois pontos.

        Usa curvas de Bézier com ruído para simular movimento humano.
        O movimento não é uma linha reta — humanos fazem curvas.
        """
        distance = ((target_x - start_x) ** 2 + (target_y - start_y) ** 2) ** 0.5

        if distance < 5:
            return [(target_x, target_y)]

        # Número de waypoints baseado na distância
        num_steps = max(5, int(distance / random.randint(*self._config.MOUSE_STEP_SIZE_RANGE)))

        # Ponto de controle para curva de Bézier
        curvature = self._config.MOUSE_CURVATURE
        ctrl_x = (start_x + target_x) / 2 + random.uniform(-distance * curvature, distance * curvature)
        ctrl_y = (start_y + target_y) / 2 + random.uniform(-distance * curvature, distance * curvature)

        waypoints = []
        for i in range(1, num_steps + 1):
            t = i / num_steps
            # Curva de Bézier quadrática
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + t ** 2 * target_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + t ** 2 * target_y

            # Adiciona ruído
            x += random.gauss(0, 1.5)
            y += random.gauss(0, 1.5)

            waypoints.append((x, y))

        return waypoints
