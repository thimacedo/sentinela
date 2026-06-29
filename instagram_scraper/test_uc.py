import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = uc.ChromeOptions()
options.headless = False
# Do not add any experimental options here; let uc handle them
driver = uc.Chrome(options=options, use_subprocess=True)
driver.get("https://www.google.com")
print(driver.title)
driver.quit()