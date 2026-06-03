"""
PASA v88.0 — DossierWorker: Sub-agente de Geração de Dossiês em PDF
Refatorado de script standalone (while True + sleep) para BaseWorker com ciclo de vida gerenciado.
Processa itens com status='Pendente' na tabela 'dossies' e gera os PDFs correspondentes.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult

logger = logging.getLogger("worker.dossier")


class DossierWorker(BaseWorker):
    """
    Sub-agente de geração de dossiês.

    Ciclo:
      1. Consulta a tabela `dossies` por itens com status='Pendente'.
      2. Para cada item, gera o PDF via ReportGenerator.
      3. Atualiza o status para 'Concluído' ou 'Falhou' no banco.

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

    def describe(self) -> str:
        return f"DossierWorker — Geração de PDFs de Dossiês (dir={self.report_dir})"

    async def setup(self) -> None:
        # Importa dependências pesadas apenas no setup (não no import time)
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
            logger.error(
                "❌ [DossierWorker] ReportGenerator não encontrado: %s. "
                "Verifique a instalação de 'processing/report_generator.py'.", e
            )

        # Garante diretório de saída
        os.makedirs(self.report_dir, exist_ok=True)
        logger.info("🚀 [DossierWorker] Pronto. %s", self.describe())

    async def teardown(self) -> None:
        self._supabase = None
        self._report_gen = None
        logger.info("🛑 [DossierWorker] Encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1

        # Verifica shutdown antes de começar
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

        # 1. Busca pendentes
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

        # 2. Processa cada um
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
            self.cycle, len(pending), success, failed,
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

    # ── Métodos privados ──────────────────────────────────────────────────────

    async def _fetch_pending(self) -> list[dict]:
        """Busca dossiês com status='Pendente' no Supabase."""
        try:
            res = self._supabase.table("dossies").select("*").eq("status", "Pendente").execute()
            return res.data or []
        except Exception as e:
            logger.error("❌ [DossierWorker] Erro ao buscar pendentes: %s", e)
            return []

    async def _process_dossier(self, dossier: dict) -> bool:
        """
        Processa um dossiê: marca como 'Processando', gera PDF e atualiza status.
        Retorna True em caso de sucesso, False em caso de falha.
        """
        import pandas as pd

        d_id = dossier.get("id")
        candidato_id = dossier.get("candidato_id", f"dossie_{d_id}")
        logger.info("→ [DossierWorker] Processando dossiê ID=%s (candidato=%s)", d_id, candidato_id)

        try:
            # Marca como Processando
            self._supabase.table("dossies").update({"status": "Processando"}).eq("id", d_id).execute()

            # Prepara dados para o gerador
            df = pd.DataFrame([dossier])
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Nome de arquivo seguro
            safe_name = "".join(
                c for c in str(candidato_id) if c.isalnum() or c in (" ", "_")
            ).strip().replace(" ", "_")
            pdf_name = f"{safe_name}_{ts}.pdf"
            out_path = os.path.join(self.report_dir, pdf_name)

            # Geração do PDF — roda em executor para não bloquear o event loop
            loop = asyncio.get_event_loop()
            gen_path = await loop.run_in_executor(
                None,
                self._report_gen.generate_pdf,
                df,
                out_path,
            )

            if gen_path and os.path.exists(gen_path):
                self._supabase.table("dossies").update({
                    "status": "Concluído",
                    "report_path": gen_path,
                }).eq("id", d_id).execute()
                logger.info("✅ [DossierWorker] PDF gerado: %s", gen_path)
                return True
            else:
                raise RuntimeError("ReportGenerator não retornou caminho válido.")

        except Exception as e:
            logger.error("❌ [DossierWorker] Erro no dossiê ID=%s: %s", d_id, e)
            try:
                self._supabase.table("dossies").update({
                    "status": "Falhou",
                    "error_log": str(e)[:500],
                }).eq("id", d_id).execute()
            except Exception as db_err:
                logger.error("❌ [DossierWorker] Erro ao registrar falha no banco: %s", db_err)
            return False
