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
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU']
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba']

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vmess.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/trojan.txt",
    "https://t.me/s/v2rayngte", "https://t.me/s/Outline_Vpn", "https://t.me/s/ConfigsHUB",
    "https://t.me/s/oneclickvpnkeys", "https://t.me/s/v2ray_outline_config", "https://t.me/s/v2_team"
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
    tags = []
    if ms < 120: tags.append("#Gaming")
    if is_vps: tags.append("#Streaming")
    if ms < 200: tags.append("#Fast")
    tags.append("#Free_VPN")
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

def send_with_buttons(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [
                    {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                    {"text": "🛠 Help", "url": "https://t.me/V2rayashaq/1"}
                ],
                [{"text": "👤 Support", "url": "https://t.me/YourUsername"}]
            ]
        })
    }
    requests.post(url, json=payload)

def post_process():
    try:
        all_found = fetch_mega()
        if not all_found: return
        v_list = [c for c in all_found if c.startswith(('vmess', 'vless'))]
        t_list = [c for c in all_found if c.startswith('trojan')]
        
        def sort_logic(lst):
            p443 = [c for c in lst if ":443" in c]; others = [c for c in lst if ":443" not in c]
            random.shuffle(p443); random.shuffle(others)
            return p443 + others

        final_list = sort_logic(v_list) + sort_logic(t_list)
        posted = 0
        for config in final_list:
            if posted >= 4: break
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
                
                send_with_buttons(msg)
                posted += 1
    except: pass

if __name__ == "__main__":
    post_process()
