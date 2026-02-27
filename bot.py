import telebot
from telebot import types
import sqlite3
from datetime import datetime

TOKEN = 'আপনার_টোকেন_এখানে_দিন'  # ধাপ ১ থেকে পাওয়া টোকেন
ADMIN_ID = 123456789  # আপনার আইডি (টেলিগ্রামে @userinfobot থেকে পাবেন)

bot = telebot.TeleBot(TOKEN)

# ডেটাবেস ফাংশন
def init_db():
    conn = sqlite3.connect('data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS info (uid TEXT, type TEXT, time TEXT)")
    conn.commit()
    conn.close()

# মেইন বাটন
def main_btns():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("Nord VPN", "IG File", "IG Single account")
    m.add("🔄 Restart")
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, f"আপনার আইডি: {msg.from_user.id}\nঅপশন বেছে নিন:", reply_markup=main_btns())

@bot.message_handler(func=lambda m: True)
def handle(m):
    if m.text == "🔄 Restart":
        bot.send_message(m.chat.id, "রিস্টার্ট হয়েছে!", reply_markup=main_btns())
    elif m.text in ["Nord VPN", "IG File", "IG Single account"]:
        bot.send_message(m.chat.id, f"আপনি {m.text} বেছে নিয়েছেন। এখন ফাইল পাঠান।")
        # ডেটাবেসে সেভ
        conn = sqlite3.connect('data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO info VALUES (?, ?, ?)", (m.from_user.id, m.text, datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"🔔 আইডি {m.from_user.id} ফাইল পাঠাচ্ছে: {m.text}")

init_db()
bot.infinity_polling()
