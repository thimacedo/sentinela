import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = uc.ChromeOptions()
# options.headless = True  # set False to see browser
driver = uc.Chrome(version_main=149, options=options)
driver.get("https://www.instagram.com/")
try:
    # Wait for login page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    print("Login page loaded successfully")
    # Optionally, we can try to login with dummy credentials (will fail) but we just want to see if page loads
except Exception as e:
    print("Error:", e)
finally:
    driver.quit()