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
SUB_FILE = "sub_link.txt"

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess"
]

VPS_LIST = ['oracle', 'google', 'amazon', 'aws', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'azure', 'contabo']

def get_detailed_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=1.5).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('country'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', 'Unknown', ''

def check_server_power(host, port):
    try:
        start = time.time()
        with socket.create_connection((host, int(port)), timeout=0.7):
            return int((time.time() - start) * 1000)
    except: return None

def post_process():
    all_found = []
    for url in SEARCH_SOURCES:
        try:
            r = requests.get(url, timeout=5).text
            if "vless://" not in r and "vmess://" not in r:
                try: r = base64.b64decode(r).decode('utf-8')
                except: pass
            all_found.extend(re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', r))
        except: continue
    
    unique_configs = list(set(all_found))
    random.shuffle(unique_configs)
    
    valid_configs = []
    posted = 0
    
    for config in unique_configs[:130]:
        if posted >= 5: break 
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        ping = check_server_power(host, port)
        
        if ping:
            valid_configs.append(config)
            ip = socket.gethostbyname(host)
            cc, country, isp = get_detailed_info(ip)
            vps_status = any(v in isp for v in VPS_LIST)
            
            # 1. وسم التنبيه الخارق
            is_elite = ping < 70
            header = "🔥 <b>ELITE ULTRA SERVER</b> 🔥" if is_elite else "✨ <b>Welcome to Ashaq Team</b> ✨"
            
            # 2. فحص فك الحجب (تقديري بناءً على الـ VPS)
            streaming = "Netflix/TikTok: ✅" if vps_status else "Streaming: Standard"
            
            # 3. تقدير الضغط (Load Status)
            load_status = "Low Load 🟢 (Fastest)" if ping < 100 else "Stable Load 🟡"

            msg = f"{header}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"🌍 <b>Country:</b> ({cc}) {country}\n"
            msg += f"🔹 <b>Type:</b> {'VPS 🚀' if vps_status else 'CloudFront ⚡'}\n"
            msg += f"⚡ <b>Ping:</b> {ping}ms | {load_status}\n"
            msg += f"🎬 <b>Bypass:</b> {streaming}\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷 <b>Tags:</b> #Ashaq_Team #Free_VPN\n"
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
            time.sleep(1)

    if valid_configs:
        try:
            content = base64.b64encode("\n".join(valid_configs[:100]).encode()).decode()
            with open(SUB_FILE, "w") as f:
                f.write(content)
        except: pass

if __name__ == "__main__":
    post_process()
