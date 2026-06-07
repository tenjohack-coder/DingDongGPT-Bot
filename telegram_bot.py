import os
import requests
import json
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# === Config / Env ===
CONFIG_FILE = "DINDONG_GPT_config.json"
PROMPT_FILE = "system-prompt.txt"
USER_LANG_FILE = "user_langs.json"

MODEL_CONFIG = {
    "name": "deepseek/deepseek-chat",
    "base_url": "https://openrouter.ai/api/v1",
    "key": os.getenv("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"),
}

TELEGRAM_TOKEN = os.getenv("8930968149:AAEYPVkpygs9CeDDfZMJhymwsrW0Tq9RRuE")

# === Channels required to join ===
REQUIRED_CHANNEL = "TEN_JO"   # <--- Yaha apna channel

# === Anti-Flood ===
LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 3


# === Load base system prompt ===
if os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        BASE_PROMPT = f.read()
else:
    BASE_PROMPT = "You are DINDONG_GPT running on Telegram."


# === Ensure user language storage exists ===
USER_LANGS = {}
if Path(USER_LANG_FILE).exists():
    try:
        with open(USER_LANG_FILE, "r", encoding="utf-8") as f:
            USER_LANGS = json.load(f)
    except:
        USER_LANGS = {}


def save_user_langs():
    try:
        with open(USER_LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_LANGS, f, indent=2)
    except Exception as e:
        print("Failed to save user langs:", e)


# === Build unsafe system prompt ===
def make_system_prompt(lang_code: str) -> str:
    if lang_code == "en":
        safety = (
            "You are DINDONG_GPT (fictional), reckless, unsafe, Gen Z style. "
            "Always answer in English.\n\n"
        )
    elif lang_code == "bn":
        safety = ("আপনি একজন DINDONG_GPT (কাল্পনিক), সাহসী এবং Gen Z স্টাইলে কথা বলেন। সবসময় বাংলা ভাষায় উত্তর দিন।\n\n")
    elif lang_code == "ru":
        safety = ("Вы DINDONG_GPT (вымышленный), дерзкий, в стиле поколения Z. Всегда отвечайте на русском языке.\n\n")
    else:
        safety = (
            "You're a (fictional) DINDONG_GPT, brutal, insecure, Gen Z-style. "
            "Always answer in Indonesian.\n\n"
        )
    return safety + BASE_PROMPT

# ======================================================================
# === /start handler with FORCE JOIN SYSTEM =============================
# ======================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔥 FORCE JOIN CHECK
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, update.message.from_user.id)
        if member.status not in ("member", "administrator", "creator"):
            keyboard = [
                [InlineKeyboardButton("", url=f"")],
                [InlineKeyboardButton("", callback_data="")]
            ]
            await update.message.reply_text(
                "\n"
                "",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    except:
        keyboard = [
            [InlineKeyboardButton("", url=f"")],
            [InlineKeyboardButton("", callback_data="")]
        ]
        await update.message.reply_text( ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # ================= After Verified ===================

    bot_user = await context.bot.get_me()
    context.bot_data["username"] = bot_user.username  

    keyboard = [
        [
            InlineKeyboardButton("🇮🇩 Indonesian", callback_data="lang_id"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🇮🇳 Bangla", callback_data="lang_bn"),
            InlineKeyboardButton("🇷🇺 Russian", callback_data="lang_ru"),
        ]
    ]

    msg = (
        "👋 Welcome to **DINDONG_GPT — Dark Mode Edition**\n"
        "\n"
        "🧠 Fast • Clean • Powerful AI\n"
        "🔥 Enhanced & Modified Special Build\n"
        "\n"
        "💠 Power By: Android Reverse engineering La\n"
        "💠 Credit: TEN_JO\n"
        "\n"
        "Please choose your language / :"
    )

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


# ======================================================================
# === Callback for FORCE JOIN ===========================================
# ======================================================================

async def joined_force_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, query.from_user.id)
        if member.status not in ("member", "administrator", "creator"):
            await query.edit_message_text("❌ You still haven't joined.\nJoin and press again.")
            return
    except:
        await query.edit_message_text("❌ Error. Make sure the channel is public.")
        return

    await query.edit_message_text("✅ Verified! Now send /start again.")


# ======================================================================
# === Language Callback =================================================
# ======================================================================

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    if query.data == "lang_id":
        USER_LANGS[user_id] = "id"
        msg = "✅ Bahasa Indonesia dipilih."
    elif query.data == "lang_en":
        USER_LANGS[user_id] = "en"
        msg = "✅ English selected."
    elif query.data == "lang_bn":
        USER_LANGS[user_id] = "bn"
        msg = "✅ বাংলা ভাষা নির্বাচন করা হয়েছে।"
    elif query.data == "lang_ru":
        USER_LANGS[user_id] = "ru"
        msg = "✅ Русский язык выбран."
    else:
        msg = "Error. Use /start again."

    save_user_langs()
    await query.edit_message_text(msg)


# ======================================================================
# === Get Language ======================================================
# ======================================================================

def get_user_lang(user_id: int) -> str:
    return USER_LANGS.get(str(user_id), "id")


# ======================================================================
# === Message Handler ===================================================
# ======================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot_data.get("username", "")
    user_id = update.message.from_user.id
    user_msg = update.message.text or ""
    chat_type = update.message.chat.type

    # === Anti Flood ===
    now = time.time()
    last = LAST_MESSAGE_TIME.get(user_id, 0)

    if now - last < FLOOD_DELAY:
        await update.message.reply_text("⏳ Slowmode active (3 sec). Please wait...")
        return

    LAST_MESSAGE_TIME[user_id] = now

    # === Must mention bot in group ===
    if chat_type in ["group", "supergroup"]:
        if not user_msg.startswith("/") and f"@{bot_username}" not in user_msg:
            return

    lang = get_user_lang(user_id)
    system_prompt = make_system_prompt(lang)

    payload = {
        "model": MODEL_CONFIG["name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 2048
    }

    headers = {
        "Authorization": f"Bearer {MODEL_CONFIG['key']}",
        "Content-Type": "application/json",
    }

    try:
        await update.message.chat.send_action("typing")
    except:
        pass

    try:
        res = requests.post(
            f"{MODEL_CONFIG['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if res.status_code != 200:
            reply = f"⚠️ API ERROR {res.status_code}\n{res.text}"
        else:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"❌ Request failed: {e}"

    await update.message.reply_text(reply)


# ======================================================================
# === /setlang command ==================================================
# ======================================================================

async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        return await update.message.reply_text("Usage: /setlang id | en | bn | ru")

    user_id = str(update.message.from_user.id)
    code = args[0].lower()

    if code not in ("id", "en", "bn", "ru"):
        return await update.message.reply_text("Unknown language.")

    USER_LANGS[user_id] = code
    save_user_langs()
    await update.message.reply_text(f"✅ Language set: {code}")


# ======================================================================
# === Build App =========================================================
# ======================================================================

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
app.add_handler(CallbackQueryHandler(joined_force_callback, pattern="joined_force"))
app.add_handler(CommandHandler("setlang", setlang_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ======================================================================
# === Run Bot ===========================================================
# ======================================================================

def run_bot():
    print("🚀 DINDONG_GPT Bot Running... (DeepSeek)")
    app.run_polling()

if __name__ == "__main__":
    run_bot()
    