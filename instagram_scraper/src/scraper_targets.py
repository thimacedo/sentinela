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
import undetected_chromedriver as uc
from dotenv import load_dotenv

load_dotenv()

class InstagramTargetScraper:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self.load_config(config_path)
        self.driver = None
        self.wait = None
        self.session_file = self.config.get("session_file", "data/session.pkl")
        self.logged_in = False
        self.all_comments = []  # list of dicts with target info

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
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        if self.config.get("use_proxy") and self.config.get("proxy"):
            options.add_argument(f'--proxy-server={self.config["proxy"]}')
        self.driver = uc.Chrome(options=options, version_main=None)
        self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
        self.wait = WebDriverWait(self.driver, self.config.get("element_wait_timeout", 10))
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def random_delay(self, min_sec: float = None, max_sec: float = None):
        if min_sec is None:
            min_sec = self.config.get("min_delay", 2)
        if max_sec is None:
            max_sec = self.config.get("max_delay", 5)
        time.sleep(random.uniform(min_sec, max_sec))

    def login(self):
        if self.load_session():
            try:
                self.driver.get("https://www.instagram.com/")
                self.random_delay(2, 4)
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::a")))
                self.logged_in = True
                print("Loaded session and verified login.")
                return
            except (TimeoutException, WebDriverException):
                print("Saved session expired or invalid. Logging in again.")
        if not self.config.get("username") or not self.config.get("password"):
            raise ValueError("Username and password must be provided in config or environment variables.")
        print("Logging into Instagram...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        self.random_delay(3, 5)
        username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
        username_input.clear()
        for char in self.config["username"]:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        self.random_delay(0.5, 1.5)
        password_input.clear()
        for char in self.config["password"]:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
        self.random_delay(0.5, 1.5)
        login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
        login_button.click()
        self.random_delay(5, 8)
        try:
            not_now_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")))
            not_now_button.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass
        try:
            not_now_button2 = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")))
            not_now_button2.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::a")))
            self.logged_in = True
            print("Login successful!")
            self.save_session()
        except TimeoutException:
            raise Exception("Login failed - check credentials or if additional verification is required.")

    def save_session(self):
        if self.driver:
            import pickle
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'wb') as f:
                pickle.dump(cookies, f)
            print(f"Session saved to {self.session_file}")

    def load_session(self) -> bool:
        if os.path.exists(self.session_file):
            try:
                import pickle
                with open(self.session_file, 'rb') as f:
                    cookies = pickle.load(f)
                if not self.driver:
                    self.init_driver()
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
        """Get URLs of recent posts for a given username posts."""
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
                    username_elem = elem.find_element(By.XPATH, ".//span[contains(@class, '_aacl')]//a | .//a[contains(@href, '/')]//span")
                    username = username_elem.text
                except NoSuchElementException:
                    username = f"user_{i}"
                # text
                try:
                    text_elem = elem.find_element(By.XPATH, ".//span[contains(@class, '_aacl')]//following-sibling::span | .//div[contains(@class, '_a9zs')]//span")
                    text = text_elem.text
                except NoSuchElementException:
                    text = ""
                # timestamp
                try:
                    time_elem = elem.find_element(By.TAG_NAME, "time")
                    timestamp = time_elem.get_attribute("datetime")
                except NoSuchElementException:
                    timestamp = None
                # likes
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

    def process_targets(self, csv_path: str, max_targets: int = None, posts_per_target: int = 2):
        """Read CSV of targets and scrape comments from their recent posts."""
        # Read CSV with pipe delimiter as seen in file
        df = pd.read_csv(csv_path, sep='|', skiprows=1)  # skip first row which seems header description
        # The CSV columns: id;nome_completo;cargo;username;status_monitoramento;sexo
        # Actually after skipping first row, we need to set column names
        # Let's read with header=None and assign
        df = pd.read_csv(csv_path, sep='|', header=None, skiprows=1)
        df.columns = ['id', 'nome_completo', 'cargo', 'username', 'status_monitoramento', 'sexo']
        # Clean usernames
        usernames = df['username'].dropna().astype(str).str.strip()
        usernames = usernames[usernames != '']
        if max_targets:
            usernames = usernames.head(max_targets)
        print(f"Processing {len(usernames)} targets...")
        for idx, username in enumerate(usernames, start=1):
            print(f"\n[{idx}/{len(usernames)}] Processing @{username}")
            try:
                if not self.driver:
                    self.init_driver()
                if not self.logged_in:
                    self.login()
                post_urls = self.get_user_recent_posts(username, limit=posts_per_target)
                if not post_urls:
                    print(f"  No posts found for @{username}")
                    continue
                for post_url in post_urls:
                    comments = self.scrape_comments_from_post(post_url)
                    for comment in comments:
                        comment['target_username'] = username
                        comment['target_name'] = df.loc[df['username'] == username, 'nome_completo'].iloc[0] if not df.loc[df['username'] == username, 'nome_completo'].empty else ''
                        comment['post_url'] = post_url
                    self.all_comments.extend(comments)
                    print(f"  Collected {len(comments)} comments from {post_url}")
                self.random_delay(5, 8)  # pause between targets
            except Exception as e:
                print(f"  Error processing @{username}: {e}")
                continue
        print(f"\nTotal comments collected: {len(self.all_comments)}")

    def save_results(self, output_prefix: str = "data/targets_comments"):
        """Save all collected comments to JSON and CSV."""
        output_path = Path(output_prefix)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.all_comments:
            print("No comments to save.")
            return
        json_file = output_path.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_comments, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.all_comments)} comments to {json_file}")
        csv_file = output_path.with_suffix('.csv')
        if self.all_comments:
            df = pd.DataFrame(self.all_comments)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"Saved {len(self.all_comments)} comments to {csv_file}")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            print("Browser closed.")

def main():
    parser = argparse.ArgumentParser(description="Scrape comments from Instagram targets listed in CSV.")
    parser.add_argument("--csv", default="../../alvos_sanitizacao.csv", help="Path to targets CSV (relative to script)")
    parser.add_argument("--output", default="data/targets_comments", help="Output file prefix (without extension)")
    parser.add_argument("--max-targets", type=int, default=5, help="Maximum number of targets to process (for testing)")
    parser.add_argument("--posts-per-target", type=int, default=2, help="Number of recent posts to scan per target")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    # Resolve CSV path relative to script location
    script_dir = Path(__file__).parent
    csv_path = (script_dir / args.csv).resolve()
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)

    scraper = InstagramTargetScraper()
    if args.headless:
        scraper.config["headless"] = True
    try:
        scraper.process_targets(str(csv_path), max_targets=args.max_targets, posts_per_target=args.posts_per_target)
        scraper.save_results(args.output)
    except Exception as e:
        print(f"Error during scraping: {e}")
        return 1
    finally:
        scraper.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())