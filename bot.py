import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import hashlib

BOT_TOKEN = "8984274382:AAF_zUdEOf8eflRtPK5MqB03RORj16TZKGc"
ADMIN_ID = 6519598716

CHANNELS = [
    {"id": -1004463483489, "url": "https://t.me/royalxarenabott"}
]

bot = telebot.TeleBot(BOT_TOKEN)

file_db = {}


# 🔐 Check user joined channels
def is_joined(user_id):
    try:
        for ch in CHANNELS:
            member = bot.get_chat_member(ch["id"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False


# 🔘 Join button
def join_buttons():
    markup = InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton("Join Channel", url=ch["url"]))
    markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify"))
    return markup


# 📥 Start
@bot.message_handler(commands=['start'])
def start(msg):
    args = msg.text.split()

    if len(args) > 1:
        file_id = args[1]

        if not is_joined(msg.from_user.id):
            bot.send_message(
                msg.chat.id,
                "⚠️ Pehle channel join karo!",
                reply_markup=join_buttons()
            )
            return

        if file_id in file_db:
            bot.copy_message(
                msg.chat.id,
                file_db[file_id]["chat_id"],
                file_db[file_id]["msg_id"]
            )
        else:
            bot.send_message(msg.chat.id, "❌ File not found")
    else:
        bot.send_message(msg.chat.id, "👋 Send me a file!")


# 🔁 Verify button
@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.send_message(call.message.chat.id, "Ab link dobara open karo 👍")
    else:
        bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)


# 📤 File receive (ONLY ADMIN)
@bot.message_handler(content_types=['document', 'video', 'photo'])
def get_file(msg):
    if msg.from_user.id != ADMIN_ID:
        return

    unique = hashlib.md5(str(msg.message_id).encode()).hexdigest()[:10]

    file_db[unique] = {
        "chat_id": msg.chat.id,
        "msg_id": msg.message_id
    }

    link = f"https://t.me/{bot.get_me().username}?start={unique}"

    bot.reply_to(msg, f"🔗 Your Link:\n{link}")


print("Bot running...")
bot.infinity_polling()