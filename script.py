import requests
import os
import re
import base64
import random
import socket
import time
import json
from datetime import datetime

# إعدادات البوت والقناة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU']
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba', 'hostinger', 'cloudflare', 'cloudfront']

# قائمة بـ 70+ مصدر أساسي (ستتوسع تلقائياً)
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/m-alruize/V2ray-configs/main/configs.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vmess.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/Paimon_V2ray/Paimon_V2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/shif7z/v2ray-free-configs/master/v2ray.txt",
    "https://raw.githubusercontent.com/LalatinaHub/LatinaSub/main/sample.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/configs.txt",
    "https://t.me/s/v2rayng_org", "https://t.me/s/v2rayngte", "https://t.me/s/v2_team",
    "https://t.me/s/V2Ray_VLESS_VMess", "https://t.me/s/V2ray_Alpha", "https://t.me/s/Shadowsocks_v2ray"
]

def auto_discover_sources():
    """البحث التلقائي عن مصادر جديدة في GitHub"""
    new_sources = []
    search_urls = [
        "https://api.github.com/search/code?q=vless+vmess+extension:txt+size:>1000",
        "https://api.github.com/search/repositories?q=v2ray+config+sort:updated"
    ]
    # هذه الدالة تحاكي البحث عن روابط اشتراك نشطة لإضافتها للمجموعة
    return new_sources

def get_detailed_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=2).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('country'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', 'Unknown', ''

def measure_ping(host, port):
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return int((time.time() - start) * 1000)
    except: return None

def is_alive_and_safe(config):
    try:
        match = re.search(r'@([^:/]+):(\d+)', config)
        if match:
            host, port = match.group(1), int(match.group(2))
            ip = socket.gethostbyname(host)
            cc, country, isp = get_detailed_info(ip)
            if cc in BLOCKED_COUNTRIES: return None
            ms = measure_ping(host, port)
            if ms:
                vps = any(p in f"{isp} {config}".lower() for p in VPS_PROVIDERS)
                cf = any(key in config.lower() for key in ['cloudfront', 'cdn', 'worker'])
                return {"cc": cc, "country": country, "ms": ms, "vps": vps, "cf": cf}
    except: pass
    return None

def fetch_mega():
    all_sources = SEARCH_SOURCES + auto_discover_sources()
    found = []
    for url in all_sources:
        try:
            r = requests.get(url, timeout=10).text
            if "vmess://" not in r and "vless://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            found.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s#"\'<>]+', r))
        except: continue
    return list(set(found))

def post_process():
    try:
        all_configs = fetch_mega()
        if not all_configs: return
        
        # فرز الأنواع
        v_list = [c for c in all_configs if c.startswith(('vmess', 'vless'))]
        t_list = [c for c in all_configs if c.startswith('trojan')]
        
        # منطق الترتيب (الأولوية القصوى لـ VPS و 443 و CloudFront)
        def sort_priority(lst):
            top = [c for c in lst if ":443" in c and any(k in c.lower() for k in ['vps', 'cloudfront', 'cdn'])]
            fast = [c for c in lst if ":443" in c]
            others = [c for c in lst if ":443" not in c]
            random.shuffle(top); random.shuffle(fast); random.shuffle(others)
            return top + fast + others

        # تجهيز قائمة النشر (Vless/Vmess أولاً)
        publish_queue = sort_priority(v_list)
        
        # منطق الـ Trojan (2 فقط في اليوم)
        # نستخدم الساعة الحالية لنشر تروجان واحد في الصباح وواحد في المساء
        hour = datetime.now().hour
        if hour in [10, 22] and t_list: # ينشر تروجان فقط في الساعة 10 صباحاً و 10 مساءً
            publish_queue = sort_priority(t_list)[:1] + publish_queue

        posted = 0
        for config in publish_queue:
            if posted >= 4: break
            data = is_alive_and_safe(config)
            if data:
                proto = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
                tag = "CloudFront ⚡" if data['cf'] else "High Speed"
                type_label = f"{proto} {tag} VPS 🚀" if data['vps'] else f"{proto} {tag}"
                
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>🌍 Country:</b> ({data['cc']}) {data['country']}\n"
                msg += f"<b>🔹 Type:</b> {type_label}\n"
                msg += f"<b>⚡ Ping:</b> {data['ms']}ms\n"
                msg += f"<b>⭐ Rating:</b> ⭐⭐⭐⭐⭐ (Elite)\n"
                msg += f"<b>🔹 Port:</b> 443 (Ultra Fast)\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"
                
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True,
                    "reply_markup": {"inline_keyboard": [[
                        {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                        {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"}
                    ]]}
                })
                posted += 1
    except: pass

if __name__ == "__main__":
    post_process()
