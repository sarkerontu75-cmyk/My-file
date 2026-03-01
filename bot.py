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

# ডাটাবেস ফাংশন
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

# মেইন কিবোর্ড (💰 Price List যোগ করা হয়েছে)
def get_main_menu():
    keyboard = [
        ['🚀 Work Start'],
        ['📜 Rules', '💰 Price List'],
        ['💳 Payment Method'],
        ['🔄 Restart']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    update_user_db(user.id, username=user.username)
    welcome_text = "স্বাগতম! কাজ শুরু করার আগে দয়া করে **প্রথমে রুলস পড়ে নিন** এবং আপনার **পেমেন্ট মেথড এড করে নিন।**"
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')
    return ConversationHandler.END

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if 'Restart' in text:
        return await start(update, context)

    elif 'Rules' in text:
        rules_text = ("🛑 **ওপেন চ্যালেঞ্জ: আগে কাজ দেখুন, তারপর বিশ্বাস করুন!** 🛑\n\n"
                      "আমরা মুখে বড় কথা নয়, কাজে বিশ্বাসী। 💯\n\n"
                      "✨ **সাপোর্টের জন্য নক দিন:** @Dinanhaji")
        await update.message.reply_text(rules_text, reply_markup=get_main_menu())

    elif 'Price List' in text:
        # এখানে আপনি আপনার পছন্দমতো দাম লিখে দিতে পারেন
        price_text = (
            "💰 **আমাদের কাজের রেট লিস্ট:**\n\n"
            "🔵 FB 00 Fnd 2fa: ৳6.00 (Per ID)\n"
            "🟠 IG Work: ৳5.00 - ৳10.00\n\n"
            "🚀 খুব শীঘ্রই রেট বাড়ানো হবে। আমাদের সাথেই থাকুন!"
        )
        await update.message.reply_text(price_text, reply_markup=get_main_menu())

    elif 'Payment Method' in text:
        keyboard = [[InlineKeyboardButton("Bkash", callback_data="pay_bkash"), InlineKeyboardButton("Nagad", callback_data="pay_nagad")],
                    [InlineKeyboardButton("Rocket", callback_data="pay_rocket"), InlineKeyboardButton("Binance", callback_data="pay_binance")]]
        await update.message.reply_text("আপনার পেমেন্ট মেথড সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif 'Work Start' in text:
        await update.message.reply_text('Select Work Category:', reply_markup=ReplyKeyboardMarkup([['🔵 FB 00 Fnd 2fa'], ['🟠 IG'], ['🔄 Restart']], resize_keyboard=True))

    elif 'FB 00 Fnd 2fa' in text:
        context.user_data['cat'] = "FB 00 Fnd 2fa"
        fb_text = "আপনি কিভাবে আইডি পাঠাতে চান? **ফাইল আকারে না সিঙ্গেল আইডি?** নিচের অপশন থেকে সিলেক্ট করুন।"
        await update.message.reply_text(fb_text, reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True), parse_mode='Markdown')

    elif 'IG' in text:
        await update.message.reply_text('IG Options:', reply_markup=ReplyKeyboardMarkup([['🍪 Cookies'], ['🔐 2fa'], ['📱 Number2fa'], ['🔄 Restart']], resize_keyboard=True))

    elif 'File' in text:
        await update.message.reply_text("দয়া করে আপনার **Excel (.xlsx)** ফাইলটি পাঠান।", reply_markup=ReplyKeyboardRemove())

    elif 'Single ID' in text:
        await update.message.reply_text('ধাপ ১: ইউজারনেম দিন:', reply_markup=ReplyKeyboardRemove())
        return GET_USERNAME

# এডমিন কমান্ডসমূহ
async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT user_id, username FROM users"); users = cursor.fetchall(); conn.close()
    msg = "👤 **User List:**\n\n"
    for u in users: msg += f"• @{u[1]} (`{u[0]}`)\n"
    await update.message.reply_text(msg + "\nCheck with `/check [ID]`")

async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = context.args[0]
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,)); d = cursor.fetchone(); conn.close()
        if d:
            msg = (f"👤 Profile: @{d[1]}\n🆔 ID: `{d[0]}`\n💰 Balance: ৳{d[2]}\n\n"
                   f"🏦 Payment:\nBkash: {d[3]}\nNagad: {d[4]}\nRocket: {d[5]}\nBinance: {d[6]}")
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("ইউজার খুঁজে পাওয়া যায়নি।")
    except:
        await update.message.reply_text("সঠিকভাবে লিখুন: `/check 12345678`")

# আইডি সাবমিশন প্রসেস (Redirect ফিক্স করা হয়েছে)
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_name'] = update.message.text
    await update.message.reply_text('ধাপ ২: পাসওয়ার্ড দিন:')
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_pass'] = update.message.text
    await update.message.reply_text('ধাপ ৩: ২এফএ (2FA) কোড দিন:')
    return GET_2FA

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    u_name, u_pass, u_2fa = context.user_data['u_name'], context.user_data['u_pass'], update.message.text
    cat = context.user_data.get('cat', 'General')
    admin_msg = f"📥 **New Submission**\nCategory: {cat}\nFrom: @{user.username} (`{user.id}`)\n\nUser: `{u_name}`\nPass: `{u_pass}`\n2FA: `{u_2fa}`"
    kb = [[InlineKeyboardButton("৳6 Add", callback_data=f"add_6_{user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    # তথ্য পাঠানোর পর মেইন মেনুতে রিডাইরেক্ট
    await update.message.reply_text("আইডি সফলভাবে জমা হয়েছে!", reply_markup=get_main_menu())
    return ConversationHandler.END

async def pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("pay_"):
        method = query.data.split("_")[1]
        context.user_data['editing_pay'] = method
        await query.message.reply_text(f"আপনার {method.capitalize()} নম্বরটি দিন:")
        return SET_PAYMENT
    elif query.data.startswith("add_6_"):
        uid = int(query.data.split("_")[2])
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor(); cursor.execute("UPDATE users SET balance = balance + 6 WHERE user_id = ?", (uid,)); conn.commit(); conn.close()
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=uid, text="✅ আপনার একাউন্টে ৳6 যোগ করা হয়েছে।")

async def save_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = context.user_data.get('editing_pay')
    update_user_db(update.message.from_user.id, field=method, value=update.message.text)
    # পেমেন্ট সেভ করার পর মেইন মেনুতে রিডাইরেক্ট
    await update.message.reply_text(f"✅ {method.capitalize()} সেভ করা হয়েছে!", reply_markup=get_main_menu())
    return ConversationHandler.END

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.document.file_name.lower().endswith('.xlsx'):
        caption = f"📄 **New Excel File Received**\nFrom: @{user.username}\nUser ID: `{user.id}`"
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption, parse_mode='Markdown')
        # ফাইল পাঠানোর পর মেইন মেনুতে রিডাইরেক্ট
        await update.message.reply_text('ফাইলটি গ্রহণ করা হয়েছে।', reply_markup=get_main_menu())
    else:
        await update.message.reply_text('❌ শুধুমাত্র **Excel (.xlsx)** ফাইল পাঠান।', reply_markup=get_main_menu())

def main():
    init_db(); keep_alive()
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
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex('Restart'), start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_list))
    app.add_handler(CommandHandler("check", check_user))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(pay_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.run_polling()

if __name__ == '__main__':
    main()
        
