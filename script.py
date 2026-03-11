import telebot
from telebot import types
import time
import threading
import random

# إعدادات البوت
API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
CHANNEL_ID = '@V2rayashaq' # معرف قناتك
bot = telebot.TeleBot(API_TOKEN)

# قائمة الـ SNI المعتمدة لمشروعك
SNI_LIST = {
    "Zain_Kafu": "m.tiktok.com",
    "Oodi": "m.youtube.com",
    "Voxi": "downloads.vodafone.co.uk",
    "CloudFront_SSL": "1.1.1.1" # مثال لكلاود فرونت
}

# دالة محاكاة لجلب السيرفرات من 120 مصدر
def get_top_servers():
    # هنا يوضع كود الزحف (Scraper) الخاص بك
    # سننشئ روابط وهمية كمثال للتوضيح
    types_list = ['vless', 'vmess']
    servers = []
    for i in range(3):
        t = random.choice(types_list)
        servers.append(f"{t}://alpha_vps_id_{random.randint(100,999)}@vps_ip:443?security=tls#Alpha_Project_{i}")
    return servers

# دالة النشر في القناة
def post_to_channel():
    new_servers = get_top_servers()
    
    for srv in new_servers:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(name, callback_data=f"fix_{name}") for name in SNI_LIST]
        markup.add(*btns)
        
        caption = (
            "🚀 **Alpha Project | صيد تلقائي**\n"
            "━━━━━━━━━━━━━━\n"
            "📡 **المصدر:** 120 مصدر (قوة قصوى)\n"
            "🔒 **النوع:** VPS + SSL + CloudFront\n"
            "⚡ **التحديث:** كل 30 دقيقة\n"
            "━━━━━━━━━━━━━━\n"
            "👇 **اختر شبكتك لتجهيز الرابط:**"
        )
        
        bot.send_message(CHANNEL_ID, f"{caption}\n\n`{srv}`", parse_mode="Markdown", reply_markup=markup)
        time.sleep(2) # فاصل بسيط بين السيرفرات الثلاثة

# محرك الوقت (يعمل في الخلفية)
def scheduler():
    while True:
        post_to_channel()
        time.sleep(1800) # الانتظار لمدة 30 دقيقة (30 * 60 ثانية)

# تشغيل الجدولة في Thread منفصل لكي لا يتوقف البوت
threading.Thread(target=scheduler).start()

# معالج الأزرار (لتعديل الـ SNI عند ضغط المستخدم)
@bot.callback_query_handler(func=lambda call: call.data.startswith("fix_"))
def handle_fix(call):
    sni_name = call.data.replace("fix_", "")
    new_sni = SNI_LIST.get(sni_name)
    
    # منطق استبدال الـ SNI داخل الرابط
    original_msg = call.message.text
    # كود مبسط لاستخراج الرابط وتعديله
    # (يفضل استخدام Regex كما في الكود السابق)
    
    bot.answer_callback_query(call.id, f"تم التجهيز لـ {sni_name} ✅")
    bot.send_message(call.message.chat.id, f"✅ **رابطك الجاهز ({sni_name}):**\n\n`سيرفر_معدل_هنا`")

print("Alpha Project is Auto-Posting every 30 mins...")
bot.polling()
