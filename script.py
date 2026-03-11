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

# --- قوائم الهوستات الذكية ---
OODI_HOSTS = [
    ("m.tiktok.com", "TikTok 🎵"), ("www.snapchat.com", "Snapchat 👻"),
    ("m.instagram.com", "Instagram 📸"), ("m.facebook.com", "Facebook 👥"),
    ("www.wechat.com", "WeChat 💬"), ("m.youtube.com", "YouTube 🎥"),
    ("www.pubgmobile.com", "PUBG Mobile 🎮"), ("web.telegram.org", "Telegram ✈️"),
    ("web.whatsapp.com", "WhatsApp 🟢"), ("invite.viber.com", "Viber 💜"),
    ("en.help.roblox.com", "Roblox 🎮")
]

VOXI_HOST = ("downloads.vodafone.co.uk", "Voxi UK 🇬🇧")
ZAIN_KAFO_HOST = ("m.tiktok.com", "Zain كفو 💎")

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def apply_sni(config, sni_host):
    # إزالة أي SNI أو Host قديم وإضافة الجديد
    config = re.sub(r'sni=[^&]+&?', '', config)
    config = re.sub(r'host=[^&]+&?', '', config)
    if "?" in config:
        config += f"&sni={sni_host}&host={sni_host}"
    else:
        config += f"?sni={sni_host}&host={sni_host}"
    return config

def get_location(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=2).json()
        if res.get('status') == 'success':
            return f"({res.get('countryCode')}) {res.get('country')}"
    except: pass
    return "🌍 Global Node"

def check_ping(host, port):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=1.5):
            return int((time.time() - start) * 1000)
    except: return None

def post_process():
    print("🚀 Starting Smart Package Injection...")
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
    
    # تحديد الهوستات لهذه الدورة
    chosen_oodi = random.choice(OODI_HOSTS)
    packages = [
        {"host": VOXI_HOST[0], "name": VOXI_HOST[1], "label": "Voxi System"},
        {"host": chosen_oodi[0], "name": chosen_oodi[1], "label": "Oodi Package"},
        {"host": ZAIN_KAFO_HOST[0], "name": ZAIN_KAFO_HOST[1], "label": "Zain Kafo"}
    ]

    posted = 0
    for config in unique_configs:
        if posted >= 3: break
        
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        host, port = match.group(1), match.group(2)
        
        if port == "443":
            ping = check_ping(host, port)
            if ping and ping < 350:
                current_pkg = packages[posted]
                final_config = apply_sni(config, current_pkg["host"])
                
                try:
                    ip_addr = socket.gethostbyname(host)
                    location = get_location(ip_addr)
                except: location = "🌍 International"

                header = "🔥 <b>ULTRA FAST SERVER</b> 🔥" if ping < 90 else "✨ <b>Welcome to Ashaq Team</b> ✨"
                
                msg = f"{header}\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"🌍 <b>Country:</b> {location}\n"
                msg += f"📦 <b>Package:</b> {current_pkg['name']}\n"
                msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 Stable\n"
                msg += f"🛡️ <b>SSL:</b> Verified ✅\n"
                msg += f"⚙️ <b>System:</b> {current_pkg['label']}\n"
                msg += f"🕒 <b>Checked:</b> Just Now\n"
                msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #{current_pkg['label'].replace(' ','_')}\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{final_config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                    "reply_markup": {"inline_keyboard": [[{"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"}]]}
                })
                posted += 1
                time.sleep(6)

if __name__ == "__main__":
    post_process()
