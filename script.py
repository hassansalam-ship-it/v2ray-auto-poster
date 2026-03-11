import requests
import os
import re
import base64
import random
import socket
import time
import json
from datetime import datetime

# الإعدادات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba', 'cloudfront']

# المصادر
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess"
]

def get_detailed_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=2).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('country'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', 'Unknown', ''

def measure_stability(host, port):
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return int((time.time() - start) * 1000)
    except: return None

def post_process():
    try:
        all_configs = []
        for url in SEARCH_SOURCES:
            try:
                r = requests.get(url, timeout=10).text
                if "vmess://" not in r and "vless://" not in r:
                    try: r = base64.b64decode(r).decode('utf-8')
                    except: pass
                all_configs.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s#"\'<>]+', r))
            except: continue
        
        all_configs = list(set(all_configs))
        v_list = [c for c in all_configs if c.startswith(('vmess', 'vless'))]
        
        posted = 0
        for config in v_list:
            if posted >= 4: break
            
            match = re.search(r'@([^:/]+):(\d+)', config)
            if not match: continue
            
            host, port = match.group(1), int(match.group(2))
            ms = measure_stability(host, port)
            
            if ms:
                ip = socket.gethostbyname(host)
                cc, country, isp = get_detailed_info(ip)
                
                # إعدادات زر الهوست المخصص
                # نستخدم رابط "المشاركة" لتسهيل دمج الهوست يدوياً للمستخدم
                custom_host_url = f"https://t.me/share/url?url={config}%0A%0A--%20Edit%20SNI/Host%20Below%20--"
                
                msg = f"🚨 <b>ELITE ASHAQ CONFIG</b> 🚨\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>🌍 Country:</b> ({cc}) {country}\n"
                msg += f"<b>⚡ Ping:</b> {ms}ms | 🟢 Online\n"
                msg += f"<b>📦 Formats:</b> #NPTV #HTTP_Custom #Dark\n"
                msg += f"<b>🛠 Feature:</b> Supports Custom Host ✅\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML",
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {"text": "📢 Join", "url": "https://t.me/V2rayashaq"},
                                {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"},
                                {"text": "🛠 Custom Host", "url": custom_host_url}
                            ]
                        ]
                    }
                })
                posted += 1
    except: pass

if __name__ == "__main__":
    post_process()
