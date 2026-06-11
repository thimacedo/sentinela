from __future__ import annotations

import asyncio
import logging
import os
import time
import json
import re
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
_BIBLIA_MAX_CHARS = 5000  
_VOYANT_CHECK_COOLDOWN = 60  

# v92.6: Dicionário de Stopwords para limpeza de bigramas
STOP_WORDS_PT = {
    "que", "não", "com", "uma", "para", "dos", "das", "nos", "nas",
    "por", "mas", "como", "mais", "ao", "aos", "seu", "sua", "seus",
    "suas", "este", "esta", "esse", "essa", "isso", "isto", "aquilo",
    "ele", "ela", "eles", "elas", "nos", "nós", "vos", "tu", "mim",
    "te", "lhe", "de", "em", "no", "na", "do", "da", "um", "uma",
    "e", "ou", "mas", "porém", "todavia", "contudo",
}

class SaVoyant(BaseSubAgent):
    """
    Subagente Linguista (SaVoyant) — PASA v92.6
    
    Resolvendo Bugs Críticos (Auditoria 2026-06-07):
      - Bug #2: Checkpoint baseado em auditoria (voyant_checkpoint) em vez de timestamps de comentários.
      - Bug #3: Fast-Drop granular que NÃO sobrescreve classificações profissionais de IA.
      - Bug #4-6: Melhoria de bigramas, sanitização de texto e proteção contra NULLs.
    """

    def __init__(self, worker_id: str = "sa-voyant-01", config: Optional[dict] = None):
        cfg = config or {}
        super().__init__(worker_id, cfg)
        self.hostile_threshold = float(os.getenv("VOYANT_HOSTILE_THRESHOLD", "0.08"))
        self._linguistics_context: str = ""
        self._last_processed_ts: Optional[str] = None
        self._voyant_ok = False
        self._last_voyant_check = 0

    def describe(self) -> str:
        return "SaVoyant — Subagente de Inteligência Linguística (PLN Determinística + Auditoria)."

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    async def setup(self) -> None:
        await super().setup()
        
        self._voyant_ok = await voyant_service.ping()
        if not self._voyant_ok:
            logger.warning("[%s] VoyantServer offline no boot. Operando em modo IA pura.", self.worker_id)
        
        # Bug #2 FIX: Carrega checkpoint persistente dos eventos de sistema
        self._last_processed_ts = await self._load_initial_checkpoint()
        
        # Carrega Bíblia Linguística em cache
        self._linguistics_context = await asyncio.to_thread(self._load_biblia)

    async def _load_initial_checkpoint(self) -> Optional[str]:
        """Busca o último ponto de análise SALVO pelo SaVoyant."""
        try:
            res = await asyncio.to_thread(
                db_client.client.table("system_events")
                .select("metadata")
                .eq("event_type", "voyant_checkpoint")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if res.data:
                ts = res.data[0]["metadata"].get("last_processed_ts")
                logger.info("[%s] Checkpoint persistente localizado: %s", self.worker_id, ts)
                return ts
        except Exception as e:
            logger.warning("[%s] Falha ao carregar checkpoint persistente: %s", self.worker_id, e)
        return None

    def _load_biblia(self) -> str:
        try:
            if os.path.exists(_BIBLIA_PATH):
                with open(_BIBLIA_PATH, "r", encoding="utf-8") as f:
                    return f.read()[:_BIBLIA_MAX_CHARS]
            return ""
        except Exception as e:
            logger.error("❌ [%s] Erro ao carregar base linguística: %s", self.worker_id, e)
            return ""

    async def teardown(self) -> None:
        await super().teardown()

    # ── Ciclo principal ──────────────────────────────────────────────────────

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        await self._ensure_voyant_connection()

        try:
            # Bug #6 FIX: Proteção contra NULLs no timestamp
            query = db_client.client.table("comentarios")\
                .select("id, texto_limpo, texto_bruto, data_coleta, processado_ia")\
                .not_.is_("data_coleta", "null")
            
            if self._last_processed_ts:
                query = query.gt("data_coleta", self._last_processed_ts)
            
            res = await asyncio.to_thread(
                query.order("data_coleta", desc=False).limit(100).execute
            )
            comments = res.data or []

            if not comments:
                return self._idle_result("Fila incremental vazia.")

            # Bug #5 FIX: Sanitização robusta e separação de texto
            texts = self._sanitize_texts(comments)
            if not texts:
                # Se não há texto, avançamos o checkpoint para não travar
                self._last_processed_ts = comments[-1]["data_coleta"]
                return self._idle_result("Lote sem conteúdo textual legível.")
            
            # Bug #4 FIX: Extração de Bigramas via Stopwords
            bigrams = self._extract_bigrams(texts)

            # Triagem Voyant
            voyant_data = None
            if self._voyant_ok:
                voyant_data = await voyant_service.triage_batch(texts)
                
                # Bug #3 FIX: Fast-Drop granular que NÃO sobrescreve IA profissional
                if voyant_data and voyant_data.get("drop"):
                    await self._apply_fast_drop_granular(comments, voyant_data)
                    # Não retornamos aqui; queremos processar o checkpoint e salvar XP

            # Geração de Insight (IA)
            insight = await self._generate_linguistic_insight(voyant_data, bigrams)
            
            xp = 5.0
            if insight and insight.get("relevancia", 0) > 0.6:
                await self._save_insight(insight)
                xp = 15.0

            # Salva Checkpoint Persistente (Bug #2)
            new_checkpoint = comments[-1]["data_coleta"]
            await self._save_checkpoint(new_checkpoint)
            self._last_processed_ts = new_checkpoint

            return self._success_result(len(comments), len(comments) if voyant_data else 0, xp, {
                "hostile_ratio": (voyant_data or {}).get("hostile_ratio", 0),
                "insight_title": (insight or {}).get("titulo") if insight else None,
                "bigrams": bigrams[:5],
                "xp_delta": xp
            })

        except Exception as e:
            logger.error("💥 [%s] Erro no ciclo: %s", self.worker_id, e, exc_info=True)
            return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="sa_voyant", error=str(e)[:200])

    # ── Lógica Interna ───────────────────────────────────────────────────────

    def _sanitize_texts(self, comments: list) -> list[str]:
        """Filtra e limpa textos para evitar ruído de URLs e menções."""
        sanitized = []
        for c in comments:
            t = c.get("texto_limpo") or c.get("texto_bruto")
            if not t: continue
            
            # Limpeza básica de URL/Menção para não poluir estatística
            t = re.sub(r'https?://\S+', '', t)
            t = re.sub(r'@\w+', '', t)
            t = t.strip()
            
            if len(t) > 5: sanitized.append(t)
        return sanitized

    def _extract_bigrams(self, texts: list[str]) -> list[str]:
        counter = Counter()
        for text in texts:
            words = text.lower().split()
            if len(words) < 2: continue
            for i in range(len(words)-1):
                w1, w2 = words[i].strip(".,;!?:()"), words[i+1].strip(".,;!?:()")
                if w1 not in STOP_WORDS_PT and w2 not in STOP_WORDS_PT:
                    counter.update([f"{w1} {w2}"])
        return [item[0] for item in counter.most_common(10)]

    async def _ensure_voyant_connection(self):
        now = time.time()
        if not self._voyant_ok or (now - self._last_voyant_check > _VOYANT_CHECK_COOLDOWN):
            self._voyant_ok = await voyant_service.ping()
            self._last_voyant_check = now

    async def _apply_fast_drop_granular(self, comments: list, voyant_data: dict):
        """Marca como triado sem sobrescrever classificações existentes (Bug #3)."""
        # Só toca em quem NÃO foi processado pela IA profissional
        ids_to_drop = [c["id"] for c in comments if not c.get("processado_ia")]
        if not ids_to_drop: return

        try:
            await asyncio.to_thread(
                db_client.client.table("comentarios").update({
                    "categoria_ia": "NEUTRO",
                    "confianca_ia": 0.80,
                    "processado_ia": True,
                    "analise_pericial": f"[SaVoyant] Fast-drop granular (ratio: {voyant_data['hostile_ratio']:.2%})"
                }).in_("id", ids_to_drop).execute
            )
        except Exception as e:
            logger.warning("[%s] Erro no fast-drop granular: %s", self.worker_id, e)

    async def _save_checkpoint(self, ts: str):
        try:
            await asyncio.to_thread(
                db_client.client.table("system_events").insert({
                    "event_type": "voyant_checkpoint",
                    "source": self.worker_id,
                    "severity": "info",
                    "description": f"Análise incremental até: {ts}",
                    "metadata": {"last_processed_ts": ts}
                }).execute
            )
        except Exception as e:
            logger.debug("Falha ao salvar checkpoint: %s", e)

    async def _generate_linguistic_insight(self, voyant_data: Optional[dict], bigrams: list[str]) -> Optional[dict]:
        if not voyant_data and not bigrams: return None
        
        ratio_display = f"{voyant_data.get('hostile_ratio', 0):.2%}" if voyant_data else 'N/A'
        
        prompt = f"""
        Estatísticas do Lote:
        - Ratio Hostil: {ratio_display}
        - Slogans (Bigramas): {bigrams}
        
        REGRAS FORENSES: {self._linguistics_context}
        
        Analise a severidade (0-100) e relevância pericial (0-1).
        RETORNE JSON: {{"titulo": str, "resumo": str, "severidade": int, "relevancia": float, "categoria_mca": str}}
        """
        try:
            res = await ai_service.chat_completion(
                prompt=prompt,
                system_prompt="Você é o SaVoyant. Seja cirúrgico na análise linguística.",
                response_format="json_object"
            )
            return res if isinstance(res, dict) and "titulo" in res else None
        except: return None

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
        except: pass

    def _idle_result(self, msg: str) -> CycleResult:
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="sa_voyant", error="no_tasks_available", metadata={"reason": msg})

    def _success_result(self, collected, processed, xp, metadata) -> CycleResult:
        metadata["xp_delta"] = xp
        return CycleResult(worker_id=self.worker_id, cycle=self.cycle, source="sa_voyant", extracted=collected, classified=processed, db_success=True, metadata=metadata)
