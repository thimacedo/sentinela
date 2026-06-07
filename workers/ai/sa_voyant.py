from __future__ import annotations

import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from workers.base.subagent_base import BaseSubAgent
from core.voyant_service import voyant_service
from core.db import db_client
from core.ai_service import ai_service

logger = logging.getLogger("SaVoyant")

class SaVoyant(BaseSubAgent):
    """
    Subagente Linguista (SaVoyant) — PASA v92.0.1
    Integra Voyant Tools com Raciocínio de IA e Bases de Linguística Forense.
    
    Responsabilidades:
      - Realizar triagem léxica profunda via TF-IDF (Voyant).
      - Aplicar regras da 'Bíblia Linguística Forense' para evitar falsos positivos.
      - Identificar padrões de 'Ataque Institucional' e 'Xenofobia' via N-gramas.
      - Gerar insights periciais salvos no system_events.
    """

    def __init__(self, worker_id: str = "sa-voyant-01", config: Optional[dict] = None):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.hostile_threshold = float(os.getenv("VOYANT_HOSTILE_THRESHOLD", "0.08"))
        self.linguistics_docs = [
            "bases_pdf/BIBLIA_LINGUISTICA_FORENSE_PASA.md",
            "bases_pdf/lf.md",
            "bases_pdf/Monitoramento de Discurso de Ódio e Violência.md"
        ]

    def describe(self) -> str:
        return "SaVoyant — Subagente de Inteligência Linguística e Triagem PLN Determinística."

    async def setup(self) -> None:
        await super().setup()
        # Verifica se o VoyantServer está online
        if not await voyant_service.ping():
            logger.warning(f"⚠️ [{self.worker_id}] VoyantServer offline. Operando em modo degradado (Apenas IA).")

    async def run_cycle(self):
        """Executa a análise linguística pericial do lote atual."""
        try:
            # 1. Puxa comentários recentes para análise de inteligência
            res = await asyncio.to_thread(
                db_client.client.table("comentarios")
                .select("*")
                .order("data_coleta", desc=True)
                .limit(100)
                .execute
            )
            comments = res.data or []
            
            if not comments:
                return self._idle_result("Sem comentários para análise linguística.")

            texts = [c.get("texto_limpo") or c.get("texto_bruto") for c in comments]
            
            # 2. Análise Determinística via VoyantService
            voyant_data = await voyant_service.triage_batch(texts)
            
            # 3. Raciocínio de IA sobre os dados do Voyant + Bases Linguísticas
            insight = await self._generate_linguistic_insight(comments, voyant_data)
            
            # 4. Registro de Evento de Inteligência
            if insight and insight.get("relevancia", 0) > 0.6:
                await self._save_insight(insight)
                logger.info(f"✅ [{self.worker_id}] Insight Linguístico gerado: {insight['titulo']}")

            # 5. Retorno de Recompensa (PASA v92.0)
            return self._success_result(
                items_collected=len(comments),
                items_processed=len(comments) if voyant_data else 0,
                score_delta=15.0 if insight else 5.0,
                metadata={
                    "hostile_ratio": voyant_data.get("hostile_ratio") if voyant_data else 0,
                    "top_terms": list(voyant_data.get("top_terms", {}).keys())[:10] if voyant_data else [],
                    "insight_title": insight.get("titulo") if insight else None
                }
            )

        except Exception as e:
            logger.error(f"💥 [{self.worker_id}] Erro no ciclo Voyant: {e}")
            return self._failure_result(str(e))

    async def _generate_linguistic_insight(self, comments: list, voyant_data: Optional[dict]) -> Optional[dict]:
        """Usa IA para cruzar dados do Voyant com a Bíblia Linguística."""
        if not voyant_data:
            return None

        # Carrega contexto da Bíblia Linguística (resumo)
        context_docs = ""
        try:
            with open("bases_pdf/BIBLIA_LINGUISTICA_FORENSE_PASA.md", "r", encoding="utf-8") as f:
                context_docs = f.read()[:2000] # Primeiros 2k chars como contexto
        except: pass

        prompt = f"""
        Analise os seguintes dados léxicos extraídos pelo Voyant Tools de um lote de redes sociais:
        
        DADOS VOYANT:
        - Ratio Hostil: {voyant_data.get('hostile_ratio', 0):.2%}
        - Termos Hostis Detectados: {voyant_data.get('hostile_terms', [])}
        - Top Vocabulário: {list(voyant_data.get('top_terms', {}).keys())[:20]}
        
        BASE LINGUÍSTICA (REGRAS):
        {context_docs}
        
        TAREFA:
        1. Identifique se há um padrão de 'Xenofobia Regionalizada', 'Ataque Institucional' ou 'Sarcasmo' baseado nos termos.
        2. Avalie a severidade real do lote (0-100).
        3. Gere um título curto e um resumo pericial.
        
        RETORNE APENAS JSON:
        {{
            "titulo": "Título do Insight",
            "resumo": "Análise detalhada...",
            "relevancia": 0.0 a 1.0,
            "severidade": 0 a 100,
            "categoria_mca": "EX: ODIO_IDENTITARIO"
        }}
        """

        try:
            res = await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é o Subagente Voyant, especialista em Linguística Forense Política.",
                response_format="json_object"
            )
            return res
        except:
            return None

    async def _save_insight(self, insight: dict):
        """Salva o insight no banco como evento de sistema."""
        try:
            await asyncio.to_thread(
                db_client.client.table("system_events").insert({
                    "event_type": "linguistic_insight",
                    "source": self.worker_id,
                    "severity": "warning" if insight.get("severidade", 0) > 50 else "info",
                    "description": f"{insight['titulo']}: {insight['resumo']}",
                    "metadata": insight
                }).execute
            )
        except Exception as e:
            logger.error(f"Erro ao salvar insight: {e}")

    def _idle_result(self, msg: str):
        from workers.base.cycle_result import CycleResult
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, error=msg)

    def _success_result(self, items_collected, items_processed, score_delta, metadata):
        from workers.base.cycle_result import CycleResult
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            extracted=items_collected,
            classified=items_processed,
            db_success=True,
            metadata=metadata
        )

    def _failure_result(self, error: str):
        from workers.base.cycle_result import CycleResult
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, error=error)

