import os
import sqlite3
import threading
from flask import Flask
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- বটের ঘুম ভাঙিয়ে রাখার অংশ (Keep-Alive) ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    # রেন্ডারের জন্য পোর্ট ৮০৮০ ব্যবহার করা হয়েছে
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- কনফিগারেশন ---
TOKEN = "8797001893:AAFjzHbtNGcibUu0zewY9QdOml-94bOogXE"
ADMIN_ID = 7541488098

# কনভারসেশন স্টেটস
GET_USERNAME, GET_PASS, GET_2FA, SET_PAYMENT = range(4)

# --- ডাটাবেস ফাংশন ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0.0, 
                       bkash TEXT DEFAULT 'Not Set', nagad TEXT DEFAULT 'Not Set', 
                       rocket TEXT DEFAULT 'Not Set', binance TEXT DEFAULT 'Not Set')''')
    conn.commit()
    conn.close()

def update_user_db(user_id, username=None, field=None, value=None):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    if username:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    if field and value:
        cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    update_user_db(user.id, username=user.username)
    
    # আপনার নতুন সিরিয়াল অনুযায়ী সিম্বলসহ কিবোর্ড
    keyboard = [
        ['🚀 Work Start'],
        ['🔄 Restart', '📜 Rules'],
        ['💳 Payment Method']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Main Menu:', reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if 'Restart' in text:
        return await start(update, context)

    elif 'Rules' in text:
        await update.message.reply_text("📜 **আমাদের নিয়মাবলী:**\n১. সঠিক তথ্য দিন।\n২. পেমেন্ট মেথড সেট করে রাখুন।")

    elif 'Payment Method' in text:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT bkash, nagad, rocket, binance FROM users WHERE user_id=?", (user.id,))
        row = cursor.fetchone() or ('Not Set', 'Not Set', 'Not Set', 'Not Set')
        conn.close()

        msg = (f"🏦 **Your Payment Methods:**\n\n"
               f"Bkash: `{row[0]}`\nNagad: `{row[1]}`\n"
               f"Rocket: `{row[2]}`\nBinance: `{row[3]}`\n\n"
               f"যেকোনো একটি আপডেট করতে নিচের বাটনে ক্লিক করুন:")
        
        keyboard = [
            [InlineKeyboardButton("Bkash", callback_data="pay_bkash"), InlineKeyboardButton("Nagad", callback_data="pay_nagad")],
            [InlineKeyboardButton("Rocket", callback_data="pay_rocket"), InlineKeyboardButton("Binance", callback_data="pay_binance")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif 'Work Start' in text:
        keyboard = [['🔵 FB 00 Fnd 2fa'], ['🟠 IG']]
        await update.message.reply_text('Select Work Category:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif 'FB 00 Fnd 2fa' in text:
        context.user_data['cat'] = "FB 00 Fnd 2fa"
        keyboard = [['📁 File'], ['🆔 Single ID']]
        await update.message.reply_text('Choose Option:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif 'IG' in text:
        keyboard = [['🍪 Cookies'], ['🔐 2fa'], ['📱 Number2fa']]
        await update.message.reply_text('IG Options:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif text in ['🍪 Cookies', '🔐 2fa', '📱 Number2fa']:
        context.user_data['cat'] = f"IG - {text}"
        keyboard = [['📁 File'], ['🆔 Single ID']]
        await update.message.reply_text(f'Selected {text}:', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    elif 'Single ID' in text:
        await update.message.reply_text('Please enter Username:', reply_markup=ReplyKeyboardRemove())
        return GET_USERNAME

    elif text == '/admin' and user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT user_id, username FROM users"); all_u = cursor.fetchall(); conn.close()
        msg = "👤 **User List:**\n"
        for u in all_u: msg += f"• @{u[1]} (`{u[0]}`)\n"
        await update.message.reply_text(msg + "\nCheck with `/check [ID]`")

async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID: return
    try:
        uid = context.args[0]
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,)); d = cursor.fetchone(); conn.close()
        if d:
            msg = (f"👤 Profile: @{d[1]}\n🆔 ID: `{d[0]}`\n💰 Balance: ৳{d[2]}\n\n"
                   f"🏦 Payment:\nBkash: {d[3]}\nNagad: {d[4]}\nRocket: {d[5]}\nBinance: {d[6]}")
            await update.message.reply_text(msg, parse_mode='Markdown')
    except: pass

# --- কনভারসেশন হ্যান্ডলারস ---
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_name'] = update.message.text
    await update.message.reply_text('Please enter Password:')
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_pass'] = update.message.text
    await update.message.reply_text('Please enter 2FA:')
    return GET_2FA

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    u_name, u_pass, u_2fa = context.user_data['u_name'], context.user_data['u_pass'], update.message.text
    cat = context.user_data.get('cat', 'General')

    # অ্যাডমিনকে কোড ব্লক আকারে পাঠানো
    admin_msg = (f"📥 **New Submission**\nCategory: {cat}\nFrom: @{user.username} (`{user.id}`)\n\n"
                 f"User: `{u_name}`\nPass: `{u_pass}`\n2FA: `{u_2fa}`")
    kb = [[InlineKeyboardButton("৳6 Add", callback_data=f"add_6_{user.id}")]]
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    await update.message.reply_text("ID Received! আপনার আইডি রিপোর্টের জন্য ২ ঘণ্টা অপেক্ষা করুন।")
    return await start(update, context)

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("pay_"):
        method = data.split("_")[1]
        context.user_data['editing_pay'] = method
        await query.message.reply_text(f"Send your {method.capitalize()} address/number:")
        return SET_PAYMENT
    elif data.startswith("add_6_"):
        uid = int(data.split("_")[2])
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("UPDATE users SET balance = balance + 6 WHERE user_id = ?", (uid,)); conn.commit(); conn.close()
        await query.edit_message_reply_markup(reply_markup=None)
        try: await context.bot.send_message(chat_id=uid, text="✅ আপনার একাউন্টে ৳6 যোগ করা হয়েছে।")
        except: pass

async def save_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = context.user_data.get('editing_pay')
    update_user_db(update.message.from_user.id, field=method, value=update.message.text)
    await update.message.reply_text(f"✅ {method.capitalize()} address saved!")
    return await start(update, context)

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, 
                                   caption=f"📄 New File from @{user.username}")
    await update.message.reply_text('File Received')

# --- মেইন ফাংশন ---
def main():
    init_db()
    keep_alive()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('Single ID'), handle_menu),
            CallbackQueryHandler(pay_callback, pattern="^pay_")
        ],
        states={
            GET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            GET_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_2fa)],
            SET_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_payment)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_user))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(pay_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    
    app.run_polling()

if __name__ == '__main__':
    main()
