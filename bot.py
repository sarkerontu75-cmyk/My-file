import os
import sqlite3
import threading
from flask import Flask
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- KEEP ALIVE ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is Alive!"
def keep_alive(): threading.Thread(target=lambda: app_flask.run(host='0.0.0.0', port=8080), daemon=True).start()

# কনফিগারেশন
TOKEN = "8797001893:AAFjzHbtNGcibUu0zewY9QdOml-94bOogXE"
ADMIN_ID = 7541488098

GET_USERNAME, GET_PASS, GET_2FA, SET_PAYMENT = range(4)

# ডাটাবেস
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
    if username: cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    if field and value: cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

# মেইন মেনু (রিস্টার্ট সবসময় নিচে থাকবে)
def get_main_menu():
    keyboard = [
        ['🚀 Work Start'],
        ['📜 Rules', '💳 Payment Method'],
        ['🔄 Restart'] # রিস্টার্ট সবার নিচে পার্মানেন্ট
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    update_user_db(user.id, username=user.username)
    await update.message.reply_text('Main Menu:', reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if 'Restart' in text:
        return await start(update, context)

    elif 'Rules' in text:
        rules_text = (
            "🛑 **ওপেন চ্যালেঞ্জ: আগে কাজ দেখুন, তারপর বিশ্বাস করুন!** 🛑\n\n"
            "অনেকেই মনে করেন \"ছোট চ্যানেল মানেই ভালো সার্ভিস দিতে পারবে না\"—আমরা এই ভুল ধারণাটি ভেঙে দিতে এসেছি। আমরা মুখে বড় কথা নয়, কাজে বিশ্বাসী। 💯\n\n"
            "✅ **আমাদের সরাসরি চ্যালেঞ্জ:**\n"
            "আমাদের সাথে অন্তত একবার কাজ করে দেখুন। আমরা আপনাকে সেরা সার্ভিসের ১০০% নিশ্চয়তা দিচ্ছি।\n\n"
            "🛑 **যদি রিপোর্ট ভালো না আসে?**\n"
            "আমাদের চ্যানেলের কমেন্ট বক্স সবার জন্য সবসময় খোলা! যদি আমাদের কাজে আপনি বিন্দুমাত্র অসন্তুষ্ট হন, তবে কমেন্টে আপনার যা মনে চায় তা-ই বলে যাবেন। আমরা কথা দিচ্ছি, আপনার একটি মন্তব্যও ডিলিট করা হবে না। 🗣️\n\n"
            "💰 **রেট ও সাপোর্ট নিয়ে কিছু কথা (মন দিয়ে পড়ুন):**\n"
            "অন্যান্য বড় চ্যানেল থেকে আমাদের রেট হয়তো ১০ থেকে ২০ পয়সা কম হতে পারে। কিন্তু একবার ঠান্ডা মাথায় ভেবে দেখুন—আমি আপনাদের প্রত্যেককে পার্সোনালি কাজ বুঝিয়ে দিই। যারা ভিডিও দেখেও কাজ বোঝেন না, তাদের আমি নিজের মূল্যবান সময় দিয়ে হাতে-কলমে শিখিয়ে দিই।\n\n"
            "\"ভাই, আমিও তো একজন মানুষ, আমারও সময়ের দাম আছে। এই যে আপনাদের পেছনে দিন-রাত সময় দিচ্ছি, এটার কি কোনো মূল্য নেই?\"\n\n"
            "🚀 **সুসংবাদ:** রেট খুব শীঘ্রই বাড়বে! জাস্ট ২ থেকে ৩ দিন অপেক্ষা করুন, আমরা আপনাদের জন্য বড় কিছু নিয়ে আসছি। ⏳\n\n"
            "**কেন আমাদের সাথে কাজ করবেন?**\n"
            "১. ১০০% স্বচ্ছতা ও সততা: ধোঁকাবাজির কোনো জায়গা নেই।\n"
            "২. পার্সোনাল গাইডেন্স: যারা নতুন, তাদের জন্য আমি নিজে আছি।\n"
            "৩. সরাসরি ফিডব্যাক: আপনার মতামতই আমাদের কাছে সবচেয়ে বড়।\n\n"
            "সুযোগ দিয়ে দেখুন, নিরাশ হবেন না। ইনশাআল্লাহ! 🤝\n\n"
            "✨ **সাপোর্টের জন্য নক দিন:** @Dinanhaji"
        )
        await update.message.reply_text(rules_text)

    elif 'Payment Method' in text:
        keyboard = [[InlineKeyboardButton("Bkash", callback_data="pay_bkash"), InlineKeyboardButton("Nagad", callback_data="pay_nagad")],
                    [InlineKeyboardButton("Rocket", callback_data="pay_rocket"), InlineKeyboardButton("Binance", callback_data="pay_binance")]]
        await update.message.reply_text("Select a method to Update:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif 'Work Start' in text:
        await update.message.reply_text('Select Work Category:', reply_markup=ReplyKeyboardMarkup([['🔵 FB 00 Fnd 2fa'], ['🟠 IG'], ['🔄 Restart']], resize_keyboard=True))

    elif 'FB 00 Fnd 2fa' in text:
        context.user_data['cat'] = "FB 00 Fnd 2fa"
        await update.message.reply_text('Choose Option:', reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))

    elif 'IG' in text:
        await update.message.reply_text('IG Options:', reply_markup=ReplyKeyboardMarkup([['🍪 Cookies'], ['🔐 2fa'], ['📱 Number2fa'], ['🔄 Restart']], resize_keyboard=True))

    elif text in ['🍪 Cookies', '🔐 2fa', '📱 Number2fa']:
        context.user_data['cat'] = f"IG - {text}"
        await update.message.reply_text(f'Selected {text}:', reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))

    elif 'Single ID' in text:
        await update.message.reply_text('Enter Username:', reply_markup=ReplyKeyboardRemove())
        return GET_USERNAME

    elif text == '/admin' and user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT user_id, username FROM users"); users = cursor.fetchall(); conn.close()
        msg = "👤 User List:\n\n"
        for u in users: msg += f"• @{u[1]} (`{u[0]}`)\n"
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

# আইডি সাবমিশন ধাপে ধাপে
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_name'] = update.message.text
    await update.message.reply_text('Enter Password:')
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_pass'] = update.message.text
    await update.message.reply_text('Enter 2FA:')
    return GET_2FA

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    u_name, u_pass, u_2fa = context.user_data['u_name'], context.user_data['u_pass'], update.message.text
    cat = context.user_data.get('cat', 'General')
    admin_msg = f"📥 **New Submission**\nCategory: {cat}\nFrom: @{user.username} (`{user.id}`)\n\nUser: `{u_name}`\nPass: `{u_pass}`\n2FA: `{u_2fa}`"
    kb = [[InlineKeyboardButton("৳6 Add", callback_data=f"add_6_{user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    await update.message.reply_text("ID Received! আপনার আইডি রিপোর্টের জন্য ২ ঘণ্টা অপেক্ষা করুন।", reply_markup=get_main_menu())
    return ConversationHandler.END

# পেমেন্ট ও বাটন হ্যান্ডলার
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("pay_"):
        method = data.split("_")[1]
        context.user_data['editing_pay'] = method
        await query.message.reply_text(f"Send your {method.capitalize()} address:")
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
    await update.message.reply_text(f"✅ {method.capitalize()} saved!", reply_markup=get_main_menu())
    return ConversationHandler.END

# ফাইল হ্যান্ডলার (ফাইল পাঠালে ইউজারের আইডি সহ আসবে)
async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    caption = f"📄 **New File Received**\nFrom: @{user.username}\nUser ID: `{user.id}`"
    await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption, parse_mode='Markdown')
    await update.message.reply_text('File Received', reply_markup=get_main_menu())

def main():
    init_db()
    keep_alive()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Single ID'), handle_menu), CallbackQueryHandler(callback_handler, pattern="^pay_")],
        states={
            GET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass)],
            GET_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_2fa)],
            SET_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_payment)],
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex('Restart'), start)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_user))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == '__main__':
    main()                                                                            
