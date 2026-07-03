import os
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
CHANNEL_URL = os.environ.get("CHANNEL_URL")

bot = telebot.TeleBot(BOT_TOKEN)

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    text_split = message.text.split()
    
    if not is_user_subscribed(user_id):
        file_param = text_split[1] if len(text_split) > 1 else ""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Join Royal", url=CHANNEL_URL))
        markup.add(InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{bot.get_me().username}?start={file_param}"))
        
        bot.send_message(
            message.chat.id,
            "⚠️ **Access Denied!**\n\nIs file ko download karne ke liye aapko hamare channel ko join karna hoga. Join karne ke baad niche 'Try Again' par click karein.",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    if len(text_split) > 1:
        file_id = text_split[1]
        bot.send_message(message.chat.id, "⏳ *Aapki file fetch ki jaa rahi hai...*", parse_mode="Markdown")
        try:
            bot.send_document(message.chat.id, file_id, caption="Aapki file yeh rahi!")
        except Exception:
            bot.send_message(message.chat.id, "❌ File nahi mili ya invalid link hai.")
    else:
        bot.send_message(message.chat.id, "👋 Hello! Main aapka personal File Share bot hu. Mujhe koi file forward kijiye.")

@bot.message_handler(content_types=['document', 'video', 'audio'])
def handle_files(message):
    file_id = ""
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id

    shareable_link = f"https://t.me/{bot.get_me().username}?start={file_id}"
    bot.send_message(
        message.chat.id,
        f"✅ **File Saved!**\n\nAapka shareable link yeh hai:\n`{shareable_link}`",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

print("Bot is running...")
bot.infinity_polling()
