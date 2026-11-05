import os
import sys
import subprocess

# অটো লাইব্রেরি ইনস্টলার (হোস্টিং এরর এড়ানোর জন্য)
def install_package(package_name):
    try:
        __import__(package_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

install_package("requests")
install_package("pyTelegramBotAPI")

import sqlite3
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date

TOKEN = "8987218086:AAG6cEdd_Jhnx9a269ibc73PQiZP28qxK7U"
OWNER_ID = 6599413664  # আপনার টেলিগ্রাম ইউজার আইডি
FORCE_CHANNEL = "@MoneyPointtBD"  # অফিশিয়াল চ্যানেলের ইউজারনেম

bot = telebot.TeleBot(TOKEN)
DB_NAME = "bot5_database.db"  # ৫ নম্বর বটের জন্য পৃথক ডাটাবেস

# ডেটাবেজ ইনিশিয়ালাইজেশন
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                points INTEGER DEFAULT 0,
                referred_by INTEGER,
                is_banned INTEGER DEFAULT 0,
                last_claim TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # পুরোনো ডেটাবেজে কলাম না থাকলে যুক্ত করার সেফটি চেক
        for col_def in [
            "ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_claim TEXT"
        ]:
            try:
                cursor.execute(col_def)
            except sqlite3.OperationalError:
                pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phone TEXT,
                message TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # কুপন টেবিল
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                code TEXT PRIMARY KEY,
                points INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ("owner_id", str(OWNER_ID)))
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ("ref_points", "5"))
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ("daily_bonus", "2"))
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", ("maintenance_mode", "off"))
        conn.commit()

init_db()

def get_config(key, default_val):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default_val

def set_config(key, value):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def get_owner_id():
    return int(get_config("owner_id", OWNER_ID))

def is_user_banned(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] == 1 if row else False

def get_user_points(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

USER_STATE = {}
ADMIN_STATE = {}

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

# ইউজার কিবোর্ড
def get_main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("📞 Send Call"),
        KeyboardButton("👤 Profile"),
        KeyboardButton("👥 Refer Link"),
        KeyboardButton("🎁 Daily Bonus"),
        KeyboardButton("🎟️ Redeem Coupon"),
        KeyboardButton("👨‍💻 Developer"),
        KeyboardButton("❓ সাহায্য")
    )
    if user_id == get_owner_id():
        markup.add(KeyboardButton("👑 Admin Panel"))
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    uname = message.from_user.username or "N/A"

    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "🚫 **আপনি এই বট থেকে ব্যান হয়েছেন!**", parse_mode="Markdown")
        return

    if get_config("maintenance_mode", "off") == "on" and user_id != get_owner_id():
        bot.send_message(message.chat.id, "🛠 **বট বর্তমানে মেইনটেনেন্স মোডে রয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন!**", parse_mode="Markdown")
        return

    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != user_id:
                referrer_id = ref_id
        except ValueError:
            pass

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            points_per_ref = int(get_config("ref_points", 5))
            if referrer_id:
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
                if cursor.fetchone():
                    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points_per_ref, referrer_id))
                    cursor.execute("INSERT INTO users (user_id, username, points, referred_by) VALUES (?, ?, 0, ?)", (user_id, uname, referrer_id))
                    
                    try:
                        bot.send_message(
                            referrer_id,
                            f"🎉 **নতুন রেফার নোটিফিকেশন!**\n\n"
                            f"👤 ইউজার: @{uname}\n"
                            f"🆔 আইডি: `{user_id}`\n"
                            f"💎 আপনি পেয়েছেন: **+{points_per_ref} পয়েন্ট**!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                else:
                    cursor.execute("INSERT INTO users (user_id, username, points) VALUES (?, ?, 0)", (user_id, uname))
            else:
                cursor.execute("INSERT INTO users (user_id, username, points) VALUES (?, ?, 0)", (user_id, uname))
            conn.commit()

    if not check_subscription(user_id):
        sub_markup = InlineKeyboardMarkup()
        sub_markup.add(InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url="https://t.me/MoneyPointtBD"))
        sub_markup.add(InlineKeyboardButton("✅ জয়েন করেছি, চেক করুন", callback_data="check_sub"))
        
        bot.send_message(
            message.chat.id,
            f"❌ বট ব্যবহার করতে হলে অবশ্যই আমাদের অফিশিয়াল চ্যানেলে জয়েন করতে হবে!\n\n👉 https://t.me/MoneyPointtBD",
            reply_markup=sub_markup
        )
        return

    bot.send_message(
        message.chat.id,
        "স্বাগতম! 🤖\n\nনিচের অপশন থেকে একটি সিলেক্ট করুন:",
        reply_markup=get_main_keyboard(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "ধন্যবাদ! এখন বট ব্যবহার করতে পারবেন।")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(
            call.message.chat.id,
            "স্বাগতম! 🤖\n\nনিচের অপশন থেকে একটি সিলেক্ট করুন:",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        bot.answer_callback_query(call.id, "আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

# ইউজার বাটনের ফাংশনসমূহ
@bot.message_handler(func=lambda msg: msg.text in ["👤 Profile", "👥 Refer Link", "🎁 Daily Bonus", "🎟️ Redeem Coupon", "👨‍💻 Developer", "❓ সাহায্য"])
def handle_menu_buttons(message):
    user_id = message.from_user.id

    if is_user_banned(user_id):
        return

    if get_config("maintenance_mode", "off") == "on" and user_id != get_owner_id():
        bot.send_message(message.chat.id, "🛠 **বট বর্তমানে মেইনটেনেন্স মোডে রয়েছে।**")
        return

    text = message.text

    if text == "👤 Profile":
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM history WHERE user_id = ?", (user_id,))
            total_calls = cursor.fetchone()[0]
            cursor.execute("SELECT points, (SELECT COUNT(*) FROM users WHERE referred_by = ?) FROM users WHERE user_id = ?", (user_id, user_id))
            row = cursor.fetchone()
            points = row[0] if row else 0
            ref_count = row[1] if row else 0

        profile_text = (
            f"👤 **আপনার প্রফাইল:**\n\n"
            f"🆔 আইডি: `{user_id}`\n"
            f"👤 নাম: {message.from_user.first_name}\n"
            f"💎 পয়েন্ট: `{points} পয়েন্ট`\n"
            f"👥 মোট রেফার: `{ref_count} জন`\n"
            f"📞 মোট প্রেরিত কল: `{total_calls} টি`\n"
            f"🟢 স্ট্যাটাস: `Active`"
        )
        bot.reply_to(message, profile_text, parse_mode="Markdown")

    elif text == "👥 Refer Link":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        ref_points = get_config("ref_points", 5)
        
        ref_msg = (
            f"👥 **রেফার এন্ড আর্ন সিস্টেম:**\n\n"
            f"আপনার নিজস্ব রেফারেল লিংক নিচে দেওয়া হলো। এই লিংক শেয়ার করুন এবং প্রতি রেফারে পান **{ref_points} পয়েন্ট**!\n\n"
            f"🔗 `{ref_link}`"
        )
        bot.reply_to(message, ref_msg, parse_mode="Markdown")

    elif text == "🎁 Daily Bonus":
        today = str(date.today())
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            last_claim = row[0] if row else None

            if last_claim == today:
                bot.reply_to(message, "⏳ আপনি আজকের ডেইলি বোনাস আগেই নিয়ে ফেলেছেন! আগামিকাল আবার চেষ্টা করুন।")
            else:
                daily_pts = int(get_config("daily_bonus", 2))
                cursor.execute("UPDATE users SET points = points + ?, last_claim = ? WHERE user_id = ?", (daily_pts, today, user_id))
                conn.commit()
                bot.reply_to(message, f"🎉 অভিনন্দন! আপনি সফলভাবে আজকের ডেইলি বোনাস **{daily_pts} পয়েন্ট** সংগ্রহ করেছেন!")

    elif text == "🎟️ Redeem Coupon":
        USER_STATE[user_id] = {"step": "WAITING_COUPON"}
        bot.reply_to(message, "🎟️ আপনার প্রোমো কোড বা কুপন কোডটি লিখে পাঠান:")

    elif text == "👨‍💻 Developer":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💬 Contact Developer", url="https://t.me/RABBYBHAIsupport_bot"))
        bot.reply_to(message, "বট সম্পর্কিত যেকোনো প্রয়োজনে সরাসরি ডেভেলপারের সাথে যোগাযোগ করুন:", reply_markup=markup)

    elif text == "❓ সাহায্য":
        bot.reply_to(message, "এই বট দিয়ে সহজে কল পাঠাতে পারবেন (প্রতিটি রিকোয়েস্টে ১ পয়েন্ট প্রয়োজন), রেফার করতে পারবেন এবং প্রতিদিন ডেইলি বোনাস ও কুপন রিডিম করে পয়েন্ট আর্ন করতে পারবেন।")

# কুপন রিডিম করার ইনপুট লজিক
@bot.message_handler(func=lambda message: USER_STATE.get(message.chat.id, {}).get("step") == "WAITING_COUPON")
def process_coupon_redeem(message):
    user_id = message.chat.id
    USER_STATE.pop(user_id, None)
    code = message.text.strip().upper()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM coupons WHERE code = ?", (code,))
        row = cursor.fetchone()

        if not row:
            bot.reply_to(message, "❌ ভুল বা মেয়াদোত্তীর্ণ কুপন কোড!")
            return

        pts = row[0]
        cursor.execute("DELETE FROM coupons WHERE code = ?", (code,))
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, user_id))
        conn.commit()

        bot.reply_to(message, f"✅ সফল! কুপন রিডিম হয়েছে। আপনার অ্যাকাউন্টে **+{pts} পয়েন্ট** যোগ করা হয়েছে!", parse_mode="Markdown")


# --- নতুন API যুক্ত কল পাঠানোর লজিক (১ পয়েন্ট কাটার নিয়মসহ) ---
@bot.message_handler(func=lambda msg: msg.text == "📞 Send Call")
def sendcall_start(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        return
    if get_config("maintenance_mode", "off") == "on" and user_id != get_owner_id():
        bot.send_message(message.chat.id, "🛠 **বট বর্তমানে মেইনটেনেন্স মোডে রয়েছে।**")
        return

    current_pts = get_user_points(user_id)
    if current_pts < 1 and user_id != get_owner_id():
        bot.reply_to(
            message,
            "❌ **আপনার অ্যাকাউন্টে পর্যাপ্ত পয়েন্ট নেই!**\n\n"
            "একটি কল পাঠাতে **১ পয়েন্ট** প্রয়োজন। বন্ধুদের রেফার করুন অথবা ডেইলি বোনাস ক্লেম করে পয়েন্ট অর্জন করুন।",
            parse_mode="Markdown"
        )
        return

    USER_STATE[user_id] = {"step": "WAITING_CALL_NUMBER"}
    bot.reply_to(message, "📱 কল পাঠানোর জন্য **ফোন নম্বর** লিখে পাঠান (যেমন: 019*********):")

@bot.message_handler(func=lambda message: USER_STATE.get(message.chat.id, {}).get("step") == "WAITING_CALL_NUMBER")
def process_call_number(message):
    num = message.text.strip()
    if len(num) < 11:
        bot.reply_to(message, "❌ অনুগ্রহ করে সঠিক ১১ ডিজিটের ফোন নম্বর দিন:")
        return

    user_id = message.chat.id
    USER_STATE.pop(user_id, None)

    if get_user_points(user_id) < 1 and user_id != get_owner_id():
        bot.reply_to(message, "❌ আপনার অ্যাকাউন্টে পর্যাপ্ত পয়েন্ট নেই!")
        return

    status_msg = bot.reply_to(message, "⏳ কল রিকোয়েস্ট পাঠানো হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

    # আপনার নতুন দেওয়া কল API লিংক
    api_url = f"https://darktoolshub.net/sms/call.php?num={num}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://darktoolshub.net/',
        'Connection': 'keep-alive'
    }

    try:
        session = requests.Session()
        response = session.get(api_url, headers=headers, timeout=20, allow_redirects=True)
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if user_id != get_owner_id():
                cursor.execute("UPDATE users SET points = points - 1 WHERE user_id = ?", (user_id,))
            cursor.execute("INSERT INTO history (user_id, phone, message, status) VALUES (?, ?, ?, ?)", (user_id, num, "Call Request", "Call Success"))
            conn.commit()

        bot.edit_message_text(
            "সফল ভাবে কল রিকোয়েস্ট পাঠানো হয়েছে 🟢\n*(আপনার অ্যাকাউন্ট থেকে ১ পয়েন্ট কেটে নেওয়া হয়েছে)*",
            chat_id=user_id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    except requests.exceptions.ConnectionError:
        bot.edit_message_text(
            "❌ **কল সার্ভার বর্তমানে ডাউন বা অফলাইন রয়েছে!**\nদয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।",
            chat_id=user_id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.edit_message_text(
            f"❌ **কল পাঠাতে সমস্যা হয়েছে:**\n`{str(e)}`",
            chat_id=user_id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )


# অ্যাডমিন প্যানেল
@bot.message_handler(func=lambda msg: msg.text == "👑 Admin Panel")
def admin_panel(message):
    if message.from_user.id != get_owner_id():
        bot.reply_to(message, "❌ আপনি এই প্যানেল ব্যবহার করতে পারবেন না।")
        return

    ref_pts = get_config("ref_points", 5)
    daily_pts = get_config("daily_bonus", 2)
    m_mode = get_config("maintenance_mode", "off").upper()
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton(f"⚙️ Ref Points ({ref_pts})", callback_data="admin_set_ref"),
        InlineKeyboardButton(f"🎁 Daily Bonus ({daily_pts})", callback_data="admin_set_daily"),
        InlineKeyboardButton("🎟️ Create Coupon", callback_data="admin_create_coupon"),
        InlineKeyboardButton(f"🛠 Maintenance ({m_mode})", callback_data="admin_toggle_maint"),
        InlineKeyboardButton("➕/➖ Add/Deduct Points", callback_data="admin_manage_points"),
        InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban_user"),
        InlineKeyboardButton("👑 Transfer Ownership", callback_data="admin_transfer")
    )
    bot.reply_to(message, "👑 **অ্যাডমিন প্যানেলে স্বাগতম:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if call.from_user.id != get_owner_id():
        bot.answer_callback_query(call.id, "অনুমতি নেই!", show_alert=True)
        return

    data = call.data

    if data == "admin_stats":
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM history")
            total_calls = cursor.fetchone()[0]

        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"📊 **বট স্ট্যাটিস্টিকস:**\n\n"
            f"👥 মোট ইউজার: `{total_users} জন`\n"
            f"📞 মোট প্রেরিত কল: `{total_calls} টি`",
            parse_mode="Markdown"
        )

    elif data == "admin_broadcast":
        ADMIN_STATE[call.from_user.id] = {"action": "BROADCAST"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📢 ব্রডকাস্ট করার জন্য মেসেজটি লিখে পাঠান:")

    elif data == "admin_set_ref":
        ADMIN_STATE[call.from_user.id] = {"action": "SET_REF_POINTS"}
        bot.answer_callback_query(call.id)
        current_pts = get_config("ref_points", 5)
        bot.send_message(call.message.chat.id, f"🔢 প্রতি রেফারে কত পয়েন্ট দিতে চান? নতুন সংখ্যা লিখুন (বর্তমান: {current_pts}):")

    elif data == "admin_set_daily":
        ADMIN_STATE[call.from_user.id] = {"action": "SET_DAILY_POINTS"}
        bot.answer_callback_query(call.id)
        current_pts = get_config("daily_bonus", 2)
        bot.send_message(call.message.chat.id, f"🎁 ডেইলি বোনাস কত পয়েন্ট দিতে চান? নতুন সংখ্যা লিখুন (বর্তমান: {current_pts}):")

    elif data == "admin_create_coupon":
        ADMIN_STATE[call.from_user.id] = {"action": "CREATE_COUPON_CODE"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🎟️ নতুন কুপন কোডটি লিখুন (যেমন: RABBY50):")

    elif data == "admin_toggle_maint":
        current = get_config("maintenance_mode", "off")
        new_status = "on" if current == "off" else "off"
        set_config("maintenance_mode", new_status)
        bot.answer_callback_query(call.id, f"মেইনটেনেন্স মোড {new_status.upper()} করা হয়েছে!", show_alert=True)
        admin_panel(call.message)

    elif data == "admin_manage_points":
        ADMIN_STATE[call.from_user.id] = {"action": "MANAGE_POINTS_ID"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "👤 যার পয়েন্ট বাড়াতে বা কমাতে চান তার **User ID** লিখে পাঠান:")

    elif data == "admin_ban_user":
        ADMIN_STATE[call.from_user.id] = {"action": "BAN_USER_ID"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🚫 যাকে ব্যান বা আনব্যান করতে চান তার **User ID** লিখে পাঠান:")

    elif data == "admin_transfer":
        ADMIN_STATE[call.from_user.id] = {"action": "TRANSFER"}
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "👑 নতুন অনারের টেলিগ্রাম ইউজার আইডি (User ID) লিখে পাঠান:")

@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_STATE)
def handle_admin_inputs(message):
    owner_id = get_owner_id()
    if message.from_user.id != owner_id:
        return

    admin_data = ADMIN_STATE.get(message.from_user.id, {})
    action = admin_data.get("action")
    text = message.text.strip()

    if action == "BROADCAST":
        ADMIN_STATE.pop(message.from_user.id, None)
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = cursor.fetchall()

        sent, failed = 0, 0
        status_msg = bot.reply_to(message, "⏳ ব্রডকাস্ট পাঠানো হচ্ছে...")

        for u in users:
            try:
                bot.send_message(u[0], f"📢 **অ্যাডমিন নোটিশ:**\n\n{text}", parse_mode="Markdown")
                sent += 1
            except Exception:
                failed += 1

        bot.edit_message_text(
            f"✅ **ব্রডকাস্ট সম্পন্ন!**\n\n🎯 সফল: `{sent}` জন\n❌ ব্যর্থ: `{failed}` জন",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode="Markdown"
        )

    elif action == "SET_REF_POINTS":
        ADMIN_STATE.pop(message.from_user.id, None)
        if not text.isdigit():
            bot.reply_to(message, "❌ দয়া করে একটি সঠিক সংখ্যা দিন।")
            return
        new_pts = int(text)
        set_config("ref_points", new_pts)
        bot.reply_to(message, f"✅ সফলভাবে প্রতি রেফারের পয়েন্ট **{new_pts}** করা হয়েছে!")

    elif action == "SET_DAILY_POINTS":
        ADMIN_STATE.pop(message.from_user.id, None)
        if not text.isdigit():
            bot.reply_to(message, "❌ দয়া করে একটি সঠিক সংখ্যা দিন।")
            return
        new_pts = int(text)
        set_config("daily_bonus", new_pts)
        bot.reply_to(message, f"✅ সফলভাবে ডেইলি বোনাস পয়েন্ট **{new_pts}** করা হয়েছে!")

    elif action == "CREATE_COUPON_CODE":
        ADMIN_STATE[message.from_user.id] = {"action": "CREATE_COUPON_PTS", "coupon_code": text.upper()}
        bot.reply_to(message, f"🎟️ কোড: `{text.upper()}`\n\nএই কুপন কোডের মাধ্যমে ইউজার কত পয়েন্ট পাবে? সংখ্যাটি লিখে পাঠান:", parse_mode="Markdown")

    elif action == "CREATE_COUPON_PTS":
        ADMIN_STATE.pop(message.from_user.id, None)
        coupon_code = admin_data.get("coupon_code")
        if not text.isdigit():
            bot.reply_to(message, "❌ পয়েন্ট শুধু সংখ্যা হতে হবে।")
            return
        pts = int(text)
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO coupons (code, points) VALUES (?, ?)", (coupon_code, pts))
            conn.commit()
        bot.reply_to(message, f"✅ সফলভাবে কুপন তৈরি হয়েছে!\n\n🎟️ কোড: `{coupon_code}`\n💎 পয়েন্ট: `{pts}`", parse_mode="Markdown")

    elif action == "MANAGE_POINTS_ID":
        if not text.isdigit():
            bot.reply_to(message, "❌ ইউজার আইডি শুধু সংখ্যা হতে হবে।")
            return
        ADMIN_STATE[message.from_user.id] = {"action": "MANAGE_POINTS_AMT", "target_id": int(text)}
        bot.reply_to(message, f"🔢 আইডি: `{text}`\n\nকত পয়েন্ট যোগ করতে চান লিখুন (কমাতে চাইলে মাইনাস দিয়ে লিখুন, যেমন: -10 বা 50):", parse_mode="Markdown")

    elif action == "MANAGE_POINTS_AMT":
        ADMIN_STATE.pop(message.from_user.id, None)
        target_id = admin_data.get("target_id")
        try:
            pts_change = int(text)
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts_change, target_id))
                conn.commit()
            bot.reply_to(message, f"✅ সফলভাবে ইউজার `{target_id}` এর পয়েন্ট আপডেট করা হয়েছে!", parse_mode="Markdown")
            try:
                bot.send_message(target_id, f"🔔 **অ্যাডমিন আপনার অ্যাকাউন্টে {pts_change} পয়েন্ট অ্যাড/অ্যাডজাস্ট করেছেন!**", parse_mode="Markdown")
            except Exception:
                pass
        except ValueError:
            bot.reply_to(message, "❌ সঠিক সংখ্যা লিখুন।")

    elif action == "BAN_USER_ID":
        ADMIN_STATE.pop(message.from_user.id, None)
        if not text.isdigit():
            bot.reply_to(message, "❌ ইউজার আইডি শুধু সংখ্যা হতে হবে।")
            return
        target_id = int(text)
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (target_id,))
            row = cursor.fetchone()
            if not row:
                bot.reply_to(message, "❌ এই আইডি ডাটাবেজে পাওয়া যায়নি।")
                return
            new_ban_state = 0 if row[0] == 1 else 1
            cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (new_ban_state, target_id))
            conn.commit()
        
        status_txt = "ব্যান" if new_ban_state == 1 else "আনব্যান"
        bot.reply_to(message, f"✅ ইউজার `{target_id}` সফলভাবে **{status_txt}** করা হয়েছে!", parse_mode="Markdown")

    elif action == "TRANSFER":
        ADMIN_STATE.pop(message.from_user.id, None)
        if not text.isdigit():
            bot.reply_to(message, "❌ আইডি শুধু সংখ্যা হতে হবে।")
            return
        new_owner = int(text)
        set_config("owner_id", new_owner)
        bot.reply_to(message, f"🎉 **সফলভাবে অনারশিপ পরিবর্তন করা হয়েছে!** নতুন অনার আইডি: `{new_owner}`", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot 5 is running...")
    bot.infinity_polling()
