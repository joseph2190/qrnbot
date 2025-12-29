import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------- STATES ----------------
CHOOSING_TEXT, CHOOSING_BUTTON = range(2)

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Use /startvote to create a new vote."
    )

async def startvote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "✍️ Send the vote question (example: *Should we order pizza?*)",
        parse_mode="Markdown",
    )
    return CHOOSING_TEXT

async def receive_vote_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["vote_text"] = update.message.text
    await update.message.reply_text(
        "🔘 Now send the button label (example: *Vote*)",
        parse_mode="Markdown",
    )
    return CHOOSING_BUTTON

async def receive_button_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    vote_text = context.user_data.get("vote_text", "Vote")
    button_text = update.message.text

    keyboard = [[InlineKeyboardButton(button_text, callback_data="vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent = await update.message.reply_text(vote_text, reply_markup=reply_markup)

    key = f"{sent.chat_id}:{sent.message_id}"

    context.application.bot_data.setdefault("votes", {})[key] = {
        "text": vote_text,
        "voters": set(),
    }

    return ConversationHandler.END

async def handle_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    name = user.first_name or user.username or "Anonymous"

    key = f"{query.message.chat_id}:{query.message.message_id}"
    votes = context.application.bot_data.setdefault("votes", {}).setdefault(
        key, {"text": query.message.text, "voters": set()}
    )

    if user_id in votes["voters"]:
        return

    votes["voters"].add(user_id)

    voters_text = ", ".join(str(uid) for uid in votes["voters"])
    updated_text = f"{votes['text']}\n\n🗳 Votes: {len(votes['voters'])}"

    await query.edit_message_text(
        text=updated_text,
        reply_markup=query.message.reply_markup,
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Vote creation cancelled.")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update error", exc_info=context.error)

# ---------------- MAIN ----------------
def main():
    token = os.getenv("8257459881:AAFZ4hihP5r3SrbD-qJRbUV95Yv_68yQBvs")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is missing")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("startvote", startvote)],
        states={
            CHOOSING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_vote_text)],
            CHOOSING_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_button_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(handle_vote))
    app.add_error_handler(error_handler)

    # 🔥 WEBHOOK MODE (Render-compatible)
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url="https://qrnbot.onrender.com/webhook",
    )

if __name__ == "__main__":
    main()
