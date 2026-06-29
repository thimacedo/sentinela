import os
import json
import time
import random
from datetime import datetime
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

class SimpleUCScraper:
    def __init__(self):
        self.username = os.getenv("IG_USER")
        self.password = os.getenv("IG_PASS")
        self.driver = None
        self.wait = None

    def init_driver(self):
        options = uc.ChromeOptions()
        # options.headless = False  # set True if you want headless
        # Use version_main to match your Chrome version (149)
        self.driver = uc.Chrome(version_main=149, options=options, use_subprocess=True)
        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 10)
        # Stealth: remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def random_delay(self, min_sec=2, max_sec=5):
        time.sleep(random.uniform(min_sec, max_sec))

    def login(self):
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
        for ch in self.username:
            username_input.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.2))
        self.random_delay(0.5, 1.5)
        password_input.clear()
        for ch in self.password:
            password_input.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.2))
        self.random_delay(0.5, 1.5)
        # Click login button
        login_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        self.random_delay(5, 8)
        # Handle popups
        try:
            not_now_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")),
                message="Not Now button not found"
            )
            not_now_button.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass
        try:
            not_now_button2 = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")),
                message="Second Not Now button not found"
            )
            not_now_button2.click()
            self.random_delay(2, 3)
        except TimeoutException:
            pass
        # Verify login
        try:
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::a")),
                message="Login verification failed"
            )
            print("Login successful!")
        except TimeoutException:
            raise Exception("Login failed - check credentials or if additional verification is required.")

    def get_user_recent_posts(self, username: str, limit: int = 1):
        profile_url = f"https://www.instagram.com/{username}/"
        print(f"Fetching profile for {username}...")
        self.driver.get(profile_url)
        self.random_delay(3, 5)
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, '_aagv')]")))
        except TimeoutException:
            print(f"Timeout waiting for posts for {username}")
            return []
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

    def scrape_comments_from_post(self, post_url: str, max_comments: int = 5):
        print(f"  Scraping comments from {post_url}")
        self.driver.get(post_url)
        self.random_delay(3, 5)
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//article")))
        except TimeoutException:
            print(f"    Post did not load properly.")
            return []
        # Scroll to load comments
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
        print(f"    Found {len(comment_elements)} comment elements")
        for i, elem in enumerate(comment_elements[:max_comments]):
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

    def save_results(self, comments, base_filename="data/target_comments"):
        if not comments:
            print("No comments to save.")
            return
        output_path = Path(base_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # JSON
        json_file = output_path.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(comments)} comments to {json_file}")
        # CSV
        csv_file = output_path.with_suffix('.csv')
        if comments:
            import pandas as pd
            df = pd.DataFrame(comments)
            # Reorder columns
            cols = ["username", "text", "timestamp", "likes", "scraped_at"]
            df = df[cols] if all(c in df.columns for c in cols) else df
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
        # Assuming semicolon delimiter
        import csv
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            username = row.get('username', '').strip()
            if username:
                usernames.append(username)
    print(f"Loaded {len(usernames)} usernames from CSV.")
    # Take first 2 for testing
    usernames = usernames[:2]
    print(f"Will process: {usernames}")
    # Initialize scraper
    scraper = SimpleUCScraper()
    try:
        scraper.init_driver()
        scraper.login()
        all_comments = []
        for username in usernames:
            print(f"\n=== Processing {username} ===")
            post_urls = scraper.get_user_recent_posts(username, limit=1)
            if not post_urls:
                print(f"No posts found for {username}")
                continue
            for post_url in post_urls:
                comments = scraper.scrape_comments_from_post(post_url, max_comments=5)
                for c in comments:
                    c["target_username"] = username
                    c["post_url"] = post_url
                all_comments.extend(comments)
                print(f"  Collected {len(comments)} comments from {post_url}")
            # Delay between targets
            scraper.random_delay(5, 10)
        # Save results
        scraper.save_results(all_comments, "data/target_comments")
        print(f"\nTotal comments collected: {len(all_comments)}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    main()