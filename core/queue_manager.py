from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from models.target import Target

logger = logging.getLogger("queue_manager")


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
            username = manual_target.strip().lstrip("@")
            if username not in blocked:
                logger.info(f"📍 [Queue] Selecionado alvo manual: @{username}")
                self._add_to_blocked(username, seen_targets, active_targets)
                return Target(username=username, candidato_id=username, source="manual")

        # 2. DISTRIBUIÇÃO PONDERADA: fila_coleta vs Fallback
        # Mecanismo de Fairness: 25% de chance de priorizar a rotação global para evitar estagnação.
        import random
        prefer_global_rotation = random.random() < 0.25
        
        target = None
        if not prefer_global_rotation:
            target = self._get_from_fila_coleta(blocked, seen_queue_ids, seen_targets, active_targets)
        
        if not target:
            target = self._get_from_global_rotation(blocked, seen_targets, active_targets)
            
        return target

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
                username = item.get("username") or item.get("candidato_id") or item.get("target_username")
                
                # Resolução de ID para Username se necessário
                if username and len(str(username)) > 30:
                    cand = self.db.table("candidatos").select("username").eq("id", username).limit(1).execute()
                    if cand.data: username = cand.data[0]["username"]
                
                username = str(username).strip().lstrip("@")
                
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

    def _ensure_queue_populated(self, min_pending: int = 5) -> None:
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

            # Busca candidatos CONCLUIDO/SEM_DADOS_RECENTES mais antigos para reinserir
            candidatos_res = self.db.table("candidatos")\
                .select("id,username,termometro")\
                .eq("status_monitoramento", "Ativo")\
                .order("last_scraped_at", desc=False)\
                .limit(20).execute()

            reinseridos = 0
            for cand in (candidatos_res.data or []):
                username = cand.get("username")
                if not username:
                    continue
                # Verifica se já existe na fila como PENDENTE
                check = self.db.table("fila_coleta")\
                    .select("id")\
                    .eq("candidato_id", cand["id"])\
                    .eq("status", "PENDENTE")\
                    .limit(1).execute()
                if check.data:
                    continue  # Já está pendente

                # Determina prioridade pelo termômetro
                termometro = cand.get("termometro", "MORNO")
                prioridade = 1 if termometro == "QUENTE" else (5 if termometro == "FRIO" else 3)

                # Reinserção via upsert (atualiza se existir, insere se não existir)
                self.db.table("fila_coleta").upsert({
                    "candidato_id": cand["id"],
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
        """Garante que todos os candidatos ativos sejam processados circularmente com Smart Backoff (PASA v70.4)."""
        try:
            # ❄️ SMART BACKOFF: Pula alvos 'FRIO' que foram processados recentemente (< 12h)
            from datetime import datetime, timedelta, timezone
            cold_threshold = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()

            # Query otimizada: Prioriza quem nunca foi coletado ou não é frio
            res = self.db.table("candidatos")\
                .select("id,username,termometro,last_scraped_at")\
                .eq("status_monitoramento", "Ativo")\
                .or_(f"termometro.neq.FRIO,last_scraped_at.lt.{cold_threshold},last_scraped_at.is.null")\
                .order("last_scraped_at", desc=False)\
                .limit(15).execute()
                
            for cand in res.data or []:
                username = cand["username"]
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
        return None

    def _add_to_blocked(self, username, seen_targets, active_targets):
        """Marca o alvo como em processamento para evitar colisão entre workers."""
        seen_targets.add(username)
        if active_targets is not None:
            active_targets.add(username)

    def rotate_target(self, target: Target) -> None:
        """Remove o item processado e reinsere no fim da fila com status e termômetro (v59.0)."""
        if not target.username:
            return

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        
        # 1. Cálculo do Termômetro de Atividade (v59.0)
        frequencia = 0.0
        termometro = "MORNO"
        
        # Se o scraper capturou metadados de postagem (timestamps)
        post_metas = getattr(target, "post_metas", [])
        if post_metas:
            valid_dates = []
            for m in post_metas:
                if m.get("timestamp"):
                    try:
                        valid_dates.append(datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')))
                    except: continue
            
            if len(valid_dates) >= 2:
                # Calcula dias entre o mais novo e o mais velho do grid capturado
                delta_days = (max(valid_dates) - min(valid_dates)).days or 1
                frequencia = round((len(valid_dates) / delta_days) * 7, 1) # Posts por semana
                
                if frequencia >= 5: termometro = "QUENTE"
                elif frequencia < 1: termometro = "FRIO"
        
        # 2. Atualiza tabela principal de candidatos
        update_data = {
            "last_scraped_at": now_iso,
            "posts_frequencia_semanal": frequencia,
            "termometro": termometro
        }
        self.db.table("candidatos").update(update_data).eq("username", target.username).execute()

        # 3. Atualiza fila_coleta (Prioridade Dinâmica)
        if target.queue_id:
            is_empty = hasattr(target, "error") and target.error in ["no_comments_found", "junk_detected"]
            
            # Se for QUENTE, forçamos prioridade 1 (Máxima) para o próximo agendamento
            # Se for FRIO, baixamos para 5.
            nova_prioridade = 1 if termometro == "QUENTE" else (5 if termometro == "FRIO" else 3)

            self.db.table("fila_coleta").update({
                "status": "SEM_DADOS_RECENTES" if is_empty else "CONCLUIDO",
                "prioridade": nova_prioridade,
                "updated_at": now_iso
            }).eq("id", target.queue_id).execute()
            
            if is_empty:
                logger.info(f"💤 [Queue] @{target.username} Hibernando ({termometro} | {frequencia} p/sem)")
                return

    def mark_candidate_scraped(self, target: Target) -> None:
        """Update the last_scraped_at timestamp for the candidate."""
        if not target.username:
            return
        self.db.table("candidatos").update({
            "last_scraped_at": datetime.now(timezone.utc).isoformat(),
        }).eq("username", target.username).execute()