import logging
import httpx
from typing import List, Dict, Any, Optional
from core.config import settings

logger = logging.getLogger("SaConsultaBanco")

class SaConsultaBanco:
    """
    Subagente de dados especializado em interagir com o Datasette local.
    Fornece consultas SQL assíncronas de alto desempenho, busca textual (FTS) e 
    consolidação de métricas estruturadas para todos os workers do Sentinela.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.DATASETTE_URL.rstrip('/')
        # O banco SQLite padrão gerado pelo sincronizador chama-se 'sentinela_data'
        self.db_name = "sentinela_data"
        self.client = httpx.AsyncClient(timeout=10.0)

    async def query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Executa uma consulta SQL arbitrária no Datasette e retorna os resultados estruturados.
        Garante tratamento de erros amigável para consultas mal-formadas.
        """
        url = f"{self.base_url}/{self.db_name}.json"
        params = {"sql": sql_query, "_shape": "objects"}
        
        try:
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("rows", [])
            else:
                error_msg = response.json().get("error", "Erro desconhecido")
                logger.error(f"Erro SQL ({response.status_code}): {error_msg} | Query: {sql_query}")
                return []
        except Exception as e:
            logger.error(f"Falha de conexão com a API do Datasette: {e}")
            return []

    async def search_comments(self, term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Realiza uma busca textual indexada (Full-Text Search FTS5) de alta performance
        nas tabelas de comentários coletados no banco de dados local.
        """
        sql = f"""
            SELECT c.* 
            FROM comentarios c
            JOIN comentarios_fts fts ON c.id = fts.id
            WHERE comentarios_fts MATCH '{term}'
            LIMIT {limit}
        """
        return await self.query(sql)

    async def get_hate_stats(self) -> List[Dict[str, Any]]:
        """
        Calcula estatísticas consolidadas de discurso de ódio agrupadas por candidato.
        Retorna a contagem de comentários neutros, de ódio e a taxa de ódio correspondente.
        """
        sql = """
            SELECT 
                candidato_id,
                COUNT(*) as total_comentarios,
                SUM(CASE WHEN categoria_ia = 'ODIO' THEN 1 ELSE 0 END) as total_odio,
                ROUND(CAST(SUM(CASE WHEN categoria_ia = 'ODIO' THEN 1 ELSE 0 END) AS REAL) / COUNT(*) * 100, 2) as taxa_odio_percent
            FROM comentarios
            GROUP BY candidato_id
            ORDER BY total_odio DESC
        """
        return await self.query(sql)

    async def get_top_attackers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Identifica as contas (autores) mais ofensivas/agressivas do banco,
        ordenadas pela quantidade de discursos de ódio classificados.
        """
        sql = f"""
            SELECT 
                autor_username,
                COUNT(*) as total_ataques,
                GROUP_CONCAT(DISTINCT candidato_id) as alvos_atacados
            FROM comentarios
            WHERE categoria_ia = 'ODIO'
            GROUP BY autor_username
            ORDER BY total_ataques DESC
            LIMIT {limit}
        """
        return await self.query(sql)

    async def get_ia_performance(self) -> Dict[str, Any]:
        """
        Consolida métricas de performance e estabilidade dos modelos da malha de IA.
        """
        sql = """
            SELECT 
                categoria_ia,
                COUNT(*) as contagem,
                AVG(confianca_ia) as confianca_media
            FROM comentarios
            GROUP BY categoria_ia
        """
        rows = await self.query(sql)
        return {row['categoria_ia']: {"total": row['contagem'], "confianca_media": row['confianca_media']} for row in rows}

    async def close(self):
        """Fecha o cliente HTTP de conexão."""
        await self.client.aclose()
