import requests
import os
import re
import base64
import socket
import time
import random

# --- إعدادات مشروع ألفا ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"

# مصادر قوية جداً ومباشرة
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha"
]

def check_server_quick(host, port):
    try:
        # زيادة الـ timeout لـ 2 ثانية لضمان التقاط السيرفرات في GitHub
        with socket.create_connection((host, int(port)), timeout=2.0):
            return True
    except: return False

def post_process():
    print("🚀 Starting Alpha Scraper...")
    all_found = []
    
    for url in SEARCH_SOURCES:
        try:
            r = requests.get(url, timeout=15).text
            if "vless://" not in r and "vmess://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            configs = re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', r)
            all_found.extend(configs)
            print(f"📡 Source {url}: Found {len(configs)}")
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
    
    unique_configs = list(set(all_found))
    random.shuffle(unique_configs)
    print(f"✅ Total Unique Configs: {len(unique_configs)}")

    posted = 0
    # فحص عينة من 100 سيرفر
    for config in unique_configs[:100]:
        if posted >= 4: break 
        
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        
        if check_server_quick(host, port):
            print(f"🟢 Server {host} is UP! Sending...")
            
            msg = f"✨ <b>Alpha Project | Ashaq Team</b> ✨\n━━━━━━━━━━━━━━━\n⚡ <b>Status:</b> Ultra Stable 🟢\n🛡 <b>Type:</b> Vless/Vmess\n🏷 <b>Tags:</b> #Ashaq_Team #VPS\n━━━━━━━━━━━━━━━\n<code>{config}</code>\n━━━━━━━━━━━━━━━\n👥 @V2rayashaq"

            res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"
            })
            
            if res.status_code == 200:
                print("🚀 Sent successfully!")
                posted += 1
                time.sleep(2)
            else:
                print(f"❌ Telegram API Error: {res.text}")

    if posted == 0:
        print("⚠️ No live servers found. Check if BOT_TOKEN is correct and Bot is Admin in @V2rayashaq")

if __name__ == "__main__":
    post_process()
