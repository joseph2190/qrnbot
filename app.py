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

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

CHOOSING_TEXT, CHOOSING_BUTTON = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("إبدأ ✨", callback_data="start_vote")]]
    await update.message.reply_text(
        "مرحبًا! 🌟\nاضغط على زر إبدأ للبدء.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def start_vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "أدخل الجزء أو الملاحظة (مثال: سورة البقرة)."
    )
    return CHOOSING_TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vote_text"] = update.message.text
    await update.message.reply_text("أدخل اسم الزر.")
    return CHOOSING_BUTTON

async def get_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["button_text"] = update.message.text
    context.user_data["voters"] = set()

    keyboard = [[InlineKeyboardButton(update.message.text, callback_data="vote")]]
    await update.message.reply_text(
        context.user_data["vote_text"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_name = query.from_user.first_name or "مستخدم"

    voters = context.user_data.setdefault("voters", set())
    if user_id in voters:
        await query.answer("تم تسجيلك بالفعل ✅")
        return

    voters.add(user_id)

    try:
        await query.edit_message_text(
            f"{context.user_data['vote_text']}\n\n" +
            "\n".join(["✔️ " + user_name for _ in voters]),
            reply_markup=query.message.reply_markup,
        )
    except BadRequest:
        pass

async def error_handler(update, context):
    print(context.error)

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_vote_callback, pattern="^start_vote$")],
        states={
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)],
            CHOOSING_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_button)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^vote$"))
    app.add_error_handler(error_handler)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
