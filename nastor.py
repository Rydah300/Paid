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
import uuid
import re

# --- CONFIGURATION ---
BOT_TOKEN = "8696958960:AAEHzxAOp95GOQDgo9XNhYL8oC64ocVYyP0"
ADMIN_ID = 7926187033

WALLETS = {
    "BTC": "bc1qu3nvpxd6qhdygkjyk46q29j6m54a9k0a03h4ky",
    "ETH": "0x342c5e23414ebe0a3325d311b8604b73006f8a94",
    "USDT_TRC20": "TTzjcKZFhjpXon6E7qrQSxsJAwQfjL2Byp",
    "USDT_ERC20": "0x342c5e23414ebe0a3325d311b8604b73006f8a94",
    "LTC": "LQpjG8CXURMzARndKQd5ey665iBqR511iu",
}

SMTP_SERVICES = {
    "Biglobe(JP)": 150,
    "Sakura(JP)": 100,
    "Kagoya(JP)": 150,
    "Nifty(JP)": 100,
    "Plala(JP)": 150,
    "Asahi Net(JP)": 100,
    "OCN(JP)": 100,
    "Lollipop(JP)": 100,
}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- WELCOME MESSAGE ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇯🇵 Biglobe (JP) - $150", callback_data="smtp_Biglobe(JP)")],
        [InlineKeyboardButton("🌸 Sakura (JP) - $100", callback_data="smtp_Sakura(JP)")],
        [InlineKeyboardButton("🏯 Kagoya (JP) - $150", callback_data="smtp_Kagoya(JP)")],
        [InlineKeyboardButton("📮 Nifty (JP) - $100", callback_data="smtp_Nifty(JP)")],
        [InlineKeyboardButton("🌐 Plala (JP) - $150", callback_data="smtp_Plala(JP)")],
        [InlineKeyboardButton("📰 Asahi Net (JP) - $100", callback_data="smtp_Asahi Net(JP)")],
        [InlineKeyboardButton("📡 OCN (JP) - $100", callback_data="smtp_OCN(JP)")],
        [InlineKeyboardButton("🍭 Lollipop (JP) - $100", callback_data="smtp_Lollipop(JP)")],
        [InlineKeyboardButton("🛠️ Contact Support", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎌 <b>Welcome to Nastor Marketplace!</b> 🎌\n\n"
        "<b>Japan's Premier SMTP Provider</b> • 99.9% Uptime • Zero Logs • Bulletproof\n\n"
        "✅ Premium Japanese SMTP Servers\n"
        "✅ Instant Delivery After Payment\n"
        "✅ Crypto Payments Only (BTC/ETH/USDT/LTC)\n"
        "✅ 24/7 Priority Support\n\n"
        "<i>Select your desired SMTP server below:</i>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

# --- MENU HANDLERS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "support":
        context.user_data["awaiting_support"] = True
        await query.edit_message_text(
            "📨 <b>Support Desk</b>\n\n"
            "Describe your issue or question. Our team will respond within 24 hours.\n\n"
            "<i>Note: For payment issues, include your Order ID.</i>",
            parse_mode="HTML"
        )
        return

    if data.startswith("smtp_"):
        smtp_name = data[5:]
        price = SMTP_SERVICES[smtp_name]
        context.user_data["selected_smtp"] = smtp_name
        context.user_data["price"] = price
        
        keyboard = [
            [InlineKeyboardButton("₿ BTC", callback_data="pay_BTC")],
            [InlineKeyboardButton("Ξ ETH", callback_data="pay_ETH")],
            [InlineKeyboardButton("💲 USDT (TRC20)", callback_data="pay_USDT_TRC20")],
            [InlineKeyboardButton("💲 USDT (ERC20)", callback_data="pay_USDT_ERC20")],
            [InlineKeyboardButton("Ł LTC", callback_data="pay_LTC")],
        ]
        await query.edit_message_text(
            f"💰 <b>Order Summary</b>\n"
            f"SMTP Server: <b>{smtp_name}</b>\n"
            f"Price: <b>${price}</b>\n\n"
            f"<b>Select payment method:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    if data.startswith("pay_"):
        crypto = data[4:]
        wallet = WALLETS[crypto]
        smtp_name = context.user_data["selected_smtp"]
        price = context.user_data["price"]
        order_id = str(uuid.uuid4())[:8].upper()
        
        context.user_data["order_id"] = order_id
        context.user_data["crypto"] = crypto
        context.user_data["awaiting_txid"] = True
        
        # Format crypto name for display
        crypto_display = {
            "BTC": "Bitcoin (BTC)",
            "ETH": "Ethereum (ETH)",
            "USDT_TRC20": "USDT (TRC20)",
            "USDT_ERC20": "USDT (ERC20)",
            "LTC": "Litecoin (LTC)"
        }.get(crypto, crypto)
        
        msg = (
            f"⚠️ <b>Payment Instructions</b>\n\n"
            f"<b>Order ID:</b> <code>{order_id}</code>\n"
            f"<b>Service:</b> {smtp_name}\n"
            f"<b>Amount:</b> ${price} USD equivalent in {crypto_display}\n"
            f"<b>Wallet:</b> <code>{wallet}</code>\n\n"
            f"📤 <b>After sending payment, reply with your TXID:</b>"
        )
        await query.edit_message_text(msg, parse_mode="HTML")
        return

# --- MESSAGE HANDLERS ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Handle TXID submission
    if context.user_data.get("awaiting_txid"):
        context.user_data["awaiting_txid"] = False
        order_id = context.user_data["order_id"]
        smtp_name = context.user_data["selected_smtp"]
        crypto = context.user_data["crypto"]
        price = context.user_data["price"]
        
        # Validate TXID format (basic check)
        if not re.match(r"^[a-zA-Z0-9]{20,}$", text):
            await update.message.reply_text(
                "❌ <b>Invalid TXID format!</b>\n\n"
                "Please send a valid transaction ID (alphanumeric, 20+ characters).",
                parse_mode="HTML"
            )
            context.user_data["awaiting_txid"] = True
            return
        
        # Notify user
        await update.message.reply_text(
            "⏳ <b>Payment Received!</b>\n\n"
            "We're verifying your transaction. Our team will deliver your SMTP credentials "
            "within 24 hours via Telegram.\n\n"
            "<i>Order ID: <code>{}</code></i>".format(order_id),
            parse_mode="HTML"
        )
        
        # Alert admin
        admin_msg = (
            f"🔔 <b>NEW ORDER | NASTOR MARKETPLACE</b>\n\n"
            f"<b>User:</b> <a href='tg://user?id={user_id}'>{user_id}</a>\n"
            f"<b>Order ID:</b> <code>{order_id}</code>\n"
            f"<b>Service:</b> {smtp_name}\n"
            f"<b>Price:</b> ${price}\n"
            f"<b>Crypto:</b> {crypto}\n"
            f"<b>TXID:</b> <code>{text}</code>"
        )
        await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
        return

    # Handle support messages
    if context.user_data.get("awaiting_support"):
        context.user_data["awaiting_support"] = False
        await update.message.reply_text(
            "✅ <b>Message Sent!</b>\n\n"
            "Our support team will contact you shortly. For urgent issues, include 'URGENT' in your message.",
            parse_mode="HTML"
        )
        support_msg = (
            f"🆘 <b>SUPPORT TICKET | NASTOR MARKETPLACE</b>\n\n"
            f"<b>User:</b> <a href='tg://user?id={user_id}'>{user_id}</a>\n"
            f"<b>Message:</b> {text}"
        )
        await context.bot.send_message(ADMIN_ID, support_msg, parse_mode="HTML")
        return

    # Default response
    await update.message.reply_text("Use /start to browse SMTP services.")

# --- ADMIN REPLY COMMAND ---
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Access denied.")
        return

    try:
        target_id = int(context.args[0])
        message = " ".join(context.args[1:])
        await context.bot.send_message(
            target_id, 
            f"🛡️ <b>Nastor Marketplace Support:</b>\n{message}", 
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Message sent successfully!")
    except (IndexError, ValueError):
        await update.message.reply_text(
            "UsageId: /reply <user_id> <message>\n"
            "Example: /reply 123456789 Your SMTP credentials are ready!"
        )

# --- MAIN FUNCTION ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Nastor Marketplace Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()