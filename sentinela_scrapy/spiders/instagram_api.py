import scrapy
import json
import hashlib
from datetime import datetime
from ..items import InstagramCommentItem

class InstagramAPISpider(scrapy.Spider):
    """
    Tier 1 (Primário): Usa a API privada do Instagram via GraphQL.
    NÃO usa Playwright - apenas requisições HTTP puras.
    """
    name = 'instagram_api'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': True,
        'ITEM_PIPELINES': {
            'sentinela_scrapy.pipelines.QualityGatePipeline': 300,
        },

    }
    
    def __init__(self, username='', sessionid='', max_posts=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.sessionid = sessionid
        self.max_posts = int(max_posts)
        self.user_id = None
        
    def start_requests(self):
        """Primeira request: obtém o user_id do perfil."""
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
        
        headers = {
            'User-Agent': 'Instagram 76.0.0.15.395 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G930F; herolte; samsungexynos8890; en_US; 138226743)',
            'X-IG-App-ID': '936619743392459',
            'X-ASBD-ID': '198387',
            'X-IG-WWW-Claim': '0',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        yield scrapy.Request(
            url=url,
            headers=headers,
            cookies={'sessionid': self.sessionid},
            callback=self.parse_profile,
            errback=self.handle_error,
            meta={'tier': 1},
            dont_filter=True
        )
    
    def parse_profile(self, response):
        """Extrai user_id e lista de posts."""
        try:
            data = json.loads(response.text)
            user_data = data.get('data', {}).get('user', {})
            
            self.user_id = user_data.get('id')
            if not self.user_id:
                self.logger.error("❌ Tier 1: Falha ao obter user_id. API pode ter mudado.")
                return
            
            # Extrai posts
            posts = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])[:self.max_posts]
            
            self.logger.info(f"✅ Tier 1: Encontrados {len(posts)} posts para @{self.username}")
            
            for post in posts:
                shortcode = post.get('node', {}).get('shortcode')
                if shortcode:
                    yield from self.fetch_post_comments(shortcode)
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Tier 1: JSON inválido. Possível bloqueio ou login wall: {e}")
        except Exception as e:
            self.logger.error(f"❌ Tier 1: Erro ao parsear perfil: {e}")
    
    def fetch_post_comments(self, shortcode):
        """Busca comentários de um post via GraphQL."""
        # Query hash atual do Instagram (pode mudar!)
        query_hash = 'bc3296d1ce80a24b1b6e40b1e72903f5'
        
        variables = {
            "shortcode": shortcode,
            "first": 50,
            "after": None
        }
        
        url = f"https://www.instagram.com/graphql/query/?query_hash={query_hash}&variables={json.dumps(variables)}"
        
        headers = {
            'User-Agent': 'Instagram 76.0.0.15.395 Android',
            'X-IG-App-ID': '936619743392459',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        yield scrapy.Request(
            url=url,
            headers=headers,
            cookies={'sessionid': self.sessionid},
            callback=self.parse_comments,
            errback=self.handle_error,
            meta={'shortcode': shortcode, 'tier': 1},
            dont_filter=True
        )
    
    def parse_comments(self, response):
        """Processa comentários do GraphQL."""
        shortcode = response.meta['shortcode']
        
        try:
            data = json.loads(response.text)
            edges = data.get('data', {}).get('shortcode_media', {}).get('edge_media_to_parent_comment', {}).get('edges', [])
            
            self.logger.info(f"✅ Tier 1: Extraindo {len(edges)} comentários do post {shortcode}")
            
            for edge in edges:
                node = edge.get('node', {})
                
                yield InstagramCommentItem(
                    comment_id=node.get('id'),
                    post_shortcode=shortcode,
                    ownerUsername=node.get('owner', {}).get('username'),
                    text=node.get('text', ''),
                    created_at=datetime.fromtimestamp(node.get('created_at', 0)).isoformat() if node.get('created_at') else None,
                    like_count=node.get('edge_liked_by', {}).get('count', 0),
                    candidato_id=self.username,
                    tier_used=1
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Tier 1: Erro ao parsear JSON do post {shortcode}: {e}")
        except Exception as e:
            self.logger.error(f"❌ Tier 1: Erro ao processar comentários: {e}")
    
    def handle_error(self, failure):
        """Log de erros com contexto de tier."""
        tier = failure.request.meta.get('tier', 1)
        self.logger.error(f"❌ Tier {tier}: Requisição falhou - {failure.value}")
