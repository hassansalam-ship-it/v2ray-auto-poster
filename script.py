import requests
import os
import re
import base64
import random
import socket

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# مصادر عملاقة تشمل تليجرام ومواقع خارجية وجيت هاب
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt",
    "https://raw.githubusercontent.com/shifureader/v2ray-conf/main/latest/all",
    "https://raw.githubusercontent.com/vpei/free-v2ray-config/master/v2ray"
]

def decode_base64(data):
    try: return base64.b64decode(data).decode('utf-8')
    except: return data

def is_server_alive(config):
    """فحص سريع للسيرفر قبل النشر للتأكد من أنه شغال"""
    try:
        # استخراج العنوان والبورت من الرابط
        host_port = re.search(r'@([^:/]+):(\int+)', config)
        if host_port:
            host, port = host_port.group(1), int(host_port.group(2))
            with socket.create_connection((host, port), timeout=2):
                return True
    except: return False
    return False

def fetch_all():
    raw_list = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                content = res.text
                if not any(x in content for x in ["vmess://", "vless://", "trojan://"]):
                    content = decode_base64(content)
                found = re.findall(r'(?:vless|vmess|trojan)://[^\s]+', content)
                raw_list.extend(found)
        except: continue
    return list(set(raw_list))

def post_to_telegram():
    all_found = fetch_all()
    if not all_found: return

    # فلترة وتصفية (الأولوية لـ 443)
    priority_443 = [c for c in all_found if ":443" in c]
    others = [c for c in all_found if ":443" not in c]
    
    # خلط عشوائي لضمان ظهور الأنواع الثلاثة (Vmess, Vless, Trojan)
    random.shuffle(priority_443)
    random.shuffle(others)
    
    combined = priority_443 + others
    posted_count = 0
    
    for config in combined:
        if posted_count >= 4: break # سننشر 4 سيرفرات شغالة في كل دورة
        
        # فحص السيرفر قبل النشر
        if is_server_alive(config):
            ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
            port = "443 (Ultra Fast)" if ":443" in config else "High Speed"
            
            # الرسالة بالترحيب الجديد
            msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<b>🔹 Type:</b> {ctype}\n"
            msg += f"<b>🔹 Port:</b> {port}\n"
            msg += f"<b>🔹 Status:</b> Tested & Working ✅\n\n"
            msg += f"<code>{config}</code>\n\n"
            msg += f"👥 @V2rayashaq"
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
            posted_count += 1

if __name__ == "__main__":
    post_to_telegram()
