import requests
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = "@V2rayashaq"

# مصادر متنوعة وكبيرة
SOURCES = [
    "https://raw.githubusercontent.com/yebekhe/TVC/main/configs/v2ray/sub",
    "https://raw.githubusercontent.com/WilliamStar007/ClashX-V2Ray-TopFreeProxy/main/v2ray.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/E03.txt"
]

def fetch_and_post():
    print("--- Start Fetching From Multiple Sources ---")
    all_configs = []
    
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                # نسحب أي سيرفر يبدأ بـ vmess أو vless أو trojan أو ss
                lines = [l.strip() for l in res.text.splitlines() if len(l) > 50]
                all_configs.extend(lines)
        except: continue

    if not all_configs:
        print("❌ Still no configs found in any source!")
        return

    # سنأخذ أول 2 سيرفرات فقط للنشر الآن كتحربة
    for config in all_configs[:2]:
        msg = f"🚀 *New V2Ray Config*\n━━━━━━━━━━━━━━━\n\n`{config}`\n\n✅ Join: @V2rayashaq"
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(send_url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    
    print(f"✅ Successfully posted {len(all_configs[:2])} configs!")

if __name__ == "__main__":
    fetch_and_post()
