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

# المصادر العملاقة (أعماق الأرض)
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess"
]

VPS_PROVIDERS = ['oracle', 'google', 'amazon', 'aws', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'azure', 'contabo']

def check_server(host, port, config):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=1.2):
            ping = int((time.time() - start) * 1000)
            is_ssl = "tls" in config.lower() or port == "443"
            is_cf = "cloudfront" in config.lower() or "104." in host or "172." in host
            return ping, is_ssl, is_cf
    except: return None, False, False

def post_process():
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
    
    posted = 0
    for config in unique_configs[:300]:
        if posted >= 3: break # ينشر 3 سيرفرات فقط كل دورة
        
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        ping, has_ssl, has_cf = check_server(host, port, config)
        
        if ping and ping < 250:
            try:
                # وسم النار للسيرفرات الخارقة
                header = "🔥 <b>ULTRA FAST SERVER</b> 🔥" if ping < 80 else "✨ <b>Welcome to Ashaq Team</b> ✨"
                
                msg = f"{header}\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"🌍 <b>Country:</b> Checking...\n" # لتسريع الكود حذفنا طلب الـ IP التفصيلي
                msg += f"🔹 <b>Type:</b> Vless/Vmess\n"
                msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 Ultra Stable\n"
                msg += f"🛡️ <b>SSL:</b> {'Verified ✅' if has_ssl else 'Standard'}\n"
                msg += f"☁️ <b>CF:</b> {'Active ⚡' if has_cf else 'Direct'}\n"
                msg += f"🕒 <b>Checked:</b> Just Now\n"
                msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #Free_VPN\n"
                msg += f"🔹 <b>Port:</b> {port}\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                        {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"}
                    ]]}
                })
                posted += 1
                time.sleep(5) # فاصل أمان بين المنشورات
            except: continue

if __name__ == "__main__":
    post_process()
