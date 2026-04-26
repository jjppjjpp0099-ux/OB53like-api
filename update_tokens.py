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

# Yahan apna Render wala link daalein
BOT_WEBHOOK_URL = "https://telegram-like-bot-8ivj.onrender.com/notify_update"

# GitHub details environment variables se lega
G_TOKEN = os.environ.get("G_TOKEN")
REPO_NAME = "jjppjjpp0099-ux/OB53like-api"

def is_token_expired_soon(token):
    """Check karta hai ki token agle 10 minute mein expire hoga ya nahi"""
    try:
        # JWT decode logic
        payload = token.split('.')[1]
        payload += '=' * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
        exp = decoded.get('exp')
        
        if not exp:
            return True
        
        # Agar current time se expiry ka gap 600 seconds (10 min) se kam hai
        remaining_time = exp - time.time()
        return remaining_time < 600
    except Exception:
        return True

def main():
    """Ye function main logic hai jo app.py se call hoga"""
    print("Checking token status...")
    
    # 1. Pehle check karo ki kya abhi wale tokens valid hain?
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                current_tokens = json.load(f)
                if current_tokens and not is_token_expired_soon(current_tokens[0]['token']):
                    print("Tokens are still fresh. No update needed.")
                    return "Tokens are still valid"
    except Exception as e:
        print(f"Read error: {e}")

    # 2. Agar expire hone wale hain, toh naye tokens fetch karo
    print("Tokens expiring soon. Starting fetch process...")
    try:
        with open(UIDPASS_FILE, "r", encoding="utf-8") as f:
            uidpass_list = json.load(f)
    except Exception as e:
        return f"Error reading uidpass.json: {e}"

    new_tokens = []
    for item in uidpass_list:
        uid = item.get("uid")
        password = item.get("password")
        
        # API se token mangna
        try:
            r = requests.get(f"{API_URL}?uid={uid}&password={password}", timeout=10)
            if r.status_code == 200:
                token_val = r.json().get("token")
                if token_val:
                    new_tokens.append({"token": token_val})
        except Exception as e:
            print(f"Error fetching for {uid}: {e}")

    # 3. Agar naye tokens mil gaye, toh save aur push karo
    if new_tokens:
        # Local save
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(new_tokens, f, ensure_ascii=False, indent=4)
        
        # GitHub Update
        if G_TOKEN:
            try:
                g = Github(G_TOKEN)
                repo = g.get_repo(REPO_NAME)
                contents = repo.get_contents(TOKEN_FILE)
                
                repo.update_file(
                    contents.path, 
                    "Auto Update Tokens via Bot/API", 
                    json.dumps(new_tokens, indent=4), 
                    contents.sha
                )
                print("GitHub updated successfully.")
                
                # Bot ko notification bhejna
                try:
                    requests.get(BOT_WEBHOOK_URL, timeout=5)
                except:
                    print("Bot notification failed but GitHub updated.")
                
                return "Tokens Updated and Pushed to GitHub"
            except Exception as e:
                return f"GitHub Push Error: {e}"
        else:
            return "Tokens updated locally but G_TOKEN missing for GitHub"
            
    return "Failed to fetch any new tokens"

if __name__ == "__main__":
    # Agar manually file chalayi jaye
    print(main())
