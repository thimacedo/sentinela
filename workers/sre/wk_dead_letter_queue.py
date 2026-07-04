# Worker Dead Letter Queue (DLQ) Manager
# Arquivo: workers/sre/wk_dead_letter_queue.py

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from workers.base.worker_base import BaseWorker, WorkerMetrics
from workers.base.cycle_result import CycleResult
from core.skills.dead_letter_queue import dead_letter_queue
from core.supabase_client import get_supabase_client
from core.ntfy import NtfyNotifier

logger = logging.getLogger("worker.dead_letter_queue")

class WkDeadLetterQueue(BaseWorker):
    """
    Worker que gerencia o reprocessamento e auditoria da Dead Letter Queue (DLQ).
    Lê os alvos em quarentena de falha, re-enfileira os que atingiram o tempo de cooldown
    e dispara alertas Ntfy de nível crítico se persistirem falhas graves por mais de 3 rodadas.
    """
    def __init__(self, worker_id: str = "sre-dlq-01", config: Optional[dict] = None):
        super().__init__(worker_id, config or {})
        # Busca URL do Ntfy do .env ou config
        ntfy_url = os.getenv("NTFY_URL") or "https://ntfy.sh/sentinela-alertas"
        self.ntfy = NtfyNotifier(ntfy_url, enabled=True)
        self.db = None

    async def setup(self) -> None:
        """Inicializa dependências do Supabase client."""
        self.logger.info("[DLQ] Setup inicializado.")
        try:
            self.db = get_supabase_client()
        except Exception as e:
            self.logger.error(f"[DLQ] Erro ao obter cliente Supabase no setup: {e}")

    async def run_cycle(self) -> "CycleResult":
        """Executa um ciclo completo de varredura e re-enfileiramento da DLQ."""
        self.logger.info("[DLQ] Iniciando varredura de alvos pendentes para reprocessamento.")
        
        result = CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            db_success=True
        )

        if self.db is None:
            try:
                self.db = get_supabase_client()
            except Exception as e_db:
                self.logger.error(f"[DLQ] Erro ao obter cliente Supabase: {e_db}")
                result.error = "db_connection_error"
                return result
        
        # 1. Obtém itens prontos para retry da DLQ local
        pending_items = dead_letter_queue.get_pending_retries()
        if not pending_items:
            self.logger.info("[DLQ] Nenhum alvo em quarentena está pronto para re-tentativa neste ciclo.")
            return result

        self.logger.info(f"[DLQ] Encontrados {len(pending_items)} itens prontos para reprocessamento.")
        
        for item in pending_items:
            dlq_id = item["id"]
            username = item["target_username"]
            queue_id = item["queue_id"]
            retry_count = item["retry_count"]
            error_type = item["error_type"]
            
            # Se já falhou 3 vezes, envia alerta definitivo e não tenta reprocessar mais automaticamente
            if retry_count >= 3:
                self.logger.warning(f"🚨 [DLQ] Alvo @{username} falhou persistentemente 3+ vezes na DLQ ({error_type}). Requer analise manual.")
                try:
                    await self.ntfy.send(
                        title=f"Sentinela — Quarentena DLQ Crítica",
                        message=f"O alvo @{username} falhou 3 vezes seguidas de forma grave ({error_type}). Processamento suspenso.",
                        priority="urgent",
                        tags=["alarm_clock", "lock"]
                    )
                except Exception as e_ntfy:
                    self.logger.debug(f"[DLQ] Erro ao enviar notificacao: {e_ntfy}")
                
                # Incrementa apenas para marcar que já alertamos e remover da fila de retry
                dead_letter_queue.increment_retry(dlq_id)
                result.failed += 1
                continue
                
            # 2. Tenta re-enfileirar o alvo no Supabase
            try:
                self.logger.info(f"[DLQ] Tentando re-enfileirar @{username} (Tentativa #{retry_count + 1})...")
                
                now_iso = datetime.now(timezone.utc).isoformat()
                
                if queue_id:
                    # Se temos o queue_id original da fila_coleta, resetamos o status dele para PENDENTE
                    await asyncio.to_thread(
                        self.db.table("fila_coleta").update({
                            "status": "PENDENTE",
                            "prioridade": 2, # Prioridade normal para re-tentativa
                            "locked_by": None,
                            "locked_at": None,
                            "updated_at": now_iso
                        }).eq("id", queue_id).execute
                    )
                    self.logger.info(f"✅ [DLQ] Status de @{username} na fila_coleta resetado para PENDENTE.")
                else:
                    # Se não temos queue_id, criamos uma nova entrada pendente
                    payload = {
                        "username": username,
                        "status": "PENDENTE",
                        "prioridade": 2,
                        "created_at": now_iso,
                        "updated_at": now_iso
                    }
                    await asyncio.to_thread(
                        self.db.table("fila_coleta").insert(payload).execute
                    )
                    self.logger.info(f"✅ [DLQ] Novo registro criado na fila_coleta para @{username}.")

                # Incrementa as tentativas do item na DLQ local para aguardar mais 24h
                dead_letter_queue.increment_retry(dlq_id)
                result.inserted += 1
                
            except Exception as e:
                self.logger.error(f"❌ [DLQ] Erro ao re-enfileirar @{username}: {e}")
                result.failed += 1
                
        return result

    async def teardown(self) -> None:
        """Limpeza de conexões no encerramento."""
        self.logger.info("[DLQ] Teardown finalizado.")

    def describe(self) -> str:
        return "Gerenciador e Auditor da Dead Letter Queue (DLQ Manager)"
