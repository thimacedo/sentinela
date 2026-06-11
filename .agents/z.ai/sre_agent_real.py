"""
SREAgent — Agente de IA para Autocura e Resiliência Operacional (PASA v52.0)
═══════════════════════════════════════════════════════════════════════════
Loop cognitivo de baixo custo (regras determinísticas + LLM sob demanda)
que gerencia e executa ferramentas de SRE para restabelecer a saúde do pipeline.
"""
import logging
import os
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("core.autopilot.sre_agent")


class SREAgent:
    """
    Agente de SRE Autônomo com registro de ferramentas e OODA loop reativo.
    """

    def __init__(self, db_client=None, ai_service=None):
        self._db = db_client
        self._ai = ai_service

    @property
    def db(self):
        if self._db is None:
            from core.supabase_service import get_supabase_client
            self._db = get_supabase_client()
        return self._db

    @property
    def ai(self):
        if self._ai is None:
            from core.ai_service import ai_service
            self._ai = ai_service
        return self._ai

    def log_thought(self, thought: str):
        """Registra os pensamentos do agente no console do Watchdog/Dashboard."""
        msg = f"🤖 [SRE Agent] PENSAMENTO: {thought}"
        logger.info(msg)
        try:
            from watchdog import state
            state.add_log("info", msg)
        except ImportError:
            pass

    def log_action(self, action: str):
        """Registra as ações do agente no console do Watchdog/Dashboard."""
        msg = f"🛠️ [SRE Agent] AÇÃO: {action}"
        logger.info(msg)
        try:
            from watchdog import state
            state.add_log("warn", msg)
        except ImportError:
            pass

    # 🛠️ REGISTRO DE FERRAMENTAS (TOOLS)
    async def tool_restart_worker(self, worker_id: str) -> str:
        """Reinicia um worker específico via EventBus."""
        self.log_action(f"Chamando restart_worker para '{worker_id}'")
        try:
            from core.event_bus import local_bus
            local_bus.publish("control_command", {"command": "restart", "worker_id": worker_id})
            return f"Sucesso: Comando de reinício enviado para {worker_id}"
        except Exception as e:
            return f"Erro ao reiniciar worker: {e}"

    async def tool_restart_main_runner(self) -> str:
        """Reinicia o processo principal main_runner.py."""
        self.log_action("Chamando restart_main_runner")
        try:
            from watchdog import state
            if state.process and state.process.poll() is None:
                state.process.terminate()
                return "Sucesso: Processo main_runner terminado (Watchdog irá reiniciar automaticamente)."
            return "Aviso: Nenhum processo ativo para terminar."
        except Exception as e:
            return f"Erro ao terminar main_runner: {e}"

    async def tool_rotate_session(self) -> str:
        """Rotaciona sessões do Instagram usando o SessionHealer."""
        self.log_action("Chamando rotate_session (SessionHealer)")
        try:
            from core.autopilot.session_healer import SessionHealer
            healer = SessionHealer()
            success = await healer.heal(force=True)
            return "Sucesso: SessionHealer executado com sucesso." if success else "Falha: SessionHealer falhou ao renovar sessões."
        except Exception as e:
            return f"Erro no SessionHealer: {e}"

    async def tool_cooldown_target(self, username: str, duration_minutes: int = 120) -> str:
        """Desativa temporariamente um perfil problemático que causa erros no banco."""
        self.log_action(f"Chamando cooldown_target para '{username}' por {duration_minutes} minutos")
        try:
            self.db.table("candidatos").update({"status_monitoramento": "DESATIVADO"}).eq("username", username).execute()
            # Registra o cooldown na tabela de eventos do sistema
            self.db.table("system_events").insert({
                "event_type": "cooldown_target",
                "source": "sre_agent",
                "severity": "warning",
                "description": f"Perfil {username} colocado em cooldown por {duration_minutes} min.",
                "metadata": {"username": username, "duration_minutes": duration_minutes}
            }).execute()
            return f"Sucesso: Perfil {username} desativado temporariamente no Supabase."
        except Exception as e:
            return f"Erro ao colocar perfil em cooldown: {e}"

    async def tool_adjust_concurrency_and_jitter(self, concurrency: int, delay_seconds: int) -> str:
        """Ajusta parâmetros de concorrência e jitter para evitar rate limit."""
        self.log_action(f"Ajustando concorrência para {concurrency} e atraso para {delay_seconds}s")
        try:
            os.environ["NUM_SCRAPER_WORKERS"] = str(concurrency)
            os.environ["AUTOPILOT_FORCE_JITTER"] = "true"
            # Define valores em formato global para novos sub-processos
            return f"Sucesso: Variáveis de ambiente NUM_SCRAPER_WORKERS={concurrency} aplicadas."
        except Exception as e:
            return f"Erro ao ajustar variáveis: {e}"

    # 🧠 LOOP COGNITIVO OODA
    async def diagnose_and_heal(self, error_type: str, logs: str) -> str:
        """
        Observa e orienta o diagnóstico, escolhe e executa a melhor ferramenta.
        """
        self.log_thought(f"Iniciando diagnóstico para tipo de erro: {error_type}...")

        # 1. Filtros Determinísticos Rápidos (0 Tokens)
        if error_type == "SESSION_EXPIRED":
            self.log_thought("Erro de sessão expirada. Executando renovação de chaves...")
            return await self.tool_rotate_session()

        if error_type == "IP_BLOCK":
            self.log_thought("Bloqueio de IP detectado. Ajustando concorrência para baixo...")
            return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=15)

        if error_type == "RATE_LIMIT":
            self.log_thought("Rate limit atingido. Aumentando jitter operacional...")
            return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=10)

        # 2. IA sob demanda (DOM_CHANGE ou UNKNOWN)
        if error_type in ["DOM_CHANGE", "UNKNOWN"]:
            self.log_thought("Erro estrutural ou desconhecido. Consultando malha de IA...")
            
            system_prompt = (
                "Você é o Agente de SRE Autônomo do Sentinela. Sua missão é ler logs de erro e escolher a melhor ferramenta.\n"
                "Ferramentas Disponíveis:\n"
                "1. restart_main_runner(): reinicia o runner principal.\n"
                "2. rotate_session(): executa re-login de cookies expirados.\n"
                "3. adjust_concurrency_and_jitter(): reduz velocidade se houver rate limit / bloqueio.\n"
                "4. cooldown_target(username): desativa perfil se houver erro contínuo associado a um perfil específico.\n"
                "\n"
                "Responda APENAS com JSON no formato:\n"
                '{"tool": "restart_main_runner|rotate_session|adjust_concurrency_and_jitter|cooldown_target", '
                '"target_param": "username se for cooldown, ou vazio", "reason": "explicação curta"}'
            )

            prompt = f"LOGS DE ERRO RECENTES:\n{logs[:2000]}\n"

            try:
                res = await self.ai.chat_completion(prompt, system_prompt=system_prompt)
                if res and isinstance(res, dict):
                    tool_name = res.get("tool")
                    reason = res.get("reason", "Sem justificativa.")
                    self.log_thought(f"Decisão da IA: ferramenta '{tool_name}' devido a: {reason}")
                    
                    if tool_name == "rotate_session":
                        return await self.tool_rotate_session()
                    elif tool_name == "adjust_concurrency_and_jitter":
                        return await self.tool_adjust_concurrency_and_jitter(concurrency=1, delay_seconds=10)
                    elif tool_name == "cooldown_target" and res.get("target_param"):
                        return await self.tool_cooldown_target(res["target_param"])
                    elif tool_name == "restart_main_runner":
                        return await self.tool_restart_main_runner()
                    else:
                        self.log_thought("Ferramenta sugerida desconhecida. Executando reinício genérico.")
                        return await self.tool_restart_main_runner()
            except Exception as e:
                logger.error("Falha ao invocar IA no SREAgent: %s", e)
                self.log_thought("Falha na IA. Executando reinício seguro.")
                return await self.tool_restart_main_runner()

        # Fallback genérico para outros erros
        self.log_thought("Erro não-mapeado. Solicitando reinício do main_runner para restaurar integridade.")
        return await self.tool_restart_main_runner()


sre_agent = SREAgent()
