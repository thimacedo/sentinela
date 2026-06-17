"""
SREAgent — Agente de IA para Autocura e Resiliência Operacional (PASA v98.2)
═══════════════════════════════════════════════════════════════════════════
Loop cognitivo de baixo custo (regras determinísticas + LLM sob demanda)
que gerencia e executa ferramentas de SRE para restabelecer a saúde do pipeline.

v98.2: Adicionada vigilância proativa de coleta (run_proactive_watch).
       O SRE Agent agora detecta silêncios no banco — não apenas erros de processo.
"""
import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("core.autopilot.sre_agent")

# Minutos sem coleta antes de considerar o sistema parado
_HEARTBEAT_MAX_GAP_MIN = int(os.getenv("HEARTBEAT_MAX_GAP_MIN", "15"))
# Intervalo do loop de vigilância proativa (segundos)
_PROACTIVE_WATCH_INTERVAL = int(os.getenv("SRE_WATCH_INTERVAL_S", "1200"))  # 20 min


class SREAgent:
    """
    Agente de SRE Autônomo com registro de ferramentas e OODA loop reativo.
    v98.2: inclui vigilância proativa de gaps de coleta.
    """

    def __init__(self, db_client=None, ai_service=None):
        self._db = db_client
        self._ai = ai_service
        self._watch_task: Optional[asyncio.Task] = None

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

    def _record_event(self, event_type: str, severity: str, description: str, metadata: dict = None):
        """Grava um evento em system_events para rastreabilidade."""
        try:
            self.db.table("system_events").insert({
                "event_type": event_type,
                "source": "sre_agent",
                "severity": severity,
                "description": description,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.warning("[SRE Agent] Falha ao gravar system_event: %s", e)

    # ─── FERRAMENTAS ──────────────────────────────────────────────────────────

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
            self._record_event(
                "cooldown_target", "warning",
                f"Perfil {username} colocado em cooldown por {duration_minutes} min.",
                {"username": username, "duration_minutes": duration_minutes}
            )
            return f"Sucesso: Perfil {username} desativado temporariamente no Supabase."
        except Exception as e:
            return f"Erro ao colocar perfil em cooldown: {e}"

    async def tool_adjust_concurrency_and_jitter(self, concurrency: int, delay_seconds: int) -> str:
        """Ajusta parâmetros de concorrência e jitter para evitar rate limit."""
        self.log_action(f"Ajustando concorrência para {concurrency} e atraso para {delay_seconds}s")
        try:
            os.environ["NUM_SCRAPER_WORKERS"] = str(concurrency)
            os.environ["AUTOPILOT_FORCE_JITTER"] = "true"
            return f"Sucesso: Variáveis de ambiente NUM_SCRAPER_WORKERS={concurrency} aplicadas."
        except Exception as e:
            return f"Erro ao ajustar variáveis: {e}"

    async def tool_kill_duplicate_processes(self) -> str:
        """
        [v98.3] Ferramenta autônoma de SRE para matar instâncias zumbis ou duplicadas do main_runner.
        Substitui o antigo script procedimental watchdog_duplicate_killer.
        """
        self.log_action("Chamando tool_kill_duplicate_processes")
        try:
            import os
            import subprocess
            
            # Utiliza powershell nativo no Win ou ps/grep no Linux para identificar
            if os.name == 'nt':
                cmd = "powershell -Command \"Get-CimInstance Win32_Process -Filter 'Name=\\'python.exe\'' | Where-Object {$_.CommandLine -match 'main_runner.py'} | Select-Object ProcessId | ConvertTo-Json\""
                flags = 0x08000000 
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True, creationflags=flags)
            else:
                cmd = "ps aux | grep main_runner.py | grep -v grep | awk '{print $2}'"
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            pids = []
            if result.returncode == 0 and result.stdout.strip():
                if os.name == 'nt':
                    import json
                    try:
                        data = json.loads(result.stdout)
                        if isinstance(data, dict): data = [data]
                        pids = [int(item.get("ProcessId", 0)) for item in data if item.get("ProcessId")]
                    except: pass
                else:
                    pids = [int(p) for p in result.stdout.strip().split('\n') if p.isdigit()]
            
            current_pid = os.getpid()
            killed = 0
            
            # Mantém apenas um processo (preferencialmente o atual se for main_runner, ou o primeiro)
            keeper_pid = current_pid if current_pid in pids else (pids[0] if pids else None)
            
            for pid in pids:
                if pid != keeper_pid and pid != current_pid:
                    try:
                        if os.name == 'nt':
                            subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True, creationflags=0x08000000)
                        else:
                            subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
                        killed += 1
                        logger.info(f"[SRE Agent] Morto processo duplicado PID {pid}")
                    except: pass

            if killed > 0:
                msg = f"Sucesso: {killed} processos zumbis/duplicados encerrados."
                self._record_event("ZOMBIE_KILL", "warning", msg, {"pids_killed": killed})
                return msg
            else:
                return "Nenhum processo duplicado encontrado para ser encerrado."
                
        except Exception as e:
            logger.error(f"[SRE Agent] Erro na ferramenta duplicate_killer: {e}")
            return f"Erro ao executar duplicate_killer: {e}"

    async def tool_check_collection_health(self) -> Dict[str, Any]:
        """
        [v98.2] Verifica o gap de coleta consultando o banco diretamente.
        Retorna status e gap em minutos. Se crítico, dispara restart automático.
        """
        self.log_thought("Verificando saúde da coleta no banco...")
        try:
            result = self.db.table("comentarios") \
                .select("data_coleta") \
                .order("data_coleta", desc=True) \
                .limit(1) \
                .execute()

            if not result.data:
                gap_min = 9999
                ultima = None
            else:
                ultima_str = result.data[0]["data_coleta"]
                ultima = datetime.fromisoformat(ultima_str.replace("Z", "+00:00"))
                gap_min = (datetime.now(timezone.utc) - ultima).total_seconds() / 60

            status = "ok" if gap_min <= _HEARTBEAT_MAX_GAP_MIN else "critico"

            logger.info(
                "[SRE Agent] Saúde da coleta: gap=%.0fmin | threshold=%dmin | status=%s",
                gap_min, _HEARTBEAT_MAX_GAP_MIN, status
            )

            if status == "critico":
                descricao = (
                    f"Coleta parada há {round(gap_min)} minutos "
                    f"(threshold: {_HEARTBEAT_MAX_GAP_MIN}min). "
                    f"Última: {ultima.strftime('%d/%m %H:%M') if ultima else 'nunca'}. "
                    "Disparando restart automático."
                )
                self.log_action(f"⚠️ {descricao}")
                self._record_event("COLETA_PARADA", "critical", descricao, {
                    "gap_minutes": round(gap_min),
                    "ultima_coleta": ultima.isoformat() if ultima else None,
                    "trigger": "sre_agent_proactive_watch",
                    "action": "restart_main_runner",
                })
                await self._notify_whatsapp(descricao)
                restart_result = await self.tool_restart_main_runner()
                self.log_action(f"Restart: {restart_result}")

            return {"status": status, "gap_min": round(gap_min), "ultima_coleta": str(ultima)}

        except Exception as e:
            logger.error("[SRE Agent] Erro ao checar saúde da coleta: %s", e)
            return {"status": "erro", "gap_min": -1, "error": str(e)}

    async def _notify_whatsapp(self, message: str):
        """Envia alerta WhatsApp via CallMeBot (se WHATSAPP_PHONE configurado)."""
        phone = os.getenv("WHATSAPP_PHONE", "")
        api_key = os.getenv("WHATSAPP_API_KEY", "")
        if not phone or not api_key:
            return
        try:
            import urllib.request
            import urllib.parse
            texto = f"🚨 [Sentinela SRE] {message}"
            url = (
                f"https://api.callmebot.com/whatsapp.php"
                f"?phone={phone}&apikey={api_key}"
                f"&text={urllib.parse.quote(texto)}"
            )
            urllib.request.urlopen(url, timeout=8)
            logger.info("[SRE Agent] Alerta WhatsApp enviado.")
        except Exception as e:
            logger.warning("[SRE Agent] Falha ao enviar WhatsApp: %s", e)

    # ─── VIGILÂNCIA PROATIVA ──────────────────────────────────────────────────

    async def run_proactive_watch(self):
        """
        [v98.2] Loop de vigilância autônoma — iniciado pelo Watchdog em background.
        Checa o gap de coleta a cada SRE_WATCH_INTERVAL_S segundos (padrão: 20min).
        Não precisa ser chamado por erro — detecta silêncios por conta própria.
        """
        logger.info(
            "[SRE Agent] 👁️ Vigilância proativa iniciada (intervalo: %ds | threshold: %dmin)",
            _PROACTIVE_WATCH_INTERVAL, _HEARTBEAT_MAX_GAP_MIN
        )
        while True:
            try:
                await self.tool_check_collection_health()
            except Exception as e:
                logger.error("[SRE Agent] Erro no loop de vigilância proativa: %s", e)
            await asyncio.sleep(_PROACTIVE_WATCH_INTERVAL)

    def start_proactive_watch(self, loop: asyncio.AbstractEventLoop = None):
        """
        Inicia o loop de vigilância proativa como task assíncrona.
        Chamado pelo Watchdog no boot para garantir monitoramento contínuo.
        """
        if self._watch_task and not self._watch_task.done():
            logger.debug("[SRE Agent] Vigilância proativa já está rodando.")
            return
        try:
            lp = loop or asyncio.get_event_loop()
            self._watch_task = lp.create_task(self.run_proactive_watch())
            logger.info("[SRE Agent] ✅ Task de vigilância proativa registrada.")
        except RuntimeError:
            logger.debug("[SRE Agent] Sem event loop para iniciar vigilância proativa.")

    # ─── LOOP COGNITIVO OODA ──────────────────────────────────────────────────

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

        if error_type == "COLETA_PARADA":
            self.log_thought("Silêncio de coleta detectado. Verificando saúde e reiniciando...")
            result = await self.tool_check_collection_health()
            return f"Verificação de saúde: {result}"

        if error_type == "NORMAL_EMPTY":
            self.log_thought("Perfil sem posts ou comentários (erro de negócio). Nenhuma ação necessária.")
            return "Nenhuma ação de SRE necessária: comportamento normal de perfil vazio ou privado."

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
                "5. check_collection_health(): verifica gap de coleta e reinicia se necessário.\n"
                "\n"
                "Responda APENAS com JSON no formato:\n"
                '{"tool": "restart_main_runner|rotate_session|adjust_concurrency_and_jitter|cooldown_target|check_collection_health", '
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
                    elif tool_name == "check_collection_health":
                        result = await self.tool_check_collection_health()
                        return str(result)
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
