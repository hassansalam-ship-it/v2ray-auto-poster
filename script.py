import requests
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# مصادر عالمية محدثة كل دقيقة تحتوي على كل الأنواع
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64/mix",
    "https://raw.githubusercontent.com/LonUp/V2Ray-Config/main/Helper/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
]

def fetch_and_post():
    print("--- Start Deep Fetching (Trojan, Vless, Vmess) ---")
    all_configs = []
    
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                # الكود هنا سيبحث عن أي سطر يبدأ بالبروتوكولات المطلوبة
                lines = res.text.splitlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith(('vmess://', 'vless://', 'trojan://', 'ss://')):
                        all_configs.append(line)
        except: continue

    if not all_configs:
        print("❌ No configs found! Checking fallback source...")
        # مصدر احتياطي في حال فشل الجميع
        fallback = requests.get("https://raw.githubusercontent.com/Mid-Night-P/V2ray-Configs/main/All_Configs_Sub.txt").text
        all_configs = [l.strip() for l in fallback.splitlines() if l.startswith(('vmess', 'vless', 'trojan'))]

    if all_configs:
        # سننشر 3 سيرفرات متنوعة في كل مرة
        selected = all_configs[:3]
        for config in selected:
            # تحديد نوع السيرفر للرسالة
            config_type = "Vmess" if "vmess" in config else "Vless" if "vless" in config else "Trojan"
            
            msg = f"🚀 *New {config_type} Config*\n━━━━━━━━━━━━━━━\n\n`{config}`\n\n✅ Channel: @V2rayashaq"
            send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(send_url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        print(f"✅ Successfully posted {len(selected)} configs!")
    else:
        print("❌ Still nothing. Please check if the sources are blocked.")

if __name__ == "__main__":
    fetch_and_post()
