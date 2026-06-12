from __future__ import annotations

import logging
import os
import random
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from models.target import Target

logger = logging.getLogger("queue_manager")

# Helper para converter timestamps armazenados sem fuso para o horário local (UTC‑3)
def _parse_local_timestamp(ts: str) -> datetime:
    """Parse ISO8601 timestamp (possivelmente sem zona) assumindo horário local UTC‑3.
    Retorna um objeto datetime em UTC para comparações consistentes.
    """
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        # fallback simples
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
    # Se o datetime não tem tzinfo, atribui o fuso local (UTC‑3)
    local_tz = timezone(timedelta(hours=-3))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz)
    else:
        dt = dt.astimezone(local_tz)
    # Converte para UTC
    return dt.astimezone(timezone.utc)



class QueueManager:
    def __init__(self, db_client):
        # Proteção v90.1: Extrai o client real se for passado o wrapper DatabaseClient
        if hasattr(db_client, 'client') and db_client.client is not None:
            self.db = db_client.client
        else:
            self.db = db_client

    async def claim_next_target(
        self,
        config: dict,
        seen_queue_ids: set,
        seen_targets: set,
        active_targets: Optional[set] = None,
    ) -> Optional[Target]:
        """
        Retorna o próximo alvo disponível com base em prioridades e distribuição (v55.1).
        Prioridades: Manual > fila_coleta (High Priority) > fila_coleta (Normal) > Fallback Rotation.
        """
        # 🔄 AUTO-REPOPULAÇÃO (v80.0): Garante que a fila nunca esvazia
        await self._ensure_queue_populated()

        blocked = seen_targets | (active_targets or set())

        # 1. PRIORIDADE MÁXIMA: Alvo Manual
        manual_target = config.get("target") or os.getenv("TEST_TARGET_USERNAME")
        if manual_target:
            username = manual_target.strip().lstrip("@").lower()
            if username not in blocked:
                logger.info(f"[Manual] Selecionado: @{username}")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(username=username, candidato_id=username, source="manual")

        # 2. DISTRIBUIÇÃO PONDERADA: fila_coleta vs Fallback
        # Mecanismo de Fairness: 25% de chance de priorizar a rotação global para evitar estagnação.
        prefer_global_rotation = random.random() < 0.25
        
        target = None
        if not prefer_global_rotation:
            target = await self._get_from_fila_coleta(blocked, seen_queue_ids, seen_targets, active_targets)
        
        if not target:
            target = await self._get_from_global_rotation(blocked, seen_targets, active_targets)
            
        return target

    # ── Travas Atômicas PASA v88.0 (Fase 8.3) ─────────────────────────────────

    async def claim_next_target_atomic(
        self,
        worker_id: str,
        seen_targets: Optional[set] = None,
        active_targets: Optional[set] = None,
        max_prioridade: int = 10,
    ) -> Optional["Target"]:
        """
        Versão atômica de claim usando SELECT FOR UPDATE SKIP LOCKED.
        Segura para múltiplos workers em paralelo (cluster horizontal).

        Usa a função SQL `fila_coleta_claim_next` que:
          1. Seleciona o próximo PENDENTE com prioridade mais alta.
          2. Marca atomicamente como EM_CURSO + locked_by.
          3. Retorna a linha — sem possibilidade de dois workers pegarem o mesmo item.

        Fallback: se a função SQL não existir, delega para claim_next_target() legado.
        """
        # 🔄 AUTO-REPOPULAÇÃO (v80.0): Garante que a fila nunca esvazia
        await self._ensure_queue_populated()

        blocked = (seen_targets or set()) | (active_targets or set())

        try:
            # Chama função SQL atômica
            res = await asyncio.to_thread(
                self.db.rpc("fila_coleta_claim_next", {
                    "p_worker_id": worker_id,
                    "p_max_prioridade": max_prioridade,
                }).execute
            )

            if not res.data:
                # Fila vazia — tenta rotação global como fallback
                return await self._get_from_global_rotation(blocked, seen_targets or set(), active_targets)

            row = res.data[0]
            username = row.get("candidato_id", "").strip().lstrip("@").lower()

            if not username or username in blocked:
                # Item claimado mas bloqueado localmente — libera e retorna None
                await self._release_atomic(row["id"], "PENDENTE", worker_id)
                return None

            self._add_to_blocked(username, seen_targets or set(), active_targets)
            logger.info(
                "[Queue:atomic] Claim atômico OK | @%s | queue_id=%s | prioridade=%s",
                username, row["id"], row.get("prioridade"),
            )
            return Target(
                username=username,
                candidato_id=username,
                queue_id=row["id"],
                source="fila_coleta_atomic",
            )

        except Exception as e:
            if "fila_coleta_claim_next" in str(e) or "function" in str(e).lower():
                logger.warning(
                    "[Queue:atomic] Função SQL não encontrada. "
                    "Execute migrations/add_queue_skip_locked.sql no Supabase. "
                    "Usando claim legado como fallback."
                )
            else:
                logger.error("[Queue:atomic] Erro no claim atômico: %s", e)
            # Fallback para o método legado
            return await self.claim_next_target(
                {}, seen_targets or set(), set(), active_targets
            )

    async def release_atomic(self, queue_id, status: str, worker_id: str) -> None:
        """Libera o item da fila após processamento via função SQL atômica."""
        await self._release_atomic(queue_id, status, worker_id)

    async def _release_atomic(self, queue_id, status: str, worker_id: str) -> None:
        """Implementação interna do release atômico."""
        try:
            await asyncio.to_thread(
                self.db.rpc("fila_coleta_release", {
                    "p_queue_id": str(queue_id),
                    "p_status": status,
                    "p_worker_id": worker_id,
                }).execute
            )
        except Exception as e:
            logger.warning("[Queue:atomic] Falha no release atômico (queue_id=%s): %s", queue_id, e)
            # Fallback: atualiza status diretamente
            try:
                await asyncio.to_thread(
                    self.db.table("fila_coleta").update({
                        "status": status,
                        "locked_by": None,
                        "locked_at": None,
                    }).eq("id", str(queue_id)).execute
                )
            except Exception as e2:
                logger.error("[Queue:atomic] Fallback de release também falhou: %s", e2)

    async def release_stale_locks(self, timeout_minutes: int = 30) -> int:
        """
        Auto-desbloqueio de locks expirados (worker crashou sem liberar).
        Deve ser chamado periodicamente pelo orquestrador (ex: a cada 10 ciclos).
        Retorna quantos itens foram desbloqueados.
        """
        try:
            res = await asyncio.to_thread(
                self.db.rpc("fila_coleta_release_stale", {
                    "p_timeout_minutes": timeout_minutes,
                }).execute
            )
            count = res.data[0] if res.data else 0
            if count:
                logger.info("[Queue:atomic] %d lock(s) expirado(s) liberado(s) (timeout=%dmin).", count, timeout_minutes)
            return count
        except Exception as e:
            logger.debug("[Queue:atomic] release_stale_locks indisponível (migração pendente): %s", e)
            return 0

    async def _get_from_fila_coleta(self, blocked, seen_queue_ids, seen_targets, active_targets) -> Optional[Target]:
        """Busca alvos na fila de prioridade, ordenados por nível de importância."""
        try:
            # Pega os Top 20 pendentes (Prioridade 1 = Máxima, depois FIFO)
            pending = await asyncio.to_thread(
                self.db.table("fila_coleta")
                .select("*")
                .eq("status", "PENDENTE")
                .order("prioridade", desc=False)
                .order("created_at", desc=False)
                .limit(20)
                .execute
            )
            
            for item in pending.data or []:
                queue_id = item["id"]
                target_val = item.get("username") or item.get("candidato_id") or item.get("target_username")
                
                if not target_val: continue
 
                # Resolução inteligente de Identidade (PASA v85.6)
                username = None
                # Se for UUID, busca o username
                if len(str(target_val)) > 30 and "-" in str(target_val):
                    cand = await asyncio.to_thread(
                        self.db.table("candidatos").select("username").eq("id", target_val).limit(1).execute
                    )
                    if cand.data: username = cand.data[0]["username"]
                else:
                    # Já é o username
                    username = str(target_val)
                
                if not username: continue
                username = username.strip().lstrip("@").lower()
                
                if queue_id in seen_queue_ids or username in blocked:
                    continue
                
                logger.info(f"⚡ [Queue] Selecionado da Fila de Prioridade (P{item.get('prioridade', 1)}): @{username}")
                seen_queue_ids.add(queue_id)
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(
                    username=username,
                    candidato_id=username,
                    queue_id=queue_id,
                    source="fila_coleta",
                )
        except Exception as e:
            logger.error(f"❌ [Queue] Erro ao consultar fila_coleta: {e}")
        return None

    async def pre_warm_queues(self) -> None:
        """
        Pré-aquecimento das filas de trabalho (v89.2).
        Popula a fila_coleta e garante alvos prontos ANTES dos workers iniciarem.
        """
        logger.info("🔥 [Queue] Iniciando pré-aquecimento das filas...")
        
        # 1. Garante que a fila_coleta tenha o mínimo necessário
        await self._ensure_queue_populated(min_pending=50)
        
        # 2. Limpeza de locks órfãos que possam travar o boot
        unlocked = await self.release_stale_locks(timeout_minutes=0) # 0 força liberação de tudo no boot
        if unlocked > 0:
            logger.info(f"🔓 [Queue] {unlocked} locks órfãos liberados no boot.")

        logger.info("✅ [Queue] Filas aquecidas e prontas para operação.")

    def _get_db_client(self):
        """Retorna o cliente Supabase real, suportando late initialization."""
        if hasattr(self.db, 'client') and self.db.client is not None:
            return self.db.client
        return self.db

    async def _ensure_queue_populated(self, min_pending: int = 50) -> None:
        """Repopula a fila_coleta automaticamente quando há poucos itens pendentes (v80.0)."""
        try:
            db_real = self._get_db_client()
            # Conta itens PENDENTE
            count_res = await asyncio.to_thread(
                db_real.table("fila_coleta")
                .select("id", count="exact")
                .eq("status", "PENDENTE")
                .execute
            )
            current_pending = count_res.count or 0

            if current_pending >= min_pending:
                return  # Fila saudável, nada a fazer

            logger.info(f"🔄 [Queue] Apenas {current_pending} itens pendentes. Repopulando fila...")

            # Busca candidatos ativos mais antigos para reinserir
            candidatos_res = await asyncio.to_thread(
                self.db.table("candidatos")
                .select("id,username,termometro")
                .filter("status_monitoramento", "ilike", "Ativo")
                .order("last_scraped_at", desc=False)
                .limit(min_pending)
                .execute
            )

            reinseridos = 0
            for cand in (candidatos_res.data or []):
                username = cand.get("username")
                if not username:
                    continue
                # Verifica se já existe na fila como PENDENTE
                check = await asyncio.to_thread(
                    self.db.table("fila_coleta")
                    .select("id")
                    .eq("candidato_id", cand["username"])
                    .eq("status", "PENDENTE")
                    .limit(1)
                    .execute
                )
                if check.data:
                    continue

                termometro = cand.get("termometro", "MORNO")
                prioridade = 1 if termometro == "QUENTE" else (5 if termometro in ("FRIO", "MORNO") else 3)

                # Reinserção via upsert
                await asyncio.to_thread(
                    self.db.table("fila_coleta").upsert({
                        "candidato_id": cand["username"],
                        "status": "PENDENTE",
                        "prioridade": prioridade,
                    }, on_conflict="candidato_id,data_agendada").execute
                )
                reinseridos += 1

                if (current_pending + reinseridos) >= min_pending:
                    break

            if reinseridos > 0:
                logger.info(f"✅ [Queue] {reinseridos} candidato(s) reinserido(s) na fila automaticamente.")
        except Exception as e:
            logger.error(f"❌ [Queue] Erro na auto-repopulação: {e}")

    async def _get_from_global_rotation(self, blocked, seen_targets, active_targets) -> Optional[Target]:
        """Garante que todos os candidatos ativos sejam processados circularmente com Smart Backoff (PASA v85.6)."""
        try:
            # ❄️ SMART BACKOFF: Pula alvos 'FRIO' que foram processados recentemente (< 12h)
            cold_threshold = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
            # 🔥 TURBO BACKOFF: Alvos 'MORNO/QUENTE' têm cooldown reduzido (2h)
            hot_threshold = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

            # Query otimizada (v85.6): Suporta Case Insensitive e Cooldown por Temperatura
            # Pega alvos validados OU alvos que ainda não foram raspados (last_scraped_at is null)
            res = await asyncio.to_thread(
                self.db.table("candidatos")
                .select("id,username,termometro,last_scraped_at")
                .filter("status_monitoramento", "ilike", "Ativo")
                .or_(f"last_scraped_at.is.null,and(termometro.eq.FRIO,last_scraped_at.lt.{cold_threshold}),and(termometro.neq.FRIO,last_scraped_at.lt.{hot_threshold})")
                .order("last_scraped_at", desc=False)
                .limit(20)
                .execute
            )
                
            for cand in res.data or []:
                username = cand["username"].lower()
                if username in blocked:
                    continue
                
                logger.info(f"🔄 [Queue] Selecionado via Rotação Global: @{username} ({cand.get('termometro', 'MORNO')})")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(
                    username=username,
                    candidato_id=username,
                    source="candidatos_fallback",
                )
        except Exception as e:
            logger.error(f"❌ [Queue] Erro ao consultar rotação global: {e}")

        # Fallback extremo (Fila Vazia)
        try:
            res_fallback = await asyncio.to_thread(
                self.db.table("candidatos")
                .select("id,username,termometro,last_scraped_at")
                .filter("status_monitoramento", "ilike", "Ativo")
                .order("last_scraped_at", desc=False)
                .limit(10)
                .execute
            )

            for cand in res_fallback.data or []:
                username = cand["username"].lower()
                if username in blocked:
                    continue
                
                logger.info(f"🔄 [Queue] Fallback extremo (Fila Vazia): @{username}")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(
                    username=username,
                    candidato_id=username,
                    source="candidatos_fallback",
                )
        except Exception as e:
            logger.error(f"❌ [Queue] Erro no fallback extremo da fila: {e}")

        return None

    def _add_to_blocked(self, username, seen_targets, active_targets):
        """Marca o alvo como em processamento para evitar colisão entre workers."""
        seen_targets.add(username)
        if active_targets is not None:
            active_targets.add(username)

    async def update_target_metrics(self, target: Target) -> str:
        """
        Calcula e atualiza o termômetro e a frequência de postagens do candidato.
        Retorna o novo valor do termômetro ('QUENTE', 'MORNO' ou 'FRIO').
        """
        if not target.username:
            return "MORNO"

        # Use horário local (UTC‑3) como referência de tempo
        LOCAL_TZ = timezone(timedelta(hours=-3))
        now = datetime.now(LOCAL_TZ)
        now_iso = now.isoformat()
        
        # PASA v86.3: Não pune o alvo se for um erro do Scraper
        is_error = hasattr(target, "error") and target.error
        is_no_comments = is_error and target.error == "no_comments_found"
        is_empty = is_error and target.error in ["junk_detected", "invalid_target: 404_not_found"]
        session_terms = ["session", "blocked", "429", "login wall", "captcha"]
        is_session_error = is_error and any(term in str(target.error).lower() for term in session_terms)
        is_system_error = is_error and not is_empty and not is_no_comments and not is_session_error
        
        if is_system_error or is_session_error:
            logger.warning(f"⚠️ [Queue] Erro sistêmico/sessão detectado para @{target.username} ({target.error}). Mantendo temperatura atual.")
            await asyncio.to_thread(
                self.db.table("candidatos").update({
                    "last_scraped_at": now_iso
                }).eq("username", target.username).execute
            )
            return getattr(target, "termometro", "MORNO")

        frequencia = 0.0
        post_metas = getattr(target, "post_metas", [])
        valid_dates = []
        if post_metas:
            for m in post_metas:
                if m.get("timestamp"):
                    try:
                        valid_dates.append(_parse_local_timestamp(m["timestamp"]))
                    except Exception:
                        continue
        
        if (is_empty or not valid_dates) and not is_no_comments:
            termometro = getattr(target, "termometro", "MORNO")
            frequencia = 0.0
        elif is_no_comments or not valid_dates:
            # PASA v88.4: Redução de ciclos com no_comments_found
            # Rebaixa o termômetro gradativamente para aumentar o cooldown
            current_term = getattr(target, "termometro", "MORNO")
            termometro = "MORNO" if current_term == "QUENTE" else "FRIO"
            frequencia = 0.0
        else:
            last_post_date = max(valid_dates)
            days_since_last_post = (now - last_post_date).days
            
            if len(valid_dates) >= 2:
                delta_days = (max(valid_dates) - min(valid_dates)).days or 1
                frequencia = round((len(valid_dates) / delta_days) * 7, 1)
            else:
                frequencia = round(7 / (days_since_last_post + 1), 1)

            if frequencia >= 5 and days_since_last_post <= 2:
                termometro = "QUENTE"
            elif days_since_last_post > 7:
                termometro = "FRIO"
            else:
                termometro = "MORNO"
        
        update_data = {
            "last_scraped_at": now_iso,
            "posts_frequencia_semanal": frequencia,
            "termometro": termometro
        }
        await asyncio.to_thread(
            self.db.table("candidatos").update(update_data).eq("username", target.username).execute
        )
        return termometro

    async def rotate_target(self, target: Target) -> None:
        """Remove o item processado e reinsere no fim da fila com status e termômetro (v86.3)."""
        if not target.username:
            return

        # Use horário local (UTC‑3) como referência de tempo
        LOCAL_TZ = timezone(timedelta(hours=-3))
        now = datetime.now(LOCAL_TZ)
        now_iso = now.isoformat()
        
        # Atualiza métricas do candidato
        termometro = await self.update_target_metrics(target)

        if target.queue_id:
            nova_prioridade = 1 if termometro == "QUENTE" else (5 if termometro in ("FRIO", "MORNO") else 3)
            is_error = hasattr(target, "error") and target.error
            is_empty = is_error and target.error in ["junk_detected", "invalid_target: 404_not_found"]
            
            await asyncio.to_thread(
                self.db.table("fila_coleta").update({
                    "status": "SEM_DADOS_RECENTES" if is_empty else "CONCLUIDO",
                    "prioridade": nova_prioridade,
                    "updated_at": now_iso
                }).eq("id", target.queue_id).execute
            )
            
        logger.info(f"[Queue] Rotação finalizada para @{target.username} -> {termometro}")


    async def mark_candidate_scraped(self, target: Target) -> None:
        """Update the last_scraped_at timestamp for the candidate."""
        if not target.username:
            return
        await asyncio.to_thread(
            self.db.table("candidatos").update({
                "last_scraped_at": datetime.now(timezone.utc).isoformat(),
            }).eq("username", target.username).execute
        )

    async def add_target_to_queue(self, username: str, priority: int = 1) -> bool:
        """
        Insere ou atualiza um alvo na fila de coleta com alta prioridade para forçar a raspagem (force_scrape).
        """
        username = username.strip().lstrip("@").lower()
        if not username:
            return False
            
        try:
            db_real = self._get_db_client()
            
            # Verifica se o candidato existe na tabela de candidatos
            cand_res = await asyncio.to_thread(
                db_real.table("candidatos").select("username").eq("username", username).limit(1).execute
            )
            if not cand_res.data:
                # Se não existir, cadastra-o como ativo temporário para coleta
                await asyncio.to_thread(
                    db_real.table("candidatos").insert({
                        "username": username,
                        "status_monitoramento": "ATIVO",
                        "nota_relevancia": 50,
                        "cargo": "ANALISE_SOLICITADA",
                        "identidade_validada": False
                    }).execute
                )
                logger.info(f"[Queue] Novo candidato cadastrado via force_scrape: @{username}")
            else:
                # Se já existe, garante que seu status de monitoramento seja ATIVO
                await asyncio.to_thread(
                    db_real.table("candidatos").update({
                        "status_monitoramento": "ATIVO"
                    }).eq("username", username).execute
                )

            # Insere ou atualiza na fila_coleta
            existing = await asyncio.to_thread(
                db_real.table("fila_coleta")
                .select("id, status")
                .eq("candidato_id", username)
                .in_("status", ["PENDENTE", "EM_CURSO"])
                .limit(1)
                .execute
            )
            
            LOCAL_TZ = timezone(timedelta(hours=-3))
            now_iso = datetime.now(LOCAL_TZ).isoformat()
            
            if existing.data:
                # Atualiza a prioridade para furar a fila
                queue_id = existing.data[0]["id"]
                await asyncio.to_thread(
                    db_real.table("fila_coleta").update({
                        "status": "PENDENTE",
                        "prioridade": priority,
                        "updated_at": now_iso
                    }).eq("id", queue_id).execute
                )
                logger.info(f"[Queue] Alvo @{username} já estava na fila. Prioridade atualizada para {priority}.")
            else:
                # Insere novo item pendente com prioridade alta
                await asyncio.to_thread(
                    db_real.table("fila_coleta").insert({
                        "candidato_id": username,
                        "status": "PENDENTE",
                        "prioridade": priority,
                        "created_at": now_iso,
                        "updated_at": now_iso
                    }).execute
                )
                logger.info(f"[Queue] Alvo @{username} inserido na fila_coleta com prioridade {priority}.")
                
            return True
        except Exception as e:
            logger.error(f"[Queue] Erro ao adicionar @{username} à fila: {e}")
            return False


# Instância global para importação direta no Watchdog e outros serviços
try:
    from core.supabase_service import get_supabase_client
    queue_manager = QueueManager(get_supabase_client())
except Exception:
    queue_manager = None

