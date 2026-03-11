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

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess"
]

def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=2).json()
        if res.get('status') == 'success':
            return f"({res.get('countryCode')}) {res.get('country')}"
    except: pass
    return "🌍 Global Node"

def check_server_status(host, port):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=1.5):
            return int((time.time() - start) * 1000)
    except: return None

def post_process():
    print("⛏️ Searching for 3 Elite Servers on Port 443 ONLY...")
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
    # فحص العينة لضمان استخراج بورت 443 فقط
    for config in unique_configs:
        if posted_count >= 3:
            break 
            
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        
        # الشرط الذهبي: بورت 443 فقط
        if port != "443":
            continue

        ping = check_server_status(host, port)
        
        if ping and ping < 350:
            try:
                ip_addr = socket.gethostbyname(host)
                location = get_location(ip_addr)
            except:
                location = "🌍 International"

            is_ssl = "tls" in config.lower() or "security=tls" in config
            is_cf = "cloudfront" in config.lower() or "104." in host
            
            header = "🔥 <b>ULTRA FAST SERVER</b> 🔥" if ping < 90 else "✨ <b>Welcome to Ashaq Team</b> ✨"
            
            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"🌍 <b>Country:</b> {location}\n"
            msg += f"🔹 <b>Type:</b> Vless/Vmess\n"
            msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 Ultra Stable\n"
            msg += f"🛡️ <b>SSL:</b> {'Verified ✅' if is_ssl else 'Standard'}\n"
            msg += f"☁️ <b>CF:</b> {'Active ⚡' if is_cf else 'Direct'}\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #Free_VPN\n"
            msg += f"🔹 <b>Port:</b> 443 (High Priority)\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{config}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            try:
                payload = {
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                        {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"}
                    ]]}
                }
                res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
                if res.status_code == 200:
                    posted_count += 1
                    time.sleep(6)
            except: pass

if __name__ == "__main__":
    post_process()
