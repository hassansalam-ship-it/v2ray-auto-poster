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
# --- إعدادات الدومين ---
MY_DOMAIN = "predator666h.duckdns.org"
DUCK_TOKEN = "e6e3c545-6677-4b7b-83c3-37651c6c518b" # توكن DuckDNS الخاص بك

# --- الباقات ---
OODI_HOSTS = [
    ("m.tiktok.com", "Oodi | TikTok 🎵"), ("m.youtube.com", "Oodi | YouTube 🎥"),
    ("m.instagram.com", "Oodi | Instagram 📸"), ("web.whatsapp.com", "Oodi | WhatsApp 🟢")
]
VOXI_HOST = ("downloads.vodafone.co.uk", "Voxi UK 🇬🇧")
ZAIN_KAFO_HOST = ("m.tiktok.com", "Zain كفو 💎")

SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def update_dns(ip):
    try:
        requests.get(f"https://www.duckdns.org/update?domains=predator666h&token={DUCK_TOKEN}&ip={ip}", timeout=5)
    except: pass

def check_443(host):
    try:
        start = time.time()
        with socket.create_connection((host, 443), timeout=1.2):
            return int((time.time() - start) * 1000)
    except: return None

def get_geo(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=country,countryCode", timeout=2).json()
        return f"({r['countryCode']}) {r['country']}"
    except: return "🌍 Global"

def inject_config(link, sni, address, use_ssl):
    # معالجة Vmess
    if "vmess://" in link:
        try:
            data = json.loads(base64.b64decode(link.split("://")[1]).decode('utf-8'))
            data['add'], data['port'], data['sni'], data['host'] = address, 443, sni, sni
            return f"vmess://{base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')}"
        except: return None
    # معالجة Vless
    link = re.sub(r'@([^:/]+):', f'@{address}:', link)
    link = re.sub(r':\d+@', ':443@', link)
    link = re.sub(r'[?&](sni|host|security)=[^&]*', '', link)
    sep = "&" if "?" in link else "?"
    link += f"{sep}sni={sni}&host={sni}"
    if use_ssl: link += "&security=tls"
    return link.replace('&amp;', '&')

def post_process():
    all_raw = []
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10).text
            if "vless://" not in r and "vmess://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            all_raw.extend(re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', r))
        except: continue
    
    unique = list(set(all_raw))
    random.shuffle(unique)
    
    chosen_oodi = random.choice(OODI_HOSTS)
    packages = [
        {"host": VOXI_HOST[0], "name": VOXI_HOST[1], "ssl": True, "use_domain": True},
        {"host": chosen_oodi[0], "name": chosen_oodi[1], "ssl": False, "use_domain": False},
        {"host": ZAIN_KAFO_HOST[0], "name": ZAIN_KAFO_HOST[1], "ssl": False, "use_domain": False}
    ]

    posted = 0
    for link in unique:
        if posted >= 3: break
        
        # استخراج الهوست الأصلي
        if "vmess://" in link:
            try: host = json.loads(base64.b64decode(link.split("://")[1]).decode('utf-8'))['add']
            except: continue
        else:
            match = re.search(r'@([^:/]+):', link)
            if not match: continue
            host = match.group(1)

        ping = check_443(host)
        if ping:
            pkg = packages[posted]
            ip = socket.gethostbyname(host)
            
            # إذا كان فوكسي، نحدث الدومين ونستخدمه
            if pkg['use_domain']:
                update_dns(ip)
                target_address = MY_DOMAIN
                time.sleep(1)
            else:
                target_address = ip # البقية IP مباشر
            
            final_link = inject_config(link, pkg['host'], target_address, pkg['ssl'])
            if not final_link: continue

            geo = get_geo(ip)
            header = "👑 <b>DOMAIN EDITION</b> 👑" if pkg['use_domain'] else "🔥 <b>ULTRA FAST SERVER</b> 🔥"
            
            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"🌍 <b>Country:</b> {geo}\n"
            msg += f"📦 <b>Package:</b> {pkg['name']}\n"
            msg += f"⚡ <b>Ping:</b> {ping}ms | 🟢 443 Only\n"
            msg += f"🛡️ <b>SSL:</b> {'Enabled ✅' if pkg['ssl'] else 'Disabled 🔓'}\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{final_link}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML",
                "reply_markup": {"inline_keyboard": [[{"text": "📢 Join", "url": "https://t.me/V2rayashaq"}],[{"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER}"}]]}
            })
            posted += 1
            time.sleep(7)

if __name__ == "__main__":
    post_process()
