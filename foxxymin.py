import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import html

# === CONFIGURATION ===
BOT_TOKEN = "8372265510:AAFkwlaCbUoS8QqVd2rRQzWRsJ7WiqVZESQ"
ADMIN_CHAT_ID = 8482794274

WALLETS = {
    "USDT (TRC20)": "TTzjcKZFhjpXon6E7qrQSxsJAwQfjL2Byp",
    "USDT (ERC20)": "0xa97827047694fce4e551af3d940e3bf0433c2fb3",
    "LTC": "LQ68YQccXg9k3ZeNaAnaDKZY2UzfJ63v1y",
    "BTC": "18ajtpJY22K4q47Bfpdoc61QASLjoKKsKf",
    "ETH": "0xb22af6a4ae905b0a86d7b12b1840fa929d69f9c5"
}

PRODUCTS = {
    "datto": {"name": "Datto RMM", "price": "$600"},
    "ninjaone": {"name": "NinjaOne RMM", "price": "$700"},
    "rdp": {"name": "Bulletproof RDP (32GB RAM)", "price": "$100"}
}

SELECTING_PRODUCT, SELECTING_WALLET, AWAITING_TXID, SUPPORT_CHAT, AWAITING_FILE = range(5)  # Added AWAITING_FILE state

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# === NEW: ADMIN FILE SENDING ===
async def admin_sendfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts file delivery flow: /sendfile <user_id>"""
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    if not context.args or len(context.args) != 1:
        await update.message.reply_text("UsageId: /sendfile <user_id>")
        return

    try:
        target_user_id = int(context.args[0])
        context.user_data['target_file_user'] = target_user_id
        await update.message.reply_text(
            f"📤 Send me the file/photo to deliver to user {target_user_id}.\n"
            "I accept: images, documents, videos, audio, ZIPs—anything!"
        )
        return AWAITING_FILE
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be numeric.")
        return

async def receive_admin_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures admin's file and forwards it to target user"""
    target_user_id = context.user_data.get('target_file_user')
    if not target_user_id:
        await update.message.reply_text("Session expired. Use /sendfile again.")
        return ConversationHandler.END

    # Extract file from any media type
    file = None
    caption = update.message.caption or ""  # Preserve admin's caption
    
    if update.message.document:
        file = update.message.document
        await context.bot.send_document(
            chat_id=target_user_id,
            document=file.file_id,
            caption=caption
        )
    elif update.message.photo:
        photo = update.message.photo[-1]  # Highest resolution
        await context.bot.send_photo(
            chat_id=target_user_id,
            photo=photo.file_id,
            caption=caption
        )
    elif update.message.video:
        await context.bot.send_video(
            chat_id=target_user_id,
            video=update.message.video.file_id,
            caption=caption
        )
    elif update.message.audio:
        await context.bot.send_audio(
            chat_id=target_user_id,
            audio=update.message.audio.file_id,
            caption=caption
        )
    elif update.message.voice:
        await context.bot.send_voice(
            chat_id=target_user_id,
            voice=update.message.voice.file_id,
            caption=caption
        )
    else:
        await update.message.reply_text("❌ Unsupported file type. Send an image, document, video, or audio.")
        return AWAITING_FILE

    await update.message.reply_text(f"✅ File delivered to user {target_user_id}!")
    context.user_data.pop('target_file_user', None)
    return ConversationHandler.END

# === Helper: Send Welcome Menu ===
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome message regardless of context (command or callback)."""
    user = update.effective_user
    welcome_text = (
        f"👋 Welcome to <b>FoxyMarket</b>, {html.escape(user.first_name)}!\n\n"
        "🔐 Premium RMM & Bulletproof RDP Solutions\n"
        "⚡ Instant Delivery | 🔒 Secure | 💎 Trusted Since 2023\n\n"
        "<b>Select a service below to get started:</b>"
    )
    keyboard = [
        [InlineKeyboardButton("🛡️ Datto RMM — $600 🔥 NEW PRICE!", callback_data="product_datto")],
        [InlineKeyboardButton("🐉 NinjaOne RMM — $700", callback_data="product_ninjaone")],
        [InlineKeyboardButton("💻 Bulletproof RDP (32GB) — $100", callback_data="product_rdp")],
        [InlineKeyboardButton("🛠️ Contact Support", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        logger.warning("send_welcome called with no message or callback_query")

# === START COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome(update, context)
    return SELECTING_PRODUCT

# === PRODUCT SELECTION ===
async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "support":
        await query.edit_message_text("📩 Please describe your issue or question. Our team will respond shortly.")
        return SUPPORT_CHAT

    product_key = data.replace("product_", "")
    if product_key not in PRODUCTS:
        await query.edit_message_text("❌ Invalid selection.")
        return SELECTING_PRODUCT

    context.user_data['selected_product'] = product_key
    product = PRODUCTS[product_key]

    wallet_buttons = [
        [InlineKeyboardButton(coin, callback_data=f"wallet_{coin}")]
        for coin in WALLETS.keys()
    ]
    wallet_buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
    reply_markup = InlineKeyboardMarkup(wallet_buttons)

    await query.edit_message_text(
        f"✅ You selected:\n<b>{html.escape(product['name'])}</b>\n💰 Price: {html.escape(product['price'])}\n\n"
        "<b>Choose your payment method:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return SELECTING_WALLET

# === WALLET SELECTION ===
async def wallet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_menu":
        await send_welcome(update, context)
        return SELECTING_PRODUCT

    if data.startswith("wallet_"):
        coin = data.replace("wallet_", "")
        address = WALLETS.get(coin)
        if not address:
            await query.edit_message_text("❌ Invalid wallet selected.")
            return SELECTING_WALLET

        context.user_data['selected_coin'] = coin
        context.user_data['wallet_address'] = address
        product_key = context.user_data['selected_product']
        product = PRODUCTS[product_key]

        safe_coin = html.escape(coin)
        safe_product = html.escape(product['name'])
        safe_price = html.escape(product['price'])
        safe_address = html.escape(address)

        msg = (
            f"<b>🪙 Payment Details</b>\n\n"
            f"Service: <b>{safe_product}</b>\n"
            f"Amount: <b>{safe_price}</b>\n"
            f"Coin: <b>{safe_coin}</b>\n"
            f"Address: <code>{safe_address}</code>\n\n"
            "⚠️ Send exact amount. After payment, paste your <b>Transaction ID (TXID)</b> below."
        )
        await query.edit_message_text(msg, parse_mode="HTML")
        return AWAITING_TXID

    return SELECTING_WALLET

# === TXID SUBMISSION ===
async def receive_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txid = update.message.text.strip()
    if not txid:
        await update.message.reply_text("❌ Please send a valid TXID.")
        return AWAITING_TXID

    product_key = context.user_data.get('selected_product')
    coin = context.user_data.get('selected_coin')
    if not product_key or not coin:
        await update.message.reply_text("Session expired. Please start again with /start.")
        return ConversationHandler.END

    user = update.effective_user
    product = PRODUCTS[product_key]

    await update.message.reply_text(
        "⏳ We are verifying your payment. You will hear from us within 10 minutes!"
    )

    admin_msg = (
        f"🔔 <b>NEW ORDER — FoxyMarket</b>\n\n"
        f"👤 User: @{user.username or 'N/A'} (ID: {user.id})\n"
        f"📦 Product: {html.escape(product['name'])}\n"
        f"💰 Price: {html.escape(product['price'])}\n"
        f"🪙 Coin: {html.escape(coin)}\n"
        f"🆔 TXID: <code>{html.escape(txid)}</code>\n\n"
        f"Reply with: <code>/reply {user.id} your message</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="HTML")

    context.user_data.clear()
    return ConversationHandler.END

# === SUPPORT CHAT ===
async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text

    admin_alert = (
        f"🆘 <b>SUPPORT TICKET — FoxyMarket</b>\n\n"
        f"👤 User: @{user.username or 'N/A'} (ID: {user.id})\n"
        f"💬 Message: {html.escape(message)}\n\n"
        f"Reply with: <code>/reply {user.id} your response</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_alert, parse_mode="HTML")
    await update.message.reply_text("✅ Your message has been sent to support. We’ll get back to you soon!")
    return ConversationHandler.END

# === ADMIN REPLY ===
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("UsageId: /reply <user_id> <message>")
        return

    try:
        target_user_id = int(context.args[0])
        reply_text = ' '.join(context.args[1:])
        safe_reply = html.escape(reply_text)
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📬 <b>Support Reply</b>:\n\n{safe_reply}",
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Message sent to user.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# === CANCEL ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled. Type /start to begin again.")
    return ConversationHandler.END

# === MAIN ===
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('sendfile', admin_sendfile)  # Added entry point
        ],
        states={
            SELECTING_PRODUCT: [CallbackQueryHandler(product_selected)],
            SELECTING_WALLET: [CallbackQueryHandler(wallet_selected)],
            AWAITING_TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_txid)],
            SUPPORT_CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_message)],
            AWAITING_FILE: [  # New state for file capture
                MessageHandler(
                    (filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE) 
                    & ~filters.COMMAND, 
                    receive_admin_file
                )
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('reply', admin_reply))

    async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Use /start to begin.")

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    application.run_polling()

if __name__ == '__main__':
    main()