import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.config import settings
from supabase import create_client, Client

from core.circuit_breaker import db_circuit_breaker

class DatabaseClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }
        self.client: Client = create_client(self.url, self.key) if self.url and self.key else None

    async def fetch_unprocessed_comments(self, limit: int = 200, org_id: str = None) -> List[Dict[str, Any]]:
        """Busca comentários que ainda não foram processados pela IA."""
        if not db_circuit_breaker.can_execute("supabase"):
            return []
        
        url = f"{self.url}/rest/v1/comentarios?processado_ia=not.eq.true&limit={limit}"
        if org_id:
            url += f"&organization_id=eq.{org_id}"
            
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    db_circuit_breaker.record_success("supabase")
                    return resp.json()
                db_circuit_breaker.record_failure("supabase", resp.status_code)
                return []
        except Exception:
            db_circuit_breaker.record_failure("supabase")
            return []

    async def fetch_all_data(self, org_id: str = None) -> List[Dict[str, Any]]:
        """Busca todos os comentários processados de uma organização."""
        url = f"{self.url}/rest/v1/comentarios?select=*"
        if org_id:
            url += f"&organization_id=eq.{org_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            return []

    async def update_comment_classification(self, comment_id: str, data: Dict[str, Any]):
        """Atualiza a classificação de um único comentário."""
        url = f"{self.url}/rest/v1/comentarios?id=eq.{comment_id}"
        async with httpx.AsyncClient() as client:
            await client.patch(url, headers=self.headers, json=data)

    async def batch_update_comments(self, updates: List[Dict[str, Any]]):
        """
        Executa atualizações em lote para comentários usando upsert do Supabase.
        Cada dicionário em 'updates' deve conter a chave 'id'.
        """
        if not self.client or not updates:
            return

        try:
            # O upsert no Supabase funciona como merge se o id_externo estiver presente
            self.client.table('comentarios').upsert(updates, on_conflict='id_externo').execute()
            print(f"[DB] {len(updates)} comentarios atualizados em lote.")
        except Exception as e:
            print(f"[DB] Erro no batch_update_comments: {e}")

    async def batch_update_ad_classification(self, updates: List[Dict[str, Any]]):
        """
        Executa atualizações em lote para classificações de anúncios.
        Cada dicionário em 'updates' deve conter a chave 'id'.
        """
        if not self.client or not updates:
            return

        try:
            self.client.table('anuncios').upsert(updates).execute()
            print(f"[DB] {len(updates)} anuncios atualizados em lote.")
        except Exception as e:
            print(f"[DB] Erro no batch_update_ad_classification: {e}")

    async def upsert_daily_metrics(self, payload: Dict[str, Any]):
        """Salva ou atualiza métricas diárias via RPC."""
        url = f"{self.url}/rest/v1/rpc/upsert_metrica_diaria"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, headers=self.headers)
                return resp.status_code in [200, 201, 204]
            except Exception as e:
                print(f"[DB] Erro RPC metrics: {e}")
                return False

    async def persist_coordinated_network(self, payload: Dict[str, Any]):
        """Persiste rede coordenada detectada."""
        url = f"{self.url}/rest/v1/redes_coordenadas"
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=self.headers)

    async def create_active_alert(self, payload: Dict[str, Any]):
        """Cria um alerta ativo no sistema."""
        url = f"{self.url}/rest/v1/alertas_ativos"
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=self.headers)

    async def fetch_targets_needing_repericia(self) -> List[str]:
        """Busca usernames de candidatos marcados para re-perícia."""
        if not self.client: return []
        try:
            res = self.client.table('candidatos').select('username').eq('needs_re_pericia', True).execute()
            return [item['username'] for item in res.data]
        except Exception as e:
            if "column" in str(e) and "needs_re_pericia" in str(e):
                return [] # Coluna ainda não existe
            print(f"⚠️ Erro ao buscar alvos para re-perícia: {e}")
            return []

    async def reset_target_comments(self, username: str):
        """Reseta o status de processamento de todos os comentários de um alvo."""
        if not self.client: return
        print(f"[DB] Resetando comentarios para @{username}...")
        
        try:
            # Busca IDs dos comentários do alvo
            res = self.client.table('comentarios').select('id').eq('candidato_id', username).execute()
            comment_ids = [c['id'] for c in res.data]
            
            if not comment_ids:
                print(f"[DB] Nenhum comentario para @{username}.")
                return

            # Reset em blocos para performance e segurança
            batch_size = 100
            for i in range(0, len(comment_ids), batch_size):
                batch = comment_ids[i:i+batch_size]
                self.client.table('comentarios').update({
                    'processado_ia': False,
                    'categoria_ia': None,
                    'confianza_ia': 0,
                    'is_hate': False
                }).in_('id', batch).execute()
            
            print(f"[DB] {len(comment_ids)} comentarios resetados para @{username}.")
        except Exception as e:
            print(f"[DB] Erro ao resetar comentarios: {e}")

    async def mark_repericia_complete(self, username: str):
        """Desmarca o flag de re-perícia para o alvo."""
        if not self.client: return
        try:
            self.client.table('candidatos').update({'needs_re_pericia': False}).eq('username', username).execute()
        except Exception as e:
            print(f"[DB] Erro ao desmarcar re-pericia para @{username}: {e}")

    async def persist_ad(self, data: Dict[str, Any]):
        """Persiste um anúncio extraído da Meta Ad Library."""
        if not self.client: return
        try:
            # Usa upsert baseado no ad_id (id_externo no contexto Meta)
            self.client.table('anuncios').upsert(data, on_conflict='ad_id').execute()
        except Exception as e:
            print(f"[DB] Erro ao persistir anuncio {data.get('ad_id')}: {e}")

    async def persist_ads_batch(self, ads: List[Dict[str, Any]]):
        """Persiste múltiplos anúncios em lote."""
        if not self.client or not ads: return
        try:
            # Supabase permite upsert de lista
            self.client.table('anuncios').upsert(ads, on_conflict='ad_id').execute()
            print(f"[DB] {len(ads)} anuncios processados em lote.")
        except Exception as e:
            print(f"[DB] Erro ao persistir lote de anuncios: {e}")

    async def fetch_unprocessed_ads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Busca anúncios que ainda não foram processados pela IA."""
        if not self.client: return []
        try:
            res = self.client.table('anuncios').select('*').eq('processado_ia', False).limit(limit).execute()
            return res.data
        except Exception as e:
            print(f"[DB] Erro ao buscar anuncios nao processados: {e}")
            return []

    async def update_ad_classification(self, ad_id: str, data: Dict[str, Any]):
        """Atualiza a classificação de um único anúncio."""
        if not self.client: return
        try:
            self.client.table('anuncios').update(data).eq('id', ad_id).execute()
        except Exception as e:
            print(f"[DB] Erro ao atualizar anuncio {ad_id}: {e}")

    async def persist_dossier(self, data: Dict[str, Any]):
        """Persiste metadados de um dossiê gerado."""
        if not self.client: return
        try:
            res = self.client.table('dossies').insert(data).execute()
            print(f"[DB] Dossie persistido: {data.get('hash_integridade')[:10]}...")
            return res.data
        except Exception as e:
            print(f"[DB] Erro ao persistir dossie: {e}")
            return None

    # --- GOVERNANÇA DE CRÉDITOS (CI - Créditos de Inteligência) ---
    async def process_ci_transaction(self, user_id: str, amount: int, type_tx: str, description: str) -> dict:
        """
        Mapeia para a RPC process_ci_transaction no Supabase.
        Retorna o dicionário/JSON.
        """
        try:
            res = self.client.rpc('process_ci_transaction', {
                "p_user_id": user_id,
                "p_amount": amount,
                "p_type": type_tx,
                "p_description": description
            }).execute()
            return res.data
        except Exception as e:
            import logging
            logger = logging.getLogger("db")
            logger.error(f"[DB] Erro ao registrar transacao CI: {e}")
            return {'success': False, 'message': str(e)}
            
    def get_user_ci_balance(self, user_id: str) -> int:
        """Retorna o saldo atual de CI do usuário."""
        try:
            res = self.client.table('profiles').select('saldo_ci').eq('id', user_id).single().execute()
            return res.data.get('saldo_ci', 0) if res.data else 0
        except: return 0

    async def fetch_dossier_history(self, candidato_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recupera o histórico de dossiês estruturados de um candidato."""
        if not self.client: return []
        try:
            res = self.client.table('dossies')\
                .select('*')\
                .eq('candidato_id', candidato_id)\
                .order('data_geracao', ascending=False)\
                .limit(limit)\
                .execute()
            return res.data
        except Exception as e:
            print(f"[DB] Erro ao buscar historico de dossies: {e}")
            return []

    async def fetch_unmined_comments(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Busca comentários processados pela IA mas ainda não minerados."""
        if not self.client: return []
        try:
            # Tenta filtrar pela coluna 'mined' se existir, caso contrário busca processados
            res = self.client.table('comentarios').select('*').eq('processado_ia', True).eq('mined', False).limit(limit).execute()
            return res.data
        except Exception as e:
            if "column" in str(e) and "mined" in str(e):
                # Fallback se a coluna não existir ainda
                res = self.client.table('comentarios').select('*').eq('processado_ia', True).limit(limit).execute()
                return res.data
            print(f"[DB] Erro ao buscar comentarios nao minerados: {e}")
            return []

    async def fetch_unmined_ads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Busca anúncios processados pela IA mas ainda não minerados."""
        if not self.client: return []
        try:
            res = self.client.table('anuncios').select('*').eq('processado_ia', True).eq('mined', False).limit(limit).execute()
            return res.data
        except Exception as e:
            if "column" in str(e) and "mined" in str(e):
                res = self.client.table('anuncios').select('*').eq('processado_ia', True).limit(limit).execute()
                return res.data
            print(f"[DB] Erro ao buscar anuncios nao minerados: {e}")
            return []

    async def upsert_candidate(self, data: Dict[str, Any]):
        """Insere ou atualiza um candidato/alvo na base de dados."""
        if not self.client: return
        try:
            # Garante que o username está em minúsculas e limpo
            if 'username' in data:
                data['username'] = str(data['username']).lower().strip().replace('@', '')
            
            res = self.client.table('candidatos').upsert(data, on_conflict='username').execute()
            print(f"[DB] Alvo @{data.get('username')} persistido com sucesso.")
            return res.data
        except Exception as e:
            print(f"[DB] Erro ao persistir alvo: {e}")
            return None

db_client = DatabaseClient()
