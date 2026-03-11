import requests
import os
import re
import base64
import random
import socket
from datetime import datetime

# الإعدادات الأساسية
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# القنوات والمصادر التي طلبتها (بصيغة ويب ليسحب منها الكود)
TG_CHANNELS = [
    "oneclickvpnkeys", "ConfigsHUB", "Outline_ir", 
    "vpnfail_v2ray", "vpnfail_vless", "v2rayngte", "Outline_Vpn"
]

SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
]

def is_alive(config):
    """فحص الاتصال الحقيقي بالسيرفر"""
    try:
        host_port = re.search(r'@([^:/]+):(\d+)', config)
        if host_port:
            host, port = host_port.group(1), int(host_port.group(2))
            with socket.create_connection((host, port), timeout=3):
                return True
    except: return False
    return False

def fetch_from_telegram():
    """صيد السيرفرات من قنوات التليجرام المحددة"""
    found_configs = []
    for channel in TG_CHANNELS:
        try:
            url = f"https://t.me/s/{channel}" # واجهة الويب للقناة
            res = requests.get(url, timeout=15)
            configs = re.findall(r'(?:vless|vmess|trojan)://[^\s#"\'<>]+', res.text)
            found_configs.extend(configs)
        except: continue
    return found_configs

def post_process():
    print(f"--- Ashaq Pro System Started: {datetime.now()} ---")
    
    # جمع السيرفرات من كل مكان
    all_configs = fetch_from_telegram()
    for src in SOURCES:
        try:
            r = requests.get(src, timeout=10)
            all_configs.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s]+', r.text))
        except: continue

    unique_configs = list(set(all_configs))
    
    # الأولوية لبورت 443
    priority_443 = [c for c in unique_configs if ":443" in c]
    others = [c for c in unique_configs if ":443" not in c]
    random.shuffle(priority_443)
    random.shuffle(others)
    
    final_list = priority_443 + others
    posted = 0
    
    for config in final_list:
        if posted >= 2: break # نشر سيرفرين فقط كل نصف ساعة كما طلبت
        
        if is_alive(config):
            ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
            port = "443" if ":443" in config else "Dynamic"
            
            msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<b>🔹 Type:</b> {ctype}\n"
            msg += f"<b>🔹 Port:</b> {port}\n"
            msg += f"<b>🔹 Online Status:</b> Tested 🟢\n\n" # الحالة خضراء عند النشر
            msg += f"<code>{config}</code>\n\n"
            msg += f"👥 @V2rayashaq"
            
            # إرسال الرسالة وحفظ الـ ID إذا أردت التعديل لاحقاً (تحتاج قاعدة بيانات للتعديل التلقائي)
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
            posted += 1

if __name__ == "__main__":
    post_process()
