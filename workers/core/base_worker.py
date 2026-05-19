"""
Contratos Base para Workers (Protocolo Diamond)
Arquitetura Open/Closed: Novos workers devem herdar desta classe.
"""
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, UTC
import logging

class BaseWorker(ABC):
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.logger = logging.getLogger(name)

    async def execute(self, *args, **kwargs):
        """Método principal. Faz o wrap de segurança e logs ao redor do processamento central."""
        self.logger.info(f"[{self.name}] Worker iniciado em {datetime.now(UTC).isoformat()}")
        try:
            await self._run(*args, **kwargs)
            self.logger.info(f"[{self.name}] Worker finalizado com sucesso.")
        except Exception as e:
            self.logger.error(f"[{self.name}] Falha crítica: {str(e)}", exc_info=True)
            self.handle_failure(e)
            raise

    @abstractmethod
    async def _run(self, *args, **kwargs):
        """A lógica de negócio central do worker. DEVE ser implementada."""
        pass

    def handle_failure(self, exception: Exception):
        """Hook opcional para tratamento customizado de falhas (ex: enviar alerta)."""
        pass
