from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Try to get the exact version
driver_path = ChromeDriverManager(driver_version="149.0.7827.197").install()
print(f"Driver path: {driver_path}")

service = ChromeService(driver_path)
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.google.com")
print(f"Title: {driver.title}")
driver.quit()