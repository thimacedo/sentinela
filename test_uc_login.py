import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = uc.ChromeOptions()
# options.headless = True
driver = uc.Chrome(version_main=149, options=options, use_subprocess=True)
driver.get("https://www.instagram.com/")
try:
    # Wait for the page to load, maybe see if we are logged in or not
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[text()='Log in']"))
    )
    print("Not logged in, login button found")
except:
    print("Login button not found, maybe already logged in or different page")
print("Title:", driver.title)
driver.quit()