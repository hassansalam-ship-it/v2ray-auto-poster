import requests
import os
import re
import base64

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt",
    "https://raw.githubusercontent.com/shifureader/v2ray-conf/main/latest/all"
]

def decode_base64(data):
    try:
        return base64.b64decode(data).decode('utf-8')
    except:
        return data

def fetch_and_post():
    print("--- Starting Ultra Fetch & Decode ---")
    raw_configs = []
    
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                content = res.text
                # محاولة فك التشفير إذا كان الرابط Base64
                if "vmess://" not in content and "vless://" not in content:
                    content = decode_base64(content)
                
                found = re.findall(r'(vless://|vmess://|trojan://)[^\s]+', content)
                raw_configs.extend(found)
        except: continue

    # تصفية السيرفرات: بورت 443 أو بورتات قوية أخرى
    final_configs = []
    for link in list(set(raw_configs)):
        if any(port in link for port in [":443", ":2053", ":2083", ":8443", ":2096"]):
            final_configs.append(link)

    print(f"Total High-Speed Configs Found: {len(final_configs)}")

    if final_configs:
        import random
        # نشر 3 سيرفرات متنوعة
        selected = random.sample(final_configs, min(len(final_configs), 3))
        for config in selected:
            ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
            msg = f"⚡️ *High Speed Config*\n━━━━━━━━━━━━━━━\n🔹 *Type:* {ctype}\n🔹 *Port:* Secure ✅\n\n`{config}`\n\n👥 Join: @V2rayashaq"
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        print("✅ Success! Check your channel.")
    else:
        print("❌ No configs found. I will try a special bypass next time.")

if __name__ == "__main__":
    fetch_and_post()
