import requests
import os
import re

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# قائمة مصادر ضخمة (مجمعات سيرفرات عالمية)
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt",
    "https://raw.githubusercontent.com/mizhen991/V2RayCloud/main/V2RayCloud",
    "https://raw.githubusercontent.com/shifureader/v2ray-conf/main/latest/all",
    "https://raw.githubusercontent.com/vpei/free-v2ray-config/master/v2ray",
    "https://raw.githubusercontent.com/awesome-vpn/vpn/master/free-v2ray",
    "https://raw.githubusercontent.com/w1770946466/Auto_Proxy/main/Long_Term_Proxy_Sub",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config",
    "https://raw.githubusercontent.com/vless-v2ray/v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/Elepworld/v2ray-free/main/v2ray.txt"
]

def fetch_and_post():
    print("--- Starting Mega Fetch ---")
    all_configs = []
    
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                # استخراج السيرفرات التي تبدأ بالأنواع المطلوبة
                found = re.findall(r'(vless://|vmess://|trojan://)[^\s]+', res.text)
                for link in found:
                    # التحقق من بورت 443
                    if ":443" in link:
                        all_configs.append(link)
        except:
            continue

    # إزالة التكرار
    unique_configs = list(set(all_configs))
    print(f"Total Unique 443 Configs Found: {len(unique_configs)}")

    if unique_configs:
        # سننشر أفضل 5 سيرفرات عشوائية من القائمة الضخمة في كل دورة (كل 50 دقيقة)
        import random
        selected = random.sample(unique_configs, min(len(unique_configs), 5))
        
        for config in selected:
            ctype = "Trojan" if "trojan" in config else "Vless" if "vless" in config else "Vmess"
            msg = f"🌟 *Premium Config (Port 443)*\n\n🔹 *Type:* {ctype}\n🔹 *Status:* Active ✅\n\n`{config}`\n\n👥 Join: @V2rayashaq"
            
            send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(send_url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    else:
        print("❌ No matching configs found this time.")

if __name__ == "__main__":
    fetch_and_post()
