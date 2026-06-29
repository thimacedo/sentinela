import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = uc.ChromeOptions()
# Run in headed mode to see what's happening
options.headless = False
# Add some arguments to make it more stealthy
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
# Let undetected_chromedriver handle the rest

# Initialize the driver
driver = uc.Chrome(options=options, use_subprocess=True)

try:
    driver.get("https://www.instagram.com/")
    # Wait for the page to load, check for the login button or the home icon
    try:
        # Wait for the login link to appear (if not logged in)
        login_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/accounts/login/')]"))
        )
        print("Not logged in, login link found.")
    except:
        # If we don't find the login link, maybe we are already logged in or on the home page
        try:
            # Check for the home icon (SVG with aria-label="Home")
            home_icon = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//svg[@aria-label='Home']"))
            )
            print("Logged in, home icon found.")
        except:
            print("Could not determine login state.")
    # Print the title
    print("Page title:", driver.title)
    # Keep the browser open for a few seconds to inspect
    time.sleep(5)
finally:
    driver.quit()