import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

# =====================
# ENV VARIABLES
# =====================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

PORT = int(os.getenv("PORT", 8080))
PUBLIC_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")
if not PUBLIC_URL:
    raise RuntimeError("RAILWAY_PUBLIC_DOMAIN is missing")

# =====================
# STATES
# =====================
CHOOSING_TEXT, CHOOSING_BUTTON = range(2)

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    keyboard = [[InlineKeyboardButton("إبدأ ✨", callback_data="start_vote")]]
    await update.message.reply_text(
        "مرحبًا! 🌟\n"
        "هذا الروبوت يساعدك في إنشاء قائمة لقراءة القرآن الكريم 📖.\n"
        "اضغط على زر (إبدأ) للبدء.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# =====================
# START BUTTON
# =====================
async def start_vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("أدخل الجزء أو الملاحظة (مثال: سورة البقرة).")
    return CHOOSING_TEXT

# =====================
# GET TEXT
# =====================
async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    context.user_data["vote_text"] = update.message.text
    await update.message.reply_text("أدخل اسم الزر (مثال: أضف إلى القائمة).")
    return CHOOSING_BUTTON

# =====================
# GET BUTTON
# =====================
async def get_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message:
        return ConversationHandler.END

    context.user_data["button_text"] = update.message.text
    context.user_data["voters"] = set()

    keyboard = [[InlineKeyboardButton(update.message.text, callback_data="vote")]]
    await update.message.reply_text(
        context.user_data["vote_text"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END

# =====================
# BUTTON CLICK (SAFE)
# =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    user_name = user.first_name or user.username or "مستخدم"

    voters = context.user_data.setdefault("voters", set())

    if user_id in voters:
        await query.answer("تم تسجيلك بالفعل ✅", show_alert=False)
        return

    voters.add(user_id)

    vote_text = context.user_data.get("vote_text", "")
    button_text = context.user_data.get("button_text", "تصويت")

    names = "\n".join(
        [user_name if uid == user_id else "✔️" for uid in voters]
    )

    keyboard = [[InlineKeyboardButton(button_text, callback_data="vote")]]

    try:
        await query.edit_message_text(
            text=f"{vote_text}\n\n{names}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise

# =====================
# ERROR HANDLER
# =====================
async def error_handler(update, context):
    print("ERROR:", context.error)

# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_vote_callback, pattern="^start_vote$")
        ],
        states={
            CHOOSING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)
            ],
            CHOOSING_BUTTON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_button)
            ],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^vote$"))
    app.add_error_handler(error_handler)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=PUBLIC_URL,
    )

if __name__ == "__main__":
    main()
