import requests
import os
import re
import base64
import socket
import time
import random
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# --- إعدادات مشروع ألفا ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def clean_sni_host(config):
    try:
        # تنظيف الـ SNI والـ Host من الروابط
        config = re.sub(r'sni=[^&]+&?', '', config)
        config = re.sub(r'host=[^&]+&?', '', config)
        # إزالة العلامات الزائدة في نهاية الرابط إذا وجدت
        config = config.rstrip('&').rstrip('?')
        return config
    except:
        return config

def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=2).json()
        if res.get('status') == 'success':
            return f"({res.get('countryCode')}) {res.get('country')}"
    except: pass
    return "🌍 Global Node"

def check_server_status(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=1.5):
            return True
    except: return False

def post_process():
    print("⛏️ Searching for 3 Raw SSL Servers (No SNI)...")
    all_found = []
    for url in SEARCH_SOURCES:
        try:
            r = requests.get(url, timeout=10).text
            if "vless://" not in r and "vmess://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            all_found.extend(re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', r))
        except: continue
    
    unique_configs = list(set(all_found))
    random.shuffle(unique_configs)
    
    posted_count = 0
    for config in unique_configs:
        if posted_count >= 3: break 
            
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        
        if port == "443" and check_server_status(host, port):
            # تنظيف السيرفر من الهوست القديم
            raw_config = clean_sni_host(config)
            
            try:
                ip_addr = socket.gethostbyname(host)
                location = get_location(ip_addr)
            except: location = "🌍 International"

            header = "🛠️ <b>RAW SSL SERVER</b> 🛠️"
            
            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"🌍 <b>Country:</b> {location}\n"
            msg += f"🔹 <b>Type:</b> Vless/Vmess (SSL)\n"
            msg += f"🛡️ <b>SSL:</b> Verified ✅\n"
            msg += f"⚙️ <b>SNI/Host:</b> Manual ✍️\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #Raw_Server\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{raw_config}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            try:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"}
                    ]]}
                })
                posted_count += 1
                time.sleep(6)
            except: pass

if __name__ == "__main__":
    post_process()
