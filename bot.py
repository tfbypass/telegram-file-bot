import os
import time
import threading
from flask import Flask
import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

apihelper.CONNECT_TIMEOUT = 60
apihelper.READ_TIMEOUT = 60

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_URL = os.environ.get("CHANNEL_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Channel ID ko handle karne ka ekdum safe tarika
raw_channel_id = os.environ.get("CHANNEL_ID", "")
if raw_channel_id.startswith("-100"):
    CHANNEL_ID = int(raw_channel_id)
else:
    CHANNEL_ID = int(f"-100{raw_channel_id.replace('-', '')}")

bot = telebot.TeleBot(BOT_TOKEN)
file_database = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def is_user_subscribed(user_id):
    # Agar admin check kar raha hai toh direct bypass
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Subscription checking failed for ID {CHANNEL_ID}: {e}")
        return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not message.text:
        return
    
    text_args = message.text.split()

    # AGAR USER LINK SE AAYA HAI
    if len(text_args) > 1:
        file_id = text_args[1]
        
        try:
            # Check subscription with fallback error message
            if is_user_subscribed(user_id):
                send_requested_file(chat_id, file_id)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("📢 Join Royal", url=CHANNEL_URL))
                markup.add(InlineKeyboardButton("🔄 Verify Subscription", callback_data=f"verify_{file_id}"))
                bot.send_message(
                    chat_id, 
                    "⚠️ <b>Access Denied!</b>\n\nYou must join our channel and then click 'Verify Subscription' to unlock your file.", 
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        except Exception as crash_error:
            bot.send_message(chat_id, f"❌ <b>Internal Verification Error:</b> {crash_error}\n\nAdmin please check CHANNEL_ID in Render!", parse_mode="HTML")
            
    else:
        # NORMAL START BINA LINK KE
        if user_id == ADMIN_ID:
            bot.send_message(chat_id, "👋 <b>Welcome Admin!</b>\n\nForward me any file to generate a link.", parse_mode="HTML")
        else:
            bot.send_message(chat_id, "👋 <b>Welcome!</b>\n\nThis bot can only open secure download links shared by the admin.", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def handle_verification(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    file_id = call.data.split('_')[1]

    if is_user_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful! Fetching file...", show_alert=False)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
        send_requested_file(chat_id, file_id)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai. Pehle Join Royal par click karein!", show_alert=True)

def send_requested_file(chat_id, file_id):
    if file_id in file_database:
        file_data = file_database[file_id]
        caption = file_data.get("caption", "")
        bot.send_message(chat_id, "📦 <b>Here is your requested file:</b>", parse_mode="HTML")
        try:
            if file_data["type"] == "document":
                bot.send_document(chat_id, file_id, caption=caption)
            elif file_data["type"] == "video":
                bot.send_video(chat_id, file_id, caption=caption)
            elif file_data["type"] == "photo":
                bot.send_photo(chat_id, file_id, caption=caption)
            elif file_data["type"] == "audio":
                bot.send_audio(chat_id, file_id, caption=caption)
        except Exception as e:
            bot.send_message(chat_id, f"❌ Telegram API Error: Unable to send file. ({e})")
    else:
        # Agar restart ki wajah se RAM clear ho gayi toh ye message dikhega
        bot.send_message(chat_id, "❌ <b>Error:</b> This link has expired because the bot was restarted. Please ask the admin for a new link.", parse_mode="HTML")

@bot.message_handler(content_types=['document', 'video', 'photo', 'audio'])
def handle_incoming_files(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return

    file_id = None
    file_type = None
    caption = message.caption if message.caption else ""

    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"

    if file_id:
        file_database[file_id] = {"type": file_type, "caption": caption}
        share_link = f"https://t.me/royal_x_arena_bot?start={file_id}"
        response_text = f"✅ <b>Link Generated Successfully!</b>\n\n🔗 <b>Your Link:</b> {share_link}"
        bot.reply_to(message, response_text, parse_mode="HTML")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot is starting cleanly with auto ID-fixing...")
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print(f"Webhook clear error: {e}")

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling crash prevented: {e}. Reconnecting in 5s...")
            time.sleep(5)
