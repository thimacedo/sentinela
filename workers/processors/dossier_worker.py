"""
PASA v88.0 — DossierWorker: Sub-agente de Geração de Dossiês em PDF
Refatorado de script standalone (while True + sleep) para BaseWorker com ciclo de vida gerenciado.
Processa itens da tabela 'dossies' e gera os PDFs correspondentes.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Optional

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("worker.dossier")


class DossierWorker(BaseWorker):
    """
    Sub-agente de geração de dossiês.

    Retorna CycleResult com:
      - extracted = total de pendentes encontrados
      - inserted  = total de PDFs gerados com sucesso
      - failed    = total de erros na geração
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.report_dir: str = config.get("report_dir", "reports")
        self._supabase = None
        self._report_gen = None
        self._status_column: Optional[str] = None
        self._path_column = "arquivo_path"
        self._error_column: Optional[str] = None

    def describe(self) -> str:
        return f"DossierWorker — Geração de PDFs de Dossiês (dir={self.report_dir})"

    async def setup(self) -> None:
        try:
            from core.supabase_service import get_supabase_client
            self._supabase = get_supabase_client()
            logger.info("✅ [DossierWorker] Conexão Supabase estabelecida.")
        except Exception as e:
            logger.error("❌ [DossierWorker] Falha ao conectar Supabase: %s", e)

        try:
            from processing.report_generator import ReportGenerator
            self._report_gen = ReportGenerator()
            logger.info("✅ [DossierWorker] ReportGenerator inicializado.")
        except ImportError as e:
            logger.error("❌ [DossierWorker] ReportGenerator não encontrado: %s", e)

        os.makedirs(self.report_dir, exist_ok=True)
        await self._detect_dossies_columns()
        logger.info("🚀 [DossierWorker] Pronto. %s", self.describe())

    async def teardown(self) -> None:
        self._supabase = None
        self._report_gen = None
        logger.info("🛑 [DossierWorker] Encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        if self.shutdown_event and self.shutdown_event.is_set():
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="dossier",
                error="shutdown_requested",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        if not self._supabase or not self._report_gen:
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="dossier",
                error="dependencies_unavailable",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        logger.info("📋 [DossierWorker] Ciclo #%d — buscando dossiês pendentes.", self.cycle)
        pending = await self._fetch_pending()
        if not pending:
            logger.info("✅ [DossierWorker] Nenhum dossiê pendente.")
            return CycleResult(
                worker_id=self.worker_id,
                cycle=self.cycle,
                source="dossier",
                error="no_tasks_available",
                duration=asyncio.get_event_loop().time() - start_time,
            )

        logger.info("📄 [DossierWorker] %d dossiê(s) encontrado(s).", len(pending))

        success = 0
        failed = 0
        for dossier in pending:
            if self.shutdown_event and self.shutdown_event.is_set():
                logger.info("🛑 [DossierWorker] Shutdown durante processamento. Parando.")
                break

            ok = await self._process_dossier(dossier)
            if ok:
                success += 1
            else:
                failed += 1

        logger.info(
            "📊 [DossierWorker] Ciclo #%d | Encontrados=%d | Gerados=%d | Falhas=%d",
            self.cycle,
            len(pending),
            success,
            failed,
        )

        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            source="dossier",
            extracted=len(pending),
            inserted=success,
            failed=failed,
            db_success=True,
            simulated=False,
            duration=asyncio.get_event_loop().time() - start_time,
            metadata={"success": success, "failed": failed},
        )

    async def _detect_dossies_columns(self) -> None:
        if not self._supabase:
            return
        try:
            sample = self._supabase.table("dossies").select("*").limit(1).execute()
            rows = sample.data or []
            if not rows:
                return

            keys = set((rows[0] or {}).keys())
            if "status" in keys:
                self._status_column = "status"
            elif "situacao" in keys:
                self._status_column = "situacao"
            elif "estado" in keys:
                self._status_column = "estado"
            else:
                self._status_column = None

            if "arquivo_path" in keys:
                self._path_column = "arquivo_path"
            elif "report_path" in keys:
                self._path_column = "report_path"

            if "error_log" in keys:
                self._error_column = "error_log"
            elif "erro" in keys:
                self._error_column = "erro"

            logger.info(
                "[DossierWorker] Schema detectado: status=%s | path=%s | error=%s",
                self._status_column or "(nenhum)",
                self._path_column,
                self._error_column or "(nenhum)",
            )
        except Exception as e:
            logger.warning("[DossierWorker] Falha ao detectar schema de dossies: %s", e)

    def _build_update_payload(self, status_value: Optional[str] = None, report_path: Optional[str] = None, error_text: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if status_value and self._status_column:
            payload[self._status_column] = status_value
        if report_path:
            payload[self._path_column] = report_path
        if error_text and self._error_column:
            payload[self._error_column] = error_text[:500]
        return payload

    async def _fetch_pending(self) -> list[dict]:
        try:
            if self._status_column:
                res = self._supabase.table("dossies").select("*").eq(self._status_column, "Pendente").execute()
                return res.data or []

            res = self._supabase.table("dossies").select("*").is_(self._path_column, "null").limit(25).execute()
            return res.data or []
        except Exception as e:
            msg = str(e)
            if "column dossies.status does not exist" in msg:
                self._status_column = None
                logger.warning("[DossierWorker] Coluna de status inexistente em dossies. Usando fallback por arquivo_path nulo.")
                try:
                    res = self._supabase.table("dossies").select("*").is_(self._path_column, "null").limit(25).execute()
                    return res.data or []
                except Exception as e2:
                    logger.error("❌ [DossierWorker] Erro ao buscar pendentes no fallback: %s", e2)
                    return []

            logger.error("❌ [DossierWorker] Erro ao buscar pendentes: %s", e)
            return []

    async def _process_dossier(self, dossier: dict) -> bool:
        d_id = dossier.get("id")
        candidato_id = dossier.get("candidato_id", f"dossie_{d_id}")
        logger.info("→ [DossierWorker] Processando dossiê ID=%s (candidato=%s)", d_id, candidato_id)

        try:
            processing_payload = self._build_update_payload(status_value="Processando")
            if processing_payload:
                self._supabase.table("dossies").update(processing_payload).eq("id", d_id).execute()

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in str(candidato_id) if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
            pdf_name = f"{safe_name}_{ts}.pdf"
            out_path = os.path.join(self.report_dir, pdf_name)

            loop = asyncio.get_event_loop()
            gen_path = await loop.run_in_executor(None, self._report_gen.generate_pdf, [dossier], out_path, str(candidato_id))

            if gen_path and os.path.exists(gen_path):
                done_payload = self._build_update_payload(status_value="Concluído", report_path=gen_path)
                if done_payload:
                    self._supabase.table("dossies").update(done_payload).eq("id", d_id).execute()
                logger.info("✅ [DossierWorker] PDF gerado: %s", gen_path)
                return True

            raise RuntimeError("ReportGenerator não retornou caminho válido.")
        except Exception as e:
            logger.error("❌ [DossierWorker] Erro no dossiê ID=%s: %s", d_id, e)
            try:
                fail_payload = self._build_update_payload(status_value="Falhou", error_text=str(e))
                if fail_payload:
                    self._supabase.table("dossies").update(fail_payload).eq("id", d_id).execute()
            except Exception as db_err:
                logger.error("❌ [DossierWorker] Erro ao registrar falha no banco: %s", db_err)
            return False
