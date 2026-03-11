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
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU'] # الدول المحظورة
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba', 'hostinger', 'cloudflare']

# 100+ مصدر عالمي متجدد (VPS ومصادر خاصة)
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vmess.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/trojan.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/trojan",
    "https://raw.githubusercontent.com/ts-sf/sh_v2ray/main/v2ray.txt",
    "https://t.me/s/v2rayngte", "https://t.me/s/Outline_Vpn", "https://t.me/s/ConfigsHUB",
    "https://t.me/s/oneclickvpnkeys", "https://t.me/s/v2ray_outline_config", "https://t.me/s/v2_team",
    "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess"
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

def get_tags(ms, is_vps):
    tags = ["#Ashaq_Team", "#Free_VPN"]
    if ms and ms < 120: tags.append("#Gaming")
    if is_vps: tags.append("#High_Speed_VPS")
    return " ".join(tags)

def get_rating(ms, is_vps):
    if ms < 100 and is_vps: return "⭐⭐⭐⭐⭐ (Gaming Pro)"
    if ms < 150: return "⭐⭐⭐⭐ (High Speed)"
    return "⭐⭐⭐ (Stable)"

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
                return {"cc": cc, "country": country, "ms": ms, "vps": vps}
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
        
        # تقسيم السيرفرات حسب النوع لضمان الأولوية
        v_list = [c for c in all_found if c.startswith(('vmess', 'vless'))]
        t_list = [c for c in all_found if c.startswith('trojan')]
        
        def sort_logic(lst):
            p443 = [c for c in lst if ":443" in c]; others = [c for c in lst if ":443" not in c]
            random.shuffle(p443); random.shuffle(others)
            return p443 + others

        # الترتيب: Vless/Vmess (بورت 443 ثم البقية) ثم Trojan (بورت 443 ثم البقية)
        final_list = sort_logic(v_list) + sort_logic(t_list)
        
        posted = 0
        for config in final_list:
            if posted >= 4: break # نشر 4 سيرفرات في كل دورة
            data = is_alive_and_safe(config)
            if data:
                proto = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
                type_label = f"{proto} VPS 🚀" if data['vps'] else proto
                rating = get_rating(data['ms'], data['vps'])
                tags = get_tags(data['ms'], data['vps'])
                
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>🌍 Country:</b> ({data['cc']}) {data['country']}\n"
                msg += f"<b>🔹 Type:</b> {type_label}\n"
                msg += f"<b>⚡ Ping:</b> {data['ms']}ms\n"
                msg += f"<b>⭐ Rating:</b> {rating}\n"
                msg += f"<b>🕒 Checked:</b> Just Now\n"
                msg += f"<b>🏷 Tags:</b> {tags}\n"
                msg += f"<b>🔹 Port:</b> {'443 (Ultra Fast)' if ':443' in config else 'Stable'}\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"
                
                # رابط النسخ السريع الذكي
                copy_url = f"https://t.me/share/url?url={config}"
                
                payload = {
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps({
                        "inline_keyboard": [
                            [
                                {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                                {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"}
                            ],
                            [{"text": "📋 Click here to Copy", "url": copy_url}]
                        ]
                    })
                }
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)
                posted += 1
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    post_process()
