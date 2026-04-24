import requests
import json
import base64
import time
import os
from github import Github

# --- Configuration ---
UIDPASS_FILE = "uidpass.json"
TOKEN_FILE = "tokens.json"
API_URL = "https://xtytdtyj-jwt.up.railway.app/token"
G_TOKEN = os.environ.get("G_TOKEN") # GitHub Token for pushing changes
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"
BOT_WEBHOOK_URL = "https://your-bot-app.onrender.com/notify_update" # Aapka Render Bot URL

def read_uidpass():
    with open(UIDPASS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def is_token_expired_soon(token):
    try:
        # JWT decode without library for efficiency
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
        exp = decoded.get('exp')
        if not exp: return True
        
        remaining_time = exp - time.time()
        # 10 minutes (600 seconds) check
        return remaining_time < 600
    except Exception:
        return True

def fetch_token(uid, password):
    url = f"{API_URL}?uid={uid}&password={password}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("token")
    except Exception as e:
        print(f"Error fetching token for UID {uid}: {e}")
        return None

def update_github_repo(token_list):
    if not G_TOKEN:
        print("GitHub Token not found!")
        return False
    try:
        g = Github(G_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(TOKEN_FILE)
        new_content = json.dumps(token_list, ensure_ascii=False, indent=4)
        repo.update_file(contents.path, "Auto Update Tokens", new_content, contents.sha)
        return True
    except Exception as e:
        print(f"GitHub Update Failed: {e}")
        return False

def notify_bot():
    try:
        requests.get(BOT_WEBHOOK_URL)
    except:
        pass

def main():
    try:
        with open(TOKEN_FILE, "r") as f:
            current_tokens = json.load(f)
    except:
        current_tokens = []

    # Check if first token is expiring (Assuming all tokens are from same source/time)
    needs_update = True
    if current_tokens:
        token_to_check = current_tokens[0].get("token")
        if not is_token_expired_soon(token_to_check):
            needs_update = False
            print("Tokens are still valid. No update needed.")

    if needs_update:
        print("Tokens expiring soon or invalid. Updating...")
        uidpass_list = read_uidpass()
        new_tokens = []
        for item in uidpass_list:
            token = fetch_token(item["uid"], item["password"])
            if token:
                new_tokens.append({"token": token})
        
        if new_tokens:
            # Update Local & GitHub
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(new_tokens, f, ensure_ascii=False, indent=4)
            
            if update_github_repo(new_tokens):
                print("GitHub repo updated.")
                notify_bot() # Tell Telegram Bot
        else:
            print("No new tokens could be fetched.")

if __name__ == "__main__":
    main()
