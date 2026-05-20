import os
import time
import instaloader
import random
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, UTC
from core.base_scraper import SentinelaScraper

load_dotenv()

# Inicializa Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class InstagramFortress(SentinelaScraper):
    def __init__(self):
        super().__init__("InstagramFortress")
        self.L = instaloader.Instaloader(
            download_videos=False, 
            download_pictures=False, 
            save_metadata=False,
            max_connection_attempts=3,
            request_timeout=30
        )
        self.session_file = "sentinela_ig_session"
        
    def login(self):
        """Faz login seguro e salva a sessão local para não precisar repetir."""
        ig_user = os.getenv("IG_USER")
        ig_pass = os.getenv("IG_PASS")
        
        if not ig_user:
            self.logger.error("Configure IG_USER e IG_PASS no .env")
            return False

        try:
            self.L.load_session_from_file(username=ig_user, filename=self.session_file)
            self.logger.info(f"Sessão local para @{ig_user} carregada.")
        except FileNotFoundError:
            self.logger.info(f"Primeiro login com a conta burner @{ig_user}...")
            
            if not ig_pass:
                self.logger.error("Senha IG_PASS não encontrada no .env")
                return False
                
            try:
                self.L.login(ig_user, ig_pass)
                self.L.save_session_to_file(filename=self.session_file)
                self.logger.info("Login realizado e sessão salva localmente!")
            except instaloader.exceptions.TwoFactorAuthRequiredException:
                self.logger.error("O Instagram pediu código 2FA. Rode manualmente.")
                return False
            except Exception as e:
                self.logger.error(f"Falha no login: {e}")
                return False
                
        return True

    def scrape(self, username: str):
        """Implementação do scraping de comentários para um alvo específico."""
        if not self.login():
            return
            
        self.logger.info(f"Iniciando extração para: @{username}")
        
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            
            # Atualiza dados do perfil
            supabase.table('candidatos').update({
                'seguidores': profile.followers,
                'last_scraped_at': datetime.now(UTC).isoformat()
            }).eq('username', username).execute()
            
            # Pega os últimos 3 posts
            post_counter = 0
            for post in profile.get_posts():
                if post_counter >= 3:
                    break
                    
                comment_counter = 0
                try:
                    for comment in post.get_comments():
                        if comment_counter >= 50:
                            break
                            
                        comment_data = {
                            'candidato_id': username,
                            'post_id': post.shortcode,
                            'autor_username': comment.owner.username,
                            'texto_bruto': comment.text,
                            'plataforma': 'INSTAGRAM',
                            'data_coleta': datetime.now(UTC).isoformat(),
                            'processado_ia': False,
                            'id_externo': f"ig_{comment.id}"
                        }
                        
                        try:
                            supabase.table('comentarios').insert(comment_data).execute()
                            comment_counter += 1
                        except Exception:
                            pass
                            
                    self.logger.info(f"Post {post.shortcode}: {comment_counter} comentários salvos.")
                    post_counter += 1
                except Exception as e:
                    self.logger.warning(f"Erro nos comentários do post {post.shortcode}: {e}")
                    
                self._human_pause(20, 60)
                
            self._human_pause(60, 180)
            
        except instaloader.exceptions.LoginRequiredException:
            self.logger.error("Sessão expirada. Delete o arquivo 'sentinela_ig_session' e rode novamente.")
        except instaloader.exceptions.ProfileNotExistsException:
            self.logger.warning(f"Perfil @{username} não existe ou é privado.")
        except Exception as e:
            self.logger.error(f"Erro em @{username}: {e}")

if __name__ == "__main__":
    scraper = InstagramFortress()
    # Exemplo de chamada simplificada
    target = os.getenv("IG_TARGET", "exemplo_perfil")
    scraper.scrape(target)
