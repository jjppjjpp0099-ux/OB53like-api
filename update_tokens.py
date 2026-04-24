import requests
import json
import time
import os
from datetime import datetime, timedelta
from github import Github

# --- CONFIGURATION ---
UIDPASS_FILE = "uidpass.json"
TOKEN_FILE = "tokens.json"
API_URL = "https://xtytdtyj-jwt.up.railway.app/token"

# GitHub Config (Naya Repo)
G_TOKEN = os.environ.get("G_TOKEN")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api" # Aapka naya repo

# Bot Notification Config
BOT_API_URL = "https://ob-53like-api.vercel.app/update_notify" # Bot ko signal bhejne ke liye

# Timing Logic
EXPIRE_MINUTES = 480  # 8 Ghante (Andazan)
UPDATE_BEFORE = 10    # 10 Minute pehle update karega
CHECK_INTERVAL = 60   # Har 1 minute mein check karega

def fetch_tokens_from_api():
    """Railway API se naye tokens nikalta hai"""
    try:
        with open(UIDPASS_FILE, "r", encoding="utf-8") as f:
            uidpass_list = json.load(f)
        
        new_tokens = []
        for item in uidpass_list:
            url = f"{API_URL}?uid={item['uid']}&password={item['password']}"
            response = requests.get(url, timeout=15)
            data = response.json()
            if data.get("token"):
                new_tokens.append({"token": data.get("token")})
        return new_tokens
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return None

def update_github_repo(token_list):
    """Naye repo OB53like-api mein tokens.json update karta hai"""
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(TOKEN_FILE)
        
        new_content = json.dumps(token_list, indent=4)
        repo.update_file(contents.path, "Auto Update Tokens", new_content, contents.sha)
        return True
    except Exception as e:
        print(f"GitHub Update Error: {e}")
        return False

def notify_bot():
    """bot.py ko inform karta hai takki wo telegram pe message bheje"""
    try:
        # Hum bot ko ek request bhejenge jise bot.py handle karega
        requests.get(BOT_API_URL)
    except:
        pass

def main_process():
    print(f"[{datetime.now()}] Starting Token Update...")
    tokens = fetch_tokens_from_api()
    if tokens:
        if update_github_repo(tokens):
            print("✅ Successfully updated GitHub.")
            notify_bot()
            return True
    return False

if __name__ == "__main__":
    print("🚀 Auto-Updater Started...")
    # Pehli baar update karega start hote hi
    last_run_time = datetime.now()
    main_process()

    while True:
        now = datetime.now()
        time_diff = (now - last_run_time).total_seconds() / 60

        # Logic: 7 ghante 50 minute baad auto-update
        if time_diff >= (EXPIRE_MINUTES - UPDATE_BEFORE):
            success = main_process()
            if success:
                last_run_time = datetime.now()
            else:
                print("❌ Update failed, retrying in 5 minutes...")
                time.sleep(300) # Fail hone pe 5 min baad phir try karega
                continue

        time.sleep(CHECK_INTERVAL)
