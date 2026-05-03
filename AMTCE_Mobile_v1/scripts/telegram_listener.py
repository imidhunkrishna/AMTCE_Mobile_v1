# scripts/telegram_listener.py
import os
import time
import requests
import sys
from dotenv import load_dotenv

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "app", "src", "main", "python"))

# Load config
load_dotenv(os.path.join(base_dir, ".env"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"

from orchestrator import AMTCE_Mobile_Orchestrator

def start_listener():
    print(f"AMTCE Telegram Listener Started (Isolated Mode)")
    print(f"Using Token: {TOKEN[:5]}...{TOKEN[-5:]}")
    
    engine = AMTCE_Mobile_Orchestrator()
    last_update_id = 0
    
    while True:
        try:
            print("Polling Telegram API...")
            # Poll for updates
            response = requests.get(f"{API_URL}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 10
            }, timeout=15)
            
            updates = response.json().get("result", [])
            
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                
                if text.startswith("http"):
                    print(f"Received Link: {text}")
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Link Received! AMTCE Mobile Engine is processing..."
                    })
                    
                    # Run the pipeline
                    result = engine.process_link(text)
                    
                    # Respond with results
                    if result["status"] == "success":
                        resp_text = f"Success!\nVideo: {result['video_id']}\nPlan: {result['edit_plan']['output_name']}"
                    else:
                        resp_text = f"Error: {result.get('message')}"
                        
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": resp_text
                    })
                elif text == "/start":
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Welcome to AMTCE Mobile! Send me a video link to begin."
                    })

        except Exception as e:
            print(f"⚠️ Listener Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)
    start_listener()
