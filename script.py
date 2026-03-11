import requests
import os
import re
import base64
import random
import socket
import time
import json

# إعدادات البوت والقناة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU']
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba', 'cloudfront', 'cloudflare']

# إضافة 20 مصدر جديد متخصص في CloudFront و CDN
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/clash-verge-rev/clash-verge-rev/main/free_configs.txt",
    "https://t.me/s/v2rayngte", "https://t.me/s/Outline_Vpn", "https://t.me/s/ConfigsHUB",
    "https://t.me/s/oneclickvpnkeys", "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha",
    "https://t.me/s/Cloudfront_VPN", "https://t.me/s/CDN_V2RAY"
]

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
        with socket.create_connection((host, port), timeout=2):
            return int((time.time() - start) * 1000)
    except: return None

def is_cloudfront(config):
    """فحص إذا كان السيرفر يدعم CloudFront أو CDN"""
    cf_keywords = ['cloudfront', 'cdn', 'worker', 'pages.dev', 'nodes.com']
    return any(key in config.lower() for key in cf_keywords)

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
                vps = any(p in f"{isp} {config}".lower() for p in VPS_PROVIDERS) or is_cloudfront(config)
                return {"cc": cc, "country": country, "ms": ms, "vps": vps, "cf": is_cloudfront(config)}
    except: pass
    return None

def fetch_mega():
    found = []
    for url in SEARCH_SOURCES:
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
        all_found = fetch_mega()
        if not all_found: return
        
        # تصفية وأولوية (بورت 443 + بروتوكول + CloudFront)
        v_list = [c for c in all_found if c.startswith(('vmess', 'vless'))]
        t_list = [c for c in all_found if c.startswith('trojan')]
        
        def sort_logic(lst):
            # الأولوية القصوى: بورت 443 مع CloudFront
            cf_443 = [c for c in lst if ":443" in c and is_cloudfront(c)]
            normal_443 = [c for c in lst if ":443" in c and not is_cloudfront(c)]
            others = [c for c in lst if ":443" not in c]
            random.shuffle(cf_443); random.shuffle(normal_443); random.shuffle(others)
            return cf_443 + normal_443 + others

        final_list = sort_logic(v_list) + sort_logic(t_list)
        
        posted = 0
        for config in final_list:
            if posted >= 4: break
            data = is_alive_and_safe(config)
            if data:
                proto = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
                # إذا كان CloudFront نضع له شعار البرق
                cf_tag = "CloudFront ⚡" if data['cf'] else ""
                type_label = f"{proto} {cf_tag} VPS 🚀" if data['vps'] else f"{proto} {cf_tag}"
                
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>🌍 Country:</b> ({data['cc']}) {data['country']}\n"
                msg += f"<b>🔹 Type:</b> {type_label}\n"
                msg += f"<b>⚡ Ping:</b> {data['ms']}ms\n"
                msg += f"<b>⭐ Rating:</b> ⭐⭐⭐⭐⭐ (Pro Choice)\n"
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
