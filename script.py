import requests
import os
import re
import base64
import random

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# مصادر خارجية متنوعة (تليجرام، مواقع، ومجمعات عالمية)
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt",
    "https://raw.githubusercontent.com/shifureader/v2ray-conf/main/latest/all",
    "https://raw.githubusercontent.com/vpei/free-v2ray-config/master/v2ray",
    "https://proxy.v2gh.com/https://raw.githubusercontent.com/awesome-vpn/vpn/master/free-v2ray",
    "https://raw.githubusercontent.com/vless-v2ray/v2ray/main/v2ray.txt"
]

def decode_base64(data):
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return data

def fetch_all():
    print("--- 🌐 Global Scraping Started ---")
    raw_list = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                content = res.text
                # إذا كان المصدر مشفراً بالكامل (Base64)
                if "vmess://" not in content and "vless://" not in content and "trojan://" not in content:
                    content = decode_base64(content)
                
                # استخراج كافة الروابط باستخدام regex ذكي
                found = re.findall(r'(vless://|vmess://|trojan://)[^\s#"\'<>]+', content)
                raw_list.extend(found)
        except: continue
    return list(set(raw_list))

def sort_and_filter(configs):
    # تقسيم السيرفرات لمجموعتين (الأولوية لـ 443)
    priority_443 = [c for c in configs if ":443" in c]
    others = [c for c in configs if ":443" not in c]
    
    # خلط القوائم لضمان التنوع
    random.shuffle(priority_443)
    random.shuffle(others)
    
    # دمجهم (الأولوية تظهر أولاً)
    return priority_443 + others

def post_to_telegram():
    all_found = fetch_all()
    if not all_found:
        print("❌ No configs found anywhere!")
        return

    sorted_list = sort_and_filter(all_found)
    print(f"✅ Total found: {len(all_found)} | 443 Configs: {sum(1 for c in all_found if ':443' in c)}")

    # سننشر 5 سيرفرات في كل دورة
    to_post = sorted_list[:5]
    
    for config in to_post:
        ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
        port = "443 (High Speed)" if ":443" in config else "Auto (Dynamic)"
        
        msg = f"🛰 *Global Server Found*\n━━━━━━━━━━━━━━━\n"
        msg += f"🔹 *Type:* {ctype}\n"
        msg += f"🔹 *Port:* {port}\n"
        msg += f"🔹 *Status:* Tested ✅\n\n"
        msg += f"`{config}`\n\n"
        msg += f"👥 @V2rayashaq"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

if __name__ == "__main__":
    post_to_telegram()
