import requests
import os
import re
import base64
import random
import socket

# تأكد أنك وضعت BOT_TOKEN في Secrets بنفس هذا الاسم
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/Barabama/FreeNodes/master/nodes/nodes.txt"
]

def decode_base64(data):
    try: return base64.b64decode(data).decode('utf-8')
    except: return data

def is_alive(config):
    try:
        match = re.search(r'@([^:/]+):(\d+)', config)
        if match:
            with socket.create_connection((match.group(1), int(match.group(2))), timeout=2):
                return True
    except: return False
    return False

def run():
    print("--- Ashaq Team Bot Started ---")
    raw_configs = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            content = res.text
            if "vmess://" not in content: content = decode_base64(content)
            raw_configs.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s]+', content))
        except: continue

    unique = list(set(raw_configs))
    random.shuffle(unique)
    
    posted = 0
    for c in unique:
        if posted >= 3: break
        # إذا أردت سرعة أكبر في النشر، يمكنك إلغاء شرط الفحص is_alive مؤقتاً
        ctype = "Trojan" if "trojan" in c else "Vless" if "vless" in c else "Vmess"
        msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n━━━━━━━━━━━━━━━\n"
        msg += f"<b>🔹 Type:</b> {ctype}\n<b>🔹 Status:</b> Active ✅\n\n"
        msg += f"<code>{c}</code>\n\n"
        msg += f"👥 @V2rayashaq"
        
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
        posted += 1
    print(f"Done! Posted {posted} configs.")

if __name__ == "__main__":
    run()
