import telebot
from telebot import types
import sqlite3
from datetime import datetime
import os
from flask import Flask
from threading import Thread

# --- কনফিগারেশন ---
TOKEN = '8603236331:AAFE7dQpKBPi1UwOSV_ar5JL3hbfjtJWyjw' 
ADMIN_ID = 7541488098 

bot = telebot.TeleBot(TOKEN)
user_data = {}

# --- Render-এ বট সচল রাখার জন্য সার্ভার ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ডেটাবেস সেটআপ ---
def init_db():
    conn = sqlite3.connect('master_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY, username TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (uid TEXT, username TEXT, type TEXT, info TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_methods (uid TEXT PRIMARY KEY, method_type TEXT, details TEXT)''')
    conn.commit()
    conn.close()

def save_submission(uid, username, acc_type, info):
    conn = sqlite3.connect('master_data.db', check_same_thread=False)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO submissions VALUES (?, ?, ?, ?, ?)", (uid, username, acc_type, info, today))
    conn.commit()
    conn.close()

# --- কিবোর্ড মেনুসমূহ ---
def main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("FB", "IG")
    m.add("💰 Payment Info", "🔄 Restart")
    return m

def payment_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("Bkash", "Nagad", "Rocket", "Binance")
    m.add("🔙 Back")
    return m

def fb_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("FB 00 FND 2FA FILE 🗃️", "SINGLE 00 FND 2FA", "🔄 Restart")
    return m

def ig_main_menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("Ig 2fa", "IG Cookies", "🔄 Restart")
    return m

def ig_2fa_submenu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("File", "Single ID", "🔄 Restart")
    return m

# --- অ্যাডমিন কন্ট্রোল ---
@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('master_data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()
        bot.send_message(ADMIN_ID, f"🛠 **অ্যাডমিন প্যানেল**\n\n👥 মোট ইউজার: `{total_users}` জন\n🔍 চেক করতে: `/check আইডি`", parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check_user(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            target_id = msg.text.split()[1]
            conn = sqlite3.connect('master_data.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT method_type, details FROM payment_methods WHERE uid=?", (target_id,))
            p = cursor.fetchone()
            cursor.execute("SELECT type, info, date FROM submissions WHERE uid=?", (target_id,))
            rows = cursor.fetchall()
            conn.close()
            
            res = f"📊 রিপোর্ট: `{target_id}`\n"
            res += f"💰 পেমেন্ট: {f'{p[0]} ({p[1]})' if p else 'নেই'}\n\n"
            if rows:
                for i, r in enumerate(rows, 1): res += f"{i}. {r[0]} | {r[1]} | {r[2]}\n"
            else: res += "কোনো কাজ নেই।"
            bot.send_message(ADMIN_ID, res)
        except: bot.send_message(ADMIN_ID, "ব্যবহার: `/check আইডি`")

# --- মেসেজ হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(msg):
    uid, uname = str(msg.from_user.id), f"@{msg.from_user.username}" if msg.from_user.username else "No Name"
    conn = sqlite3.connect('master_data.db', check_same_thread=False)
    conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (uid, uname))
    conn.commit()
    conn.close()
    bot.send_message(msg.chat.id, "ক্যাটাগরি বেছে নিন:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    uid, uname, text = str(m.from_user.id), f"@{m.from_user.username}" if m.from_user.username else "No Name", m.text

    if text == "🔄 Restart" or text == "🔙 Back":
        user_data.pop(uid, None)
        bot.send_message(m.chat.id, "মেনুতে ফিরে আসা হয়েছে।", reply_markup=main_menu())
    
    elif text == "💰 Payment Info":
        bot.send_message(m.chat.id, "পেমেন্ট মেথড বেছে নিন:", reply_markup=payment_menu())
    
    elif text in ["Bkash", "Nagad", "Rocket", "Binance"]:
        user_data[uid] = {'step': 'pay', 'method': text}
        bot.send_message(m.chat.id, f"আপনার {text} ডিটেইলস দিন:")
    
    elif text == "FB": bot.send_message(m.chat.id, "FB অপশন:", reply_markup=fb_menu())
    elif text == "IG": bot.send_message(m.chat.id, "IG অপশন:", reply_markup=ig_main_menu())
    elif text == "Ig 2fa": bot.send_message(m.chat.id, "Ig 2fa টাইপ:", reply_markup=ig_2fa_submenu())
    
    elif text == "IG Cookies":
        bot.send_message(m.chat.id, "[Click Here](https://t.me/ostmd/32) এখানে সাবমিট করুন", parse_mode="Markdown")
        save_submission(uid, uname, "IG Cookies", "Clicked Link")

    elif text in ["FB 00 FND 2FA FILE 🗃️", "File"]:
        bot.send_message(m.chat.id, "ফাইল পাঠান।")

    elif text in ["SINGLE 00 FND 2FA", "Single ID"]:
        user_data[uid] = {'step': 'u', 'type': text}
        bot.send_message(m.chat.id, "Username দিন:")

    elif uid in user_data:
        s = user_data[uid]
        if s.get('step') == 'pay':
            conn = sqlite3.connect('master_data.db', check_same_thread=False)
            conn.execute("INSERT OR REPLACE INTO payment_methods VALUES (?, ?, ?)", (uid, s['method'], text))
            conn.commit()
            conn.close()
            bot.send_message(m.chat.id, "পেমেন্ট তথ্য সেভ হয়েছে।", reply_markup=main_menu())
            bot.send_message(ADMIN_ID, f"💰 পেমেন্ট আপডেট: {uname} ({uid})\n{s['method']}: {text}")
            user_data.pop(uid)
        elif s.get('step') == 'u':
            user_data[uid].update({'u': text, 'step': 'p'})
            bot.send_message(m.chat.id, "Password দিন:")
        elif s.get('step') == 'p':
            user_data[uid].update({'p': text, 'step': 'k'})
            bot.send_message(m.chat.id, "Key🔐 দিন:")
        elif s.get('step') == 'k':
            info = f"U: {s['u']} | P: {s['p']} | K: {text}"
            save_submission(uid, uname, s['type'], info)
            bot.send_message(ADMIN_ID, f"📩 নতুন আইডি!\n👤 {uname}\n🆔 `{uid}`\n📌 {s['type']}\n📝 `{info}`", parse_mode="Markdown")
            bot.send_message(m.chat.id, "তথ্য জমা হয়েছে।", reply_markup=main_menu())
            user_data.pop(uid)

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    uid, uname = str(m.from_user.id), f"@{m.from_user.username}" if m.from_user.username else "No Name"
    save_submission(uid, uname, "FILE", m.document.file_name)
    bot.send_message(ADMIN_ID, f"📄 নতুন ফাইল: {uname} ({uid})")
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.reply_to(m, "ফাইলটি জমা হয়েছে।")

if __name__ == "__main__":
    init_db()
    keep_alive() # Render-এর জন্য সচল রাখা
    bot.infinity_polling()
