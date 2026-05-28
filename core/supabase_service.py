"""
Serviço de conexão centralizado com o Supabase.
PASA v48.2: Adaptado para usar ANON_KEY se SERVICE_KEY não estiver presente.
"""
import os
from dotenv import load_dotenv

# Garante que as variáveis do .env sejam carregadas antes de qualquer coisa
load_dotenv()

from supabase import create_client, Client
from core.circuit_breaker import db_circuit_breaker

class SupabaseService:
    """
    Serviço centralizado de conexão com o Supabase (Singleton com Lazy Loading).
    Garante que o client só seja criado quando necessário, evitando crashes no Pytest.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._client = None
        return cls._instance

    def get_client(self) -> Client:
        """Retorna o cliente Supabase. Conecta apenas na primeira chamada."""
        if self._client is None:
            url = os.getenv("SUPABASE_URL")
            # Ordem de preferência: SERVICE_KEY (bypass RLS) -> KEY -> ANON_KEY
            key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

            if not url or not key:
                extra_info = ""
                if os.getenv("GITHUB_ACTIONS"):
                    extra_info = " (Ambiente GitHub Actions detectado: certifique-se de cadastrar SUPABASE_URL e SUPABASE_SERVICE_KEY nos Repository Secrets do repositório)"
                raise ValueError(f"[ERROR] SUPABASE_URL ou SUPABASE_KEY não encontradas no .env ou variáveis de ambiente{extra_info}")

            self._client = create_client(url, key)
            print("[OK] Conexão com Supabase estabelecida (PASA v48.2 REST).")
        return self._client

# Função de conveniência para não precisar instanciar a classe em todo lugar
def get_supabase_client() -> Client:
    return SupabaseService().get_client()

# Singleton para uso simplificado
supabase = get_supabase_client()

def save_alerts(alerts_data: list):
    """Insere ou atualiza uma lista de alertas no Supabase."""
    try:
        supabase_client = get_supabase_client()
        supabase_client.table('threat_alerts').upsert(
            alerts_data,
            on_conflict="id"
        ).execute()
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar no Supabase: {e}")
        return False

def get_next_targets_to_scrape(limit: int = 5) -> list:
    """Busca os alvos mais prioritários e que não foram raspados recentemente."""
    if not db_circuit_breaker.can_execute("supabase"):
        return []
    try:
        supabase_client = get_supabase_client()
        response = supabase_client.table('candidatos') \
            .select('username, prioridade_coleta') \
            .ilike('status_monitoramento', 'ATIVO') \
            .order('prioridade_coleta', desc=True) \
            .order('last_scraped_at', desc=False) \
            .limit(limit) \
            .execute()

        db_circuit_breaker.record_success("supabase")
        return response.data
    except Exception as e:
        print(f"❌ Erro ao buscar alvos no banco: {e}")
        db_circuit_breaker.record_failure("supabase")
        return []

def update_last_scraped_at(username: str):
    """Atualiza o timestamp de raspagem para esfriar o alvo na fila."""
    try:
        supabase_client = get_supabase_client()
        supabase_client.table('candidatos') \
            .update({'last_scraped_at': 'NOW()'}) \
            .eq('username', username) \
            .execute()
    except Exception as e:
        print(f"❌ Erro ao atualizar last_scraped_at para @{username}: {e}")

def save_comments(comments_data: list):
    """Insere ou atualiza comentários extraídos na tabela 'comentarios'."""
    if not db_circuit_breaker.can_execute("supabase"):
        return False
    try:
        supabase_client = get_supabase_client()
        supabase_client.table('comentarios').upsert(
            comments_data,
            on_conflict="id_externo"
        ).execute()
        db_circuit_breaker.record_success("supabase")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar comentários no Supabase: {e}")
        db_circuit_breaker.record_failure("supabase")
        return False

def save_scrape_error(username: str, error_type: str):
    """Registra uma falha de raspagem para análise de resiliência."""
    try:
        print(f"⚠️ Registrando erro {error_type} para @{username}")
    except Exception as e:
        print(f"❌ Erro ao registrar falha para @{username}: {e}")
