import requests
import os
import re
import base64
import random
import socket

# الإعدادات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU'] # الدول المحظورة
# شركات الـ VPS المعروفة
VPS_PROVIDERS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps', 'contabo', 'alibaba']

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://t.me/s/oneclickvpnkeys", "https://t.me/s/ConfigsHUB", 
    "https://t.me/s/Outline_ir", "https://t.me/s/vpnfail_v2ray",
    "https://t.me/s/v2rayngte", "https://t.me/s/Outline_Vpn"
]

def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode,isp", timeout=5).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', ''

def check_vps(isp, config_name):
    """التحقق إذا كان السيرفر VPS بناءً على اسم الشركة"""
    text = f"{isp} {config_name}".lower()
    return any(provider in text for provider in VPS_PROVIDERS)

def is_alive_and_safe(config):
    try:
        match = re.search(r'@([^:/]+):(\d+)', config)
        if match:
            host, port = match.group(1), int(match.group(2))
            ip = socket.gethostbyname(host)
            country, isp = get_ip_info(ip)
            if country in BLOCKED_COUNTRIES: return False, False
            with socket.create_connection((host, port), timeout=3):
                return True, check_vps(isp, config)
    except: pass
    return False, False

def fetch_mega():
    found = []
    for url in SEARCH_SOURCES:
        try:
            r = requests.get(url, timeout=15).text
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

        # فرز: أولوية بورت 443 ثم البروتوكولات
        p443 = [c for c in all_found if ":443" in c]
        others = [c for c in all_found if ":443" not in c]
        
        def sort_logic(lst):
            v = [c for c in lst if c.startswith(('vmess', 'vless'))]
            t = [c for c in lst if c.startswith('trojan')]
            random.shuffle(v); random.shuffle(t)
            return v + t

        final_list = sort_logic(p443) + sort_logic(others)
        posted = 0
        
        for config in final_list:
            if posted >= 2: break
            alive, vps_status = is_alive_and_safe(config)
            if alive:
                proto = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
                # التعديل المطلوب: يكتب VPS فقط إذا كان فعلاً VPS
                type_label = f"{proto} VPS 🚀" if vps_status else proto
                port_label = "443 (Ultra Fast)" if ":443" in config else "Stable"
                
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n━━━━━━━━━━━━━━━\n"
                msg += f"<b>🔹 Type:</b> {type_label}\n"
                msg += f"<b>🔹 Port:</b> {port_label}\n"
                msg += f"<b>🔹 Online Status:</b> Online Tested 🟢\n\n"
                msg += f"<code>{config}</code>\n\n"
                msg += f"👥 @V2rayashaq"
                
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                posted += 1
    except: pass

if __name__ == "__main__":
    post_process()
