import os
import time
import threading
from flask import Flask
import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
CHANNEL_URL = os.environ.get("CHANNEL_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

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
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if not message.text:
        return
    text_args = message.text.split()

    if len(text_args) > 1:
        file_id = text_args[1]
        if is_user_subscribed(user_id):
            send_requested_file(message.chat.id, file_id)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Join Royal", url=CHANNEL_URL))
            markup.add(InlineKeyboardButton("🔄 Verify Subscription", callback_data=f"verify_{file_id}"))
            bot.send_message(
                message.chat.id, 
                "⚠️ **Access Denied!**\n\nYou must join our channel and then click 'Verify Subscription' to unlock your file.", 
                reply_markup=markup
            )
    else:
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "👋 **Welcome Admin!**\n\nForward me any file to generate a link.")
        else:
            bot.send_message(message.chat.id, "👋 **Welcome!**\n\nThis bot can only open secure download links shared by the admin.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('verify_'))
def handle_verification(call):
    user_id = call.from_user.id
    file_id = call.data.split('_')[1]

    if is_user_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful! Fetching file...", show_alert=False)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_requested_file(call.message.chat.id, file_id)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai. Pehle Join Royal par click karein!", show_alert=True)

def send_requested_file(chat_id, file_id):
    if file_id in file_database:
        file_data = file_database[file_id]
        caption = file_data.get("caption", "")
        bot.send_message(chat_id, "📦 **Here is your requested file:**")
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
        bot.send_message(chat_id, "❌ **Error:** This link has expired because the bot was restarted. Please ask the admin for a new link.")

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
        response_text = f"✅ **Link Generated Successfully!**\n\n🔗 **Your Link:** {share_link}"
        bot.reply_to(message, response_text, parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception:
            time.sleep(5)
