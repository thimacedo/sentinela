from __future__ import annotations

import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from core.voyant_service import voyant_service
from core.db import db_client
from core.ai_service import ai_service

logger = logging.getLogger("SaVoyant")

class SaVoyant(BaseSubAgent):
    """
    Subagente Linguista (SaVoyant) — PASA v92.4
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
        self._linguistics_context = ""
        self.biblia_path = "bases_pdf/BIBLIA_LINGUISTICA_FORENSE_PASA.md"

    def describe(self) -> str:
        return "SaVoyant — Subagente de Inteligência Linguística e Triagem PLN Determinística."

    async def setup(self) -> None:
        """Inicialização robusta com carregamento de bases em cache."""
        await super().setup()
        
        # 1. Verifica conectividade com Voyant
        if not await voyant_service.ping():
            logger.warning(f"⚠️ [{self.worker_id}] VoyantServer offline na porta 8888.")
        
        # 2. Carrega Bíblia Linguística em cache (evita I/O repetitivo)
        try:
            self._linguistics_context = await asyncio.to_thread(self._read_biblia)
            logger.info(f"✅ [{self.worker_id}] Base linguística carregada em cache.")
        except Exception as e:
            logger.error(f"❌ [{self.worker_id}] Falha ao carregar Bíblia Linguística: {e}")

    def _read_biblia(self) -> str:
        if os.path.exists(self.biblia_path):
            with open(self.biblia_path, "r", encoding="utf-8") as f:
                return f.read()[:3000] # Limite de 3k chars para contexto de prompt
        return ""

    async def teardown(self) -> None:
        """Limpeza de recursos do subagente."""
        await super().teardown()
        logger.info(f"🧹 [{self.worker_id}] Teardown concluído.")

    async def run_cycle(self) -> CycleResult:
        """Executa a análise linguística pericial do lote atual."""
        self.cycle += 1 # v92.4: Correção de contagem de ciclo
        
        try:
            # 1. Puxa comentários recentes para análise de inteligência
            res = await asyncio.to_thread(
                db_client.client.table("comentarios")
                .select("*")
                .eq("processado_ia", False) # Foca no que ainda não foi triado profundamente
                .order("data_coleta", desc=True)
                .limit(100)
                .execute
            )
            comments = res.data or []
            
            if not comments:
                return self._idle_result("Sem comentários pendentes para análise linguística.")

            # v92.4: Filtro de textos None/Vazios para evitar distorção no Voyant
            texts = [c.get("texto_bruto") for c in comments if c.get("texto_bruto")]
            if not texts:
                return self._idle_result("Lote de comentários sem conteúdo textual válido.")
            
            # 2. Análise Determinística via VoyantService
            voyant_data = await voyant_service.triage_batch(texts)
            
            # 3. Lógica de Fast-Drop (Economia de Tokens)
            # Se o Voyant estiver OK e o ratio for baixo, marcamos como NEUTRO e pulamos IA
            if voyant_data and voyant_data.get("drop"):
                await self._process_fast_drop(comments)
                return self._success_result(
                    items_collected=len(comments),
                    items_processed=len(comments),
                    score_delta=5.0,
                    metadata={"method": "voyant_fast_drop", "ratio": voyant_data.get("hostile_ratio")}
                )

            # 4. Raciocínio de IA sobre os dados do Voyant + Bases Linguísticas
            # Ocorre apenas se houver suspeita léxica (ratio >= threshold)
            insight = await self._generate_linguistic_insight(comments, voyant_data)
            
            # 5. Registro de Evento de Inteligência
            xp_reward = 5.0
            if insight and insight.get("relevancia", 0) > 0.6:
                await self._save_insight(insight)
                xp_reward = 15.0 # Bônus por insight relevante
                logger.info(f"✅ [{self.worker_id}] Insight Linguístico gerado: {insight['titulo']}")

            # 6. Retorno de Recompensa
            return self._success_result(
                items_collected=len(comments),
                items_processed=len(comments) if voyant_data else 0,
                score_delta=xp_reward,
                metadata={
                    "hostile_ratio": voyant_data.get("hostile_ratio") if voyant_data else 0,
                    "insight_title": insight.get("titulo") if insight else None,
                    "xp_delta": xp_reward # Explicitamente para o RewardEngine
                }
            )

        except Exception as e:
            logger.error(f"💥 [{self.worker_id}] Erro no ciclo SaVoyant: {e}")
            return self._failure_result(str(e))

    async def _process_fast_drop(self, comments: list):
        """Marca o lote como neutro no banco sem acionar LLM cloud."""
        ids = [c["id"] for c in comments]
        try:
            await asyncio.to_thread(
                db_client.client.table("comentarios").update({
                    "categoria_ia": "NEUTRO",
                    "confianca_ia": 0.85,
                    "is_hate": False,
                    "analise_pericial": "[SaVoyant] Fast-drop: vocabulário neutro validado por PLN determinístico local.",
                    "processado_ia": True
                }).in_("id", ids).execute
            )
            logger.info(f"⚡ [{self.worker_id}] Fast-drop concluído para {len(ids)} itens.")
        except Exception as e:
            logger.warning(f"⚠️ [{self.worker_id}] Falha ao gravar fast-drop: {e}")

    async def _generate_linguistic_insight(self, comments: list, voyant_data: Optional[dict]) -> Optional[dict]:
        """Usa IA para cruzar dados do Voyant com a Bíblia Linguística."""
        if not voyant_data:
            return None

        prompt = f"""
        Analise os seguintes dados léxicos extraídos pelo Voyant Tools de um lote de redes sociais:
        
        DADOS VOYANT:
        - Ratio Hostil: {voyant_data.get('hostile_ratio', 0):.2%}
        - Termos Hostis Detectados: {voyant_data.get('hostile_terms', [])}
        - Top Vocabulário: {list(voyant_data.get('top_terms', {}).keys())[:20]}
        
        BASE LINGUÍSTICA (REGRAS FORENSES):
        {self._linguistics_context}
        
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
                system_prompt="Você é o SaVoyant, subagente de Linguística Forense. Seja cínico, preciso e siga a Bíblia PASA.",
                response_format="json_object"
            )
            return res
        except Exception as e:
            logger.warning(f"⚠️ [{self.worker_id}] Falha na geração de insight via IA: {e}")
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
            logger.error(f"Erro ao salvar insight no banco: {e}")

    def _idle_result(self, msg: str) -> CycleResult:
        return CycleResult(
            worker_id=self.worker_id, 
            cycle=self.cycle, 
            error="no_tasks_available",
            source="sa_voyant",
            metadata={"reason": msg}
        )

    def _success_result(self, items_collected, items_processed, score_delta, metadata) -> CycleResult:
        # Garante que o xp_delta esteja no metadata para o RewardEngine
        metadata["xp_delta"] = score_delta
        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            status="success",
            extracted=items_collected,
            classified=items_processed,
            db_success=True,
            source="sa_voyant",
            metadata=metadata
        )

    def _failure_result(self, error: str) -> CycleResult:
        return CycleResult(
            worker_id=self.worker_id, 
            cycle=self.cycle, 
            status="failed", 
            error=error,
            source="sa_voyant"
        )
