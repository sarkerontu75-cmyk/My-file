import os
import sqlite3
import threading
from flask import Flask
from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- RENDER & PORT KEEP ALIVE ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Bot is running perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    threading.Thread(target=run_flask, daemon=True).start()

# কনফিগারেশন
TOKEN = "8797001893:AAFjzHbtNGcibUu0zewY9QdOml-94bOogXE"
ADMIN_ID = 7541488098

# স্টেট নির্ধারণ
GET_USERNAME, GET_PASS, GET_2FA, SET_WITHDRAW_VAL, ADMIN_ADD_MONEY, GET_PAY_ADDR = range(6)

# ডাটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0.0, 
                       bkash TEXT, nagad TEXT, rocket TEXT, binance TEXT, 
                       total_ids INTEGER DEFAULT 0, total_files INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_main_menu():
    # Rules এবং Price List বাটনকে এক করা হয়েছে
    keyboard = [['🚀 Work Start'], ['📜 Rules & Price List'], ['💳 Payment Withdraw'], ['🔄 Restart']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username))
    conn.commit(); conn.close()
    context.user_data.clear()
    
    msg = "স্বাগতম! কাজ শুরু করতে নিচের বাটন ব্যবহার করুন।"
    if update.message:
        await update.message.reply_text(msg, reply_markup=get_main_menu())
    else:
        await update.callback_query.message.reply_text(msg, reply_markup=get_main_menu())
    return ConversationHandler.END

# --- মেনু হ্যান্ডলার ---
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text: return

    if 'Restart' in text:
        return await start(update, context)

    # Rules & Price List লজিক (নতুন)
    if 'Rules & Price List' in text:
        kb = [[InlineKeyboardButton("🔗 View Rules & Price", url="https://t.me/instafbhub/19")]]
        await update.message.reply_text(
            "Price এবং Rules এর মেথড দেখতে নিচের লিঙ্কে ক্লিক করুন:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if 'Work Start' in text:
        await update.message.reply_text('Category:', reply_markup=ReplyKeyboardMarkup([['🔵 Facebook'], ['🟠 Instagram'], ['🔄 Restart']], resize_keyboard=True))
    elif 'Facebook' in text:
        context.user_data['cat'] = "Facebook"
        await update.message.reply_text("মোড বেছে নিন:", reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))
    elif 'Instagram' in text:
        await update.message.reply_text('IG Options:', reply_markup=ReplyKeyboardMarkup([['🍪 Cookies'], ['🔐 2fa'], ['📱 Number2fa'], ['🔄 Restart']], resize_keyboard=True))
    elif text in ['🍪 Cookies', '🔐 2fa', '📱 Number2fa']:
        context.user_data['cat'] = f"IG {text}"
        await update.message.reply_text(f"{text} এর জন্য অপশন:", reply_markup=ReplyKeyboardMarkup([['📁 File'], ['🆔 Single ID'], ['🔄 Restart']], resize_keyboard=True))
    elif 'Single ID' in text:
        await update.message.reply_text('ধাপ ১: ইউজারনেম দিন:', reply_markup=get_main_menu())
        return GET_USERNAME
    elif 'Payment Withdraw' in text:
        user_id = update.message.from_user.id
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]; conn.close()
        msg = f"💰 আপনার ব্যালেন্স: ৳{balance}\n⚠️ মিনিমাম উইথড্র: ৳৫০"
        kb = [[InlineKeyboardButton("Bkash", callback_data="set_bkash"), InlineKeyboardButton("Nagad", callback_data="set_nagad")],
              [InlineKeyboardButton("✅ Withdraw Request", callback_data="req_withdraw")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

# --- সাবমিশন লজিক (Single ID) ---
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_name'] = update.message.text
    await update.message.reply_text('ধাপ ২: পাসওয়ার্ড দিন:')
    return GET_PASS

async def get_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_pass'] = update.message.text
    if context.user_data.get('cat') == "IG 🍪 Cookies":
        return await submit_id_final(update, context)
    await update.message.reply_text('ধাপ ৩: ২এফএ (2FA) কোড দিন:')
    return GET_2FA

async def get_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['u_2fa'] = update.message.text
    return await submit_id_final(update, context)

async def submit_id_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
    cursor.execute("UPDATE users SET total_ids = total_ids + 1 WHERE user_id = ?", (user.id,))
    conn.commit(); conn.close()
    admin_msg = (f"📥 **New Submission**\nUID: `{user.id}`\nCat: {context.user_data.get('cat')}\n\n"
                 f"U: `{context.user_data['u_name']}`\nP: `{context.user_data['u_pass']}`\n"
                 f"2FA: `{context.user_data.get('u_2fa', 'N/A')}`")
    kb = [[InlineKeyboardButton("৳6 Add", callback_data=f"add_6_{user.id}"), 
           InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")]]
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    await update.message.reply_text("আইডি জমা হয়েছে!", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- বাটন ক্লিক হ্যান্ডলার (Reject & Others) ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("reject_"):
        uid = int(data.split("_")[1])
        try:
            await context.bot.send_message(chat_id=uid, text="❌ দুঃখিত, আপনার পাঠানো আইডিটি রিজেক্ট করা হয়েছে।")
            await query.edit_message_text(text=query.message.text + "\n\n🚫 **Status: Rejected**")
        except: pass
    elif data.startswith("add_6_"):
        uid = int(data.split("_")[2])
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + 6 WHERE user_id = ?", (uid,))
        conn.commit(); conn.close()
        await context.bot.send_message(chat_id=uid, text="✅ আপনার আইডির জন্য ৳৬ যোগ হয়েছে।")
        await query.edit_message_reply_markup(reply_markup=None)
    elif data == "req_withdraw":
        await query.message.reply_text("কত টাকা তুলতে চান? (সংখ্যা লিখুন)")
        return SET_WITHDRAW_VAL
    elif data.startswith("set_"):
        context.user_data['editing_method'] = data.split("_")[1]
        await query.message.reply_text(f"আপনার {data.split('_')[1]} নম্বর দিন:")
        return GET_PAY_ADDR
    elif data.startswith("custom_"):
        context.user_data['target_user'] = data.split("_")[1]
        await query.message.reply_text("টাকার পরিমাণ লিখুন:")
        return ADMIN_ADD_MONEY

# --- উইথড্র ও ফাইল হ্যান্ডলিং ---
async def process_withdraw_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        uid = update.message.from_user.id
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        balance = cursor.fetchone()[0]
        if balance >= amount and amount >= 50:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, uid))
            conn.commit(); cursor.execute("SELECT bkash, nagad FROM users WHERE user_id=?", (uid,))
            p = cursor.fetchone(); conn.close()
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 **Withdraw Req**\nUID: `{uid}`\nAmount: ৳{amount}\nBkash: {p[0]}\nNagad: {p[1]}")
            await update.message.reply_text(f"✅ ৳{amount} মাইনাস হয়েছে এবং রিকোয়েস্ট পাঠানো হয়েছে।")
        else: await update.message.reply_text("ব্যালেন্স কম বা ভুল ইনপুট।")
    except: await update.message.reply_text("ভুল ইনপুট।")
    return ConversationHandler.END

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if update.message.document.file_name.lower().endswith('.xlsx'):
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET total_files = total_files + 1 WHERE user_id = ?", (user.id,))
        conn.commit(); conn.close()
        caption = f"📄 **New Excel File**\nUID: `{user.id}`"
        kb = [[InlineKeyboardButton("💰 Add Money", callback_data=f"custom_{user.id}")]]
        await context.bot.send_document(chat_id=ADMIN_ID, document=update.message.document.file_id, caption=caption, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        await update.message.reply_text('ফাইল পাওয়া গেছে!', reply_markup=get_main_menu())

async def save_pay_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = context.user_data.get('editing_method')
    conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {method} = ? WHERE user_id = ?", (update.message.text, update.message.from_user.id))
    conn.commit(); conn.close()
    await update.message.reply_text("✅ সফলভাবে সেভ হয়েছে।")
    return ConversationHandler.END

async def admin_add_money_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
        uid = context.user_data.get('target_user')
        conn = sqlite3.connect('bot_data.db'); cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
        conn.commit(); conn.close()
        await context.bot.send_message(chat_id=uid, text=f"✅ আপনার একাউন্টে ৳{amount} যোগ হয়েছে।")
        await update.message.reply_text("টাকা যোগ করা হয়েছে।")
    except: await update.message.reply_text("ভুল ইনপুট।")
    return ConversationHandler.END

def main():
    init_db(); keep_alive()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('Single ID'), handle_menu), CallbackQueryHandler(callback_handler, pattern="^(set_|req_withdraw|custom_|reject_|add_6_)")],
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
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
