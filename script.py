import requests
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq" 
CHANNEL_NAME = "ashaq v2ray"

SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/configs/v2ray/sub",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/v2ray.txt",
    "https://raw.githubusercontent.com/Iranian-v2ray/v2ray-configs/main/splited/vless.txt"
]

def fetch_and_post():
    all_configs = []
    for url in SOURCES:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if ":443" in line:
                        all_configs.append(line.strip())
        except: continue
    unique_configs = list(set(all_configs))[:3]
    for config in unique_configs:
        message = f"🚀 *{CHANNEL_NAME}*\n━━━━━━━━━━━━━━━\n✅ *New Config (Port 443)*\n\n`{config}`\n\n🔗 [Join Channel](https://t.me/V2rayashaq)"
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True})

if __name__ == "__main__":
    fetch_and_post()
