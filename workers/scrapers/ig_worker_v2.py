from __future__ import annotations

import logging
import asyncio
import os
from typing import List, Dict

from workers.base.worker_base import BaseWorker
from workers.base.cycle_result import CycleResult
from core.queue_manager import QueueManager
from core.supabase_service import get_supabase_client
from core.ai_service import ai_service, clean_null_chars
from core.instagram_scraper_v2 import InstagramScraperV2

from core.local_buffer import local_buffer
from core.lexical_filter import lexical_filter
from core.process_cleaner import cleanup_orphans

logger = logging.getLogger("worker.ig_v2")

class IGWorkerV2(BaseWorker):
    """
    Worker Instagram V2 (Independente).
    Implementa o fluxo completo de coleta e classificação usando o motor V2.
    """

    def __init__(self, worker_id: str, config: dict):
        super().__init__(worker_id, config)
        self.cycle = 0
        self.consecutive_blocks = 0
        self.db = get_supabase_client()
        self.queue = QueueManager(self.db)
        self.seen_queue_ids: set = set()
        self.seen_targets: set = set()
        self.scraper = InstagramScraperV2(
            headless=config.get("headless", True),
            max_retries=config.get("max_retries", 3)
        )

    def describe(self) -> str:
        return "Instagram Scraper V2 - Independente com Playwright"

    async def setup(self) -> None:
        logger.info(f"🚀 Worker {self.worker_id} configurado.")
        await local_buffer.sync_with_supabase(self.db)

    async def teardown(self) -> None:
        logger.info(f"🛑 Worker {self.worker_id} encerrado.")

    async def run_cycle(self) -> CycleResult:
        self.cycle += 1
        
        # 🛡️ HIBERNAÇÃO INTELIGENTE (PASA v65.1)
        if self.consecutive_blocks >= 3:
            hibernation_time = 3600 # 1 hora
            self.logger.warning(f"🛌 [V2] Detectados {self.consecutive_blocks} bloqueios seguidos. Hibernando por {hibernation_time//60} min...")
            await asyncio.sleep(hibernation_time)
            self.consecutive_blocks = 0 # Reseta após hibernar

        # 🧹 CLEANUP DE PROCESSOS (Épico 1)
        if self.cycle % 10 == 0:
            cleanup_orphans()

        # 📦 SINCRONIZAÇÃO DE BACKGROUND (SQLite -> Supabase)
        if self.cycle % 5 == 0:
            synced = await local_buffer.sync_with_supabase(self.db)
            if synced: self.logger.info(f"🔄 [V2] Sincronizados {synced} registros pendentes do SQLite.")

        self.seen_targets.clear()
        self.seen_queue_ids.clear()
        result = None # Inicializa para o finally

        # 🛡️ SELEÇÃO ATÔMICA (PASA v55.1)
        target = None
        if hasattr(self, "claim_lock"):
            async with self.claim_lock:
                target = self.queue.claim_next_target(
                    self.config, self.seen_queue_ids, self.seen_targets,
                    active_targets=getattr(self, "active_targets", None),
                )
        else:
            target = self.queue.claim_next_target(
                self.config, self.seen_queue_ids, self.seen_targets,
                active_targets=getattr(self, "active_targets", None),
            )

        if not target:
            # Backlog de classificação se não houver alvo
            classified = await ai_service.run_batch_classification(limit=50)
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle,
                source="batch_classification", simulated=False, error="no_target",
                classified=classified
            )

        self.logger.info(f"🔄 [V2] Ciclo {self.cycle} | Alvo: @{target.username}")
        
        # Jitter inicial (PASA v52.0) para quebrar padrões
        import random
        jitter = random.uniform(5, 30)
        self.logger.debug(f"[V2] Aplicando jitter inicial de {jitter:.1f}s")
        await asyncio.sleep(jitter)

        self.queue.mark_candidate_scraped(target)

        try:
            # 1. Scraping (v61.2: Robusto contra retornos de lista ou dict)
            scrape_data = await self.scraper.scrape_profile(
                username=target.username,
                candidato_id=target.candidato_id,
                max_posts=self.config.get("max_posts", 3),
                max_comments_per_post=100
            )
            
            # Sucesso técnico no scrape -> Reseta contador de bloqueios
            self.consecutive_blocks = 0
            
            if isinstance(scrape_data, list):
                comments = scrape_data
                target.post_metas = []
            elif isinstance(scrape_data, dict):
                comments = scrape_data.get("comments", [])
                target.post_metas = scrape_data.get("post_metas", [])
            else:
                comments = []
                target.post_metas = []
            
        except ValueError as e:
            if "invalid_target" in str(e):
                self.logger.error(f"🚫 [V2] Alvo @{target.username} marcado como INVÁLIDO (404/Privado/Mismatch).")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, 
                    error=str(e), db_success=False # db_success=False garante score baixo
                )
            # Outros ValueErrors (ex: bloqueio de sessão) incrementam bloqueios
            self.consecutive_blocks += 1
            raise e

        try:
            stats = self.scraper.get_stats()

            if not comments:
                if stats.get("junk_detected", 0) > 0:
                    self.logger.warning(f"⚠️ [V2] Apenas lixo detectado para @{target.username}. Sinalizando falha de extração.")
                    return CycleResult(
                        worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                        source="v2_engine", extracted=0, simulated=False, error="junk_detected"
                    )
                # Se o scraper retornou vazio mas não levantou erro, pode ser apenas falta de conteúdo
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, simulated=False, error="no_comments_found"
                )

            # 2. Detecção de Comportamento Coordenado (Bots) - PASA v56.0
            import re
            import collections
            
            def normalize_for_bot_detection(text: str) -> str:
                # Remove emojis, pontuação e espaços extras para detectar padrões de robô
                t = text.lower()
                t = re.sub(r'[^\w\s]', '', t)
                # Remove emojis específicos se o regex acima não pegar tudo
                t = re.sub(r'[^\x00-\x7F]+', '', t) 
                return " ".join(t.split())

            # Mapeia textos normalizados para encontrar repetições
            normalized_map = collections.defaultdict(list)
            for idx, c in enumerate(comments):
                norm = normalize_for_bot_detection(c.get("texto_bruto", ""))
                if len(norm) > 5: # Ignora textos muito curtos (ex: "voto", "top")
                    normalized_map[norm].append(idx)
            
            bot_detected_count = 0
            for norm, indices in normalized_map.items():
                if len(indices) >= 3: # Threshold: 3 ou mais repetições do mesmo padrão
                    bot_detected_count += len(indices)
                    for i in indices:
                        comments[i]["is_bot"] = True
                        comments[i]["bot_pattern"] = norm
                        # Ajusta categoria IA preventivamente se for bot
                        comments[i]["categoria_ia_sugerida"] = "CAMPANHA_COORDENADA"

            if bot_detected_count > 0:
                self.logger.info(f"🤖 [V2] Detectados {bot_detected_count} indícios de comportamento coordenado (Bots) em @{target.username}")

            # 3. Persistência com Resiliência de Schema (v58.3)
            inserted = 0
            duplicated = 0
            inserted_ids = []
            
            # Filtra campos para garantir que apenas colunas existentes sejam enviadas
            safe_comments = []
            for c in comments:
                safe_c = {
                    "id_externo": c.get("id_externo"),
                    "texto_bruto": c.get("texto_bruto"),
                    "autor_username": c.get("autor_username"),
                    "data_publicacao": c.get("data_publicacao"),
                    "data_coleta": c.get("data_coleta"),
                    "candidato_id": c.get("candidato_id"),
                    "post_shortcode": c.get("post_shortcode"),
                    "plataforma": c.get("plataforma"),
                    "processado_ia": False,
                    "tier_used": c.get("tier_used")
                }
                if c.get("is_bot"):
                    pericial_obs = f"[BOT DETECTED] Padrão: {c.get('bot_pattern')}"
                    safe_c["evidence_extracted"] = pericial_obs # Usa coluna existente
                    safe_c["categoria_ia"] = "CAMPANHA_COORDENADA"
                safe_comments.append(safe_c)

            # --- BUFFER DE EMERGÊNCIA SQLITE (Zero Loss Policy v65.0) ---
            local_buffer.save(safe_comments)

            try:
                # 🛡️ TENTATIVA 1: Upsert Completo (v63.0)
                res = self.db.table("comentarios").upsert(
                    clean_null_chars(safe_comments), 
                    on_conflict="candidato_id,post_shortcode,id_externo",
                    ignore_duplicates=True
                ).execute()
                
                if res.data:
                    inserted = len(res.data)
                    duplicated = len(comments) - inserted
                    inserted_ids = [str(item["id"]) for item in res.data]
                    # O recovery via sync_with_supabase lidará com o SQLite periodicamente.
                else:
                    inserted = 0
                    duplicated = len(comments)

            except Exception as e:
                # 🆘 SALVAMENTO DE EMERGÊNCIA (v63.0): Fallback para Schema Mismatch
                self.logger.warning(f"⚠️ [V2] Erro de Schema Detectado: {e}. Iniciando Fallback de Emergência...")
                
                # Remove colunas que costumam causar conflito se não existirem
                emergency_comments = []
                for sc in safe_comments:
                    # Mantém APENAS o core absoluto garantido no banco
                    emergency_comments.append({
                        "id_externo": sc["id_externo"],
                        "texto_bruto": sc["texto_bruto"],
                        "candidato_id": sc["candidato_id"],
                        "post_shortcode": sc["post_shortcode"],
                        "autor_username": sc["autor_username"],
                        "data_publicacao": sc["data_publicacao"],
                        "data_coleta": sc["data_coleta"],
                        "plataforma": sc["plataforma"],
                        "tier_used": sc["tier_used"]
                    })

                try:
                    res = self.db.table("comentarios").upsert(
                        clean_null_chars(emergency_comments),
                        on_conflict="candidato_id,post_shortcode,id_externo",
                        ignore_duplicates=True
                    ).execute()
                    
                    self.logger.info(f"✅ [V2] Salvamento de emergência concluído ({len(res.data)} registros salvos).")
                    await self._clear_buffer()
                    inserted = len(res.data)
                    duplicated = len(comments) - inserted
                    inserted_ids = [str(item["id"]) for item in res.data]
                except Exception as e2:
                    self.logger.error(f"❌ [V2] Falha total na persistência: {e2}")
                    raise ValueError(f"db_persistence_fatal: {str(e2)}")

            # 4. Classificação
            classified = 0
            ai_junk_count = 0
            
            if inserted_ids:
                for cid in inserted_ids:
                    try:
                        # Busca comentário e classifica
                        c_data = self.db.table("comentarios").select("*").eq("id", cid).single().execute()
                        if c_data.data:
                            # Se o worker já marcou como bot, passamos essa info para a IA ou forçamos a categoria
                            is_pre_flagged_bot = any(
                                c.get("id_externo") == c_data.data["id_externo"] and c.get("is_bot") 
                                for c in comments
                            )
                            
                            if is_pre_flagged_bot:
                                # Forçamos a classificação de Bot para economizar tokens ou guiar a IA
                                self.db.table("comentarios").update({
                                    "processado_ia": True,
                                    "is_hate": True, # Bots de campanha são considerados hostilidade ao processo democrático (MCA v2.2)
                                    "categoria_ia": "CAMPANHA_COORDENADA",
                                    "confianca_ia": 1.0,
                                    "analise_pericial": "Detectado comportamento coordenado inautêntico (Bot) via análise de densidade léxica."
                                }).eq("id", cid).execute()
                                classified += 1
                                continue

                            result = await ai_service.classify_text(c_data.data["texto_bruto"], comment_id=cid)
                            
                            if result.get("categoria_ia") == "LIXO":
                                # Lixo detectado pela IA pós-inserção
                                self.db.table("comentarios").delete().eq("id", cid).execute()
                                inserted -= 1
                                ai_junk_count += 1
                                # Remove também dos extraídos para não premiar na coleta
                                comments = [c for c in comments if c.get("id_externo") != cid] # Tenta manter sync, mas o len(comments) inicial já foi feito. Vamos apenas decrementar uma variável.
                                continue
                                
                            self.db.table("comentarios").update({
                                "processado_ia": True,
                                "is_hate": result["is_hate"],
                                "categoria_ia": result["categoria_ia"],
                                "confianca_ia": result["confianca_ia"],
                                "evidence_extracted": result["evidencia_lexical"]
                            }).eq("id", cid).execute()
                            classified += 1
                    except: continue

            stats = self.scraper.get_stats()
            final_extracted = len(comments) - ai_junk_count
            
            if final_extracted <= 0 and (stats.get("junk_detected", 0) > 0 or ai_junk_count > 0):
                self.logger.warning(f"⚠️ [V2] Todo o conteúdo extraído de @{target.username} era LIXO. Sinalizando falha e anulando recompensas.")
                return CycleResult(
                    worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                    source="v2_engine", extracted=0, inserted=0, classified=0, simulated=False, error="junk_detected"
                )

            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                source="v2_engine",
                extracted=final_extracted,
                inserted=inserted,
                duplicated=duplicated,
                classified=classified,
                db_success=inserted > 0,
                classifier_success=classified > 0,
                simulated=False
            )

        except Exception as e:
            self.logger.error(f"💥 Erro crítico no ciclo V2: {e}")
            return CycleResult(
                worker_id=self.worker_id, cycle=self.cycle, target=target.username,
                failed=1, error=str(e)[:200], simulated=False
            )
        finally:
            # PASA v58.2: Injeta erro no alvo para que o rotate_target decida pela hibernação
            if isinstance(result, dict) and result.get("error"):
                target.error = result.get("error")
            elif hasattr(result, "error") and result.error:
                target.error = result.error
            self.queue.rotate_target(target)
