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

# --- الباقات والهوستات ---
OODI_HOSTS = [
    ("m.tiktok.com", "TikTok 🎵"), ("m.youtube.com", "YouTube 🎥"),
    ("m.instagram.com", "Instagram 📸"), ("m.facebook.com", "Facebook 👥"),
    ("web.whatsapp.com", "WhatsApp 🟢"), ("web.telegram.org", "Telegram ✈️")
]
VOXI_HOST = ("downloads.vodafone.co.uk", "Voxi UK 🇬🇧")
ZAIN_KAFO_HOST = ("m.tiktok.com", "Zain كفو 💎")

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def clean_and_inject(config, sni_host, use_ssl=True):
    # تنظيف الرابط من الهوست والتشفير القديم
    config = re.sub(r'sni=[^&]+&?', '', config)
    config = re.sub(r'host=[^&]+&?', '', config)
    config = re.sub(r'security=[^&]+&?', '', config)
    
    connector = "&" if "?" in config else "?"
    if use_ssl:
        config += f"{connector}sni={sni_host}&host={sni_host}&security=tls"
    else:
        config += f"{connector}host={sni_host}" # بدون SSL لأودي وزين
    return config

def check_ping(host, port):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=1.2):
            return int((time.time() - start) * 1000)
    except: return None

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
    
    chosen_oodi = random.choice(OODI_HOSTS)
    # توزيع المهام: فوكسي (SSL)، أودي وزين (بدون SSL)
    packages = [
        {"host": VOXI_HOST[0], "name": VOXI_HOST[1], "ssl": True},
        {"host": chosen_oodi[0], "name": f"Oodi | {chosen_oodi[1]}", "ssl": False},
        {"host": ZAIN_KAFO_HOST[0], "name": ZAIN_KAFO_HOST[1], "ssl": False}
    ]

    posted = 0
    for config in unique_configs:
        if posted >= 3: break
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        host, port = match.group(1), match.group(2)
        
        ping = check_ping(host, port)
        if ping:
            current_pkg = packages[posted]
            final_link = clean_and_inject(config, current_pkg["host"], current_pkg["ssl"])
            
            header = "🔥 <b>ULTRA FAST SERVER</b> 🔥" if ping < 90 else "✨ <b>Welcome to Ashaq Team</b> ✨"
            
            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"📦 <b>Package:</b> {current_pkg['name']}\n"
            msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 Ultra Stable\n"
            msg += f"🛡️ <b>SSL:</b> {'Enabled ✅' if current_pkg['ssl'] else 'Disabled 🔓'}\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #V2ray\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{final_link}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": [[{"text": "📢 Join", "url": "https://t.me/V2rayashaq"}]]}
            })
            posted += 1
            time.sleep(5)

if __name__ == "__main__":
    post_process()
