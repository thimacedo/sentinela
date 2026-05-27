"""
SessionHealer — Renovação Automática de Sessões Instagram (PASA v83.6)

Responsabilidades:
  - Invocar o script unificado de cookies para múltiplos slots do .env.
  - Sincronizar sessionids na memória do processo atual.
"""
import asyncio
import logging
import os
import sys

logger = logging.getLogger("core.autopilot.session_healer")


class SessionHealer:
    """
    Renova sessões Instagram expiradas de forma automatizada (PASA v83.6).
    Invocador do script unificado de exportação e login de múltiplos slots.
    """

    def __init__(self):
        self.script_path = os.path.join(os.getcwd(), "scripts", "export_playwright_cookies.py")

    async def heal(self, force: bool = False) -> bool:
        """
        Ponto de entrada de cura. Executa o script de renovação de cookies.
        Se force=True, passa a flag --force para realizar re-login geral por usuário/senha.
        """
        if not os.path.exists(self.script_path):
            logger.error(f"❌ [SessionHealer] Script de cookies não localizado em {self.script_path}")
            return False

        cmd = [sys.executable, self.script_path]
        if force:
            cmd.append("--force")

        logger.info(f"🔑 [SessionHealer] Iniciando subprocesso de cookies: {' '.join(cmd)}")
        
        try:
            # Executa de forma assíncrona para não bloquear a thread do Autopilot
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                logger.info("✅ [SessionHealer] Script de renovação de cookies concluído com sucesso.")
                # Recarrega variáveis do .env para a memória do processo ativo
                try:
                    from dotenv import load_dotenv
                    load_dotenv(override=True)
                    logger.info("🔄 [SessionHealer] Variáveis do .env recarregadas na memória atual.")
                except ImportError:
                    pass
                return True
            else:
                logger.error(f"❌ [SessionHealer] Script de cookies terminou com erro (code: {process.returncode})")
                logger.error(f"Stdout:\n{stdout_str}\nStderr:\n{stderr_str}")
                return False
                
        except Exception as e:
            logger.error(f"💥 [SessionHealer] Exceção ao executar script de cookies: {e}")
            return False

