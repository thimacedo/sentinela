import asyncio
import logging
import json
import os
import re
from typing import Dict, Any, Optional
from core.instagram_scraper_v2 import InstagramScraperV2
from core.ai_service import ai_service
from core.db import db_client

logger = logging.getLogger("TargetResearchWorker")

class TargetResearchWorker:
    """
    Worker especializado em pesquisar e enriquecer dados de novos alvos.
    Utiliza Instagram para dados básicos e IA para inferência e estruturação.
    """

    def __init__(self):
        self.scraper = InstagramScraperV2(headless=True)

    async def research_target(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Executa a pesquisa completa de um alvo a partir do handle do Instagram.
        """
        username = username.lower().strip().replace('@', '')
        logger.info(f"🔍 Iniciando pesquisa profunda para @{username}...")

        # 1. Coleta básica via Instagram
        ig_data = await self._fetch_ig_basic_info(username)
        if not ig_data:
            logger.error(f"❌ Não foi possível acessar o perfil @{username} no Instagram.")
            return None

        # 2. Pesquisa em Fontes Oficiais (TSE/TRE) via IA
        official_data = await self._search_official_sources(username, ig_data.get("display_name"))

        # 3. Enriquecimento via IA (Mistral) - Consolidando tudo
        enriched_data = await self._enrich_with_ai(username, ig_data, official_data)
        
        # 4. Consolidação e Persistência
        final_data = {
            "username": username,
            "nome_completo": enriched_data.get("nome_completo") or ig_data.get("display_name"),
            "bio": ig_data.get("biography"),
            "seguidores": ig_data.get("followers_count", 0),
            "cargo": enriched_data.get("cargo", "DESCONHECIDO"),
            "partido": enriched_data.get("partido"),
            "estado": enriched_data.get("estado"),
            "ideologia": enriched_data.get("ideologia"),
            "status_monitoramento": "ATIVO",
            "data_entrada": enriched_data.get("data_entrada", "2026-05-28"), 
            "termometro": "MORNO"
        }

        # 4. Salva no banco
        res = await db_client.upsert_candidate(final_data)
        if res:
            logger.info(f"✅ Alvo @{username} enriquecido e salvo com sucesso.")
            return final_data
        
        return None

    async def _fetch_ig_basic_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Acessa o IG e extrai o que for possível da Bio."""
        try:
            # Usando o método privado de validação que já captura bio info
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                # Pega uma sessão válida
                session = self.scraper._get_next_session()
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                await context.add_cookies([{'name': 'sessionid', 'value': session.session_id, 'domain': '.instagram.com', 'path': '/'}])
                page = await context.new_page()
                
                await page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                
                validation = await self.scraper._validate_target_identity(page, username)
                await browser.close()
                
                if validation["valid"]:
                    # Converte seguidores string (ex: "1.5M") para int se possível
                    followers_str = validation.get("followers", "0")
                    followers_count = self._parse_followers(followers_str)
                    
                    return {
                        "display_name": validation.get("display_name"),
                        "biography": validation.get("biography"),
                        "followers_count": followers_count,
                        "is_verified": validation.get("is_verified", False)
                    }
        except Exception as e:
            logger.error(f"Erro ao coletar dados do IG: {e}")
        return None

    def _parse_followers(self, s: str) -> int:
        try:
            s = s.lower().replace('seguidores', '').replace('followers', '').strip()
            if 'mi' in s or 'm' in s:
                return int(float(s.replace('mi', '').replace('m', '').replace(',', '.')) * 1_000_000)
            if 'mil' in s or 'k' in s:
                return int(float(s.replace('mil', '').replace('k', '').replace(',', '.')) * 1_000)
            return int(re.sub(r'\D', '', s) or 0)
        except: return 0

    async def _search_official_sources(self, username: str, name: str) -> Dict[str, Any]:
        """
        Simula a consulta a órgãos oficiais (TSE/TRE) usando IA para extrair dados públicos conhecidos.
        Em produção, aqui poderia haver uma integração com API de busca ou scraping do DivulgaCand.
        """
        prompt = f"""
        Aja como um pesquisador de dados eleitorais brasileiros.
        Pesquise informações oficiais sobre a figura pública: "{name}" (@{username}).
        Fontes de referência: TSE (DivulgaCand), TREs, Portais de Transparência.

        Retorne um JSON com os dados oficiais encontrados:
        {{
            "nome_urna": "Nome usado na urna",
            "cargo_eletivo": "Cargo atual ou pleiteado",
            "partido_atual": "Sigla do Partido",
            "uf": "Estado",
            "situacao": "ELEITO|SUPLENTE|EXERCÍCIO|ATIVISTA",
            "biografia_oficial": "Resumo biográfico focado na carreira política"
        }}
        Se não encontrar dados específicos para este nome exato, retorne campos como null.
        """
        try:
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {}

    async def _enrich_with_ai(self, username: str, ig_data: Dict[str, Any], official_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolida dados do IG e de fontes oficiais usando Mistral."""
        prompt = f"""
        Consolide os dados do Instagram e de Fontes Oficiais para criar o perfil definitivo do alvo monitorado.
        
        --- DADOS INSTAGRAM ---
        Username: @{username}
        Display: {ig_data.get('display_name')}
        Bio: {ig_data.get('biography')}

        --- DADOS OFICIAIS (TSE/TRE) ---
        Nome Urna: {official_data.get('nome_urna')}
        Cargo: {official_data.get('cargo_eletivo')}
        Partido: {official_data.get('partido_atual')}
        UF: {official_data.get('uf')}
        Bio Oficial: {official_data.get('biografia_oficial')}

        Crie um perfil estruturado para o sistema Sentinela.
        Retorne um JSON:
        {{
            "nome_completo": "Nome Real Completo",
            "cargo": "Cargo Político Padronizado",
            "partido": "Sigla",
            "estado": "UF",
            "ideologia": "DIREITA|ESQUERDA|CENTRO|DESCONHECIDO",
            "data_entrada": "YYYY-MM-DD"
        }}
        Priorize dados oficiais para Nome e Cargo. Priorize Instagram para a Bio (que já foi salva).
        """
        try:
            response = await ai_service.mistral_client.chat.completions.create(
                model="open-mistral-nemo",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Erro no enriquecimento via IA: {e}")
            return {}

target_research_worker = TargetResearchWorker()

if __name__ == "__main__":
    # Teste rápido
    async def test():
        worker = TargetResearchWorker()
        res = await worker.research_target("erikahiltonoficial")
        print(json.dumps(res, indent=2))
    
    asyncio.run(test())
