import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("IG_USER")
PASSWORD = os.getenv("IG_PASS")

print(f"Username: {USERNAME}")
print(f"Password length: {len(PASSWORD) if PASSWORD else 0}")

options = uc.ChromeOptions()
# We don't set headless so we can see what's happening
# options.headless = True
driver = uc.Chrome(options=options, use_subprocess=True)

try:
    driver.get("https://www.instagram.com/accounts/login/")
    wait = WebDriverWait(driver, 10)
    # Wait for username field
    username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    
    # Enter username
    username_input.clear()
    for ch in USERNAME:
        username_input.send_keys(ch)
        time.sleep(0.1)
    time.sleep(0.5)
    # Enter password
    password_input.clear()
    for ch in PASSWORD:
        password_input.send_keys(ch)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Click login
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    login_button.click()
    
    # Wait for login to complete, either by seeing the home icon or by being redirected
    time.sleep(5)  # give it a bit
    
    # Check for popups
    try:
        not_now_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")), 
                                     message="Not now button not found", 
                                     timeout=5)
        not_now_button.click()
        time.sleep(2)
    except TimeoutException:
        pass
    try:
        not_now_button2 = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]")), 
                                      message="Second not now button not found", 
                                      timeout=5)
        not_now_button2.click()
        time.sleep(2)
    except TimeoutException:
        pass
    
    # Check if we are logged in by looking for the search bar (which appears when logged in)
    try:
        search_icon = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='Search']")), 
                                  timeout=10)
        print("Logged in successfully!")
        # Now go to a profile to test
        driver.get("https://www.instagram.com/" + USERNAME + "/")
        time.sleep(3)
        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)
        # Try to find the first post
        try:
            first_post = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/p/')]")), 
                                     timeout=10)
            print("First post link found:", first_post.get_attribute('href'))
        except TimeoutException:
            print("No posts found on profile")
    except TimeoutException:
        print("Login failed or still on login page")
        print("Current URL:", driver.current_url)
        # Save a screenshot for debugging
        driver.save_screenshot("login_debug.png")
        print("Saved screenshot to login_debug.png")
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    driver.quit()