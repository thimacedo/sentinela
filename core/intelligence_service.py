import asyncio
import logging
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.instagram_scraper_v2 import InstagramScraperV2
from core.ai_service import ai_service
from core.db import db_client

logger = logging.getLogger("core.intelligence")

class IntelligenceService:
    """
    Serviço centralizado para pesquisa, enriquecimento e governança de alvos.
    Pode ser usado inline por coletores ou em background por pesquisadores.
    """

    def __init__(self, scraper: Optional[InstagramScraperV2] = None):
        # Reutiliza o scraper se fornecido, senão cria um local
        self.scraper = scraper or InstagramScraperV2(headless=True)

    async def research_and_validate(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Executa o pipeline completo de inteligencia para um alvo.
        """
        username = username.lower().strip().replace('@', '')
        logger.info(f"Inteligencia: Analisando @{username}...")

        # 1. Coleta basica via Instagram
        ig_res = await self._fetch_ig_basic_info(username)
        
        # Se falhou mas temos um motivo claro (404 ou Privado), podemos validar negativamente ja
        if not ig_res or not ig_res.get("valid"):
            reason = ig_res.get("reason") if ig_res else "unknown_error"
            
            if reason in ["404_not_found", "account_private", "header_not_found"]:
                logger.warning(f"Inteligencia: @{username} negado por {reason}.")
                final_data = {
                    "username": username,
                    "identidade_validada": False,
                    "status_monitoramento": "DESATIVADO",
                    "motivo_desativacao": f"Perfil inacessivel no Instagram: {reason}",
                    "atualizado_em": datetime.now(timezone.utc).isoformat()
                }
                await db_client.upsert_candidate(final_data)
                return final_data
            
            logger.warning(f"Inteligencia: @{username} inacessivel temporariamente ({reason}).")
            return None

        # 2. Pesquisa em Fontes Oficiais
        ig_data = ig_res # Para compatibilidade com os metodos abaixo
        official_data = await self._search_official_sources(username, ig_data.get("display_name"))

        # 3. Consolidacao e Validacao de Escopo via IA
        enriched = await self._enrich_and_validate(username, ig_data, official_data)
        
        # 4. Decisao de Governanca
        is_valid = enriched.get("identidade_validada", False)
        status = "ATIVO" if is_valid else "DESATIVADO"
        motivo = enriched.get("motivo_rejeicao") if not is_valid else None

        # 5. Consolidacao Final
        final_data = {
            "username": username,
            "nome_completo": enriched.get("nome_completo") or ig_data.get("display_name"),
            "bio": ig_data.get("biography"),
            "seguidores": ig_data.get("followers_count", 0),
            "cargo": enriched.get("cargo", "DESCONHECIDO"),
            "partido": enriched.get("partido"),
            "estado": enriched.get("estado"),
            "ideologia": enriched.get("ideologia"),
            "identidade_validada": is_valid,
            "status_monitoramento": status,
            "motivo_desativacao": motivo,
            "atualizado_em": datetime.now(timezone.utc).isoformat()
        }

        # 6. Persistencia
        await db_client.upsert_candidate(final_data)
        
        final_data["_quality"] = enriched.get("quality_confidence", 0.5)
        return final_data

    async def _fetch_ig_basic_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Retorna o dicionario de validacao completo do scraper."""
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
                
                # Se for valido, adiciona campo de seguidores formatado
                if validation["valid"]:
                    validation["followers_count"] = self._parse_followers(validation.get("followers", "0"))
                
                return validation
        except Exception as e:
            return {"valid": False, "reason": f"exception: {str(e)[:50]}"}
        return None

    async def _search_official_sources(self, username: str, name: str) -> Dict[str, Any]:
        prompt = f"Pesquise dados oficiais para a figura pública: {name} (@{username}). Retorne JSON com nome_urna, cargo_eletivo, partido_atual, uf."
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
        prompt = f"""
        Consolidador de Inteligência Sentinela. Analise a elegibilidade do alvo para monitoramento.
        ESCOPO: Candidatos reais, Políticos em mandato, Jornalistas de política, Ativistas e Influenciadores Políticos.
        
        IG={json.dumps(ig_data)}
        OFICIAL={json.dumps(official_data)}

        REGRA DE OURO: Diferencie Influenciadores/Comunicadores de Pré-Candidatos.
        Só atribua cargos como 'Deputado', 'Prefeito' ou 'Candidato' se houver evidência oficial (DivulgaCand/Notícias).
        Se for uma figura pública que apenas comenta política ou tem influência, use 'Influenciador Político'.

        Retorne JSON:
        {{
            "identidade_validada": boolean,
            "motivo_rejeicao": "string ou null",
            "nome_completo": "string",
            "cargo": "Ex: Influenciador Político, Deputado Federal, Jornalista",
            "partido": "Sigla ou 'SEM PARTIDO'",
            "estado": "Sigla UF ou 'NACIONAL'",
            "ideologia": "DIREITA|ESQUERDA|CENTRO|DESCONHECIDO",
            "quality_confidence": float (0.0-1.0)
        }}
        """
        try:
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except: return {"identidade_validada": False, "motivo_rejeicao": "Erro de IA", "quality_confidence": 0.0}

    def _parse_followers(self, s: str) -> int:
        try:
            import re
            s = s.lower().replace('seguidores', '').replace('followers', '').strip()
            if 'mi' in s or 'm' in s: return int(float(s.replace('mi', '').replace('m', '').replace(',', '.')) * 1_000_000)
            if 'mil' in s or 'k' in s: return int(float(s.replace('mil', '').replace('k', '').replace(',', '.')) * 1_000)
            return int(re.sub(r'\D', '', s) or 0)
        except: return 0

intelligence_service = IntelligenceService()
