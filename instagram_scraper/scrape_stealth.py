import os
import sys
import json
import time
import random
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

class StealthEngine:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self.load_config(config_path)
        self.driver = None
        self.wait = None
        self.session_file = self.config.get("session_file", "data/session.pkl")
        self.logged_in = False

    def load_config(self, config_path: str) -> dict:
        default_config = {
            "username": os.getenv("IG_USER", ""),
            "password": os.getenv("IG_PASS", ""),
            "session_file": "data/session.pkl",
            "min_delay": 2,
            "max_delay": 5,
            "headless": False,
            "use_proxy": False,
            "proxy": "",
            "page_load_timeout": 30,
            "element_wait_timeout": 10
        }
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        return default_config

    def init_driver(self):
        options = webdriver.ChromeOptions()
        if self.config.get("headless", False):
            # Hack: O binário Chromium v149 patched do usuário sofre crash fatal (GetHandleVerifier)
            # ao tentar rodar em qualquer modo headless (--headless ou --headless=new).
            # Solução: Rodar no modo GUI nativo, mas mover a janela para fora da tela invisível.
            options.add_argument("--window-position=-32000,-32000")
            options.add_argument("--window-size=1920,1080")
        
        # Stealth settings integradas do scrape_working.py
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.197 Safari/537.36")
        
        if self.config.get("use_proxy") and self.config.get("proxy"):
            options.add_argument(f'--proxy-server={self.config["proxy"]}')
        
        # Configuração do Service com fix pythonw.exe + webdriver-manager específico (v149)
        import subprocess
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Garante que o diretório de logs existe
        os.makedirs("logs", exist_ok=True)
        log_path = os.path.abspath("logs/chromedriver_stealth.log")
        
        os.environ['WDM_CACHE_VALID_RANGE'] = '1'
        try:
            driver_path = ChromeDriverManager().install()
            service = ChromeService(driver_path, log_output=log_path)
        except Exception as e:
            print(f"Failed to get driver via WDM: {e}")
            service = ChromeService(ChromeDriverManager().install(), log_output=log_path)
            
        # Não usar CREATE_NO_WINDOW porque binários patched crasham se não tiverem handles válidos
        # O log_output cria file handles reais, o que impede o crash do GetHandleVerifier no pythonw.exe
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
        self.wait = WebDriverWait(self.driver, self.config.get("element_wait_timeout", 10))
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def random_delay(self, min_sec: float = None, max_sec: float = None):
        if min_sec is None:
            min_sec = self.config.get("min_delay", 2)
        if max_sec is None:
            max_sec = self.config.get("max_delay", 5)
        time.sleep(random.uniform(min_sec, max_sec))

    def get_available_accounts(self) -> List[Dict[str, str]]:
        accounts = []
        if os.getenv("IG_USER") and os.getenv("IG_PASS"):
            accounts.append({"username": os.getenv("IG_USER"), "password": os.getenv("IG_PASS")})
        for i in range(1, 11):
            user = os.getenv(f"IG_USER_{i}")
            pwd = os.getenv(f"IG_PASS_{i}")
            if user and pwd:
                accounts.append({"username": user, "password": pwd})
        return accounts

    def login(self):
        accounts = self.get_available_accounts()
        if not accounts:
            if not self.config.get("username") or not self.config.get("password"):
                raise ValueError("Nenhuma conta do Instagram configurada no .env (IG_USER ou IG_USER_1).")
            accounts = [{"username": self.config.get("username"), "password": self.config.get("password")}]

        for idx, account in enumerate(accounts):
            username = account["username"]
            password = account["password"]
            print(f"\n[LOGIN] Tentando login com a conta [{idx+1}/{len(accounts)}]: {username}")

            self.config["username"] = username
            self.config["password"] = password
            self.session_file = f"data/session_{username}.pkl"

            # Tenta reaproveitar sessão existente
            if self.load_session():
                try:
                    self.driver.get("https://www.instagram.com/")
                    self.random_delay(2, 4)
                    self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/explore/')]")))
                    self.logged_in = True
                    print(f"[OK] Sessão carregada e validada para {username}.")
                    return
                except (TimeoutException, WebDriverException):
                    print(f"[AVISO] Sessão expirada para {username}. Tentando login do zero.")

            # Login do zero
            try:
                if not self.driver:
                    self.init_driver()
                self.driver.get("https://www.instagram.com/accounts/login/")
                self.random_delay(3, 5)

                username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
                password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))

                username_input.clear()
                for char in username:
                    username_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2))
                self.random_delay(0.5, 1.5)

                password_input.clear()
                for char in password:
                    password_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.2))
                self.random_delay(0.5, 1.5)

                login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
                login_button.click()
                self.random_delay(5, 8)

                # Tratamento de Popups
                try:
                    not_now = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Agora não')]")), message="Not Now 1")
                    not_now.click()
                    self.random_delay(2, 3)
                except TimeoutException:
                    pass
                try:
                    not_now2 = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now') or contains(text(), 'Agora não')]")), message="Not Now 2")
                    not_now2.click()
                    self.random_delay(2, 3)
                except TimeoutException:
                    pass

                self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/explore/')]")), message="Login verification failed")
                self.logged_in = True
                print(f"[OK] Login manual com {username} efetuado com sucesso!")
                self.save_session()
                return

            except Exception as e:
                print(f"[ERRO] Falha ao logar com {username}: {e}")
                # Reiniciar driver caso tenha crashado, para tentar a próxima conta num browser limpo
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None

        raise Exception("Nenhuma das contas Instagram configuradas no .env obteve sucesso de login.")

    def save_session(self):
        """Save current session cookies to file."""
        if self.driver:
            import pickle
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'wb') as f:
                pickle.dump(cookies, f)
            print(f"Session saved to {self.session_file}")

    def load_session(self) -> bool:
        """Load session from file if exists and is valid."""
        if os.path.exists(self.session_file):
            try:
                import pickle
                with open(self.session_file, 'rb') as f:
                    cookies = pickle.load(f)
                # Initialize driver if not already done
                if not self.driver:
                    self.init_driver()
                # Go to domain to set cookies
                self.driver.get("https://www.instagram.com")
                for cookie in cookies:
                    if 'sameSite' in cookie:
                        del cookie['sameSite']
                    self.driver.add_cookie(cookie)
                print(f"Loaded session from {self.session_file}")
                return True
            except Exception as e:
                print(f"Failed to load session: {e}")
                return False
        return False

    def get_user_profile_url(self, username: str) -> str:
        return f"https://www.instagram.com/{username}/"

    def get_user_recent_posts(self, username: str, limit: int = 3) -> List[str]:
        """Get URLs of recent posts for a given username."""
        profile_url = self.get_user_profile_url(username)
        print(f"Fetching profile for {username}...")
        self.driver.get(profile_url)
        self.random_delay(3, 5)
        # Wait for posts to load
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_aagv')]")))
        except TimeoutException:
            print(f"Timeout waiting for posts for {username}")
            return []
        # Find post links: each post is an <a> with href containing /p/
        post_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
        post_urls = []
        seen = set()
        for elem in post_elements:
            href = elem.get_attribute('href')
            if href and '/p/' in href and href not in seen:
                seen.add(href)
                post_urls.append(href)
                if len(post_urls) >= limit:
                    break
        print(f"Found {len(post_urls)} recent posts for {username}")
        return post_urls

    def scrape_comments_from_post(self, post_url: str) -> List[Dict]:
        """Navigate to post and scrape comments."""
        print(f"  Scraping comments from {post_url}")
        self.driver.get(post_url)
        self.random_delay(3, 5)
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//article")))
        except TimeoutException:
            print(f"    Post did not load properly.")
            return []
        # Load more comments by scrolling
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 10
        while scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay(2, 4)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                try:
                    load_more = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Load more comments') or contains(text(), 'Ver mais comentários')]")
                    if load_more.is_displayed():
                        load_more.click()
                        self.random_delay(2, 3)
                        continue
                except NoSuchElementException:
                    break
            else:
                last_height = new_height
                scroll_count += 1
        # Extract comments
        comments = []
        comment_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, '_a9zs')]")
        if not comment_elements:
            comment_elements = self.driver.find_elements(By.XPATH, "//ul//li//div[contains(@class, '_a9zs')]")
        if not comment_elements:
            comment_elements = self.driver.find_elements(By.XPATH, "//div[@role='button' and contains(@tabindex, '0')]//..//following-sibling::div")
        print(f"    Found {len(comment_elements)} comment elements")
        for i, elem in enumerate(comment_elements):
            try:
                # username
                try:
                    username_elem = elem.find_element(By.XPATH, ".//a[contains(@href, '/')]//span | .//span[contains(@class, '_aacl')]//a")
                    username = username_elem.text
                except NoSuchElementException:
                    username = f"user_{i}"
                # text
                try:
                    text_elem = elem.find_element(By.XPATH, ".//span[@dir='auto'] | .//span[contains(@class, '_aacl')]//following-sibling::span | .//div[contains(@class, '_a9zs')]//span")
                    text = text_elem.text
                except NoSuchElementException:
                    text = ""
                # timestamp
                try:
                    time_elem = elem.find_element(By.TAG_NAME, "time")
                    timestamp = time_elem.get_attribute("datetime")
                except NoSuchElementException:
                    timestamp = None
                # likes count (if visible)
                try:
                    likes_elem = elem.find_element(By.XPATH, ".//span[contains(@class, '_aacl')]//following-sibling::span[contains(text(), 'like') or contains(text(), 'curtida')]//preceding-sibling::span")
                    likes_text = likes_elem.text
                    import re
                    likes_match = re.search(r'[\d,]+', likes_text)
                    likes = int(likes_match.group().replace(',', '')) if likes_match else 0
                except NoSuchElementException:
                    likes = 0
                comments.append({
                    "id": f"comment_{i}_{int(time.time())}",
                    "username": username,
                    "text": text,
                    "timestamp": timestamp,
                    "likes": likes,
                    "scraped_at": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"    Error extracting comment {i}: {e}")
                continue
        return comments

    def scrape_targets(self, target_usernames: List[str], posts_per_target: int = 1) -> List[Dict]:
        """Scrape recent posts for a list of target usernames."""
        all_results = []
        for username in target_usernames:
            print(f"\n=== Processing target: {username} ===")
            try:
                post_urls = self.get_user_recent_posts(username, limit=posts_per_target)
                if not post_urls:
                    print(f"No posts found for {username}")
                    continue
                for post_url in post_urls:
                    comments = self.scrape_comments_from_post(post_url)
                    for comment in comments:
                        comment["target_username"] = username
                        comment["post_url"] = post_url
                    all_results.extend(comments)
                    print(f"  Collected {len(comments)} comments from {post_url}")
                # Delay between targets to avoid rate limiting
                self.random_delay(5, 10)
            except Exception as e:
                print(f"Error processing {username}: {e}")
                continue
        return all_results

    def save_results(self, comments: List[Dict], output_file: str = None):
        """Save comments to JSON and CSV formats."""
        if not comments:
            print("No comments to save.")
            return
        output_path = Path(output_file) if output_file else Path("data/comments")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as JSON
        json_file = output_path.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(comments)} comments to {json_file}")
        # Save as CSV
        csv_file = output_path.with_suffix('.csv')
        if comments:
            df = pd.DataFrame(comments)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"Saved {len(comments)} comments to {csv_file}")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            print("Browser closed.")
