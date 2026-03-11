import requests
import os
import re
import base64
import socket
import time
import random
import json

# --- إعدادات فريق عشق الملكية ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "genie_2000"

# --- باقات الهوستات ---
OODI_HOSTS = [
    ("m.tiktok.com", "Oodi | TikTok 🎵"), ("m.youtube.com", "Oodi | YouTube 🎥"),
    ("m.instagram.com", "Oodi | Instagram 📸"), ("m.facebook.com", "Oodi | Facebook 👥"),
    ("web.whatsapp.com", "Oodi | WhatsApp 🟢")
]
VOXI_HOST = ("downloads.vodafone.co.uk", "Voxi UK 🇬🇧")
ZAIN_KAFO_HOST = ("m.tiktok.com", "Zain كفو 💎")

SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def get_geo(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=2).json()
        if res.get('status') == 'success':
            return f"({res.get('countryCode')}) {res.get('country')}"
    except: pass
    return "🌍 Global Node"

def check_ping(host, port):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=1.2):
            return int((time.time() - start) * 1000)
    except: return None

def fix_vmess(link, sni):
    try:
        # فك تشفير Vmess وتعديل الـ SNI داخله
        data_b64 = link.split("://")[1]
        decoded = json.loads(base64.b64decode(data_b64).decode('utf-8'))
        decoded['sni'] = sni
        decoded['host'] = sni
        # إرجاع الرابط مشفراً وجاهزاً للتطبيق
        new_b64 = base64.b64encode(json.dumps(decoded).encode('utf-8')).decode('utf-8')
        return f"vmess://{new_b64}"
    except: return link

def clean_vless(link, sni, use_ssl):
    # مسح أي SNI أو host أو security قديم
    link = re.sub(r'[?&](sni|host|security)=[^&]*', '', link)
    connector = "&" if "?" in link else "?"
    if use_ssl:
        link += f"{connector}sni={sni}&host={sni}&security=tls"
    else:
        link += f"{connector}host={sni}"
    return link.replace('&amp;', '&')

def post_process():
    print("🚀 Starting The Empire Scraper...")
    all_links = []
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10).text
            if "vless://" not in r and "vmess://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            all_links.extend(re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', r))
        except: continue
    
    unique_links = list(set(all_links))
    random.shuffle(unique_links)
    
    chosen_oodi = random.choice(OODI_HOSTS)
    packages = [
        {"host": VOXI_HOST[0], "name": VOXI_HOST[1], "ssl": True},
        {"host": chosen_oodi[0], "name": chosen_oodi[1], "ssl": False},
        {"host": ZAIN_KAFO_HOST[0], "name": ZAIN_KAFO_HOST[1], "ssl": False}
    ]

    posted = 0
    for link in unique_links:
        if posted >= 3: break
        
        # استخراج الهوست والبورت للفحص
        if "vmess://" in link:
            try:
                data = json.loads(base64.b64decode(link.split("://")[1]).decode('utf-8'))
                host, port = data['add'], data['port']
            except: continue
        else:
            match = re.search(r'@([^:/]+):(\d+)', link)
            if not match: continue
            host, port = match.group(1), match.group(2)

        ping = check_ping(host, port)
        if ping:
            geo = get_geo(socket.gethostbyname(host)) if ping < 200 else "🌍 Global"
            pkg = packages[posted]
            
            # حقن الهوست حسب النوع
            if "vmess://" in link:
                final_link = fix_vmess(link, pkg['host'])
            else:
                final_link = clean_vless(link, pkg['host'], pkg['ssl'])
            
            header = "🔥 <b>ULTRA FAST SERVER</b> 🔥" if ping < 90 else "✨ <b>Welcome to Ashaq Team</b> ✨"
            
            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"🌍 <b>Country:</b> {geo}\n"
            msg += f"📦 <b>Package:</b> {pkg['name']}\n"
            msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 Ultra Stable\n"
            msg += f"🛡️ <b>SSL:</b> {'Enabled ✅' if pkg['ssl'] else 'Disabled 🔓'}\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷️ <b>Tags:</b> #Ashaq_Team #Alpha\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{final_link}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": [
                    [{"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"}],
                    [{"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER}"}]
                ]}
            })
            posted += 1
            time.sleep(7)

if __name__ == "__main__":
    post_process()
