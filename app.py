import os
import time
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)

# ----------------------------
# Driver setup
# ----------------------------
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Use environment variable CHROME_BIN
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    if not os.path.exists(chrome_bin):
        raise Exception(f"Chrome/Chromium binary not found at {chrome_bin}")
    options.binary_location = chrome_bin

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver

# ----------------------------
# Instagram Scraper Functions
# ----------------------------
def login_instagram(driver, username, password):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(4)
    try:
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password + Keys.RETURN)
        time.sleep(6)
    except:
        time.sleep(4)

def search_hashtag(driver, tag):
    driver.get(f"https://www.instagram.com/explore/tags/{tag}/")
    time.sleep(4)

def get_post_links(driver, limit=50):
    links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    while len(links) < limit:
        anchors = driver.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/p/" in href:
                links.add(href)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    return list(links)[:limit]

def extract_info(driver, post_url):
    driver.get(post_url)
    time.sleep(4)
    try:
        username_el = driver.find_element(By.XPATH, '//header//a[contains(@href, "/")]')
        username = username_el.get_attribute("href").split("/")[-2]
    except:
        username = "Unknown"

    try:
        caption_el = driver.find_element(By.XPATH, '//div[@data-testid="post-comment-root"]')
        caption = caption_el.text
    except:
        try:
            alt = driver.find_element(By.XPATH, '//div[contains(@class,"C4VMK")]/span')
            caption = alt.text
        except:
            caption = ""

    bio = ""
    if username != "Unknown":
        try:
            driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(3)
            try:
                bio_section = driver.find_element(By.CSS_SELECTOR, "div.-vDIg span")
                bio = bio_section.text
            except:
                try:
                    meta_desc = driver.find_element(By.XPATH, '//meta[@name="description"]').get_attribute('content')
                    bio = meta_desc
                except:
                    bio = ""
        except:
            bio = ""

    numbers = re.findall(r'\+?\d[\d\s\-\(\)]{7,}\d', bio + " " + caption)
    numbers = list(dict.fromkeys(numbers))
    return {"Username": username, "Phone Numbers": ", ".join(numbers), "Bio": bio.strip()}

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def home():
    return render_template("index.html")  # Ensure index.html exists

@app.route("/scrape", methods=["POST"])
def scrape():
    payload = request.get_json() or {}
    hashtag = (payload.get("hashtag") or "").strip()
    limit = int(payload.get("limit", 50))

    if not hashtag:
        return jsonify({"error": "hashtag required"}), 400

    IG_USER = os.environ.get("INSTAGRAM_USERNAME")
    IG_PASS = os.environ.get("INSTAGRAM_PASSWORD")
    if not IG_USER or not IG_PASS:
        return jsonify({"error": "instagram credentials not configured"}), 500

    driver = None
    try:
        driver = create_driver()
        login_instagram(driver, IG_USER, IG_PASS)
        search_hashtag(driver, hashtag)
        links = get_post_links(driver, limit)
        results, seen = [], set()
        for url in links:
            info = extract_info(driver, url)
            if info["Username"] not in seen and info["Username"] != "Unknown":
                seen.add(info["Username"])
                results.append(info)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
