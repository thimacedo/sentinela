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
        # Reutiliza o scraper se fornecido, senão cria um local (Lazy Load v90.6)
        self._scraper = scraper

    @property
    def scraper(self) -> InstagramScraperV2:
        if self._scraper is None:
            from core.instagram_scraper_v2 import InstagramScraperV2
            self._scraper = InstagramScraperV2(headless=True)
        return self._scraper

    async def research_and_validate(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Executa o pipeline completo de inteligência para um alvo usando o framework OODA.
        """
        username = username.lower().strip().replace('@', '')
        logger.info(f"OODA [Intelligence]: Analisando @{username}...")

        # 1. OBSERVE: Coleta os sinais vitais brutos do alvo
        ig_res = await self._fetch_ig_basic_info(username)
        
        # 2. ORIENT: Interpreta a saúde do perfil antes de gastar recursos avançados
        if not ig_res or not ig_res.get("valid"):
            reason = ig_res.get("reason") if ig_res else "unknown_error"
            
            if reason in ["404_not_found", "account_private", "header_not_found"]:
                logger.warning(f"OODA [Orient]: @{username} negado por {reason}. Baixa confiança inicial.")
                # DECIDE & ACT Early (Abortar)
                final_data = {
                    "username": username,
                    "identidade_validada": False,
                    "status_monitoramento": "DESATIVADO",
                    "motivo_desativacao": f"Perfil inacessível no Instagram: {reason}",
                    "atualizado_em": datetime.now(timezone.utc).isoformat()
                }
                await db_client.upsert_candidate(final_data)
                return final_data
            
            logger.warning(f"OODA [Orient]: @{username} inacessível temporariamente ({reason}). Reagendar.")
            return None

        ig_data = ig_res
        
        # 3. DECIDE: Determinar a real identidade e cruzar com dados oficiais
        official_data = await self._search_official_sources(username, ig_data.get("display_name"))
        enriched = await self._enrich_and_validate(username, ig_data, official_data)
        
        is_valid = enriched.get("identidade_validada", False)
        status = "ATIVO" if is_valid else "DESATIVADO"
        motivo = enriched.get("motivo_rejeicao") if not is_valid else None

        # 4. ACT: Aplicar as restrições e salvar o veredito final
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

        await db_client.upsert_candidate(final_data)
        logger.info(f"OODA [Act]: Conclusão para @{username} salva (Válido: {is_valid})")
        
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
            logger.error(f"Erro ao capturar info básica de @{username}: {e}", exc_info=True)
            return {"valid": False, "reason": f"exception: {str(e)[:100]}"}
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
        from core.ground_truth import ground_truth
        
        # 1. Verifica Tabela da Verdade
        verdade = ground_truth.get_truth(username)
        if verdade:
            return {
                "identidade_validada": True,
                "motivo_rejeicao": None,
                "nome_completo": verdade["nome_completo"],
                "cargo": verdade["cargo"],
                "sexo": verdade["sexo"],
                "partido": "SEM PARTIDO", # Será enriquecido depois se necessário
                "estado": "NACIONAL",
                "ideologia": "Centro",
                "quality_confidence": 1.0
            }

        # 2. Taxonomia Fechada (PASA v94.0)
        TAXONOMIA_CARGOS_VALIDOS = [
            "Presidente", "Presidenta", "Vice-Presidente", "Vice-Presidenta",
            "Governador", "Governadora", "Vice-Governador", "Vice-Governadora",
            "Senador", "Senadora", "Deputado Federal", "Deputada Federal",
            "Deputado Estadual", "Deputada Estadual", "Prefeito", "Prefeita",
            "Vereador", "Vereadora", "Ministro STF", "Ministra STF",
            "Ministro", "Ministra", "Influenciador Político", "Influenciadora Política",
            "Institucional", "Pré-candidato", "Pré-candidata", "Nacional",
            "Ex-Prefeito", "Ex-Prefeita", "Jornalista"
        ]

        prompt = f"""
        Consolidador de Inteligência Sentinela. Analise a elegibilidade do alvo para monitoramento.
        ESCOPO: Candidatos reais, Políticos em mandato, Jornalistas de política, Ativistas e Influenciadores Políticos.
        
        IG={json.dumps(ig_data)}
        OFICIAL={json.dumps(official_data)}

        REGRAS ESTRITAS DE SANITIZAÇÃO:
        1. O campo "cargo" DEVE ser estritamente um destes da lista: {TAXONOMIA_CARGOS_VALIDOS}
        2. O campo "sexo" DEVE ser apenas "M" (Masculino), "F" (Feminino) ou "NI" (Não identificado).
        3. Se o sexo for "F", utilize obrigatoriamente a versão feminina do cargo (ex: "Deputada Federal", "Senadora", "Governadora", "Vereadora", "Ministra", "Influenciadora Política", "Pré-candidata").
        4. Se o sexo for "M", utilize a versão masculina correspondente.
        5. Se não houver certeza absoluta do cargo atual, use "Influenciador Político" (ou "Influenciadora Política" se o sexo for "F").
        6. O username é o dono da conta. Não confunda com apoiadores.

        Retorne JSON:
        {{
            "identidade_validada": boolean,
            "motivo_rejeicao": "string ou null",
            "nome_completo": "string",
            "cargo": "string_exatamente_como_na_lista",
            "sexo": "M_ou_F_ou_NI",
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
