import telebot
from telebot import types
import sqlite3
from datetime import datetime

# আপনার দেওয়া তথ্য এখানে বসানো হয়েছে
TOKEN = '8603236331:AAFE7dQpKBPi1UwOSV_ar5JL3hbfjtJWyjw' 
ADMIN_ID = 7541488098 

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS info (uid TEXT, type TEXT, time TEXT)")
    conn.commit()
    conn.close()

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
        bot.send_message(m.chat.id, "বট রিস্টার্ট হয়েছে!", reply_markup=main_btns())
    elif m.text in ["Nord VPN", "IG File", "IG Single account"]:
        bot.send_message(m.chat.id, f"আপনি {m.text} বেছে নিয়েছেন। এখন ফাইল পাঠান।")
        
        conn = sqlite3.connect('data.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO info VALUES (?, ?, ?)", (m.from_user.id, m.text, datetime.now().strftime("%d/%m/%Y")))
        conn.commit()
        conn.close()
        
        # আপনার কাছে (Admin) নোটিফিকেশন যাবে
        bot.send_message(ADMIN_ID, f"🔔 নতুন এন্ট্রি!\nইউজার আইডি: {m.from_user.id}\nটাইপ: {m.text}")

init_db()
print("বট চলছে...")
bot.infinity_polling()
