from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up ChromeDriver
driver_path = ChromeDriverManager().install()
print(f"Using ChromeDriver: {driver_path}")
service = ChromeService(driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.197 Safari/537.36")
driver = webdriver.Chrome(service=service, options=options)
driver.set_page_load_timeout(30)
try:
    driver.get("https://www.google.com")
    print(f"Google title: {driver.title}")
    driver.get("https://www.instagram.com/")
    print(f"Instagram title: {driver.title}")
    # Check if we are on login page
    try:
        login_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Log in']"))
        )
        print("Login page detected")
    except:
        print("Not on login page, maybe already logged in or redirect")
finally:
    driver.quit()