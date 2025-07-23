import os
import time
import re
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
USERNAME = os.getenv("LOGIN_USERNAME")
PASSWORD = os.getenv("LOGIN_PASSWORD")
LOGIN_URL = os.getenv("LOGIN_URL")
SMS_URL = os.getenv("SMS_PAGE_URL")

sent_hashes = set()

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Failed to send message:", e)

def solve_captcha(question):
    match = re.search(r'(\d+)\s*\+\s*(\d+)', question)
    if match:
        return str(int(match.group(1)) + int(match.group(2)))
    return ""

def login_and_fetch_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(LOGIN_URL)

    try:
        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        captcha_text = driver.find_element(By.ID, "captcha_text").text
        captcha_answer = solve_captcha(captcha_text)
        driver.find_element(By.NAME, "captcha").send_keys(captcha_answer)
        driver.find_element(By.NAME, "login").click()

        time.sleep(2)
        if "Dashboard" in driver.page_source or "SMSCDRStats" in driver.page_source:
            return driver
        else:
            send_to_telegram("⚠️ Login failed.")
            driver.quit()
            return None
    except Exception as e:
        send_to_telegram(f"⚠️ Error during login: {str(e)}")
        driver.quit()
        return None

def extract_otp_data(text):
    number_match = re.search(r'\b\+?\d{6,15}\b', text)
    code_match = re.search(r'\b\d{4,8}\b', text)
    sender_match = re.search(r'From:\s*(.*)', text)
    sender = sender_match.group(1).strip() if sender_match else "Unknown"

    country = "বাংলাদেশ"  # Static for now
    number = number_match.group(0) if number_match else "N/A"
    code = code_match.group(0) if code_match else "N/A"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    full_message = f"""🚨 New {sender} OTP Received Successfully

📅 Date: {now}
🌍 Country: {country}
📞 Number: {number}
📱 App/Sender: {sender}
🔑 OTP: {code}

📬 Full Message : {text}

🕹️ BOT MAKER BY : @MR_OWNER_057.""" 
    return full_message

def check_new_messages(driver):
    driver.get(SMS_URL)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.find_all("tr")

    for row in rows:
        columns = row.find_all("td")
        if len(columns) >= 5:
            msg = columns[4].text.strip()
            hash_val = hashlib.md5(msg.encode()).hexdigest()
            if hash_val not in sent_hashes:
                sent_hashes.add(hash_val)
                formatted = extract_otp_data(msg)
                send_to_telegram(formatted)

if __name__ == "__main__":
    send_to_telegram("✅ OTP BOT IS RUNNING")

    driver = login_and_fetch_driver()
    if driver:
        send_to_telegram("✅ Login successful")
        while True:
            check_new_messages(driver)
            time.sleep(10)
