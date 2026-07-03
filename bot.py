import os
import time
import threading
from flask import Flask
import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Global timeouts set kiya taaki network stable rahe
apihelper.CONNECT_TIMEOUT = 90
apihelper.READ_TIMEOUT = 90

# Fetch configuration from Render Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
CHANNEL_URL = os.environ.get("CHANNEL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
file_database = {}

# --- DUMMY FLASK WEB SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Successfully!"

def run_flask():
    # Render automatically PORT environment variable deta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
# -----------------------------------------

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return True

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    text_args = message.text.split()

    if len(text_args) > 1:
        file_id = text_args[1]

        if is_user_subscribed(user_id):
            if file_id in file_database:
                file_data = file_database[file_id]
                caption = file_data.get("caption", "")
                
                bot.send_message(message.chat.id, "📦 **Here is your requested file:**")
                
                if file_data["type"] == "document":
                    bot.send_document(message.chat.id, file_id, caption=caption)
                elif file_data["type"] == "video":
                    bot.send_video(message.chat.id, file_id, caption=caption)
                elif file_data["type"] == "photo":
                    bot.send_photo(message.chat.id, file_id, caption=caption)
                elif file_data["type"] == "audio":
                    bot.send_audio(message.chat.id, file_id, caption=caption)
            else:
                bot.send_message(message.chat.id, "❌ Error: This file link has expired or is invalid.")
        else:
            try:
                bot_username = bot.get_me().username
            except Exception:
                bot_username = "YourBot"
                
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_URL))
            markup.add(InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{bot_username}?start={file_id}"))
            
            bot.send_message(
                message.chat.id, 
                "⚠️ **Access Denied!**\n\nYou must join our updates channel before you can download any files from this bot.", 
                reply_markup=markup
            )
    else:
        bot.send_message(
            message.chat.id, 
            "👋 **Welcome!**\n\nForward any file, video, or photo to me, and I will generate a secure, high-speed download link with a force-subscription lock for your channel."
        )

@bot.message_handler(content_types=['document', 'video', 'photo', 'audio'])
def handle_incoming_files(message):
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
        
        try:
            bot_username = bot.get_me().username
        except Exception:
            bot_username = "YourBot"
            
        share_link = f"https://t.me/{bot_username}?start={file_id}"
        
        response_text = (
            "✅ **Link Generated Successfully!**\n\n"
            f"🔗 **Your Link:** {share_link}\n\n"
            "📢 *Users must join your channel to access this file.*"
        )
        bot.reply_to(message, response_text, parse_mode="Markdown")

if __name__ == "__main__":
    print("Starting Flask web server in a separate thread...")
    # Flask ko alag thread mein chalaya taaki bot ka polling loop na ruke
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot is booting up with polling loop...")
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=90)
        except Exception as e:
            print(f"Network error caught: {e}. Retrying in 5 seconds...")
            time.sleep(5)
