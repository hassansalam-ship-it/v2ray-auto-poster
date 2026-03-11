import requests
import os
import re
import base64
import random
import socket

# الإعدادات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
BLOCKED_COUNTRIES = ['IR', 'CN', 'RU']
VPS_KEYWORDS = ['oracle', 'digitalocean', 'hetzner', 'ovh', 'linode', 'vultr', 'aws', 'amazon', 'google', 'azure', 'vps']

TG_CHANNELS = [
    "oneclickvpnkeys", "ConfigsHUB", "Outline_ir", 
    "vpnfail_v2ray", "vpnfail_vless", "v2rayngte", "Outline_Vpn"
]

def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,countryCode,isp", timeout=5).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', ''

def is_vps(isp_name, config_name):
    full_text = f"{isp_name} {config_name}".lower()
    return any(key in full_text for key in VPS_KEYWORDS)

def is_alive_and_safe(config):
    try:
        match = re.search(r'@([^:/]+):(\d+)', config)
        if match:
            host, port = match.group(1), int(match.group(2))
            ip = socket.gethostbyname(host)
            country, isp = get_ip_info(ip)
            if country in BLOCKED_COUNTRIES: return False, False
            with socket.create_connection((host, port), timeout=3):
                return True, is_vps(isp, config)
    except: pass
    return False, False

def fetch_all():
    found = []
    # سحب من التليجرام (واجهة الويب)
    for ch in TG_CHANNELS:
        try:
            res = requests.get(f"https://t.me/s/{ch}", timeout=10)
            found.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s#"\'<>]+', res.text))
        except: continue
    # سحب من GitHub والمصادر العالمية
    sources = [
        "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
        "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
        "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
    ]
    for src in sources:
        try:
            r = requests.get(src, timeout=10).text
            found.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s]+', r))
        except: continue
    return list(set(found))

def send_alert(message):
    """إرسال تنبيه لك في حال توقف السكربت أو فشله"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": f"⚠️ <b>تنبيه من بوت فريق عشق:</b>\n{message}", "parse_mode": "HTML"})

def post_process():
    try:
        all_found = fetch_all()
        if not all_found:
            send_alert("لم يتم العثور على أي سيرفرات في المصادر حالياً!")
            return

        # ترتيب الأولويات: Vmess/Vless أولاً ثم Trojan
        v_configs = [c for c in all_found if c.startswith(('vmess', 'vless'))]
        t_configs = [c for c in all_found if c.startswith('trojan')]
        random.shuffle(v_configs)
        random.shuffle(t_configs)
        
        final_list = v_configs + t_configs
        posted = 0
        
        for config in final_list:
            if posted >= 2: break
            alive, vps_flag = is_alive_and_safe(config)
            if alive:
                ctype = "Vmess" if "vmess" in config else "Vless" if "vless" in config else "Trojan"
                vps_tag = "🚀 (High Speed VPS)" if vps_flag else "✅ (Premium)"
                
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n━━━━━━━━━━━━━━━\n"
                msg += f"<b>🔹 Type:</b> {ctype} {vps_tag}\n"
                msg += f"<b>🔹 Online Status:</b> Online Tested 🟢\n\n"
                msg += f"<code>{config}</code>\n\n"
                msg += f"👥 @V2rayashaq"
                
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                              data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                posted += 1
        
        if posted == 0:
            send_alert("تم العثور على سيرفرات ولكن جميعها فشلت في فحص الاتصال (Offline)!")

    except Exception as e:
        send_alert(f"حدث خطأ برمي مفاجئ: {str(e)}")

if __name__ == "__main__":
    post_process()
