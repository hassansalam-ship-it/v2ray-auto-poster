import requests
import os
import re
import base64
import random

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# المصادر الشاملة
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt",
    "https://raw.githubusercontent.com/shifureader/v2ray-conf/main/latest/all"
]

def decode_base64(data):
    try: return base64.b64decode(data).decode('utf-8')
    except: return data

def fetch_all():
    raw_list = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                content = res.text
                if "vmess://" not in content and "vless://" not in content and "trojan://" not in content:
                    content = decode_base64(content)
                # استخراج السيرفر كاملاً حتى نهاية السطر
                found = re.findall(r'(?:vless|vmess|trojan)://[^\s]+', content)
                raw_list.extend(found)
        except: continue
    return list(set(raw_list))

def post_to_telegram():
    all_found = fetch_all()
    if not all_found: return

    # ترتيب حسب الأولوية لبورت 443
    priority = [c for c in all_found if ":443" in c]
    others = [c for c in all_found if ":443" not in c]
    random.shuffle(priority)
    random.shuffle(others)
    sorted_list = priority + others

    # نشر 3 سيرفرات لتجنب السبام
    to_post = sorted_list[:3]
    
    for config in to_post:
        ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
        port = "443" if ":443" in config else "Auto"
        
        # استخدام HTML لضمان ظهور الكود كاملاً وقابليته للنسخ
        msg = f"<b>🛰 Global Server Found</b>\n"
        msg += f"━━━━━━━━━━━━━━━\n"
        msg += f"<b>🔹 Type:</b> {ctype}\n"
        msg += f"<b>🔹 Port:</b> {port}\n"
        msg += f"<b>🔹 Status:</b> Tested ✅\n\n"
        msg += f"<code>{config}</code>\n\n"  # وسم code في HTML يجعل النص قابلاً للنسخ
        msg += f"👥 @V2rayashaq"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # تغيير parse_mode إلى HTML
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    post_to_telegram()
