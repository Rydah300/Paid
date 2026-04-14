```python
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- CONFIGURATION ---
BOT_TOKEN = '8034411966:AAEHkKmkysF6LO9RgYLzxdi78u_FA8pbPXE'
ADMIN_CHAT_ID = 8792427543

# Wallets
WALLETS = {
    'BTC': '18ajtpJY22K4q47Bfpdoc61QASLjoKKsKf',
    'USDT (TRC20)': 'THVdG2CKwhNsn5LgxmZtxWeweUUPHEgTpu',
    'USDT (ERC20)': '0xb22af6a4ae905b0a86d7b12b1840fa929d69f9c5',
    'LTC': 'LQ68YQccXg9k3ZeNaAnaDKZY2UzfJ63v1y',
    'ETH': '0xa97827047694fce4e551af3d940e3bf0433c2fb3'
}

# Pricing
PRICES = {
    '8GB': 100,
    '16GB': 150
}

# --- STATES ---
(SELECT_SERVICE, SELECT_COUNTRY, SELECT_STORAGE, 
 BROWSING_CART, CHECKOUT_PAYMENT, AWAITING_TXID) = range(6)

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- KEYBOARD FUNCTIONS ---

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("Buy RDP"), KeyboardButton("Buy VPS")],
        [KeyboardButton("View Cart"), KeyboardButton("Clear Cart")],
        [KeyboardButton("Contact Support"), KeyboardButton("About Us")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_country_keyboard(service_type):
    keyboard = [
        [InlineKeyboardButton("USA", callback_data=f'country_US|{service_type}')],
        [InlineKeyboardButton("UK", callback_data=f'country_UK|{service_type}')],
        [InlineKeyboardButton("Pakistan", callback_data=f'country_Pakistan|{service_type}')],
        [InlineKeyboardButton("Germany", callback_data=f'country_Germany|{service_type}')],
        [InlineKeyboardButton("Europe", callback_data=f'country_Europe|{service_type}')],
        [InlineKeyboardButton("Main Menu", callback_data='action_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_storage_keyboard(service_type, country):
    keyboard = [
        [InlineKeyboardButton(f"8GB RAM - ${PRICES['8GB']}", callback_data=f'storage_8GB|{service_type}|{country}')],
        [InlineKeyboardButton(f"16GB RAM - ${PRICES['16GB']}", callback_data=f'storage_16GB|{service_type}|{country}')],
        [InlineKeyboardButton("Back", callback_data=f'back_to_country|{service_type}')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = []
    for currency in WALLETS:
        keyboard.append([InlineKeyboardButton(currency, callback_data=f'pay_{currency}')])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data='cancel_checkout')])
    return InlineKeyboardMarkup(keyboard)

def get_cart_keyboard():
    keyboard = [
        [InlineKeyboardButton("Checkout Now", callback_data='start_checkout')],
        [InlineKeyboardButton("Add More Items", callback_data='add_more')],
        [InlineKeyboardButton("Clear Cart", callback_data='clear_cart')],
        [InlineKeyboardButton("Main Menu", callback_data='action_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['cart'] = []
    
    welcome_text = (
        f"Welcome to HiTent Server, {user.first_name}!\n\n"
        "Your #1 Source for Bulletproof RDP & VPS\n"
        "All Ports Open | DDoS Protected | 99.9% Uptime\n\n"
        "Instructions:\n"
        "1. Select 'Buy RDP' or 'Buy VPS'\n"
        "2. Configure your server\n"
        "3. Add to Cart\n"
        "4. Checkout"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_data = context.user_data

    if 'cart' not in user_data:
        user_data['cart'] = []

    # --- NAVIGATION: MAIN MENU ---
    if data == 'action_main_menu':
        try:
            await query.edit_message_text("Returned to Main Menu.", reply_markup=get_main_keyboard())
        except Exception:
            pass # Ignore if message wasn't modified
        return ConversationHandler.END

    # --- STEP 1: SELECT COUNTRY ---
    if data.startswith('country_'):
        parts = data.split('|')
        country = parts[0].replace('country_', '')
        service_type = parts[1]
        user_data['temp_service'] = service_type
        text = f"Selected Location: {country}\n\nSelect RAM for {service_type}:"
        await query.edit_message_text(text, reply_markup=get_storage_keyboard(service_type, country))
        return SELECT_STORAGE

    # --- STEP 2: SELECT STORAGE (ADD TO CART) ---
    if data.startswith('storage_'):
        parts = data.split('|')
        storage = parts[0].replace('storage_', '')
        service_type = parts[1]
        country = parts[2]
        price = PRICES[storage]
        
        item = {
            'service': service_type,
            'country': country,
            'storage': storage,
            'price': price
        }
        user_data['cart'].append(item)
        
        cart_count = len(user_data['cart'])
        total = sum(i['price'] for i in user_data['cart'])
        
        text = (
            f"Added to Cart!\n\n"
            f"{service_type} ({storage}) - {country}\n"
            f"Price: ${price}\n\n"
            f"Cart Items: {cart_count}\n"
            f"Total: ${total}"
        )
        await query.edit_message_text(text, reply_markup=get_cart_keyboard())
        return BROWSING_CART

    # --- BACK BUTTONS ---
    if data.startswith('back_to_country'):
        service_type = data.split('|')[1]
        await query.edit_message_text("Select Location:", reply_markup=get_country_keyboard(service_type))
        return SELECT_COUNTRY

    # --- CART ACTIONS ---
    if data == 'add_more':
        await query.message.reply_text("Select next item:", reply_markup=get_main_keyboard())
        return SELECT_SERVICE

    if data == 'clear_cart':
        user_data['cart'] = []
        await query.edit_message_text("Cart Cleared.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    if data == 'cancel_checkout':
        await query.edit_message_text("Checkout cancelled.", reply_markup=get_cart_keyboard())
        return BROWSING_CART

    # --- CHECKOUT FLOW ---
    if data == 'start_checkout':
        cart = user_data.get('cart', [])
        if not cart:
            await query.answer("Cart is empty!", show_alert=True)
            return BROWSING_CART
            
        total = sum(i['price'] for i in cart)
        items_list = "\n".join([f"- {item['service']} | {item['country']} | {item['storage']} (${item['price']})" for item in cart])
        
        text = f"Final Checkout\n\nItems:\n{items_list}\n\nTotal Amount: ${total}\n\nSelect Payment:"
        await query.edit_message_text(text, reply_markup=get_payment_keyboard())
        return CHECKOUT_PAYMENT

    # --- PAYMENT SELECTION ---
    if data.startswith('pay_'):
        currency = data.replace('pay_', '')
        wallet = WALLETS[currency]
        total = sum(i['price'] for i in user_data['cart'])
        
        user_data['payment_currency'] = currency
        user_data['payment_wallet'] = wallet
        
        text = (
            f"Payment Method: {currency}\n\n"
            f"Send ${total} to:\n\n{wallet}\n\n"
            "Paste the Transaction Hash below to confirm."
        )
        await query.edit_message_text(text)
        return AWAITING_TXID

    return ConversationHandler.END

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    text = update.message.text
    
    if 'cart' not in user_data:
        user_data['cart'] = []

    # --- MAIN MENU HANDLERS ---
    if text == "Buy RDP":
        await update.message.reply_text("Select Country for RDP:", reply_markup=get_country_keyboard('RDP'))
        return SELECT_COUNTRY
        
    if text == "Buy VPS":
        await update.message.reply_text("Select Country for VPS:", reply_markup=get_country_keyboard('VPS'))
        return SELECT_COUNTRY
        
    if text == "View Cart":
        cart = user_data.get('cart', [])
        if not cart:
            await update.message.reply_text("Your cart is empty.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        
        total = sum(i['price'] for i in cart)
        items_list = "\n".join([f"{idx+1}. {item['service']} | {item['country']} | {item['storage']} (${item['price']})" for idx, item in enumerate(cart)])
        msg = f"Your Cart\n\n{items_list}\n\nTotal: ${total}"
        await update.message.reply_text(msg, reply_markup=get_cart_keyboard())
        return BROWSING_CART
        
    if text == "Clear Cart":
        user_data['cart'] = []
        await update.message.reply_text("Cart has been cleared.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    if text == "Contact Support":
        await update.message.reply_text("For support, contact admin: @hitent_support", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    if text == "About Us":
        about = (
            "HiTent Server\n\n"
            "Providing elite bulletproof hosting solutions since 2020.\n"
            "We specialize in offshore hosting with high anonymity and DDoS protection."
        )
        await update.message.reply_text(about, reply_markup=get_main_keyboard())
        return ConversationHandler.END

    # --- TRANSACTION HASH HANDLER ---
    if context.user_data.get('payment_currency'):
        tx_hash = text
        cart = user_data.get('cart', [])
        total = sum(i['price'] for i in cart)
        currency = user_data.get('payment_currency')
        wallet = user_data.get('payment_wallet')
        
        items_str = "\n".join([f"- {c['service']} ({c['storage']}) {c['country']}" for c in cart])
        
        admin_msg = (
            f"NEW ORDER ALERT\n\n"
            f"User ID: {update.effective_user.id}\n"
            f"Username: @{update.effective_user.username}\n\n"
            f"Order Details:\n{items_str}\n"
            f"Total: ${total}\n\n"
            f"Payment Info:\n"
            f"Currency: {currency}\n"
            f"To Wallet: {wallet}\n"
            f"TxID: {tx_hash}"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
            
            await update.message.reply_text(
                "Order Submitted Successfully!\n\n"
                "Payment is being verified on the blockchain.\n"
                "Please wait for 30mins - 1hour to receive your Server details.\n\n"
                "Thank you for choosing HiTent Server!",
                reply_markup=get_main_keyboard()
            )
            
            user_data.clear()
            user_data['cart'] = []
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("Error processing order. Contact support.")
            
        return ConversationHandler.END

    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

# --- MAIN EXECUTION ---

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
        states={
            SELECT_SERVICE: [CallbackQueryHandler(button_click)],
            SELECT_COUNTRY: [CallbackQueryHandler(button_click)],
            SELECT_STORAGE: [CallbackQueryHandler(button_click)],
            BROWSING_CART: [CallbackQueryHandler(button_click)],
            CHECKOUT_PAYMENT: [CallbackQueryHandler(button_click)],
            AWAITING_TXID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel_conv)],
    )

    application.add_handler(conv_handler)

    print("HiTent Server Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
```