"""
Priorização Cognitiva de Alvos
================================
Estensão do QueueManager que prioriza perfis com picos de engajamento
baseada em métricas agregadas do Supabase.

CAPACIDADE DE MENOR RISCO E MAIOR ROI IMEDIATO:
    - Não requer LLM — apenas SQL agregado sobre tabela comentarios
    - Implementável como extensão da lógica de claim_next_target()
    - Lê volume recente de comentários e ajusta score de prioridade

Integração com QueueManager existente:
    - queue_manager.add_target_to_queue(username, priority=N)
    - claim_next_target() — ponto de extensão para priorização dinâmica

Métricas usadas para scoring:
    1. Volume de comentários nas últimas 24h (peso 40%)
    2. Proporção de comentários de ódio (peso 30%)
    3. Tempo desde última coleta (peso 20%)
    4. Nota de relevância do candidato (peso 10%)
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("agent_scraper.cognitive_prioritizer")


# ---------------------------------------------------------------------------
# Score de Prioridade
# ---------------------------------------------------------------------------

class TargetScore:
    """Score de prioridade de um alvo de coleta."""

    def __init__(
        self,
        username: str,
        volume_score: float = 0.0,
        hate_ratio_score: float = 0.0,
        recency_score: float = 0.0,
        relevance_score: float = 0.0,
    ):
        self.username = username
        self.volume_score = volume_score
        self.hate_ratio_score = hate_ratio_score
        self.recency_score = recency_score
        self.relevance_score = relevance_score

        # Pesos normalizados (soma = 1.0)
        self._weights = {
            "volume": 0.40,
            "hate_ratio": 0.30,
            "recency": 0.20,
            "relevance": 0.10,
        }

    @property
    def total_score(self) -> float:
        """Score ponderado total (0-100)."""
        return (
            self.volume_score * self._weights["volume"]
            + self.hate_ratio_score * self._weights["hate_ratio"]
            + self.recency_score * self._weights["recency"]
            + self.relevance_score * self._weights["relevance"]
        )

    @property
    def priority_level(self) -> int:
        """
        Nível de prioridade para o QueueManager.

        Returns:
            1-10 (1 = baixa, 10 = crítica)
        """
        score = self.total_score
        if score >= 80:
            return 10  # Crítica — ataque coordenado ou pico extremo
        elif score >= 60:
            return 8   # Alta — volume elevado de ódio
        elif score >= 40:
            return 5   # Média — padrão normal
        elif score >= 20:
            return 3   # Baixa — pouca atividade
        else:
            return 1   # Mínima — quase sem atividade

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "volume_score": round(self.volume_score, 2),
            "hate_ratio_score": round(self.hate_ratio_score, 2),
            "recency_score": round(self.recency_score, 2),
            "relevance_score": round(self.relevance_score, 2),
            "total_score": round(self.total_score, 2),
            "priority_level": self.priority_level,
        }


# ---------------------------------------------------------------------------
# Priorizador Cognitivo
# ---------------------------------------------------------------------------

class CognitivePrioritizer:
    """
    Priorização cognitiva de alvos baseada em métricas do Supabase.

    Não usa LLM — apenas SQL agregado. Esta é a capacidade de
    menor risco e maior ROI imediato do ScrapeAgent.

    Uso:
        prioritizer = CognitivePrioritizer(supabase_client)
        scores = await prioritizer.prioritize_targets(["user1", "user2"])
        for score in scores:
            await queue_manager.add_target_to_queue(
                score.username,
                priority=score.priority_level
            )
    """

    # Categorias de ódio usadas para cálculo de hate_ratio
    HATE_CATEGORIES = [
        "ODIO_RACIAL",
        "ODIO_GENERO",
        "ODIO_RELIGIOSO",
        "ODIO_XENOFOBIA",
        "ODIO_LGBTFOBIA",
        "AMEACA",
        "INCITACAO_VIOLENCIA",
    ]

    def __init__(
        self,
        supabase_client: Any = None,
        config: dict[str, Any] | None = None,
    ):
        self._supabase = supabase_client
        self._config = config or {}
        self._cache: dict[str, tuple[float, TargetScore]] = {}
        self._cache_ttl = self._config.get("cache_ttl", 300)  # 5 min

    # -----------------------------------------------------------------------
    # Priorização Principal
    # -----------------------------------------------------------------------

    async def prioritize_targets(
        self,
        usernames: list[str],
    ) -> list[TargetScore]:
        """
        Calcula scores de prioridade para uma lista de alvos.

        Args:
            usernames: Lista de usernames para priorizar

        Returns:
            Lista de TargetScore ordenada por prioridade decrescente
        """
        if not usernames:
            return []

        if not self._supabase:
            logger.warning("[prioritizer] Supabase não disponível — usando prioridade padrão")
            return [
                TargetScore(username=u, volume_score=50, recency_score=50)
                for u in usernames
            ]

        scores = []
        for username in usernames:
            score = await self._calculate_score(username)
            scores.append(score)

        # Ordena por score total decrescente
        scores.sort(key=lambda s: s.total_score, reverse=True)

        logger.info(
            f"[prioritizer] {len(scores)} alvos priorizados. "
            f"Top: {scores[0].username} (score={scores[0].total_score:.1f}, "
            f"priority={scores[0].priority_level})"
            if scores else "Nenhum alvo"
        )

        return scores

    async def _calculate_score(self, username: str) -> TargetScore:
        """
        Calcula score de prioridade para um único alvo.

        Verifica cache primeiro, depois consulta Supabase.
        """
        # Verifica cache
        now = time.time()
        if username in self._cache:
            cached_time, cached_score = self._cache[username]
            if (now - cached_time) < self._cache_ttl:
                return cached_score

        # Consulta métricas do Supabase
        metrics = await self._fetch_metrics(username)

        # Calcula scores parciais
        volume_score = self._normalize_volume(metrics["recent_comments"])
        hate_ratio_score = self._normalize_hate_ratio(
            metrics["recent_hate_comments"],
            metrics["recent_comments"],
        )
        recency_score = self._normalize_recency(metrics["last_collection_ago_s"])
        relevance_score = self._normalize_relevance(metrics["nota_relevancia"])

        score = TargetScore(
            username=username,
            volume_score=volume_score,
            hate_ratio_score=hate_ratio_score,
            recency_score=recency_score,
            relevance_score=relevance_score,
        )

        # Atualiza cache
        self._cache[username] = (now, score)

        return score

    # -----------------------------------------------------------------------
    # Consultas ao Supabase
    # -----------------------------------------------------------------------

    async def _fetch_metrics(self, username: str) -> dict:
        """
        Busca métricas agregadas do Supabase para um alvo.

        Queries:
            1. Contagem de comentários nas últimas 24h
            2. Contagem de comentários de ódio nas últimas 24h
            3. Tempo desde última coleta
            4. Nota de relevância do candidato
        """
        metrics = {
            "recent_comments": 0,
            "recent_hate_comments": 0,
            "last_collection_ago_s": 86400,  # Default: 24h
            "nota_relevancia": 5.0,          # Default: média
        }

        try:
            from datetime import datetime, timezone, timedelta

            yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

            # Query 1: Comentários nas últimas 24h
            comments_res = (
                self._supabase.table("comentarios")
                .select("id", count="exact")
                .eq("candidato_id", username)
                .gte("data_coleta", yesterday)
                .execute()
            )
            metrics["recent_comments"] = comments_res.count or 0

            # Query 2: Comentários de ódio nas últimas 24h
            hate_res = (
                self._supabase.table("comentarios")
                .select("id", count="exact")
                .eq("candidato_id", username)
                .in_("categoria_ia", self.HATE_CATEGORIES)
                .gte("data_coleta", yesterday)
                .execute()
            )
            metrics["recent_hate_comments"] = hate_res.count or 0

            # Query 3: Última coleta
            last_res = (
                self._supabase.table("comentarios")
                .select("data_coleta")
                .eq("candidato_id", username)
                .order("data_coleta", desc=True)
                .limit(1)
                .execute()
            )
            if last_res.data:
                last_date_str = last_res.data[0].get("data_coleta", "")
                try:
                    last_date = datetime.fromisoformat(last_date_str.replace("Z", "+00:00"))
                    metrics["last_collection_ago_s"] = (
                        datetime.now(timezone.utc) - last_date
                    ).total_seconds()
                except (ValueError, TypeError):
                    pass

            # Query 4: Nota de relevância
            cand_res = (
                self._supabase.table("candidatos")
                .select("nota_relevancia")
                .eq("username", username)
                .limit(1)
                .execute()
            )
            if cand_res.data:
                metrics["nota_relevancia"] = cand_res.data[0].get("nota_relevancia", 5.0) or 5.0

        except Exception as e:
            logger.error(f"[prioritizer] Erro ao buscar métricas para {username}: {e}")

        return metrics

    # -----------------------------------------------------------------------
    # Normalização de Scores (0-100)
    # -----------------------------------------------------------------------

    def _normalize_volume(self, count: int) -> float:
        """
        Normaliza volume de comentários para score 0-100.

        Escala logarítmica para evitar que perfis com milhares de
        comentários dominem completamente a priorização.

        Benchmarks:
            - 0 comentários → 0
            - 10 comentários → ~30
            - 50 comentários → ~55
            - 200 comentários → ~75
            - 500+ comentários → ~90+
        """
        import math
        if count <= 0:
            return 0.0
        return min(100.0, 100 * math.log10(count + 1) / math.log10(501))

    def _normalize_hate_ratio(self, hate_count: int, total_count: int) -> float:
        """
        Normaliza proporção de ódio para score 0-100.

        Ratio > 30% = score alto (>80)
        Ratio > 15% = score médio-alto (>60)
        Ratio < 5%  = score baixo (<30)
        """
        if total_count <= 0:
            return 0.0
        ratio = hate_count / total_count
        # Escala não-linear para dar mais peso a ratios altos
        return min(100.0, ratio * 300)

    def _normalize_recency(self, ago_s: float) -> float:
        """
        Normaliza tempo desde última coleta para score 0-100.

        Quanto mais tempo sem coletar, maior a urgência.
            - Coletou há 1h  → ~25
            - Coletou há 6h  → ~50
            - Coletou há 12h → ~65
            - Coletou há 24h → ~75
            - Coletou há 48h → ~90
        """
        if ago_s <= 0:
            return 0.0
        hours = ago_s / 3600
        # Escala logarítmica
        import math
        return min(100.0, 100 * math.log10(hours + 1) / math.log10(49))

    def _normalize_relevance(self, nota: float) -> float:
        """
        Normaliza nota de relevância (0-10) para score 0-100.
        """
        return min(100.0, max(0.0, nota * 10))

    # -----------------------------------------------------------------------
    # API de Conveniência para QueueManager
    # -----------------------------------------------------------------------

    async def get_next_priority(self, usernames: list[str]) -> tuple[str, int]:
        """
        Retorna o próximo alvo de maior prioridade e seu nível.

        Usado pelo QueueManager como extensão de claim_next_target().

        Args:
            usernames: Lista de usernames candidatos

        Returns:
            (username, priority_level)
        """
        scores = await self.prioritize_targets(usernames)

        if not scores:
            return ("", 1)

        top = scores[0]
        return (top.username, top.priority_level)

    async def update_queue_priorities(
        self,
        queue_manager: Any,
        usernames: list[str] | None = None,
    ) -> int:
        """
        Atualiza prioridades na fila do QueueManager.

        Se usernames não fornecido, busca alvos ativos do Supabase.

        Returns:
            Número de alvos atualizados
        """
        if not usernames and self._supabase:
            try:
                res = (
                    self._supabase.table("candidatos")
                    .select("username")
                    .eq("status_monitoramento", "ATIVO")
                    .execute()
                )
                usernames = [c["username"] for c in (res.data or []) if c.get("username")]
            except Exception as e:
                logger.error(f"[prioritizer] Erro ao buscar alvos ativos: {e}")
                return 0

        if not usernames:
            return 0

        scores = await self.prioritize_targets(usernames)
        updated = 0

        for score in scores:
            try:
                await queue_manager.add_target_to_queue(
                    score.username,
                    priority=score.priority_level,
                )
                updated += 1
            except Exception as e:
                logger.warning(f"[prioritizer] Erro ao atualizar fila para {score.username}: {e}")

        logger.info(f"[prioritizer] {updated} alvos atualizados na fila de prioridade")
        return updated
