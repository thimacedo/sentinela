"""
ScrapeAgent — Loop Cognitivo OODA
===================================
Agente de IA autônomo para coleta de dados que segue o padrão OODA
(Observar, Orientar, Decidir, Agir) com filtros determinísticos
de baixo custo (0 tokens) para casos conhecidos.

Molde seguido: core/autopilot/sre_agent.py
- Filtros determinísticos rápidos para erros conhecidos (SESSION_EXPIRED,
  IP_BLOCK, RATE_LIMIT) — 0 tokens
- Consulta à IA SOMENTE para casos ambíguos (DOM_CHANGE, UNKNOWN)

Fluxo do Loop:
    1. OBSERVAR: Coleta sinais do ambiente (status HTTP, DOM, latência)
    2. ORIENTAR: Classifica severidade via filtros determinísticos
    3. DECIDIR: Seleciona ferramenta/ação (automática ou via LLM)
    4. AGIR: Executa ação via tools.py e retorna feedback

Integração:
    - tools.py: Registro de ferramentas do agente
    - dom_healing.py: Cura autônoma de seletores DOM
    - ai_service.vision_completion(): Chamadas multimodais
    - wk_coleta_instagram.py: Worker que instancia o agente
"""
from __future__ import annotations

import asyncio
import collections
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger("agent_scraper.agent")


# ---------------------------------------------------------------------------
# Data Classes de Estado e Resultado
# ---------------------------------------------------------------------------

class ObservationType(str, Enum):
    """Tipos de observação que o agente pode fazer."""
    HTTP_STATUS = "http_status"
    DOM_INTEGRITY = "dom_integrity"
    PROXY_HEALTH = "proxy_health"
    SESSION_VALIDITY = "session_validity"
    RATE_LIMIT = "rate_limit"


class Severity(str, Enum):
    """Severidade da observação — usada para roteamento determinístico vs LLM."""
    SESSION_EXPIRED = "SESSION_EXPIRED"
    IP_BLOCK = "IP_BLOCK"
    RATE_LIMIT = "RATE_LIMIT"
    CAPTCHA = "CAPTCHA"
    DOM_CHANGE = "DOM_CHANGE"
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"


class DecisionType(str, Enum):
    """Tipo de decisão tomada pelo agente."""
    DETERMINISTIC = "deterministic"  # 0 tokens — ação automática
    COGNITIVE = "cognitive"          # LLM consultado — custo de tokens


@dataclass
class Observation:
    """Sinal coletado do ambiente de scraping."""
    obs_type: ObservationType
    severity: Severity = Severity.HEALTHY
    status_code: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Decision:
    """Decisão tomada pelo agente após orientação."""
    tool_name: str
    params: dict[str, Any] = field(default_factory=dict)
    decision_type: DecisionType = DecisionType.DETERMINISTIC
    reasoning: str = ""
    tokens_used: int = 0


@dataclass
class ActionResult:
    """Resultado da execução de uma ação pelo agente."""
    success: bool
    tool_name: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    elapsed_s: float = 0.0
    tokens_used: int = 0


@dataclass
class CycleResult:
    """Resultado completo de um ciclo OODA do agente."""
    observation: Observation
    decision: Decision
    action_result: ActionResult
    total_tokens: int = 0
    cycle_elapsed_s: float = 0.0
    fallback_to_hitl: bool = False

    def to_dict(self) -> dict:
        return {
            "severity": self.observation.severity.value,
            "decision_type": self.decision.decision_type.value,
            "tool": self.decision.tool_name,
            "action_success": self.action_result.success,
            "tokens": self.total_tokens,
            "elapsed_s": round(self.cycle_elapsed_s, 3),
            "fallback_hitl": self.fallback_to_hitl,
        }


# ---------------------------------------------------------------------------
# Filtros Determinísticos (0 Tokens)
# ---------------------------------------------------------------------------

# Mapa de severidade -> ação determinística
# Casos conhecidos NÃO consultam o LLM — seguem o padrão sre_agent.py
DETERMINISTIC_ROUTING: dict[Severity, tuple[str, dict]] = {
    Severity.SESSION_EXPIRED: ("flag_cooldown_session", {"session_label": "session_expired", "duration_s": 300}),
    Severity.IP_BLOCK: ("adjust_navigation_profile", {"block_type": "403"}),
    Severity.RATE_LIMIT: ("adjust_navigation_profile", {"block_type": "429"}),
    Severity.CAPTCHA: ("emergency_hibernate", {"duration_s": 3600}),
}

# Casos que exigem consulta ao LLM (custo de tokens > 0)
COGNITIVE_SEVERITIES = {Severity.DOM_CHANGE, Severity.UNKNOWN}


# ---------------------------------------------------------------------------
# ScrapeAgent — Loop OODA Principal
# ---------------------------------------------------------------------------

class ScrapeAgent:
    """
    Agente cognitivo de scraping com loop OODA.

    Responsabilidades:
        1. Avaliar o ambiente de scraping a cada ciclo
        2. Classificar problemas via filtros determinísticos (0 tokens)
        3. Consultar LLM apenas para casos ambíguos (DOM_CHANGE, UNKNOWN)
        4. Executar ações de recuperação/evasão via tools.py
        5. Retornar resultado estruturado ao worker

    Uso:
        agent = ScrapeAgent(scraper=scraper, ai_service=ai_service)
        result = await agent.run_cycle(observation)
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

        # Importa ferramentas
        from core.agent_scraper.tools import ScrapeAgentTools
        self._tools = ScrapeAgentTools(
            scraper_instance=scraper,
            ai_service=ai_service,
        )

        # Estatísticas do agente
        self._stats = {
            "total_cycles": 0,
            "deterministic_decisions": 0,
            "cognitive_decisions": 0,
            "total_tokens_used": 0,
            "fallback_to_hitl": 0,
        }

        # Histórico recente para contexto do LLM
        # Fix Bug B: deque(maxlen) elimina pop(0) O(n) e o append manual de controle de tamanho
        self._recent_decisions: collections.deque[CycleResult] = collections.deque(maxlen=5)
        self._max_history = 5

        # Configuração
        self._max_cognitive_retries = self._config.get("max_cognitive_retries", 1)
        self._hitl_fallback_enabled = self._config.get("hitl_fallback_enabled", True)

    @property
    def stats(self) -> dict:
        """Estatísticas de execução do agente."""
        return {**self._stats, "tools_stats": self._tools.get_execution_stats()}

    @property
    def tools(self):
        """Acesso ao registro de ferramentas (para uso direto pelo worker)."""
        return self._tools

    # -----------------------------------------------------------------------
    # Loop OODA Principal
    # -----------------------------------------------------------------------

    async def run_cycle(self, observation: Observation) -> CycleResult:
        """
        Executa um ciclo completo do loop OODA.

        Args:
            observation: Sinal do ambiente (status HTTP, DOM, etc.)

        Returns:
            CycleResult com decisão, ação e métricas
        """
        start = time.time()
        self._stats["total_cycles"] += 1

        try:
            # --- ORIENTAR: Classifica severidade ---
            severity = await self._orient(observation)
            observation.severity = severity

            # --- DECIDIR: Seleciona ação ---
            decision = await self._decide(observation)

            # --- AGIR: Executa ação ---
            action_result = await self._act(decision)

            # Constrói resultado
            cycle_result = CycleResult(
                observation=observation,
                decision=decision,
                action_result=action_result,
                total_tokens=decision.tokens_used + action_result.tokens_used,
                cycle_elapsed_s=time.time() - start,
                fallback_to_hitl=False,
            )

            # Verifica se precisa fallback para HITL
            if not action_result.success and self._hitl_fallback_enabled:
                if severity in (Severity.DOM_CHANGE, Severity.UNKNOWN):
                    cycle_result.fallback_to_hitl = True
                    self._stats["fallback_to_hitl"] += 1
                    logger.warning(
                        f"[agent] Ação falhou e severidade={severity.value} — "
                        "ativando fallback HITL"
                    )

            # Atualiza estatísticas
            if decision.decision_type == DecisionType.DETERMINISTIC:
                self._stats["deterministic_decisions"] += 1
            else:
                self._stats["cognitive_decisions"] += 1
            self._stats["total_tokens_used"] += cycle_result.total_tokens

            # Mantém histórico (deque com maxlen=5 descarta automaticamente os mais antigos)
            self._recent_decisions.append(cycle_result)

            logger.info(
                f"[agent] Ciclo #{self._stats['total_cycles']} concluído: "
                f"severity={severity.value}, decision={decision.tool_name}, "
                f"type={decision.decision_type.value}, "
                f"tokens={cycle_result.total_tokens}, "
                f"elapsed={cycle_result.cycle_elapsed_s:.2f}s"
            )

            return cycle_result

        except Exception as e:
            logger.error(f"[agent] Erro no ciclo OODA: {e}", exc_info=True)
            return CycleResult(
                observation=observation,
                decision=Decision(
                    tool_name="error",
                    decision_type=DecisionType.DETERMINISTIC,
                    reasoning=f"Exceção no loop: {e}",
                ),
                action_result=ActionResult(
                    success=False,
                    tool_name="error",
                    error=str(e),
                    elapsed_s=time.time() - start,
                ),
                total_tokens=0,
                cycle_elapsed_s=time.time() - start,
                fallback_to_hitl=True,
            )

    # -----------------------------------------------------------------------
    # Fase: ORIENTAR (Classificação de Severidade)
    # -----------------------------------------------------------------------

    async def _orient(self, observation: Observation) -> Severity:
        """
        Classifica a severidade da observação.

        Estratégia determinística (padrão sre_agent.py):
            - Casos conhecidos: classificação direta via filtros — 0 tokens
            - Casos ambíguos: marcados como DOM_CHANGE/UNKNOWN para decisão cognitiva

        O orient usa os mesmos filtros do get_block_severity da tools.py,
        mas com lógica adicional para DOM integrity.
        """
        # Verificação de integridade do DOM (0 posts vazios consecutivos)
        if observation.obs_type == ObservationType.DOM_INTEGRITY:
            empty_count = observation.data.get("consecutive_empty_posts", 0)
            if empty_count >= 3:
                logger.info(f"[agent] DOM_CHANGE detectado: {empty_count} posts vazios consecutivos")
                return Severity.DOM_CHANGE

        # Verificação de status HTTP
        if observation.obs_type == ObservationType.HTTP_STATUS:
            result = await self._tools.get_block_severity(
                status_code=observation.status_code,
                response_body=observation.data.get("response_body"),
            )
            if result.success:
                severity_str = result.data.get("severity", "UNKNOWN")
                try:
                    return Severity(severity_str)
                except ValueError:
                    return Severity.UNKNOWN

        # Verificação de rate limit
        if observation.obs_type == ObservationType.RATE_LIMIT:
            return Severity.RATE_LIMIT

        # Verificação de sessão
        if observation.obs_type == ObservationType.SESSION_VALIDITY:
            if observation.data.get("expired", False):
                return Severity.SESSION_EXPIRED

        # Default: caso não classificado, marca como UNKNOWN para decisão cognitiva
        return Severity.HEALTHY if observation.status_code == 0 else Severity.UNKNOWN

    # -----------------------------------------------------------------------
    # Fase: DECIDIR (Seleção de Ação)
    # -----------------------------------------------------------------------

    async def _decide(self, observation: Observation) -> Decision:
        """
        Seleciona a ação apropriada com base na severidade.

        Roteamento:
            - Severidades conhecidas (SESSION_EXPIRED, IP_BLOCK, RATE_LIMIT,
              CAPTCHA): Ação determinística — 0 tokens
            - Severidades ambíguas (DOM_CHANGE, UNKNOWN): Consulta ao LLM

        Para DOM_CHANGE, tenta DOM Healing primeiro (custo fixo de ~50 tokens
        de visão). Se falhar, consulta o LLM para decisão mais ampla.
        """
        severity = observation.severity

        # --- Roteamento Determinístico (0 tokens) ---
        if severity in DETERMINISTIC_ROUTING:
            tool_name, params = DETERMINISTIC_ROUTING[severity]
            return Decision(
                tool_name=tool_name,
                params=params,
                decision_type=DecisionType.DETERMINISTIC,
                reasoning=f"Severidade conhecida: {severity.value} — ação automática",
                tokens_used=0,
            )

        if severity == Severity.HEALTHY:
            return Decision(
                tool_name="none",
                params={},
                decision_type=DecisionType.DETERMINISTIC,
                reasoning="Ambiente saudável — nenhuma ação necessária",
                tokens_used=0,
            )

        # --- Roteamento Cognitivo (LLM) ---
        if severity in COGNITIVE_SEVERITIES:
            # DOM_CHANGE: tenta DOM Healing direto (mais eficiente que LLM genérico)
            if severity == Severity.DOM_CHANGE:
                screenshot_b64 = observation.data.get("screenshot_b64", "")
                html_snippet = observation.data.get("html_snippet", "")
                cache_key = observation.data.get("cache_key")

                if screenshot_b64 and html_snippet:
                    return Decision(
                        tool_name="heal_dom_selectors",
                        params={
                            "screenshot_b64": screenshot_b64,
                            "html_snippet": html_snippet,
                            "cache_key": cache_key,
                        },
                        decision_type=DecisionType.COGNITIVE,
                        reasoning="DOM_CHANGE detectado — tentando cura via IA de visão",
                        tokens_used=0,  # Tokens contabilizados na execução
                    )

            # UNKNOWN ou DOM_CHANGE sem screenshot: consulta LLM genérico
            return await self._cognitive_decision(observation)

        # Fallback
        return Decision(
            tool_name="flag_cooldown_session",
            params={"session_label": "unknown_severity", "duration_s": 300},
            decision_type=DecisionType.DETERMINISTIC,
            reasoning=f"Severidade não mapeada: {severity.value} — cooldown seguro",
        )

    async def _cognitive_decision(self, observation: Observation) -> Decision:
        """
        Consulta o LLM para decisão em caso ambíguo.

        O prompt inclui contexto do histórico recente e ferramentas disponíveis
        para que o LLM escolha a melhor ação.
        """
        if not self._ai_service:
            logger.warning("[agent] ai_service não disponível para decisão cognitiva")
            return Decision(
                tool_name="flag_cooldown_session",
                params={"session_label": "cognitive_fallback", "duration_s": 300},
                decision_type=DecisionType.DETERMINISTIC,
                reasoning="ai_service indisponível — fallback para cooldown",
            )

        # Monta contexto para o LLM
        recent_context = []
        for r in self._recent_decisions[-3:]:
            recent_context.append(
                f"- severity={r.observation.severity.value}, "
                f"tool={r.decision.tool_name}, "
                f"success={r.action_result.success}"
            )

        available_tools = self._tools.tool_descriptions
        tools_desc = "\n".join(f"  - {name}: {desc}" for name, desc in available_tools.items())

        system_prompt = (
            "Você é o ScrapeAgent, um agente de IA para coleta de dados. "
            "Analise a situação e escolha a melhor ação do registro de ferramentas. "
            "Responda em JSON: {\"tool\": \"nome_da_ferramenta\", \"params\": {...}, \"reasoning\": \"...\"}"
        )

        user_prompt = (
            f"Situação atual:\n"
            f"- Tipo de observação: {observation.obs_type.value}\n"
            f"- Severidade: {observation.severity.value}\n"
            f"- Status HTTP: {observation.status_code}\n"
            f"- Dados: {observation.data}\n\n"
            f"Decisões recentes:\n{chr(10).join(recent_context) if recent_context else 'Nenhuma'}\n\n"
            f"Ferramentas disponíveis:\n{tools_desc}\n\n"
            f"Escolha a melhor ação."
        )

        try:
            response = await self._ai_service.chat_completion(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
            )

            content = response.get("content", "")
            tokens = response.get("tokens_used", 0)

            # Parse da resposta JSON
            # Fix Bug C: LLM frequentemente envolve JSON em backticks mesmo com response_format="json".
            # Sem strip, json.loads lança JSONDecodeError — capturado pelo except externo mas
            # loga um erro enganoso que dificulta o diagnóstico real.
            import json
            import re as _re
            content_clean = _re.sub(r"```(?:json)?\s*|\s*```", "", content).strip()
            json_match = _re.search(r"\{.*\}", content_clean, _re.DOTALL)
            content_clean = json_match.group(0) if json_match else content_clean
            llm_decision = json.loads(content_clean)

            tool_name = llm_decision.get("tool", "flag_cooldown_session")
            params = llm_decision.get("params", {})
            reasoning = llm_decision.get("reasoning", "Decisão do LLM")

            # Valida se a ferramenta existe
            if tool_name not in self._tools.available_tools:
                logger.warning(f"[agent] LLM sugeriu ferramenta inexistente: {tool_name}")
                tool_name = "flag_cooldown_session"
                params = {"session_label": "llm_invalid_tool", "duration_s": 300}

            return Decision(
                tool_name=tool_name,
                params=params,
                decision_type=DecisionType.COGNITIVE,
                reasoning=reasoning,
                tokens_used=tokens,
            )

        except Exception as e:
            logger.error(f"[agent] Erro na decisão cognitiva: {e}")
            return Decision(
                tool_name="flag_cooldown_session",
                params={"session_label": "cognitive_error", "duration_s": 300},
                decision_type=DecisionType.DETERMINISTIC,
                reasoning=f"Erro na consulta ao LLM: {e}",
            )

    # -----------------------------------------------------------------------
    # Fase: AGIR (Execução)
    # -----------------------------------------------------------------------

    async def _act(self, decision: Decision) -> ActionResult:
        """
        Executa a ação decidida via tools.py.

        Se a ferramenta for "none" (ambiente saudável), retorna sucesso imediato.
        """
        if decision.tool_name == "none":
            return ActionResult(
                success=True,
                tool_name="none",
                data={"message": "Nenhuma ação necessária"},
            )

        result = await self._tools.execute(decision.tool_name, decision.params)

        return ActionResult(
            success=result.success,
            tool_name=result.tool_name,
            data=result.data,
            error=result.error,
            tokens_used=result.tokens_used,
        )

    # -----------------------------------------------------------------------
    # API de Conveniência para o Worker
    # -----------------------------------------------------------------------

    async def evaluate_environment(
        self,
        target: str = "",
        status_code: int = 0,
        response_body: str | None = None,
        consecutive_empty_posts: int = 0,
        screenshot_b64: str = "",
        html_snippet: str = "",
        cache_key: str | None = None,
    ) -> CycleResult:
        """
        API de conveniência para o worker chamar o ciclo OODA.

        Encapsula a criação da Observation e executa o ciclo completo.

        Args:
            target: Username do alvo sendo coletado
            status_code: Último status HTTP recebido
            response_body: Corpo da resposta HTTP (para análise)
            consecutive_empty_posts: Posts vazios consecutivos (DOM integrity)
            screenshot_b64: Screenshot em base64 (para DOM Healing)
            html_snippet: Fragmento HTML (para DOM Healing)
            cache_key: Chave de cache (ex: shortcode do post)

        Returns:
            CycleResult com decisão e ação executada
        """
        # Determina o tipo de observação
        if consecutive_empty_posts >= 3:
            obs_type = ObservationType.DOM_INTEGRITY
        elif status_code >= 400:
            obs_type = ObservationType.HTTP_STATUS
        elif status_code == 200 or status_code == 0:
            # Fix Bug A: status_code=0 (sem erro HTTP) e status_code=200 são ambientes saudáveis.
            # Entrar em HTTP_STATUS nesses casos causava um tool call get_block_severity
            # desnecessário — overhead sem benefício. Retorna HEALTHY diretamente via SESSION_VALIDITY.
            obs_type = ObservationType.SESSION_VALIDITY
        else:
            obs_type = ObservationType.HTTP_STATUS

        observation = Observation(
            obs_type=obs_type,
            status_code=status_code,
            data={
                "target": target,
                "response_body": response_body,
                "consecutive_empty_posts": consecutive_empty_posts,
                "screenshot_b64": screenshot_b64,
                "html_snippet": html_snippet,
                "cache_key": cache_key,
            },
        )

        return await self.run_cycle(observation)

    async def execute_action(self, cycle_result: CycleResult) -> dict:
        """
        Executa a ação sugerida pelo ciclo OODA.

        Usado pelo worker quando quer separar a decisão da execução.
        """
        if not cycle_result.action_result.success:
            return {
                "success": False,
                "tool": cycle_result.action_result.tool_name,
                "error": cycle_result.action_result.error,
            }

        return {
            "success": True,
            "tool": cycle_result.action_result.tool_name,
            "data": cycle_result.action_result.data,
        }
