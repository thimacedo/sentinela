import os
import unicodedata
from typing import List, Dict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class TargetNormalizer:
    """Normaliza nomes genéricos de alvos para usernames do Instagram."""
    
    # Mapeamento manual para alvos críticos que frequentemente causam ambiguidade
    FALLBACK_MAP = {
        "lula": "lulaoficial",
        "bolsonaro": "jairmessiasbolsonaro",
        "tarcisio": "tarcisiogdf",
        "haddad": "fernandohaddadoficial",
        "janja": "janjalula",
        "dino": "flaviodino",
        "moraes": "alexandre",
        "nicolas": "nikolasferreiradm"
    }
    
    def __init__(self):
        self.client: Client = self._init_client()
        self._cache: Dict[str, str] = self.FALLBACK_MAP.copy()
        self._loaded = False

    def _init_client(self) -> Client:
        url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        return create_client(url, key) if url and key else None

    def _clean(self, text: str) -> str:
        if not text or str(text).lower() == 'none': return ""
        # Remove acentos e converte para minúsculas
        nfkc_form = unicodedata.normalize('NFKD', str(text))
        return "".join([c for c in nfkc_form if not unicodedata.combining(c)]).lower().strip()

    def _load(self):
        if not self.client or self._loaded: return

        try:
            # Prioriza perfis com mais seguidores e status ATIVO
            resp = self.client.table('candidatos') \
                .select('username, nome_completo, seguidores, status_monitoramento') \
                .order('seguidores', desc=True).execute()
            
            # Lista de handles genéricos protegidos (nunca devem ser usados como alvo automático por nome parcial)
            PROTECTED_HANDLES = ["alexandre", "joao", "maria", "paulo"]

            for item in resp.data:
                user = self._clean(item.get('username'))
                nome = self._clean(item.get('nome_completo'))
                if not user or len(user) <= 2: continue
                if user in PROTECTED_HANDLES: continue

                # Mapeia o próprio username
                self._cache.setdefault(user, user)
                
                # Mapeia partes do nome completo para o username mais popular
                if nome and len(nome) > 3:
                    self._cache.setdefault(nome, user)
                    for p in nome.split():
                        if len(p) > 3: 
                            # Evita que nomes muito comuns sobrescrevam o fallback manual
                            if p not in self.FALLBACK_MAP:
                                self._cache.setdefault(p, user)
            
            self._loaded = True
            print(f"✅ [Normalizer] {len(self._cache)} perfis mapeados (incluindo fallbacks).")
        except Exception as e:
            print(f"❌ [Normalizer] Falha no carregamento: {e}")

    def normalize(self, target: str) -> str:
        if not target: return ""
        self._load()
        
        # 1. Limpeza básica
        clean_target = self._clean(target).replace("@", "")
        
        # 2. Busca no cache (inclui fallback map e dados do banco)
        normalized = self._cache.get(clean_target)
        
        # 3. Se não achar, tenta busca parcial ou retorna o original limpo
        if not normalized:
            normalized = clean_target

        if normalized != clean_target:
            print(f"🔄 [Normalizer] '{target}' -> @{normalized}")
        return normalized

    def normalize_list(self, targets: List[str]) -> List[str]:
        return list(dict.fromkeys(self.normalize(t) for t in targets if t))

target_normalizer = TargetNormalizer()
