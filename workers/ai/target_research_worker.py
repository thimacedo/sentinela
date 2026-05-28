from __future__ import annotations
import asyncio
import logging
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.instagram_scraper_v2 import InstagramScraperV2
from core.ai_service import ai_service
from core.db import db_client

logger = logging.getLogger("worker.researcher")

class TargetResearchWorker(BaseWorker):
    """
    Worker especializado em curadoria, pesquisa e manutenção de dados de alvos (PASA v84.9).
    Implementa inteligência contínua para evitar dados ausentes ou incorretos.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.scraper = InstagramScraperV2(headless=config.get("headless", True))
        self.cycle = 0
        self.total_xp = 0.0

    def describe(self) -> str:
        return "Motor de Curadoria e Inteligência de Alvos"

    async def setup(self) -> None:
        logger.info(f"🚀 {self.worker_id} pronto para curadoria.")

    async def teardown(self) -> None:
        logger.info(f"🛑 {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        start_time = asyncio.get_event_loop().time()
        self.cycle += 1
        
        # Estratégia: 30% tempo Pesquisa de Novos, 70% Curadoria de Existentes
        import random
        mode = "research" if random.random() < 0.3 else "curation"
        
        target_username = None
        extracted = 0
        error = None
        quality_score = 0.0
        
        try:
            if mode == "research":
                # Busca alvos marcados para pesquisa inicial ou recém-adicionados sem dados
                res = db_client.client.table('candidatos')\
                    .select('username')\
                    .or_('cargo.eq.ANALISE_SOLICITADA,nome_completo.is.null')\
                    .limit(1)\
                    .execute()
                
                if res.data:
                    target_username = res.data[0]['username']
                    logger.info(f"🔎 [{self.worker_id}] Iniciando pesquisa de novo alvo: @{target_username}")
                    data = await self.research_target(target_username)
                    if data:
                        extracted = 1
                        quality_score = data.get("_quality", 0.5)
                else:
                    mode = "curation" # Fallback se não houver novos

            if mode == "curation":
                # Busca alvos com dados possivelmente defasados ou incompletos
                res = db_client.client.table('candidatos')\
                    .select('username')\
                    .or_('cargo.eq.DESCONHECIDO,cargo.is.null,partido.is.null,estado.is.null')\
                    .order('atualizado_em', ascending=True)\
                    .limit(1)\
                    .execute()
                
                if res.data:
                    target_username = res.data[0]['username']
                    logger.info(f"🧹 [{self.worker_id}] Executando curadoria: @{target_username}")
                    data = await self.research_target(target_username)
                    if data:
                        extracted = 1
                        quality_score = data.get("_quality", 0.5)
                else:
                    error = "no_tasks_available"

        except Exception as e:
            logger.error(f"💥 Erro no ciclo de pesquisa: {e}")
            error = str(e)

        # Cálculo de XP Customizado para Pesquisador
        # Reward: +15 XP (Alta Qualidade), +5 XP (Básico), -10 XP (Erro/Inacessível)
        xp_delta = 0.0
        if extracted > 0:
            if quality_score > 0.8: xp_delta = 15.0
            elif quality_score > 0.4: xp_delta = 5.0
            else: xp_delta = -5.0 # Punição por imprecisão
        elif error and error != "no_tasks_available":
            xp_delta = -10.0

        return CycleResult(
            worker_id=self.worker_id,
            cycle=self.cycle,
            target=target_username,
            source=f"research_{mode}",
            extracted=extracted,
            db_success=extracted > 0,
            classifier_success=True if extracted > 0 else False,
            duration=asyncio.get_event_loop().time() - start_time,
            error=error,
            metadata={"xp_delta": xp_delta, "quality": quality_score}
        )

    async def research_target(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Executa a pesquisa profunda e enriquecimento.
        """
        # 1. Coleta básica via Instagram
        ig_data = await self._fetch_ig_basic_info(username)
        if not ig_data:
            return None

        # 2. Pesquisa em Fontes Oficiais (Simulada via IA de Busca)
        official_data = await self._search_official_sources(username, ig_data.get("display_name"))

        # 3. Consolidação e Validação
        enriched = await self._enrich_and_validate(username, ig_data, official_data)
        
        # 4. Persistência
        final_data = {
            "username": username,
            "nome_completo": enriched.get("nome_completo") or ig_data.get("display_name"),
            "bio": ig_data.get("biography"),
            "seguidores": ig_data.get("followers_count", 0),
            "cargo": enriched.get("cargo", "DESCONHECIDO"),
            "partido": enriched.get("partido"),
            "estado": enriched.get("estado"),
            "ideologia": enriched.get("ideologia"),
            "status_monitoramento": "ATIVO",
            "atualizado_em": datetime.now(timezone.utc).isoformat()
        }

        await db_client.upsert_candidate(final_data)
        final_data["_quality"] = enriched.get("quality_confidence", 0.5)
        return final_data

    async def _fetch_ig_basic_info(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                session = self.scraper._get_next_session()
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                await context.add_cookies([{'name': 'sessionid', 'value': session.session_id, 'domain': '.instagram.com', 'path': '/'}])
                page = await context.new_page()
                await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                validation = await self.scraper._validate_target_identity(page, username)
                await browser.close()
                if validation["valid"]:
                    return {
                        "display_name": validation.get("display_name"),
                        "biography": validation.get("biography"),
                        "followers_count": self._parse_followers(validation.get("followers", "0")),
                        "is_verified": validation.get("is_verified", False)
                    }
        except: pass
        return None

    async def _search_official_sources(self, username: str, name: str) -> Dict[str, Any]:
        prompt = f"Pesquise dados oficiais (TSE/TRE/Wikipedia) para a figura pública: {name} (@{username}). Retorne JSON com nome_urna, cargo_eletivo, partido_atual, uf, nota_pesquisa."
        try:
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except: return {}

    async def _enrich_and_validate(self, username: str, ig_data: Dict[str, Any], official_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""Consolidador de Inteligência Sentinela.
        IG={json.dumps(ig_data)}, OFICIAL={json.dumps(official_data)}. 
        Retorne JSON com nome_completo, cargo, partido, estado, ideologia, quality_confidence (0.0-1.0). 
        Seja rigoroso com a quality_confidence."""
        try:
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except: return {"quality_confidence": 0.0}

    def _parse_followers(self, s: str) -> int:
        try:
            s = s.lower().replace('seguidores', '').replace('followers', '').strip()
            if 'mi' in s or 'm' in s: return int(float(s.replace('mi', '').replace('m', '').replace(',', '.')) * 1_000_000)
            if 'mil' in s or 'k' in s: return int(float(s.replace('mil', '').replace('k', '').replace(',', '.')) * 1_000)
            return int(re.sub(r'\D', '', s) or 0)
        except: return 0
