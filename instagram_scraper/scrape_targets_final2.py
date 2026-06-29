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
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dotenv import load_dotenv

load_dotenv()

class TargetScraper:
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
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        # Only essential options to avoid detection; let undetected-chromedriver handle the rest
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Note: Do NOT add experimental options that undetected-chromedriver doesn't accept
        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
        self.wait = WebDriverWait(self.driver, self.config.get("element_wait_timeout", 10))
        # Additional stealth: remove webdriver property
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
        # Wait for username field
        username_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_input = self.wait.until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        # Type credentials with human-like delays
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
        # Click login button
        login_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        self.random_delay(5, 8)
        # Handle "Save Login Info?" popup if appears
        try:
            not_now_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")),
                message="Not Now button not found"
            )
            not_now_button.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass  # Popup didn't appear
        # Handle "Turn on Notifications?" popup
        try:
            not_now_button2 = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")),
                message="Second Not Now button not found"
            )
            not_now_button2.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass
        # Verify login successful
        try:
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::a")),
                message="Login verification failed"
            )
            self.logged_in = True
            print("Login successful!")
            self.save_session()
        except TimeoutException:
            raise Exception("Login failed - check credentials or if additional verification is required.")

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

def main():
    # Read targets from CSV
    csv_path = r"C:\Projetos\sentinela\alvos_sanitizacao.csv"
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    usernames = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            username = row.get('username', '').strip()
            if username:
                usernames.append(username)
    print(f"Loaded {len(usernames)} usernames from CSV.")
    # Limit to first 2 for testing
    usernames = usernames[:2]
    print(f"Will process first {len(usernames)} usernames: {usernames}")
    # Initialize scraper
    scraper = TargetScraper()
    try:
        scraper.init_driver()
        scraper.login()
        # Scrape targets
        comments = scraper.scrape_targets(usernames, posts_per_target=1)
        # Save results
        output_file = "data/target_comments"
        scraper.save_results(comments, output_file)
        print(f"\nTotal comments collected: {len(comments)}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()