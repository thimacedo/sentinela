# workers/processors/classifier_worker.py
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  ⚠️  DEPRECADO — PASA v88.0                                          ║
# ║  Este worker foi substituído por AIProcessorWorker.                  ║
# ║  Use: workers/processors/ai_processor_worker.py                      ║
# ║  Razão: ClassifierWorker usa Gemini diretamente (sem cascata de IA,  ║
# ║  sem circuit breaker e sem fallback). O AIProcessorWorker integra a  ║
# ║  cascata completa de provedores via core/ai_service.py.              ║
# ║  Será removido após validação de que nenhum módulo de produção       ║
# ║  o importa diretamente (ver: tests/sandbox_full_cycle.py).           ║
# ╚══════════════════════════════════════════════════════════════════════╝
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from workers.core.base_worker import BaseWorker
from core.event_bus import bus
from core.supabase_service import get_supabase_client

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

PASA_SYSTEM_PROMPT = """
Você é um classificador forense do sistema PASA v16.4.
Analise o comentário e retorne APENAS um JSON com este formato exato:
{"categoria": "CATEGORIA", "is_hate": true/false, "confianca": 0.0}

Categorias válidas:
- NEUTRO: apoio, crítica legítima, comentário neutro
- AMEACA: ameaças físicas, chamados à violência
- ODIO_IDENTITARIO: ódio por raça, gênero, religião, origem
- VIOLENCIA_GENERO: misoginia, ataques baseados em gênero
- RIGOR_CRIMINAL: acusações criminais sem evidência, difamação
- INSULTO_AD_HOMINEM: insultos pessoais sem conteúdo político
- ATAQUE_INSTITUCIONAL: ataques ao STF, TSE, urnas, democracia

Regras:
- is_hate=true apenas para AMEACA, ODIO_IDENTITARIO, VIOLENCIA_GENERO
- confianca entre 0.0 e 1.0
- Responda SOMENTE o JSON, sem markdown, sem explicação
""".strip()


class ClassifierWorker(BaseWorker):
    def __init__(self):
        super().__init__("ClassifierWorker")
        self.db = get_supabase_client()
        self.queue = "classify_comments"
        self.gold_path = PROJECT_ROOT / 'data' / 'classifier_gold_dataset.json'

    def _get_system_prompt(self) -> str:
        """Gera o prompt do sistema com injeção dinâmica de exemplos (Padrão Ouro)."""
        prompt = PASA_SYSTEM_PROMPT
        
        if self.gold_path.exists():
            try:
                with open(self.gold_path, 'r', encoding='utf-8') as f:
                    gold_data = json.load(f)
                
                if gold_data:
                    prompt += "\n\nUse os seguintes exemplos reais auditados para guiar sua decisão (Padrão Ouro):\n"
                    # Pega apenas os 10 exemplos mais recentes para não estourar o contexto
                    for item in gold_data[-10:]:
                        prompt += f"- Texto: \"{item['text']}\" -> Categoria: {item['label'].upper()}\n"
                    
                    self.logger.info(f"💉 Injetados {len(gold_data[:10])} exemplos de Padrão Ouro no prompt.")
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao carregar Padrão Ouro: {e}")
        
        return prompt

    async def _classify_one(
        self, client: httpx.AsyncClient, comment: dict
    ) -> dict | None:
        texto = comment.get("texto_bruto", "").strip()
        if not texto:
            return None

        body = {
            "system_instruction": {"parts": [{"text": self._get_system_prompt()}]},
            "contents": [{"parts": [{"text": texto}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 100,
            },
        }

        try:
            resp = await client.post(
                GEMINI_URL,
                params={"key": GEMINI_API_KEY},
                json=body,
            )
            resp.raise_for_status()
            raw = resp.json()
            text_out = (
                raw["candidates"][0]["content"]["parts"][0]["text"].strip()
            )
            
            # Sanitização básica para o caso do Gemini retornar markdown ```json ... ```
            if "```json" in text_out:
                text_out = text_out.split("```json")[1].split("```")[0].strip()
            elif "```" in text_out:
                text_out = text_out.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text_out)

            return {
                "id": comment["id"],
                "categoria_ia": parsed.get("categoria", "NEUTRO"),
                "is_hate": parsed.get("is_hate", False),
                "confianca_ia": float(parsed.get("confianca", 0.5)),
                "processado_ia": True,
            }

        except json.JSONDecodeError as exc:
            self.logger.warning(
                f"Gemini retornou JSON inválido para {comment['id']}: {exc}"
            )
            return None
        except httpx.HTTPStatusError as exc:
            self.logger.error(f"Gemini HTTP {exc.response.status_code}: {exc}")
            raise  # Sobe para o retry do BaseWorker

    def _fetch_unclassified_ids(self, limit: int = 20) -> list[str]:
        res = (
            self.db.table("comentarios")
            .select("id")
            .eq("processado_ia", False)
            .eq("mined", True)
            .limit(limit)
            .execute()
        )
        return [row["id"] for row in (res.data or [])]

    def _fetch_comments(self, ids: list[str]) -> list[dict]:
        res = (
            self.db.table("comentarios")
            .select("id, texto_bruto")
            .in_("id", ids)
            .execute()
        )
        return res.data or []

    def _persist_classifications(self, results: list[dict]) -> None:
        for r in results:
            self.db.table("comentarios").update({
                "categoria_ia":  r["categoria_ia"],
                "is_hate":       r["is_hate"],
                "confianca_ia":  r["confianca_ia"],
                "processado_ia": True,
            }).eq("id", r["id"]).execute()

        self.logger.info(f"✅ {len(results)} classificações persistidas.")
