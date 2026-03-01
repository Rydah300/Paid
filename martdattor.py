import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Configuration
BOT_TOKEN = "8609873462:AAFDwtkB_zFipNFBBmOV3PrhKWanq83xjws"
ADMIN_CHAT_ID = 7926187033

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("✉️ Submit Support Request", callback_data="submit_request")],
        [InlineKeyboardButton("📚 Documentation", url="https://dattomart.com/docs")],
        [InlineKeyboardButton("🌐 Official Website", url="https://dattomart.com")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 <b>Welcome to DattoMart Support!</b>\n\n"
        "We're here to assist you with your Datto RMM partner credentials and services. "
        "Our team provides priority support for all verified customers.\n\n"
        "<b>How can we help you today?</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "submit_request":
        context.user_data["awaiting_support"] = True
        await query.edit_message_text(
            "📝 <b>Submit Support Request</b>\n\n"
            "Please describe your issue or question in detail. Include your Order ID if applicable.\n\n"
            "<i>Our support team typically responds within 24 business hours.</i>",
            parse_mode="HTML"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    user = update.effective_user
    message = update.message.text
    
    # Handle support requests
    if context.user_data.get("awaiting_support"):
        context.user_data["awaiting_support"] = False
        
        # Notify user
        await update.message.reply_text(
            "✅ <b>Request Received!</b>\n\n"
            "Thank you for contacting DattoMart Support. Our team has received your request and will get back to you shortly.\n\n"
            "<i>Please allow up to 24 business hours for a response.</i>",
            parse_mode="HTML"
        )
        
        # Notify admin
        admin_message = (
            f"🔔 <b>New Support Request | DattoMart</b>\n\n"
            f"<b>User:</b> {user.full_name} (ID: {user.id})\n"
            f"<b>Username:</b> @{user.username}\n"
            f"<b>Message:</b>\n{message}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode="HTML"
        )
        
        return
    
    # Default response for non-support messages
    await update.message.reply_text(
        "ℹ️ Please use /start to access our support options."
    )

async def reply_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow admin to reply to users."""
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Access denied.")
        return
    
    try:
        # Parse command: /reply <user_id> <message>
        parts = update.message.text.split(maxsplit=2)
        if len(parts) < 3:
            await update.message.reply_text(
                "UsageId: /reply <user_id> <message>\n"
                "Example: /reply 123456789 Your credentials have been activated!"
            )
            return
        
        user_id = int(parts[1])
        reply_message = parts[2]
        
        # Send reply to user
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🛡️ <b>DattoMart Support:</b>\n{reply_message}",
            parse_mode="HTML"
        )
        
        # Confirm to admin
        await update.message.reply_text("✅ Message sent successfully!")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "UsageId: /reply <user_id> <message>\n"
            "Example: /reply 123456789 Your credentials have been activated!"
        )
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        await update.message.reply_text("❌ Failed to send message. Please check the user ID.")

def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reply", reply_to_user))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    logger.info("DattoMart Support Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()