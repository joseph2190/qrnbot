import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# =====================
# ENV TOKEN (Render)
# =====================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

# =====================
# Conversation states
# =====================
CHOOSING_TEXT, CHOOSING_BUTTON = range(2)

# =====================
# /start command
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return

    keyboard = [[InlineKeyboardButton("إبدأ ✨", callback_data="start_vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "مرحبًا! 🌟\n"
        "هذا الروبوت مصمم لمساعدتك في إضافة أسماء الأفراد إلى قائمة مخصصة لقراءة القرآن الكريم 📖.\n"
        "يمكنك إنشاء قائمة لتوزيع الأجزاء 📜 أو تذكير المستخدمين بالمواعيد ⏰.",
        reply_markup=reply_markup,
    )

# =====================
# Start vote (button)
# =====================
async def start_vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("أدخل الجزء أو الملاحظة (مثال: سورة البقرة).")
    return CHOOSING_TEXT

# =====================
# Get vote text
# =====================
async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    context.user_data["vote_text"] = update.message.text
    await update.message.reply_text("أدخل اسم الزر (مثال: أضف إلى القائمة).")
    return CHOOSING_BUTTON

# =====================
# Get button text
# =====================
async def get_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END

    vote_text = context.user_data.get("vote_text")
    button_text = update.message.text

    context.user_data["button_text"] = button_text

    keyboard = [[InlineKeyboardButton(button_text, callback_data="vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(vote_text, reply_markup=reply_markup)
    return ConversationHandler.END

# =====================
# Vote button handler
# =====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data != "vote":
        return

    user = query.from_user
    user_name = user.first_name or user.username or "مستخدم"

    vote_text = context.user_data.get("vote_text", "")
    button_text = context.user_data.get("button_text", "تصويت")

    keyboard = [[InlineKeyboardButton(button_text, callback_data="vote")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"{vote_text}\n\n{user_name}",
        reply_markup=reply_markup,
    )

# =====================
# MAIN (Webhook)
# =====================
def main():
    application = Application.builder().token(TOKEN).build()

    # handlers here ...

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        url_path="webhook",
        webhook_url=os.getenv("RAILWAY_PUBLIC_DOMAIN"),
    )

if __name__ == "__main__":
    main()

