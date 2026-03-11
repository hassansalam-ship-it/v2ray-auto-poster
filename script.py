import requests
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

def fetch_and_post():
    print("--- Start Fetching ---")
    url = "https://raw.githubusercontent.com/yebekhe/TVC/main/configs/v2ray/sub"
    try:
        response = requests.get(url, timeout=15)
        configs = [line.strip() for line in response.text.splitlines() if ":443" in line]
        
        if not configs:
            print("❌ No configs found!")
            return

        config = configs[0]
        msg = f"🚀 *New Config Found*\n\n`{config}`\n\n✅ @V2rayashaq"
        
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        res = requests.post(send_url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        print(f"📡 Telegram Server Response: {res.text}")
        
    except Exception as e:
        print(f"⚠️ Error occurred: {e}")

if __name__ == "__main__":
    fetch_and_post()
