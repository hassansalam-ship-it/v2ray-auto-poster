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

# خوارزمية جلب آلاف المصادر (توليد روابط تلقائي + روابط نخبة)
BASE_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess"
]

def check_active(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=1.5):
            return True
    except: return False

def deep_crawl():
    print("⛏️ جاري التنقيب في أعماق المصادر...")
    found_configs = []
    
    # محاكاة البحث في 1000 مصدر عبر دمج المجمّعات الكبرى
    for url in BASE_SOURCES:
        try:
            res = requests.get(url, timeout=15).text
            # التنقيب داخل التشفير (باطن الأرض)
            if "vless://" not in res and "vmess://" not in res:
                try: res = base64.b64decode(res).decode('utf-8')
                except: pass
            
            # استخراج النخبة فقط
            matches = re.findall(r'(?:vless|vmess)://[^\s#"\'<>]+', res)
            found_configs.extend(matches)
        except: continue
        
    return list(set(found_configs))

def post_to_ashaq():
    configs = deep_crawl()
    print(f"💎 تم استخراج {len(configs)} سيرفر من باطن الأرض.")
    
    if not configs:
        print("⚠️ الأرض قاحلة اليوم، جاري محاولة البحث في الأرشيف...")
        return

    random.shuffle(configs)
    posted = 0
    
    # فحص مكثف لأول 300 سيرفر لضمان إيجاد "ذهب" (سيرفرات شغالة)
    for config in configs[:300]:
        if posted >= 5: break
        
        match = re.search(r'@([^:/]+):(\d+)', config)
        if not match: continue
        
        host, port = match.group(1), match.group(2)
        
        if check_active(host, port):
            print(f"🚀 وجدنا صيداً ثميناً! [{host}]")
            
            msg = f"✨ <b>Alpha Project | Deep Earth</b> ✨\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"⚡ <b>Status:</b> Ultra Stable 🟢\n"
            msg += f"🛡 <b>Type:</b> Vless/Vmess\n"
            msg += f"🕒 <b>Checked:</b> Just Now\n"
            msg += f"🏷 <b>Tags:</b> #Ashaq_Team #Elite\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"<code>{config}</code>\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"👥 @V2rayashaq"

            try:
                r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
                if r.status_code == 200:
                    posted += 1
                    time.sleep(2)
            except: pass

if __name__ == "__main__":
    post_to_ashaq()
