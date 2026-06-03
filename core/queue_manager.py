from __future__ import annotations

import logging
import os
import random
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
        self.db = db_client

    def claim_next_target(
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
        self._ensure_queue_populated()

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
            target = self._get_from_fila_coleta(blocked, seen_queue_ids, seen_targets, active_targets)
        
        if not target:
            target = self._get_from_global_rotation(blocked, seen_targets, active_targets)
            
        return target

    # ── Travas Atômicas PASA v88.0 (Fase 8.3) ─────────────────────────────────

    def claim_next_target_atomic(
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
        blocked = (seen_targets or set()) | (active_targets or set())

        try:
            # Chama função SQL atômica
            res = self.db.rpc("fila_coleta_claim_next", {
                "p_worker_id": worker_id,
                "p_max_prioridade": max_prioridade,
            }).execute()

            if not res.data:
                # Fila vazia — tenta rotação global como fallback
                return self._get_from_global_rotation(blocked, seen_targets or set(), active_targets)

            row = res.data[0]
            username = row.get("candidato_id", "").strip().lstrip("@").lower()

            if not username or username in blocked:
                # Item claimado mas bloqueado localmente — libera e retorna None
                self._release_atomic(row["id"], "PENDENTE", worker_id)
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
            return self.claim_next_target(
                {}, seen_targets or set(), set(), active_targets
            )

    def release_atomic(self, queue_id, status: str, worker_id: str) -> None:
        """Libera o item da fila após processamento via função SQL atômica."""
        self._release_atomic(queue_id, status, worker_id)

    def _release_atomic(self, queue_id, status: str, worker_id: str) -> None:
        """Implementação interna do release atômico."""
        try:
            self.db.rpc("fila_coleta_release", {
                "p_queue_id": str(queue_id),
                "p_status": status,
                "p_worker_id": worker_id,
            }).execute()
        except Exception as e:
            logger.warning("[Queue:atomic] Falha no release atômico (queue_id=%s): %s", queue_id, e)
            # Fallback: atualiza status diretamente
            try:
                self.db.table("fila_coleta").update({
                    "status": status,
                    "locked_by": None,
                    "locked_at": None,
                }).eq("id", str(queue_id)).execute()
            except Exception as e2:
                logger.error("[Queue:atomic] Fallback de release também falhou: %s", e2)

    def release_stale_locks(self, timeout_minutes: int = 30) -> int:
        """
        Auto-desbloqueio de locks expirados (worker crashou sem liberar).
        Deve ser chamado periodicamente pelo orquestrador (ex: a cada 10 ciclos).
        Retorna quantos itens foram desbloqueados.
        """
        try:
            res = self.db.rpc("fila_coleta_release_stale", {
                "p_timeout_minutes": timeout_minutes,
            }).execute()
            count = res.data[0] if res.data else 0
            if count:
                logger.info("[Queue:atomic] %d lock(s) expirado(s) liberado(s) (timeout=%dmin).", count, timeout_minutes)
            return count
        except Exception as e:
            logger.debug("[Queue:atomic] release_stale_locks indisponível (migração pendente): %s", e)
            return 0

    # ── Fim das Travas Atômicas ────────────────────────────────────────────────

    def _get_from_fila_coleta(self, blocked, seen_queue_ids, seen_targets, active_targets) -> Optional[Target]:
        """Busca alvos na fila de prioridade, ordenados por nível de importância."""
        try:
            # Pega os Top 20 pendentes (Prioridade 1 = Máxima, depois FIFO)
            pending = self.db.table("fila_coleta")\
                .select("*")\
                .eq("status", "PENDENTE")\
                .order("prioridade", desc=False)\
                .order("created_at", desc=False)\
                .limit(20).execute()
            
            for item in pending.data or []:
                queue_id = item["id"]
                target_val = item.get("username") or item.get("candidato_id") or item.get("target_username")
                
                if not target_val: continue

                # Resolução inteligente de Identidade (PASA v85.6)
                username = None
                # Se for UUID, busca o username
                if len(str(target_val)) > 30 and "-" in str(target_val):
                    cand = self.db.table("candidatos").select("username").eq("id", target_val).limit(1).execute()
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

    def _ensure_queue_populated(self, min_pending: int = 50) -> None:
        """Repopula a fila_coleta automaticamente quando há poucos itens pendentes (v80.0)."""
        try:
            # Conta itens PENDENTE
            count_res = self.db.table("fila_coleta")\
                .select("id", count="exact")\
                .eq("status", "PENDENTE")\
                .execute()
            current_pending = count_res.count or 0

            if current_pending >= min_pending:
                return  # Fila saudável, nada a fazer

            logger.info(f"🔄 [Queue] Apenas {current_pending} itens pendentes. Repopulando fila...")

            # Busca candidatos ativos mais antigos para reinserir
            candidatos_res = self.db.table("candidatos")\
                .select("id,username,termometro")\
                .filter("status_monitoramento", "ilike", "Ativo")\
                .order("last_scraped_at", desc=False)\
                .limit(min_pending).execute()

            reinseridos = 0
            for cand in (candidatos_res.data or []):
                username = cand.get("username")
                if not username:
                    continue
                # Verifica se já existe na fila como PENDENTE
                check = self.db.table("fila_coleta")\
                    .select("id")\
                    .eq("candidato_id", cand["username"])\
                    .eq("status", "PENDENTE")\
                    .limit(1).execute()
                if check.data:
                    continue

                termometro = cand.get("termometro", "MORNO")
                prioridade = 1 if termometro == "QUENTE" else (5 if termometro in ("FRIO", "MORNO") else 3)

                # Reinserção via upsert
                self.db.table("fila_coleta").upsert({
                    "candidato_id": cand["username"],
                    "status": "PENDENTE",
                    "prioridade": prioridade,
                }, on_conflict="candidato_id,data_agendada").execute()
                reinseridos += 1

                if (current_pending + reinseridos) >= min_pending:
                    break

            if reinseridos > 0:
                logger.info(f"✅ [Queue] {reinseridos} candidato(s) reinserido(s) na fila automaticamente.")
        except Exception as e:
            logger.error(f"❌ [Queue] Erro na auto-repopulação: {e}")

    def _get_from_global_rotation(self, blocked, seen_targets, active_targets) -> Optional[Target]:
        """Garante que todos os candidatos ativos sejam processados circularmente com Smart Backoff (PASA v85.6)."""
        try:
            # ❄️ SMART BACKOFF: Pula alvos 'FRIO' que foram processados recentemente (< 12h)
            cold_threshold = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
            # 🔥 TURBO BACKOFF: Alvos 'MORNO/QUENTE' têm cooldown reduzido (2h)
            hot_threshold = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

            # Query otimizada (v85.6): Suporta Case Insensitive e Cooldown por Temperatura
            # Pega alvos validados OU alvos que ainda não foram raspados (last_scraped_at is null)
            res = self.db.table("candidatos")\
                .select("id,username,termometro,last_scraped_at")\
                .filter("status_monitoramento", "ilike", "Ativo")\
                .or_(f"last_scraped_at.is.null,and(termometro.eq.FRIO,last_scraped_at.lt.{cold_threshold}),and(termometro.neq.FRIO,last_scraped_at.lt.{hot_threshold})")\
                .order("last_scraped_at", desc=False)\
                .limit(20).execute()
                
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
            res_fallback = self.db.table("candidatos")\
                .select("id,username,termometro,last_scraped_at")\
                .filter("status_monitoramento", "ilike", "Ativo")\
                .order("last_scraped_at", desc=False)\
                .limit(10).execute()

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

    def rotate_target(self, target: Target) -> None:
        """Remove o item processado e reinsere no fim da fila com status e termômetro (v86.3)."""
        if not target.username:
            return

        # Use horário local (UTC‑3) como referência de tempo
        LOCAL_TZ = timezone(timedelta(hours=-3))
        now = datetime.now(LOCAL_TZ)
        now_iso = now.isoformat()
        
        # PASA v86.3: Não pune o alvo se for um erro do Scraper
        # Apenas "junk_detected" ou "invalid_target: 404_not_found" justificam diminuir a temperatura
        # "no_comments_found" será tratado como falta de dados, mas não será classificado como FRIO
        is_error = hasattr(target, "error") and target.error
        is_no_comments = is_error and target.error == "no_comments_found"
        is_empty = is_error and target.error in ["junk_detected", "invalid_target: 404_not_found"]
        # Detecta erros de sessão ou bloqueio (ex: cookies expirados, 429, captcha, login wall)
        session_terms = ["session", "blocked", "429", "login wall", "captcha"]
        is_session_error = is_error and any(term in str(target.error).lower() for term in session_terms)
        is_system_error = is_error and not is_empty and not is_no_comments and not is_session_error
        
        # Se for um erro do sistema ou sessão, atualizamos o last_scraped_at mas NÃO mudamos o termômetro
        if is_system_error or is_session_error:
            logger.warning(f"⚠️ [Queue] Erro sistêmico/sessão detectado para @{target.username} ({target.error}). Mantendo temperatura atual.")
            self.db.table("candidatos").update({
                "last_scraped_at": now_iso
            }).eq("username", target.username).execute()
            
            if target.queue_id:
                self.db.table("fila_coleta").update({
                    "status": "FALHA",
                    "updated_at": now_iso
                }).eq("id", target.queue_id).execute()
            return

        frequencia = 0.0
        post_metas = getattr(target, "post_metas", [])
        valid_dates = []
        if post_metas:
            for m in post_metas:
                if m.get("timestamp"):
                    try:
                        # Usa horário local (UTC-3) para normalizar timestamps armazenados sem zona
                        valid_dates.append(_parse_local_timestamp(m["timestamp"]))
                    except Exception:
                        continue
        
        if (is_empty or not valid_dates) and not is_no_comments:
            # Tenta manter a temperatura atual se possível, senão MORNO
            termometro = getattr(target, "termometro", "MORNO")
            frequencia = 0.0
        elif is_no_comments or not valid_dates:
            # Caso especial: nenhum comentário encontrado, mas ainda não há dados suficientes
            # Tenta manter a temperatura atual
            termometro = getattr(target, "termometro", "MORNO")
            frequencia = 0.0
        else:
            last_post_date = max(valid_dates)
            days_since_last_post = (now - last_post_date).days
            
            if len(valid_dates) >= 2:
                delta_days = (max(valid_dates) - min(valid_dates)).days or 1
                frequencia = round((len(valid_dates) / delta_days) * 7, 1)
            else:
                frequencia = round(7 / (days_since_last_post + 1), 1)

            # Prioridade: frequência alta → QUENTE, caso contrário verifica tempo desde o último post
            if frequencia >= 5:
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
        self.db.table("candidatos").update(update_data).eq("username", target.username).execute()

        if target.queue_id:
            nova_prioridade = 1 if termometro == "QUENTE" else (5 if termometro in ("FRIO", "MORNO") else 3)
            self.db.table("fila_coleta").update({
                "status": "SEM_DADOS_RECENTES" if is_empty else "CONCLUIDO",
                "prioridade": nova_prioridade,
                "updated_at": now_iso
            }).eq("id", target.queue_id).execute()
            
        logger.info(f"[Queue] @{target.username} -> {termometro} ({frequencia} posts/sem)")

    def mark_candidate_scraped(self, target: Target) -> None:
        """Update the last_scraped_at timestamp for the candidate."""
        if not target.username:
            return
        self.db.table("candidatos").update({
            "last_scraped_at": datetime.now(timezone.utc).isoformat(),
        }).eq("username", target.username).execute()
