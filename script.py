import telebot
from telebot import types
import time
import threading
import random
import re

# --- إعدادات مشروع ألفا ---
API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
CHANNEL_ID = '@V2rayashaq' # تأكد أن البوت "أدمن" في القناة
bot = telebot.TeleBot(API_TOKEN)

# قائمة الـ SNI (مشروع ألفا)
SNI_LIST = {
    "Zain_Kafu": "m.tiktok.com",
    "Oodi": "m.youtube.com",
    "Voxi": "downloads.vodafone.co.uk",
    "CloudFront": "1.1.1.1"
}

# دالة جلب السيرفرات (Alpha Scraper)
def get_top_servers():
    # محاكاة لجلب سيرفرات حقيقية
    servers = []
    configs = [
        "vless://631d8e12-c283-4a8b-98f1@104.16.51.111:443?encryption=none&security=tls&sni=google.com&fp=chrome&type=ws&host=google.com&path=%2F#Ashaq_Alpha",
        "vmess://ewogICJ2IjogIjIiLAogICJwcyI6ICJBc2hhcV9WUFMiLAogICJhZGQiOiAiMTcyLjY3LjE3NC45OCIsCiAgInBvcnQiOiA0NDMsCiAgImlkIjogImY4MWI3Y2IwLTcwYzYtM2QxYS05YjMwLWM5NWIxMjI3ZjZlZCIsCiAgInF1ZXJ5IjogInNlY3VyaXR5PXRscyIsCiAgInNuaSI6ICJnb29nbGUuY29tIiwKICAiaG9zdCI6ICJnb29nbGUuY29tIiwKICAidHlwZSI6ICJ3cyIsCiAgInBhdGgiOiAiLyIKfQ=="
    ]
    return random.sample(configs, k=min(len(configs), 3))

# دالة تعديل الـ SNI برمجياً
def modify_sni(config, new_sni):
    # للـ Vless
    if "vless://" in config:
        config = re.sub(r'sni=[^&]+', f'sni={new_sni}', config)
        config = re.sub(r'host=[^&]+', f'host={new_sni}', config)
    # للـ Vmess (تحتاج فك التشفير وتعديله ثم إعادة التشفير)
    elif "vmess://" in config:
        # تبسيط للمثال: نغير الـ SNI في الروابط المفتوحة فقط
        pass 
    return config

# دالة النشر الاحترافية
def post_to_channel():
    print("🔄 جاري صيد السيرفرات ونشرها في فريق عشق...")
    new_servers = get_top_servers()
    
    for srv in new_servers:
        # الأفضل في القنوات استخدام أزرار URL أو توجيه للبوت الخاص بك
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # تحويل الأزرار إلى روابط Share تفتح في تليجرام لتعديل الـ SNI (الحل الأمثل للقنوات)
        btns = []
        for name, sni in SNI_LIST.items():
            modified_srv = modify_sni(srv, sni)
            share_url = f"https://t.me/share/url?url={modified_srv}%0A%0A✅_Ready_for_{name}"
            btns.append(types.InlineKeyboardButton(f"🛠 {name}", url=share_url))
        
        markup.add(*btns)
        markup.add(types.InlineKeyboardButton("👤 Admin", url="https://t.me/genie_2000"))

        caption = (
            "🚀 **Alpha Project | صيد تلقائي**\n"
            "━━━━━━━━━━━━━━━\n"
            "🌍 **Type:** VPS + CloudFront ⚡\n"
            "⚡ **Ping:** Ultra Fast (443)\n"
            "🕒 **Updated:** Just Now\n"
            "🏷 **Tags:** #Ashaq_Team #Free_VPN\n"
            "━━━━━━━━━━━━━━━\n"
            "👇 **اختر شبكتك للنسخ المباشر بالـ SNI:**"
        )
        
        try:
            bot.send_message(CHANNEL_ID, f"{caption}\n\n`{srv}`", parse_mode="Markdown", reply_markup=markup)
            time.sleep(5) # فاصل لتجنب الـ Spam
        except Exception as e:
            print(f"❌ خطأ في النشر: {e}")

# الجدولة
def run_scheduler():
    while True:
        post_to_channel()
        time.sleep(1800) # كل 30 دقيقة

if __name__ == "__main__":
    # تشغيل الجدولة
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    print("✅ مشروع ألفا يعمل الآن... النشر كل 30 دقيقة")
    # تشغيل البوت لاستقبال الرسائل (إذا أردت ميزات أخرى)
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        time.sleep(15)
