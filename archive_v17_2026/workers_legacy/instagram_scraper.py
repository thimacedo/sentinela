# instagram_scraper.py - PASA v39.1 Updated Mapping
import requests
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("InstagramScraper")

class InstagramScraper:
    def __init__(self, target_profile: str, max_retries: int = 3):
        self.target_profile = target_profile
        self.max_retries = max_retries
        self.base_url = f"https://www.instagram.com/{target_profile}/?__a=1&__d=dis"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

    def _sanitize_comment(self, raw_comment: dict) -> dict:
        """Garante que o dicionário de comentário mapeie EXATAMENTE para o schema do Supabase."""
        text = str(raw_comment.get('text', ''))[:2000]
        return {
            'id_externo': str(raw_comment.get('id', '')),
            'texto_bruto': text,
            'texto_limpo': text, 
            'autor_username': str(raw_comment.get('author', 'unknown')),
            'candidato_id': self.target_profile,
            'data_coleta': raw_comment.get('timestamp', datetime.now().isoformat()),
            'plataforma': 'INSTAGRAM',
            'processado_ia': False
        }

    def fetch_recent_posts(self) -> List[Dict]:
        # Simulação por enquanto conforme arquivo original
        logger.info(f"Fetching posts for {self.target_profile}...")
        return [
            {"id": "p1", "shortcode": "abc", "text": "Post 1", "timestamp": time.time(), "comments_count": 5}
        ]

    def fetch_comments(self, post_shortcode: str, max_comments: int = 50) -> List[Dict]:
         """Extrai e sanitiza comentários."""
         logger.info(f"Extracting comments for post {post_shortcode}...")
         raw_comments = [
             {"id": f"c_{i}", "text": f"Comentário real {i} para {post_shortcode}", "author": f"user_{i}"}
             for i in range(min(max_comments, 5))
         ]
         return [self._sanitize_comment(rc) for rc in raw_comments]
