import telebot
from telebot import types
import sqlite3
from datetime import datetime

# আপনার তথ্য
TOKEN = '8603236331:AAFE7dQpKBPi1UwOSV_ar5JL3hbfjtJWyjw' 
ADMIN_ID = 7541488098 

bot = telebot.TeleBot(TOKEN)
user_data = {}

# ডেটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('master_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (uid TEXT PRIMARY KEY, username TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions 
                      (uid TEXT, username TEXT, type TEXT, info TEXT, date TEXT)''')
    # পেমেন্ট মেথড সেভ করার জন্য টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS payment_methods 
                      (uid TEXT PRIMARY KEY, method_type TEXT, details TEXT)''')
    conn.commit()
    conn.close()

def register_user(uid, username):
    conn = sqlite3.connect('master_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (uid, username))
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
    # নিচের স্থায়ী বাটন (Permanent Buttons)
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

# --- অ্যাডমিন কমান্ডসমূহ ---

@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('master_data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()
        text = (f"🛠 **অ্যাডমিন ড্যাশবোর্ড**\n\n👥 মোট ইউজার: `{total_users}` জন\n\n"
                f"ইউজারের পেমেন্ট ও কাজ চেক করতে: `/check আইডি`")
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

@bot.message_handler(commands=['check'])
def check_user(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            target_id = msg.text.split()[1]
            conn = sqlite3.connect('master_data.db', check_same_thread=False)
            cursor = conn.cursor()
            
            # সাবমিশন রিপোর্ট
            cursor.execute("SELECT type, info, date FROM submissions WHERE uid=?", (target_id,))
            rows = cursor.fetchall()
            
            # পেমেন্ট মেথড রিপোর্ট
            cursor.execute("SELECT method_type, details FROM payment_methods WHERE uid=?", (target_id,))
            p_method = cursor.fetchone()
            
            conn.close()
            
            res = f"📊 আইডি `{target_id}` এর রিপোর্ট:\n\n"
            if p_method:
                res += f"💰 পেমেন্ট মেথড: {p_method[0]}\n💳 ডিটেইলস: {p_method[1]}\n\n"
            else:
                res += "💰 পেমেন্ট মেথড: সেট করা নেই\n\n"
            
            if rows:
                res += "📝 কাজের হিস্ট্রি:\n"
                for i, row in enumerate(rows, 1):
                    res += f"{i}. {row[0]} | {row[1]} | {row[2]}\n"
            else:
                res += "❌ কোনো সাবমিশন পাওয়া যায়নি।"
                
            bot.send_message(ADMIN_ID, res)
        except:
            bot.send_message(ADMIN_ID, "ভুল ফরম্যাট। লিখুন: `/check আইডি`")

# --- ইউজার হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.from_user.id)
    uname = f"@{msg.from_user.username}" if msg.from_user.username else "No Username"
    register_user(uid, uname)
    bot.send_message(msg.chat.id, "স্বাগতম! নিচের অপশনগুলো দেখুন:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    uid = str(m.from_user.id)
    uname = f"@{m.from_user.username}" if m.from_user.username else "No Username"
    text = m.text

    # --- পেমেন্ট বাটন হ্যান্ডলিং ---
    if text == "💰 Payment Info":
        bot.send_message(m.chat.id, "পেমেন্ট মেথড বেছে নিন (পরিবর্তন করতে চাইলে আবার সেট করুন):", reply_markup=payment_menu())
        return

    if text in ["Bkash", "Nagad", "Rocket", "Binance"]:
        user_data[uid] = {'step': 'payment_details', 'method': text}
        bot.send_message(m.chat.id, f"আপনার {text} নাম্বার বা ডিটেইলস দিন:")
        return

    if text == "🔙 Back" or text == "🔄 Restart":
        user_data.pop(uid, None)
        bot.send_message(m.chat.id, "মেনুতে ফিরে আসা হয়েছে।", reply_markup=main_menu())
        return

    # --- মেনু নেভিগেশন ---
    if text == "FB":
        bot.send_message(m.chat.id, "FB অপশন:", reply_markup=fb_menu())
    elif text == "IG":
        bot.send_message(m.chat.id, "IG অপশন:", reply_markup=ig_main_menu())
    elif text == "Ig 2fa":
        bot.send_message(m.chat.id, "Ig 2fa টাইপ:", reply_markup=ig_2fa_submenu())
    
    elif text == "IG Cookies":
        link_text = "[Click Here](https://t.me/ostmd/32) এখানে সাবমিট করুন"
        bot.send_message(m.chat.id, link_text, parse_mode="Markdown")
        save_submission(uid, uname, "IG Cookies Click", "Clicked Link")

    elif text in ["FB 00 FND 2FA FILE 🗃️", "File"]:
        bot.send_message(m.chat.id, f"আপনি {text} বেছে নিয়েছেন। ফাইল পাঠান।")

    elif text in ["SINGLE 00 FND 2FA", "Single ID"]:
        user_data[uid] = {'step': 'user', 'type': text}
        bot.send_message(m.chat.id, "Username দিন:")

    # --- ধাপে ধাপে তথ্য সংগ্রহ ---
    elif uid in user_data:
        state = user_data[uid]
        
        # পেমেন্ট ডিটেইলস সেভ করা
        if state.get('step') == 'payment_details':
            method = state['method']
            conn = sqlite3.connect('master_data.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO payment_methods VALUES (?, ?, ?)", (uid, method, text))
            conn.commit()
            conn.close()
            bot.send_message(m.chat.id, f"সফলভাবে {method} ডিটেইলস সেভ হয়েছে।", reply_markup=main_menu())
            bot.send_message(ADMIN_ID, f"💰 **পেমেন্ট আপডেট!**\n👤 {uname}\n🆔 `{uid}`\n🔹 {method}: `{text}`")
            user_data.pop(uid)
            
        # একাউন্ট তথ্য সংগ্রহ
        elif state.get('step') == 'user':
            user_data[uid]['u'] = text
            user_data[uid]['step'] = 'pass'
            bot.send_message(m.chat.id, "Password দিন:")
        elif state.get('step') == 'pass':
            user_data[uid]['p'] = text
            user_data[uid]['step'] = 'key'
            bot.send_message(m.chat.id, "Key🔐 দিন:")
        elif state.get('step') == 'key':
            info = f"U: {user_data[uid]['u']} | P: {user_data[uid]['p']} | K: {text}"
            save_submission(uid, uname, state['type'], info)
            bot.send_message(ADMIN_ID, f"📩 **নতুন আইডি!**\n👤 {uname}\n🆔 `{uid}`\n📌 {state['type']}\n📝 `{info}`", parse_mode="Markdown")
            bot.send_message(m.chat.id, "তথ্য জমা হয়েছে।", reply_markup=main_menu())
            user_data.pop(uid)

@bot.message_handler(content_types=['document'])
def handle_docs(m):
    uid = str(m.from_user.id)
    uname = f"@{m.from_user.username}" if m.from_user.username else "No Username"
    save_submission(uid, uname, "FILE SUBMIT", m.document.file_name)
    bot.send_message(ADMIN_ID, f"📄 **নতুন ফাইল!**\n👤 {uname}\n🆔 `{uid}`")
    bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    bot.reply_to(m, "ফাইলটি সফলভাবে জমা হয়েছে।")

init_db()
print("বট চলছে...")
bot.infinity_polling()
