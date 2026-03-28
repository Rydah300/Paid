import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# 🔐 Configuration
BOT_TOKEN = "8737983102:AAFev0CSaM9KzIE55ZxUjBnv4WxzfyL4oIE"
ADMIN_CHAT_ID = 8457282877

# 📝 Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🧠 In-memory storage for user sessions (use a DB in production)
user_sessions = {}

# 🎨 Welcome message with stylish formatting
WELCOME_MESSAGE = (
    "👋 <b>Welcome to CloudNexus VPS Support!</b>\n\n"
    "🛡️ Your trusted partner in high-performance virtual servers.\n\n"
    "📥 Please submit your support report below.\n"
    "Our team will respond as soon as possible.\n\n"
    "<i>Tip: Be as detailed as possible for faster resolution!</i>"
)

# 🚀 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📤 Submit New Report")],
        [KeyboardButton("ℹ️ About CloudNexus")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ℹ️ About handler
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "☁️ <b>CloudNexus VPS</b>\n\n"
        "• Enterprise-grade virtual servers\n"
        "• 99.99% Uptime Guarantee\n"
        "• 24/7 Expert Support\n"
        "• Global Data Centers\n\n"
        "🌐 We Are WorldWide"
    )
    await update.message.reply_text(about_text, parse_mode="HTML")

# 📤 Handle user messages (non-commands)
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    # Ignore commands from users (except /start)
    if message.text and message.text.startswith("/"):
        return

    # Store user info for reply
    user_sessions[user.id] = {
        "first_name": user.first_name,
        "username": user.username or "NoUsername"
    }

    # Forward message to admin with context
    forward_text = (
        f"📩 <b>New Support Message</b>\n"
        f"👤 User: {user.first_name} (@{user.username or 'N/A'})\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"──────────────────\n"
        f"{message.text or '[Media/Attachment]'}"
    )

    try:
        # Send to admin
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=forward_text,
            parse_mode="HTML"
        )
        # Confirm to user
        await message.reply_text(
            "✅ Your message has been sent to our support team!\n"
            "We'll get back to you shortly. 🕒",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📤 Submit New Report")]],
                resize_keyboard=True
            )
        )
    except Exception as e:
        logger.error(f"Failed to forward message: {e}")
        await message.reply_text("❌ Failed to send your message. Please try again.")

# 📨 Handle admin replies
async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_CHAT_ID:
        return  # Only admin can trigger this

    message = update.message
    if not message.reply_to_message:
        await message.reply_text("⚠️ Please reply to a user's forwarded message to respond.")
        return

    # Extract user ID from the forwarded message text
    original_text = message.reply_to_message.text or ""
    if "🆔 User ID: " not in original_text:
        await message.reply_text("❌ Unable to identify user. Please reply to a valid support message.")
        return

    try:
        # Parse user ID from the forwarded message
        start = original_text.find("🆔 User ID: ") + len("🆔 User ID: ")
        end = original_text.find("\n", start)
        user_id = int(original_text[start:end].strip().replace("<code>", "").replace("</code>", ""))
    except (ValueError, IndexError):
        await message.reply_text("❌ Failed to parse user ID. Message may be corrupted.")
        return

    # Send admin's reply to the user
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "📬 <b>Support Team Reply:</b>\n\n"
                f"{message.text}"
            ),
            parse_mode="HTML"
        )
        await message.reply_text("✅ Reply sent to user.")
    except Exception as e:
        logger.error(f"Failed to send reply to user {user_id}: {e}")
        await message.reply_text("❌ Failed to deliver reply. User may have blocked the bot.")

# 🧩 Main
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ About CloudNexus$"), about))
    application.add_handler(MessageHandler(filters.Chat(ADMIN_CHAT_ID), handle_admin_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    # Start bot
    logger.info("🚀 CloudNexus Support Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()