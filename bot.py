import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import hashlib

BOT_TOKEN = "8984274382:AAEZ4cOePReBDHrZs7Az7qv2XMLi0fLMXZg"
ADMIN_ID = 6519598716

bot = telebot.TeleBot(BOT_TOKEN)

database = {}
pending_requests = {}

CHANNELS = [
    {"id": -1004341093289, "url": "https://t.me/royalxarena", "name": "Main Channel"},
    {"id": -1004469666098, "url": "https://t.me/royalxarenasetup", "name": "Setup Channel"},
    {"id": -1004424577716, "url": "https://t.me/royalxarenapaymentproof", "name": "Payment Proof"},
]


def is_user_joined(user_id):
    try:
        for channel in CHANNELS:
            member = bot.get_chat_member(channel["id"], user_id)
            if member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False


def get_join_keyboard():
    keyboard = InlineKeyboardMarkup()
    for channel in CHANNELS:
        keyboard.add(InlineKeyboardButton(channel["name"], url=channel["url"]))
    keyboard.add(InlineKeyboardButton("Verify", callback_data="verify"))
    return keyboard


@bot.message_handler(commands=["start"])
def handle_start(message):
    args = message.text.split()

    if len(args) > 1:
        key = args[1]

        if not is_user_joined(message.from_user.id):
            pending_requests[message.from_user.id] = key

            bot.send_message(
                message.chat.id,
                "Please Join Our All Required channels to continue.",
                reply_markup=get_join_keyboard()
            )
            return

        send_content(message.chat.id, key)
    else:
        bot.send_message(message.chat.id, "Send any content to generate a secure link.")


@bot.callback_query_handler(func=lambda call: call.data == "verify")
def handle_verify(call):
    user_id = call.from_user.id

    if is_user_joined(user_id):
        bot.answer_callback_query(call.id, "Verification successful.")

        if user_id in pending_requests:
            key = pending_requests[user_id]
            send_content(call.message.chat.id, key)
            del pending_requests[user_id]
        else:
            bot.send_message(call.message.chat.id, "Session expired. Please reopen the link.")
    else:
        bot.answer_callback_query(call.id, "Please join all channels first.", show_alert=True)


def send_content(chat_id, key):
    if key not in database:
        bot.send_message(chat_id, "Content not found.")
        return

    data = database[key]

    if data["type"] == "text":
        bot.send_message(chat_id, data["content"])
    else:
        bot.copy_message(chat_id, data["chat_id"], data["message_id"])


@bot.message_handler(content_types=["text", "photo", "video", "document"])
def save_content(message):
    if message.from_user.id != ADMIN_ID:
        return

    unique_key = hashlib.md5(str(message.message_id).encode()).hexdigest()[:10]

    if message.content_type == "text":
        database[unique_key] = {
            "type": "text",
            "content": message.text
        }
    else:
        database[unique_key] = {
            "type": "file",
            "chat_id": message.chat.id,
            "message_id": message.message_id
        }

    bot_username = bot.get_me().username
    link = f"https://t.me/{bot_username}?start={unique_key}"

    bot.reply_to(message, f"Generated Link:\n{link}")


bot.infinity_polling()
