import requests
import os
import re
import base64
import random
import socket
import time
import json

# الإعدادات
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"

SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha"
]

def get_detailed_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=2).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('country')
    except: pass
    return 'Unknown', 'Unknown'

def measure_stability(host, port):
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=1.5):
            return int((time.time() - start) * 1000)
    except: return None

def post_process():
    try:
        all_configs = []
        for url in SEARCH_SOURCES:
            try:
                r = requests.get(url, timeout=10).text
                if "vmess://" not in r and "vless://" not in r:
                    try: r = base64.b64decode(r).decode('utf-8')
                    except: pass
                all_configs.extend(re.findall(r'(?:vless|vmess|trojan)://[^\s#"\'<>]+', r))
            except: continue
        
        all_configs = list(set(all_configs))
        # تصفية وأولوية (Vless/Vmess أولاً ثم Trojan)
        v_list = [c for c in all_configs if c.startswith(('vmess', 'vless'))]
        t_list = [c for c in all_configs if c.startswith('trojan')]
        publish_queue = sorted(v_list, key=lambda x: ":443" not in x) + sorted(t_list, key=lambda x: ":443" not in x)
        
        posted = 0
        for config in publish_queue:
            if posted >= 4: break
            
            match = re.search(r'@([^:/]+):(\d+)', config)
            if not match: continue
            
            host, port = match.group(1), int(match.group(2))
            ms = measure_stability(host, port)
            
            if ms:
                ip = socket.gethostbyname(host)
                cc, country = get_detailed_info(ip)
                
                # تقييم النجوم حسب السرعة
                stars = "⭐⭐⭐⭐⭐" if ms < 150 else "⭐⭐⭐"
                rating_text = "(Elite)" if ms < 150 else "(Stable)"
                
                # تنسيق الرسالة كما في الصورة تماماً
                msg = f"✨ <b>Welcome to Ashaq Team</b> ✨\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"🌍 <b>Country:</b> ({cc}) {country}\n"
                msg += f"🔹 <b>Type:</b> {'Trojan' if config.startswith('trojan') else 'Vless/Vmess'}\n"
                msg += f"⚡ <b>Ping:</b> {ms}ms\n"
                msg += f"⭐ <b>Rating:</b> {stars} {rating_text}\n"
                msg += f"🕒 <b>Checked:</b> Just Now\n"
                msg += f"🏷 <b>Tags:</b> #Ashaq_Team #Free_VPN\n" # التاكات المطلوبة
                msg += f"🔹 <b>Port:</b> 443 (Ultra Fast)\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"👥 @V2rayashaq"

                # إرسال المنشور الجديد
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "reply_markup": {
                        "inline_keyboard": [[
                            {"text": "📢 Join Channel", "url": "https://t.me/V2rayashaq"},
                            {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"}
                        ]]
                    }
                })
                posted += 1
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    post_process()
