import os
import sys
import json
import time
import random
import argparse
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

# Load environment variables from .env file if exists (though we already loaded via sentinel's .env)
load_dotenv()

class InstagramCommentScraper:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self.load_config(config_path)
        self.driver = None
        self.wait = None
        self.session_file = self.config.get("session_file", "data/session.pkl")
        self.logged_in = False

    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
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

    def save_config(self, config_path: str):
        """Save current configuration to JSON file."""
        if ".." in config_path:
            raise Exception("Invalid file path")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def init_driver(self):
        """Initialize the Chrome driver with stealth settings."""
        options = uc.ChromeOptions()
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        # Additional options to avoid detection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # Set a realistic user agent
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Proxy if configured
        if self.config.get("use_proxy") and self.config.get("proxy"):
            options.add_argument(f'--proxy-server={self.config["proxy"]}')

        self.driver = uc.Chrome(options=options, version_main=None)
        self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
        self.wait = WebDriverWait(self.driver, self.config.get("element_wait_timeout", 10))
        
        # Execute script to remove webdriver flag
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def random_delay(self, min_sec: float = None, max_sec: float = None):
        """Sleep for a random time to mimic human behavior."""
        if min_sec is None:
            min_sec = self.config.get("min_delay", 2)
        if max_sec is None:
            max_sec = self.config.get("max_delay", 5)
        time.sleep(random.uniform(min_sec, max_sec))

    def login(self):
        """Log into Instagram using saved session or credentials."""
        if self.load_session():
            # Test if session is still valid by visiting the homepage
            try:
                self.driver.get("https://www.instagram.com/")
                self.random_delay(2, 4)
                # Check if we're logged in by looking for the search bar or profile icon
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Search']/ancestor::a")))
                self.logged_in = True
                print("Loaded session and verified login.")
                return
            except (TimeoutException, WebDriverException):
                print("Saved session expired or invalid. Logging in again.")
        
        # Perform fresh login
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
                    # Ensure cookie has required fields
                    if 'sameSite' in cookie:
                        del cookie['sameSite']  # Remove sameSite if problematic
                    self.driver.add_cookie(cookie)
                print(f"Loaded session from {self.session_file}")
                return True
            except Exception as e:
                print(f"Failed to load session: {e}")
                return False
        return False

    def navigate_to_post(self, post_url: str):
        """Navigate to the Instagram post."""
        print(f"Navigating to post: {post_url}")
        self.driver.get(post_url)
        self.random_delay(3, 5)
        
        # Wait for post to load
        try:
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//article")),
                message="Post did not load"
            )
        except TimeoutException:
            print("Warning: Post may not have loaded properly or is private/unavailable.")
    
    def load_all_comments(self, max_scrolls: int = 50):
        """Scroll to load all comments."""
        print("Loading comments...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        
        while scroll_count < max_scrolls:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay(2, 4)  # Wait for comments to load
            
            # Calculate new scroll height and compare with last
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try to click "Load more comments" button if exists
                try:
                    load_more_button = self.driver.find_element(
                        By.XPATH, 
                        "//button[contains(text(), 'Load more comments') or contains(text(), 'Ver mais comentários')]"
                    )
                    if load_more_button.is_displayed():
                        load_more_button.click()
                        self.random_delay(2, 3)
                        continue
                except NoSuchElementException:
                    # No more comments to load
                    print("No more comments to load.")
                    break
            else:
                last_height = new_height
                scroll_count += 1
                print(f"Scrolled {scroll_count} times...")
                
        print(f"Finished scrolling after {scroll_count} attempts.")

    def extract_comments(self) -> List[Dict]:
        """Extract all comments from the currently loaded post."""
        print("Extracting comments...")
        comments = []
        
        # Find all comment containers
        comment_elements = self.driver.find_elements(
            By.XPATH, 
            "//div[contains(@class, '_a9zs')]"  # This class may change; Instagram updates frequently
        )
        
        # Alternative selectors if the above doesn't work
        if not comment_elements:
            comment_elements = self.driver.find_elements(
                By.XPATH, 
                "//ul//li//div[contains(@class, '_a9zs')]"
            )
        if not comment_elements:
            # Another common pattern
            comment_elements = self.driver.find_elements(
                By.XPATH, 
                "//div[@role='button' and contains(@tabindex, '0')]//..//following-sibling::div"
            )
        
        print(f"Found {len(comment_elements)} comment elements.")
        
        for i, comment_elem in enumerate(comment_elements):
            try:
                # Extract username
                try:
                    username_elem = comment_elem.find_element(
                        By.XPATH, 
                        ".//span[contains(@class, '_aacl')]//a | .//a[contains(@href, '/')]//span"
                    )
                    username = username_elem.text
                except NoSuchElementException:
                    username = f"user_{i}"
                
                # Extract comment text
                try:
                    text_elem = comment_elem.find_element(
                        By.XPATH, 
                        ".//span[contains(@class, '_aacl')]//following-sibling::span | .//div[contains(@class, '_a9zs')]//span"
                    )
                    text = text_elem.text
                except NoSuchElementException:
                    text = ""
                
                # Extract timestamp
                try:
                    time_elem = comment_elem.find_element(
                        By.TAG_NAME, 
                        "time"
                    )
                    timestamp = time_elem.get_attribute("datetime")
                except NoSuchElementException:
                    timestamp = None
                
                # Extract likes count (if visible)
                try:
                    likes_elem = comment_elem.find_element(
                        By.XPATH, 
                        ".//span[contains(@class, '_aacl')]//following-sibling::span[contains(text(), 'like') or contains(text(), 'curtida')]//preceding-sibling::span"
                    )
                    likes_text = likes_elem.text
                    # Extract number from text like "123 likes"
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
                print(f"Error extracting comment {i}: {e}")
                continue
        
        return comments

    def scrape_comments(self, post_url: str, output_file: str = None) -> List[Dict]:
        """Main method to scrape comments from a post."""
        try:
            if not self.driver:
                self.init_driver()
            
            if not self.logged_in:
                self.login()
            
            self.navigate_to_post(post_url)
            self.load_all_comments()
            comments = self.extract_comments()
            
            if output_file:
                self.save_results(comments, output_file)
            
            return comments
        except Exception as e:
            print(f"Error during scraping: {e}")
            raise
        finally:
            # Keep driver open for potential reuse; caller should close if needed
            pass

    def save_results(self, comments: List[Dict], output_file: str):
        """Save comments to JSON and CSV formats."""
        output_path = Path(output_file)
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
        else:
            print("No comments to save to CSV.")

    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            print("Browser closed.")

def main():
    parser = argparse.ArgumentParser(description="Instagram Comment Scraper")
    parser.add_argument("--post-url", required=True, help="URL of the Instagram post to scrape comments from")
    parser.add_argument("--output", default="data/comments", help="Output file prefix (without extension)")
    parser.add_argument("--config", default="config/config.json", help="Path to configuration file")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--max-scrolls", type=int, default=50, help="Maximum number of scrolls to load comments")
    
    args = parser.parse_args()
    
    scraper = InstagramCommentScraper(config_path=args.config)
    if args.headless:
        scraper.config["headless"] = True
    
    try:
        comments = scraper.scrape_comments(
            post_url=args.post_url,
            output_file=args.output
        )
        print(f"\nSuccessfully scraped {len(comments)} comments.")
    except Exception as e:
        print(f"Failed to scrape comments: {e}")
        return 1
    finally:
        scraper.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())