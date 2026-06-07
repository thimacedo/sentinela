from __future__ import annotations

import asyncio
import logging
import os
import time
import json
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from workers.base.subagent_base import BaseSubAgent
from workers.base.cycle_result import CycleResult
from core.voyant_service import voyant_service
from core.db import db_client
from core.ai_service import ai_service

logger = logging.getLogger("SaVoyant")

# Configurações de Contexto
_BIBLIA_PATH = "bases_pdf/BIBLIA_LINGUISTICA_FORENSE_PASA.md"
_BIBLIA_MAX_CHARS = 5000  # v92.5: Aumentado para 5k para preservar regras críticas
_VOYANT_CHECK_COOLDOWN = 60  # Segundos entre verificações de saúde do servidor


class SaVoyant(BaseSubAgent):
    """
    Subagente Linguista (SaVoyant) — PASA v92.5
    Análise pericial incremental com suporte a N-gramas e resiliência de rede.

    Melhorias v92.5:
      - Processamento Incremental: usa checkpoint de timestamp para evitar re-análise.
      - Reconexão Dinâmica: tenta re-estabelecer contato com VoyantServer sem crashar.
      - Extração de Bigramas: identifica slogans coordenados localmente.
      - Validação de Schema: garante que o LLM retornou um insight íntegro.
    """

    def __init__(self, worker_id: str = "sa-voyant-01", config: Optional[dict] = None):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.hostile_threshold = float(os.getenv("VOYANT_HOSTILE_THRESHOLD", "0.08"))
        self._linguistics_context: str = ""
        
        # Checkpoint de processamento (Incremental)
        self._last_processed_ts: Optional[str] = None
        
        # Resiliência de Conexão
        self._voyant_ok = False
        self._last_voyant_check = 0

    def describe(self) -> str:
        return "SaVoyant — Subagente de Inteligência Linguística e Triagem PLN Determinística."

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    async def setup(self) -> None:
        await super().setup()
        
        # 1. Primeira verificação de conexão
        self._voyant_ok = await voyant_service.ping()
        if not self._voyant_ok:
            logger.warning("[%s] VoyantServer offline no boot. Modo degradado ativo.", self.worker_id)
        
        # 2. Carrega Checkpoint Inicial (Pega o timestamp do último comentário do banco como âncora)
        try:
            res = await asyncio.to_thread(
                db_client.client.table("comentarios")
                .select("data_coleta")
                .order("data_coleta", desc=True)
                .limit(1)
                .execute
            )
            if res.data:
                self._last_processed_ts = res.data[0]["data_coleta"]
                logger.info("[%s] Checkpoint inicial: %s", self.worker_id, self._last_processed_ts)
        except Exception as e:
            logger.warning("[%s] Falha ao carregar checkpoint inicial: %s", self.worker_id, e)

        # 3. Carrega Bíblia Linguística em cache
        self._linguistics_context = await asyncio.to_thread(self._load_biblia)

    async def teardown(self) -> None:
        await super().teardown()

    # ── Ciclo principal ──────────────────────────────────────────────────────

    async def run_cycle(self) -> CycleResult:
        """Executa a análise linguística pericial do lote atual."""
        self.cycle += 1

        # 1. Garante resiliência de conexão com Voyant
        await self._ensure_voyant_connection()

        try:
            # 2. Busca Incremental: apenas novos comentários desde o último ciclo
            query = db_client.client.table("comentarios").select("id, texto_limpo, texto_bruto, data_coleta")
            
            if self._last_processed_ts:
                query = query.gt("data_coleta", self._last_processed_ts)
            
            res = await asyncio.to_thread(
                query.order("data_coleta", desc=False).limit(100).execute
            )
            comments = res.data or []

            if not comments:
                return self._idle_result("Aguardando novos comentários para análise.")

            # 3. Atualiza Checkpoint para o próximo ciclo
            self._last_processed_ts = comments[-1]["data_coleta"]

            # 4. Normalização e Extração local de N-gramas (Bigramas)
            texts = [c.get("texto_limpo") or c.get("texto_bruto") for c in comments if (c.get("texto_limpo") or c.get("texto_bruto"))]
            if not texts:
                return self._idle_result("Lote sem conteúdo textual válido.")
            
            bigrams = self._extract_bigrams(texts)

            # 5. Triagem Voyant (Fast-Drop)
            voyant_data = None
            if self._voyant_ok:
                voyant_data = await voyant_service.triage_batch(texts)
                
                if voyant_data and voyant_data.get("drop"):
                    await self._apply_fast_drop(comments)
                    return self._success_result(len(comments), len(comments), 5.0, {
                        "method": "voyant_fast_drop", 
                        "ratio": voyant_data["hostile_ratio"],
                        "bigrams": bigrams[:5]
                    })

            # 6. Geração de Insight (IA + N-gramas + Voyant)
            insight = await self._generate_linguistic_insight(voyant_data, bigrams)
            
            xp = 5.0
            if insight and insight.get("relevancia", 0) > 0.6:
                await self._save_insight(insight)
                xp = 15.0
                logger.info("✅ [%s] Insight Linguístico Gerado: %s", self.worker_id, insight["titulo"])

            return self._success_result(len(comments), len(comments) if voyant_data else 0, xp, {
                "hostile_ratio": voyant_data.get("hostile_ratio", 0) if voyant_data else 0,
                "insight_title": insight.get("titulo") if insight else None,
                "bigrams": bigrams[:5],
                "xp_delta": xp
            })

        except Exception as e:
            logger.error("💥 [%s] Erro no ciclo SaVoyant: %s", self.worker_id, e, exc_info=True)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="sa_voyant", error=str(e)[:200])

    # ── Lógica Interna ───────────────────────────────────────────────────────

    async def _ensure_voyant_connection(self):
        """Tenta reconectar ao VoyantServer periodicamente se estiver offline."""
        now = time.time()
        if not self._voyant_ok or (now - self._last_voyant_check > _VOYANT_CHECK_COOLDOWN):
            self._voyant_ok = await voyant_service.ping()
            self._last_voyant_check = now
            if not self._voyant_ok:
                logger.debug("[%s] VoyantServer ainda inacessível.", self.worker_id)

    def _extract_bigrams(self, texts: list[str]) -> list[str]:
        """Extrai bigramas frequentes localmente para detectar slogans coordenados."""
        counter = Counter()
        for text in texts:
            words = text.lower().split()
            if len(words) < 2: continue
            bgs = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) if len(words[i]) > 3 and len(words[i+1]) > 3]
            counter.update(bgs)
        return [item[0] for item in counter.most_common(10)]

    def _load_biblia(self) -> str:
        try:
            if os.path.exists(_BIBLIA_PATH):
                with open(_BIBLIA_PATH, "r", encoding="utf-8") as f:
                    return f.read()[:_BIBLIA_MAX_CHARS]
            return ""
        except Exception as e:
            logger.error("❌ [%s] Erro ao carregar base linguística: %s", self.worker_id, e)
            return ""

    async def _generate_linguistic_insight(self, voyant_data: Optional[dict], bigrams: list[str]) -> Optional[dict]:
        """Usa IA para cruzar dados do Voyant, Bigramas e Regras Forenses."""
        prompt = f"""
        Analise estatística e pericial deste lote de comentários políticos:
        
        VOYANT (Unigramas): {list(voyant_data.get('top_terms', {}).keys())[:15] if voyant_data else 'Offline'}
        BIGRAMAS (Slogans): {bigrams}
        RATIO HOSTIL: {voyant_data.get('hostile_ratio', 0):.2% if voyant_data else 'N/A'}
        
        REGRAS PASA:
        {self._linguistics_context}
        
        TAREFA:
        1. Identifique se há 'Xenofobia', 'Ataque Institucional' ou 'Coordenação de Milícia Digital'.
        2. Avalie severidade (0-100) e relevância (0-1).
        
        RETORNE JSON:
        {{
            "titulo": "curto e impactante",
            "resumo": "análise técnica",
            "severidade": int,
            "relevancia": float,
            "categoria_mca": "EX: DANO_A_IMAGEM"
        }}
        """

        try:
            res = await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é o SaVoyant, analista de Linguística Forense. Siga o MCA v2.2.",
                response_format="json_object"
            )
            
            # Validação mínima de schema v92.5
            if isinstance(res, dict) and all(k in res for k in ["titulo", "resumo", "relevancia"]):
                return res
            return None
        except Exception as e:
            logger.warning("[%s] Falha na inferência de insight: %s", self.worker_id, e)
            return None

    async def _apply_fast_drop(self, comments: list):
        ids = [c["id"] for c in comments]
        try:
            await asyncio.to_thread(
                db_client.client.table("comentarios").update({
                    "categoria_ia": "NEUTRO",
                    "confianca_ia": 0.85,
                    "processado_ia": True,
                    "analise_pericial": "[SaVoyant] Fast-drop incremental: vocabulário seguro."
                }).in_("id", ids).execute
            )
        except Exception as e:
            logger.warning("[%s] Erro ao gravar fast-drop: %s", self.worker_id, e)

    async def _save_insight(self, insight: dict):
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
            logger.error("[%s] Erro ao salvar insight no banco: %s", self.worker_id, e)

    def _idle_result(self, msg: str) -> CycleResult:
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="sa_voyant", error="no_tasks_available", metadata={"reason": msg})

    def _success_result(self, collected, processed, xp, metadata) -> CycleResult:
        metadata["xp_delta"] = xp
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, status="success", source="sa_voyant", extracted=collected, classified=processed, db_success=True, metadata=metadata)

