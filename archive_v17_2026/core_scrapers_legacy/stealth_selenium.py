import os, time, hashlib
import undetected_chromedriver as uc
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
supa = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
CHROME_PROFILE = r"C:\Users\THIAGO\AppData\Local\Google\Chrome\User Data"

class StealthSelenium:
    def __init__(self):
        print("🚀 Iniciando Undetected Chromedriver...")
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        opts = uc.ChromeOptions()
        opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = uc.Chrome(options=opts, browser_executable_path=chrome_exe)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"❌ Falha ao iniciar UC: {e}")
            raise e

    def login(self):
        self.driver.get("https://www.instagram.com/")
        time.sleep(5)
        if "login" in self.driver.current_url:
            print("🔑 O Instagram solicitou login. Por favor, realize o login manualmente no navegador.")
            print("💡 Dica: Resolva o 2FA se necessário.")
            input("✅ Pressione ENTER aqui quando estiver na tela inicial do Instagram...")
        else:
            print("✅ Sessão do Chrome ativa e logada.")

    def scrape(self, limit=15):
        self.login()
        # Busca candidatos que NUNCA foram raspados
        res = supa.table('candidatos').select('id, username, nome_completo').is_('last_scraped_at', 'null').limit(limit).execute()
        targets = res.data
        if not targets:
            print("✅ Nenhum candidato pendente de raspagem inicial.")
            return

        for t in targets:
            uname = t['username']
            cid = t['id']
            print(f"\n🔍 Analisando @{uname} ({t.get('nome_completo', '')})")
            try:
                self.driver.get(f"https://www.instagram.com/{uname}/")
                time.sleep(5)
                
                # Marcar como raspado imediatamente para evitar loop em caso de erro no meio
                supa.table('candidatos').update({'last_scraped_at': datetime.utcnow().isoformat()}).eq('id', cid).execute()
                
                # Localizar links de posts ou reels
                posts = self.driver.find_elements("xpath", '//article//a[contains(@href, "/p/") or contains(@href, "/reel/")]')
                
                if not posts:
                    print(f"⚠️ Nenhum post encontrado para @{uname}")
                    continue

                for p in posts[:3]: # Analisa os 3 últimos posts
                    try:
                        href = p.get_attribute("href")
                        p.click()
                        time.sleep(4)
                        
                        current_url = self.driver.current_url
                        if "/p/" in current_url:
                            shortcode = current_url.split("/p/")[1].split("/")[0]
                        elif "/reel/" in current_url:
                            shortcode = current_url.split("/reel/")[1].split("/")[0]
                        else:
                            shortcode = f"unknown_{hashlib.md5(href.encode()).hexdigest()[:8]}"

                        print(f"  📸 Post: {shortcode}")
                        
                        # Extrai textos visíveis (comentários)
                        # XPaths atualizados para a estrutura atual da modal do IG
                        elements = self.driver.find_elements("xpath", '//div[contains(@class, "x9f619")]//span[@dir="auto"]')
                        
                        # Filtra textos que pareçam ser comentários (tamanho mínimo)
                        texts = [el.text for el in elements if el.text and len(el.text) > 10]
                        # Remove duplicatas e pega os últimos/principais
                        unique_texts = list(dict.fromkeys(texts))[-20:]
                        
                        for txt in unique_texts:
                            # Gerar um ID único estável baseado no texto e usuário
                            txt_hash = hashlib.md5(f"{uname}_{txt}".encode()).hexdigest()[:12]
                            data = {
                                "id_externo": f"sel_{txt_hash}",
                                "candidato_id": uname,
                                "post_id": shortcode,
                                "autor_username": "selenium_user",
                                "texto_bruto": txt,
                                "plataforma": "INSTAGRAM",
                                "data_coleta": datetime.utcnow().isoformat(),
                                "processado_ia": False
                            }
                            try:
                                supa.table('comentarios').upsert(data, on_conflict='id_externo').execute()
                            except Exception as e:
                                pass # Provavelmente duplicado
                        
                        # Fechar a modal (ESC)
                        self.driver.find_element("tag name", "body").send_keys(u'\ue00c')
                        time.sleep(2)
                    except Exception as post_err:
                        print(f"  ❌ Erro no post: {post_err}")
                        self.driver.execute_script("window.history.go(-1)") # Tenta voltar se travar
                        time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Erro geral em @{uname}: {e}")

        print("\n🏁 Sessão de raspagem finalizada.")

if __name__ == "__main__":
    bot = StealthSelenium()
    try:
        bot.scrape(limit=15)
    finally:
        bot.driver.quit()
