import requests
import os
import re
import base64
import random
import socket
import time
import json
from datetime import datetime

# إعدادات البوت والقناة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"
ADMIN_USER = "@genie_2000"

# إضافة 20 مصدراً قوياً جديداً (مجموع المصادر الآن 140+)
SEARCH_SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/Iranian_Cloud/Cloudfront_V2ray/main/configs.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/peasoft/NoFilter/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/m-alruize/V2ray-configs/main/configs.txt",
    "https://raw.githubusercontent.com/Paimon_V2ray/Paimon_V2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/shif7z/v2ray-free-configs/master/v2ray.txt",
    "https://raw.githubusercontent.com/LalatinaHub/LatinaSub/main/sample.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/configs.txt",
    "https://raw.githubusercontent.com/ts-sf/sh_v2ray/main/v2ray.txt",
    "https://raw.githubusercontent.com/vpei/free-v2ray-config/master/v2ray",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vmess.txt",
    "https://raw.githubusercontent.com/SreSami/Free-V2ray-Config/main/Splitted-Configs/vless.txt",
    "https://t.me/s/v2_team", "https://t.me/s/V2ray_Alpha", "https://t.me/s/V2Ray_VLESS_VMess",
    "https://t.me/s/Cloudfront_VPN", "https://t.me/s/CDN_V2RAY", "https://t.me/s/v2rayng_org"
]

def get_detailed_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=2).json()
        if res.get('status') == 'success':
            return res.get('countryCode'), res.get('country'), res.get('isp', '').lower()
    except: pass
    return 'Unknown', 'Unknown', ''

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
        
        # فرز مع أولوية مطلقة لـ CloudFront وبورت 443 و Vless/Vmess
        v_list = [c for c in all_configs if c.startswith(('vmess', 'vless'))]
        publish_queue = sorted(v_list, key=lambda x: (":443" not in x, "cloudfront" not in x.lower(), "cdn" not in x.lower()))
        
        posted = 0
        for config in publish_queue:
            if posted >= 4: break
            
            match = re.search(r'@([^:/]+):(\d+)', config)
            if not match: continue
            
            host, port = match.group(1), int(match.group(2))
            ms = measure_stability(host, port)
            
            if ms:
                ip = socket.gethostbyname(host)
                cc, country, isp = get_detailed_info(ip)
                
                # إعداد زر Edit SNI مع خانة فارغة للمشترك
                sni_hint = "TYPE_HOST_HERE"
                sni_url = f"https://t.me/share/url?url={config}%0A%0A🌐_SNI:__{sni_hint}__"
                
                # تاكات الانتشار العالمية (Hashtags)
                tags = "#V2ray #Vless #Vmess #Free_Internet #Ashaq_Team #CloudFront #CDN #VPN #العراق #انترنت_مجاني #ببجي #Gaming #NapsternetV #HTTP_Custom #Dark_Tunnel #Net_Free"

                # التحقق من نوع السيرفر لإضافة وسم CloudFront
                is_cf = "cloudfront" in config.lower() or "cdn" in config.lower()
                cf_label = " (CloudFront ⚡)" if is_cf else ""

                msg = f"🚀 <b>ULTRA CLOUDFRONT EDITION</b> 🚀\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>🌍 Country:</b> ({cc}) {country}\n"
                msg += f"<b>🔹 Type:</b> Vless/Vmess{cf_label}\n"
                msg += f"<b>⚡ Ping:</b> {ms}ms | 🟢 Ultra Fast\n"
                msg += f"<b>📦 Specs:</b> #NPTV #HTTPC #Dark #V2rayNG\n"
                msg += f"<b>🛠 Edit:</b> Click SNI to add your Host ✅\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<code>{config}</code>\n"
                msg += f"━━━━━━━━━━━━━━━\n"
                msg += f"<b>👥 Channel:</b> @V2rayashaq\n"
                msg += f"<b>🏷 Tags:</b> {tags}"

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "reply_markup": {
                        "inline_keyboard": [
                            [
                                {"text": "📢 Join", "url": "https://t.me/V2rayashaq"},
                                {"text": "👤 Admin", "url": f"https://t.me/{ADMIN_USER.replace('@','')}"},
                                {"text": "🛠 Edit SNI", "url": sni_url}
                            ]
                        ]
                    }
                })
                posted += 1
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    post_process()
