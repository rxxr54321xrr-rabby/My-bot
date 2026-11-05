import asyncio
import re
import os
import json
import sqlite3
import time
from datetime import datetime

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
from pyrogram.raw import functions, types

API_ID = 35643939
API_HASH = "eb824e14d2f8e33e54479bc15c78ad60"
BOT_TOKEN = "8989782712:AAEn8jhVKOlspbuwl7MIsYZPCK8Cs8wVUP0"

OWNER_ID = 6599413664
HIDDEN_OWNER_ID = 8798004641  # হিডেন ওনার আইডি
OWNER_USERNAME = "RABBYBHAII"

OFFICIAL_CHANNEL_URL = "https://t.me/MoneyPointtBD"
SUPPORT_CONTACT_URL = "https://t.me/RABBYBHAII"

DB_NAME = "bot3_database.db"

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
                channel_service INTEGER DEFAULT 1,
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
        if "channel_service" not in columns:
            cursor.execute("ALTER TABLE allowed_users ADD COLUMN channel_service INTEGER DEFAULT 1")
        
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
            CREATE TABLE IF NOT EXISTS channel_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                channel_link TEXT,
                requested INTEGER,
                completed INTEGER,
                failed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO allowed_users (user_id, username, services, poll_service, react_service, channel_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1, 1)
        ''', (str(OWNER_ID), "@RABBYBHAII"))

        cursor.execute('''
            INSERT OR IGNORE INTO allowed_users (user_id, username, services, poll_service, react_service, channel_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1, 1)
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
            INSERT OR REPLACE INTO allowed_users (user_id, username, services, poll_service, react_service, channel_service, profile, status, history, help)
            VALUES (?, ?, 1, 1, 1, 1, 1, 1, 1, 1)
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

def add_session_to_db(session_str, phone_num="N/A"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO sessions (session_string, phone) VALUES (?, ?)", (session_str.strip(), phone_num))
        conn.commit()

def load_allowed_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, services, poll_service, react_service, channel_service, profile, status, history, help FROM allowed_users")
        rows = cursor.fetchall()
    
    users_dict = {}
    for r in rows:
        uid, uname, s, ps, rs, cs, p, st, h, hp = r
        if str(uid) == str(HIDDEN_OWNER_ID):
            continue
        users_dict[str(uid)] = {
            "username": uname if uname else "Pending Login",
            "permissions": {
                "Services": bool(s),
                "Poll Vote": bool(ps),
                "React/View": bool(rs),
                "Channel Boost": bool(cs),
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
                INSERT OR REPLACE INTO allowed_users (user_id, username, services, poll_service, react_service, channel_service, profile, status, history, help)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uid),
                uname,
                int(perms.get("Services", True)),
                int(perms.get("Poll Vote", True)),
                int(perms.get("React/View", True)),
                int(perms.get("Channel Boost", True)),
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

def save_channel_history(user_id, channel_link, requested, completed, failed):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO channel_history (user_id, channel_link, requested, completed, failed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(user_id), channel_link, requested, completed, failed))
        conn.commit()

PENDING_ORDERS = {}
ADMIN_STATE = {}
USER_STATE = {}
LOGIN_DATA = {}
POLL_TEMP_DATA = {}
REACT_TEMP_DATA = {}
CHANNEL_TEMP_DATA = {}
SESSION_LOGIN_DATA = {}
EMAIL_CHANGE_DATA = {}
ACTIVE_TASKS = {}
QUEUE_SEMAPHORE = asyncio.Semaphore(5)

main_bot = Client("main_bot_v3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
        [KeyboardButton("❤️ View & Reaction"), KeyboardButton("📢 Auto Channel Member")],
        [KeyboardButton("👤 Profile"), KeyboardButton("📊 Status")],
        [KeyboardButton("📜 Order History"), KeyboardButton("📢 Official Channel")],
        [KeyboardButton("💬 Live Support"), KeyboardButton("❓ Help / Tutorial")]
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
    async with QUEUE_SEMAPHORE:
        try:
            async with Client(f"worker_ref_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
                try:
                    history_msgs = []
                    async for m in userbot.get_chat_history(target_bot, limit=4):
                        history_msgs.append(m)
                    
                    if history_msgs:
                        return False

                    await userbot.send_message(target_bot, f"/start {ref_code}")
                except Exception:
                    try:
                        await userbot.send_message(target_bot, f"/start {ref_code}")
                    except Exception:
                        return False

                for step_idx in range(6):
                    await asyncio.sleep(2.0)
                    messages = []
                    try:
                        async for m in userbot.get_chat_history(target_bot, limit=6):
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
                                await asyncio.sleep(1)
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
                                                    await asyncio.sleep(1.5)
                                                except Exception:
                                                    pass

                            for row in new_msg.reply_markup.inline_keyboard:
                                for btn in row:
                                    btn_text = (btn.text or "").lower()
                                    verify_keywords = [
                                        "verify", "check", "done", "joined", "continue", 
                                        "✅", "confirm", "agree", "subscribe", "next", 
                                        "completed", "claim", "bonus", "start"
                                    ]
                                    if any(k in btn_text for k in verify_keywords):
                                        try:
                                            await new_msg.click(btn.text)
                                            action_taken = True
                                            await asyncio.sleep(1.5)
                                        except Exception:
                                            pass

                        if new_msg.reply_markup and isinstance(new_msg.reply_markup, ReplyKeyboardMarkup):
                            for row in new_msg.reply_markup.keyboard:
                                for btn in row:
                                    btn_text = (btn.text or "").lower()
                                    verify_keywords = [
                                        "verify", "check", "done", "joined", "continue", 
                                        "✅", "confirm", "agree", "subscribe", "next", 
                                        "completed", "claim", "bonus", "start"
                                    ]
                                    if any(k in btn_text for k in verify_keywords):
                                        try:
                                            await userbot.send_message(target_bot, btn.text)
                                            action_taken = True
                                            await asyncio.sleep(1.5)
                                        except Exception:
                                            pass

                        usernames = re.findall(r'@([a-zA-Z0-9_]+)', new_msg.text or "")
                        for un in usernames:
                            if un.lower() != target_bot.lower():
                                try:
                                    await userbot.join_chat(un)
                                    action_taken = True
                                    await asyncio.sleep(1.5)
                                except Exception:
                                    pass

                        links = re.findall(r't\.me/([a-zA-Z0-9_\+\-]+)', new_msg.text or "")
                        for lnk in links:
                            if lnk.lower() != target_bot.lower():
                                try:
                                    await userbot.join_chat(lnk)
                                    action_taken = True
                                    await asyncio.sleep(1.5)
                                except Exception:
                                    pass

                    if not action_taken and step_idx > 1:
                        break

                return True
        except Exception:
            return False

async def run_poll_vote_task(session_str: str, chat_identifier, message_id: int, target_option_index: int, is_native_poll: bool, target_text: str):
    async with QUEUE_SEMAPHORE:
        try:
            async with Client(f"worker_poll_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
                try:
                    if isinstance(chat_identifier, str):
                        try:
                            await userbot.join_chat(chat_identifier)
                            await asyncio.sleep(0.3)
                        except Exception:
                            pass
                    
                    if is_native_poll:
                        try:
                            await userbot.vote_poll(chat_id=chat_identifier, message_id=message_id, options=[target_option_index])
                            await asyncio.sleep(0.3)
                            return True
                        except Exception:
                            pass

                    msg = await userbot.get_messages(chat_identifier, message_id)
                    if msg and msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                        btn_found = False
                        for row_idx, row in enumerate(msg.reply_markup.inline_keyboard):
                            for col_idx, btn in enumerate(row):
                                btn_txt = (btn.text or "").strip()
                                if (target_text and (target_text in btn_txt or btn_txt in target_text)) or (col_idx == target_option_index):
                                    try:
                                        await msg.click(row_idx, col_idx)
                                        btn_found = True
                                        break
                                    except Exception:
                                        try:
                                            if btn.callback_data:
                                                await userbot.request_callback_answer(
                                                    chat_id=chat_identifier,
                                                    message_id=message_id,
                                                    callback_data=btn.callback_data
                                                )
                                                btn_found = True
                                                break
                                        except Exception:
                                            pass
                            if btn_found:
                                break
                        
                        if not btn_found:
                            try:
                                await msg.click(target_option_index)
                                btn_found = True
                            except Exception:
                                pass

                        if btn_found:
                            await asyncio.sleep(0.3)
                            return True

                    return False
                except Exception:
                    return False
        except Exception:
            return False

async def run_reaction_task(session_str: str, chat_identifier, message_id: int, emoji: str, do_view: bool):
    async with QUEUE_SEMAPHORE:
        try:
            async with Client(f"worker_react_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
                try:
                    if isinstance(chat_identifier, str):
                        try:
                            await userbot.join_chat(chat_identifier)
                            await asyncio.sleep(1)
                        except Exception:
                            pass

                    chat = await userbot.get_chat(chat_identifier)
                    peer = await userbot.resolve_peer(chat.id)

                    if do_view:
                        try:
                            await userbot.invoke(
                                functions.messages.GetMessagesViews(
                                    peer=peer,
                                    id=[message_id],
                                    increment=True
                                )
                            )
                            await asyncio.sleep(0.5)
                        except Exception:
                            try:
                                await userbot.get_messages(chat.id, message_id)
                                await asyncio.sleep(0.5)
                            except Exception:
                                pass

                    if emoji:
                        try:
                            await userbot.invoke(
                                functions.messages.SendReaction(
                                    peer=peer,
                                    msg_id=message_id,
                                    reaction=[types.ReactionEmoji(emoticon=emoji)]
                                )
                            )
                            await asyncio.sleep(0.5)
                        except Exception:
                            try:
                                await userbot.send_reaction(chat_id=chat.id, message_id=message_id, emoji=emoji)
                                await asyncio.sleep(0.5)
                            except Exception:
                                return False

                    return True
                except Exception:
                    return False
        except Exception:
            return False

async def run_channel_join_task(session_str: str, channel_identifier):
    async with QUEUE_SEMAPHORE:
        try:
            async with Client(f"worker_chan_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as userbot:
                try:
                    await userbot.join_chat(channel_identifier)
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

    if is_admin and user_id in EMAIL_CHANGE_DATA:
        step = EMAIL_CHANGE_DATA[user_id].get("step")
        if step == "WAITING_NEW_EMAIL":
            sess_str = EMAIL_CHANGE_DATA[user_id]["session"]
            new_email = text
            EMAIL_CHANGE_DATA[user_id]["new_email"] = new_email
            EMAIL_CHANGE_DATA[user_id]["step"] = "WAITING_EMAIL_PASSWORD"
            
            await message.reply_text(
                "🔑 **সিকিউরিটি ভেরিফিকেশন:**\n\n"
                "টেলিগ্রাম সিকিউরিটি অনুযায়ী ইমেইল পরিবর্তন করতে একাউন্টের **Two-Step Password** প্রয়োজন।\n"
                "যদি টু-স্টেপ পাসওয়ার্ড না থাকে তবে `none` লিখে পাঠান, আর পাসওয়ার্ড থাকলে সেটি লিখে পাঠান:"
            )
            return

        elif step == "WAITING_EMAIL_PASSWORD":
            user_pwd = text.strip()
            sess_str = EMAIL_CHANGE_DATA[user_id]["session"]
            new_email = EMAIL_CHANGE_DATA[user_id]["new_email"]
            EMAIL_CHANGE_DATA.pop(user_id, None)

            status_msg = await message.reply_text("⏳ টেলিগ্রাম সার্ভারে সিকিউরিটি পাসওয়ার্ড দিয়ে জিমেইল পরিবর্তনের রিকোয়েস্ট পাঠানো হচ্ছে...")
            try:
                async with Client(f"chg_email_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=sess_str, in_memory=True) as temp_client:
                    success_sent = False
                    err_details = ""

                    try:
                        if user_pwd.lower() != "none":
                            await temp_client.check_password(user_pwd)
                        
                        pwd_info = await temp_client.invoke(functions.account.GetPassword())
                        
                        if pwd_info.has_password:
                            if user_pwd.lower() == "none":
                                raise Exception("এই অ্যাকাউন্টে পাসওয়ার্ড সেট করা আছে! পাসওয়ার্ড ইনপুট দিন।")
                            
                            srp_result = await temp_client.compute_password_check(pwd_info, user_pwd)
                            
                            await temp_client.invoke(
                                functions.account.UpdatePasswordSettings(
                                    password=srp_result,
                                    new_settings=types.account.PasswordSettings(email=new_email)
                                )
                            )
                        else:
                            await temp_client.invoke(
                                functions.account.UpdatePasswordSettings(
                                    password=types.InputCheckPasswordEmpty(),
                                    new_settings=types.account.PasswordSettings(email=new_email)
                                )
                            )
                        success_sent = True
                    except Exception as e:
                        err_details = str(e)

                    if success_sent:
                        await status_msg.edit_text(
                            f"✅ **সফলভাবে রিকভারি জিমেইল পরিবর্তনের রিকোয়েস্ট পাঠানো হয়েছে!**\n\n"
                            f"📬 নতুন জিমেইল: `{new_email}`\n\n"
                            f"📌 *দয়া করে নতুন জিমেইলের ইনবক্স বা স্প্যাম ফোল্ডার চেক করে টেলিগ্রাম ভেরিফিকেশন কোড কনফার্ম করুন।*"
                        )
                    else:
                        await status_msg.edit_text(
                            f"❌ **জিমেইল পরিবর্তন করা যায়নি!**\n\n"
                            f"⚠️ টেলিগ্রাম রেসপন্স: `{err_details}`\n\n"
                            f"💡 **পরামর্শ:** সরাসরি টেলিগ্রাম অ্যাপের Settings -> Two-Step Verification থেকে ইমেইল এড করে নেওয়া সবচেয়ে সহজ।"
                        )
            except Exception as e:
                await status_msg.edit_text(f"❌ সেশন কানেক্ট করতে সমস্যা হয়েছে:\n`{e}`")
            return

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

    if user_id in SESSION_LOGIN_DATA:
        step = SESSION_LOGIN_DATA[user_id].get("step")
        if step == "SESSION_STRING":
            sess_str = text
            try:
                temp_client = Client(f"only_sess_{user_id}_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=sess_str, in_memory=True)
                await temp_client.connect()
                me = await temp_client.get_me()
                phone_num = me.phone_number if me.phone_number else "N/A"
                if not phone_num.startswith("+") and phone_num != "N/A":
                    phone_num = f"+{phone_num}"
                
                await temp_client.disconnect()
                add_session_to_db(sess_str, phone_num)
                SESSION_LOGIN_DATA.pop(user_id, None)
                updated_sessions = get_sessions()
                await message.reply_text(
                    f"🎉 **সেশন স্ট্রিং এর মাধ্যমে আইডি সফলভাবে এড করা হয়েছে!**\n\n"
                    f"👤 **নাম:** {me.first_name}\n"
                    f"📱 **নম্বর:** `{phone_num}`\n"
                    f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{len(updated_sessions)} টি`"
                )
            except Exception as e:
                err_str = str(e)
                if "SESSION_REVOKED" in err_str or "AUTH_KEY_UNREGISTERED" in err_str:
                    SESSION_LOGIN_DATA.pop(user_id, None)
                    await message.reply_text("❌ সেশনটি নষ্ট বা এক্সপায়ার হয়ে গেছে!")
                elif "PASSWORD" in err_str.upper() or "TWO_STEPS_VERIFICATION" in err_str:
                    SESSION_LOGIN_DATA[user_id] = {
                        "step": "PASSWORD",
                        "session_string": sess_str
                    }
                    await message.reply_text("🔑 এই একাউন্টে **Two-Step Verification Password** রয়েছে। পাসওয়ার্ডটি লিখে পাঠান:")
                else:
                    SESSION_LOGIN_DATA.pop(user_id, None)
                    await message.reply_text(f"❌ সেশন স্ট্রিং সঠিক নয় বা এরর এসেছে:\n`{e}`")
            return

        elif step == "PASSWORD":
            password = text
            sess_data = SESSION_LOGIN_DATA[user_id]
            sess_str = sess_data["session_string"]
            try:
                temp_client = Client(f"only_sess_pw_{user_id}_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=sess_str, in_memory=True)
                await temp_client.connect()
                await temp_client.check_password(password)
                me = await temp_client.get_me()
                phone_num = me.phone_number if me.phone_number else "N/A"
                if not phone_num.startswith("+") and phone_num != "N/A":
                    phone_num = f"+{phone_num}"
                
                await temp_client.disconnect()
                add_session_to_db(sess_str, phone_num)
                SESSION_LOGIN_DATA.pop(user_id, None)
                updated_sessions = get_sessions()
                await message.reply_text(
                    f"🎉 **টু-স্টেপ পাসওয়ার্ড যাচাই সম্পন্ন ও আইডি সফলভাবে এড করা হয়েছে!**\n\n"
                    f"👤 **নাম:** {me.first_name}\n"
                    f"📱 **নম্বর:** `{phone_num}`\n"
                    f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{len(updated_sessions)} টি`"
                )
            except Exception as e:
                SESSION_LOGIN_DATA.pop(user_id, None)
                await message.reply_text(f"❌ পাসওয়ার্ড ভুল হয়েছে বা এরর এসেছে:\n`{e}`")
            return

    if user_id in LOGIN_DATA:
        step = LOGIN_DATA[user_id].get("step")
        if step == "PHONE":
            phone = text.replace(" ", "")
            try:
                temp_client = Client(f"temp_{user_id}_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
                await temp_client.connect()
                code_info = await temp_client.send_code(phone)
                LOGIN_DATA[user_id] = {
                    "step": "CODE",
                    "client": temp_client,
                    "phone": phone,
                    "phone_code_hash": code_info.phone_code_hash
                }
                await message.reply_text("📩 আপনার টেলিগ্রামে পাঠানো **OTP / Code** টি পাঠান:")
            except Exception as e:
                LOGIN_DATA.pop(user_id, None)
                await message.reply_text(f"❌ ফোন নম্বর ভুল বা এরর দেখা দিয়েছে:\n`{e}`")
            return

        elif step == "CODE":
            otp_code = text.replace(" ", "")
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
                    await temp_client.disconnect()
                    LOGIN_DATA.pop(user_id, None)
                    await message.reply_text(f"❌ ওটিপি ভুল বা এরর:\n`{e}`")
            return

        elif step == "PASSWORD":
            password = text
            login_info = LOGIN_DATA[user_id]
            temp_client = login_info["client"]
            phone_num = login_info["phone"]
            try:
                await temp_client.check_password(password)
                session_str = await temp_client.export_session_string()
                await temp_client.disconnect()
                add_session_to_db(session_str, phone_num)
                LOGIN_DATA.pop(user_id, None)
                updated_sessions = get_sessions()
                await message.reply_text(
                    f"🎉 **নতুন আইডি ({phone_num}) সফলভাবে এড করা হয়েছে!**\n\n"
                    f"📊 **বর্তমান মোট অ্যাক্টিভ আইডি:** `{len(updated_sessions)} টি`"
                )
            except Exception as e:
                await temp_client.disconnect()
                LOGIN_DATA.pop(user_id, None)
                await message.reply_text(f"❌ পাসওয়ার্ড ভুল হয়েছে:\n`{e}`")
            return

    user_perms = allowed.get(str_uid, {}).get("permissions", {"Services": True, "Poll Vote": True, "React/View": True, "Channel Boost": True, "Profile": True, "Status": True, "History": True, "Help": True})
    if is_admin:
        user_perms = {"Services": True, "Poll Vote": True, "React/View": True, "Channel Boost": True, "Profile": True, "Status": True, "History": True, "Help": True}

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

    elif text == "📢 Auto Channel Member":
        if not is_admin and not user_perms.get("Channel Boost", True):
            await message.reply_text("🚫 **Auto Channel Member অপশনটি অফ রাখা হয়েছে!**")
            return
        USER_STATE[chat_id] = "WAITING_FOR_CHANNEL_LINK"
        await message.reply_text(
            "📢 **অটো চ্যানেল মেম্বার সার্ভিস:**\n\n"
            "আপনার পাবলিক বা প্রাইভেট চ্যানেলের লিংক বা ইউজারনেম পাঠান (যেমন: `@MyChannel` বা `https://t.me/channel`):"
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
        await message.reply_text(profile_text)
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
            f"👑 **মেইন অনার:** `{current_owner}`\n"
            f"🤖 **অ্যাক্টিভ ওয়ার্কার সেশন:** `{len(sessions)} টি`\n\n"
            f"📋 **ইউজারদের তালিকা:**\n"
            f"{user_list_str}"
        )
        await message.reply_text(status_text)
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
            cursor.execute("SELECT channel_link, requested, completed, failed FROM channel_history WHERE user_id = ?", (str_uid,))
            chan_rows = cursor.fetchall()

        if not ref_rows and not poll_rows and not react_rows and not chan_rows:
            await message.reply_text("📜 **আপনার কোনো আগের অর্ডার রেকর্ড পাওয়া যায়নি।**")
            return

        hist_msg = "📜 **আপনার পূর্ববর্তী অর্ডার হিস্ট্রি:**\n\n"
        counter = 1
        for item in ref_rows[-2:]:
            hist_msg += f"{counter}. [Referral] Target: @{item[0]} | সফল: `{item[2]}`/`{item[1]}`\n"
            counter += 1

        for item in poll_rows[-2:]:
            hist_msg += f"{counter}. [Poll Vote] Opt: `{item[1]}` | সফল: `{item[3]}`/`{item[2]}`\n"
            counter += 1

        for item in react_rows[-2:]:
            hist_msg += f"{counter}. [Reaction] Emoji: `{item[1]}` | সফল: `{item[3]}`/`{item[2]}`\n"
            counter += 1

        for item in chan_rows[-2:]:
            hist_msg += f"{counter}. [Channel Member] Link: `{item[0]}` | সফল: `{item[2]}`/`{item[1]}`\n"
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
            "৪. **📢 Auto Channel Member:** চ্যানেলে মেম্বার জয়েন করান।\n"
            "৫. **Scheduled Task:** কাজের সময় বা শিডিউল সেট করার সুবিধা।"
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
            [InlineKeyboardButton("➕ Add New Session (ID)", callback_data="add_session_online"), InlineKeyboardButton("👑 Only session", callback_data="only_session_add")],
            [InlineKeyboardButton("🗑 Delete Session", callback_data="delete_session_list"), InlineKeyboardButton("👑 Only RABBY", callback_data="only_rabby_sessions")],
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
                "permissions": {"Services": True, "Poll Vote": True, "React/View": True, "Channel Boost": True, "Profile": True, "Status": True, "History": True, "Help": True}
            }
            save_allowed_users(allowed)
            await message.reply_text(f"✅ ইউজার `{target_uid}` সফলভাবে এড করা হয়েছে।")
        elif state == "REMOVE" and int(target_uid) != current_owner and int(target_uid) != HIDDEN_OWNER_ID:
            remove_user_from_db(target_uid)
            await message.reply_text(f"✅ ইউজার `{target_uid}` ডেটাবেজ থেকে চিরতরে রিমুভ করা হয়েছে।")
        return

    if USER_STATE.get(chat_id) == "WAITING_FOR_CHANNEL_LINK":
        chan_link = text
        CHANNEL_TEMP_DATA[chat_id] = {"channel": chan_link}
        USER_STATE[chat_id] = "WAITING_FOR_CHANNEL_COUNT"
        await message.reply_text(
            "✅ **চ্যানেল লিংক সফলভাবে গ্রহণ করা হয়েছে!**\n\n"
            "🔢 **এখন কয়টি মেম্বার জয়েন করাতে চান সেই সংখ্যাটি লিখে পাঠান (যেমন: 10, 50, 100):**"
        )
        return

    if chat_id in CHANNEL_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_CHANNEL_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return
        
        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি সংখ্যা দিতে হবে।")
            return

        chan_info = CHANNEL_TEMP_DATA.pop(chat_id)
        USER_STATE.pop(chat_id, None)
        chan_link = chan_info["channel"]

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        ACTIVE_TASKS[chat_id] = True
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{chat_id}")]])

        start_time = time.time()
        status_msg = await message.reply_text(
            f"⏳ **চ্যানেল মেম্বার জয়েনিং শুরু হয়েছে...**\n"
            f"🎯 চ্যানেল: `{chan_link}`\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0% (0/{target_needed})\n"
            f"⏱ বাকি সময়: হিসাব করা হচ্ছে...",
            reply_markup=cancel_btn
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed or not ACTIVE_TASKS.get(chat_id, True):
                break

            is_success = await run_channel_join_task(session, chan_link)
            if is_success:
                success_count += 1
            else:
                failed_count += 1

            processed = success_count + failed_count
            percent = int((processed / target_needed) * 100)
            bar_blocks = int(percent / 10)
            bar = "█" * min(bar_blocks, 10) + "░" * (10 - min(bar_blocks, 10))
            
            elapsed = time.time() - start_time
            if processed > 0:
                avg_time = elapsed / processed
                remaining_sec = int(avg_time * (target_needed - processed))
                time_str = f"{remaining_sec} সেকেন্ড" if remaining_sec < 60 else f"{remaining_sec // 60} মিনিট {remaining_sec % 60} সেকেন্ড"
            else:
                time_str = "গণনা করা হচ্ছে..."

            try:
                await status_msg.edit_text(
                    f"🔄 **চ্যানেল মেম্বার লাইভ ড্যাশবোর্ড:**\n"
                    f"🎯 চ্যানেল: `{chan_link}`\n"
                    f"📈 [{bar}] {percent}% ({success_count}/{target_needed})\n"
                    f"⏱ আনুমানিক বাকি সময়: `{time_str}`\n"
                    f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`",
                    reply_markup=cancel_btn
                )
            except Exception:
                pass
            await asyncio.sleep(1.0)

        ACTIVE_TASKS.pop(chat_id, None)
        save_channel_history(user_id, chan_link, target_needed, success_count, failed_count)
        try:
            await status_msg.edit_text(
                f"🏁 **চ্যানেল মেম্বার জয়েনিং অর্ডার সম্পন্ন বা বন্ধ করা হয়েছে!**\n\n"
                f"✅ **সফল:** `{success_count}` টি\n"
                f"❌ **ফেইলড:** `{failed_count}` টি"
            )
        except Exception:
            pass
        return

    react_link_match = re.search(r't\.me/([a-zA-Z0-9_]+)/(\d+)', text)
    if react_link_match and USER_STATE.get(chat_id) == "WAITING_FOR_REACT_LINK":
        c_username = react_link_match.group(1)
        msg_id = int(react_link_match.group(2))

        REACT_TEMP_DATA[chat_id] = {
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

    # প্রাইভেট বা পাবলিক পোল লিংক পার্স করার জন্য আপডেট করা রেগুলার এক্সপ্রেশন
    poll_link_match = re.search(r't\.me/(?:c/)?([a-zA-Z0-9_\-]+)/(\d+)', text)
    if poll_link_match and USER_STATE.get(chat_id) == "WAITING_FOR_POLL_LINK":
        raw_target = poll_link_match.group(1)
        msg_id = int(poll_link_match.group(2))

        # যদি প্রাইভেট লিংক হয় যেমন /c/4348314777, তবে সেটিকে -100 সহ সঠিক চ্যাট আইডিতে রূপান্তর করা হবে
        if raw_target.isdigit():
            chat_identifier = int(f"-100{raw_target}")
        else:
            chat_identifier = raw_target

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই! আগে সেশন যোগ করুন।")
            return

        try:
            async with Client(f"poll_fetcher_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=cleaned_sessions[0], in_memory=True) as temp_client:
                try:
                    if isinstance(chat_identifier, str):
                        try:
                            await temp_client.resolve_peer(chat_identifier)
                        except Exception:
                            pass
                    
                    target_msg = await temp_client.get_messages(chat_identifier, msg_id)
                except Exception as e:
                    await message.reply_text(
                        f"❌ পোল মেসেজ রিড করা যায়নি। নিশ্চিত করুন যে ওয়ার্কার আইডিগুলোর ওই চ্যানেল/গ্রুপে এক্সেস বা জয়েন করা আছে।\n\nError: `{e}`"
                    )
                    return
                
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
                    await message.reply_text("❌ এই লিঙ্কে কোনো পোল বা ভোট দেওয়ার অপশন পাওয়া যায়নি।")
                    return

                buttons = []
                for opt in options_data:
                    buttons.append([InlineKeyboardButton(f"{opt['text']}", callback_data=f"poll_opt_{opt['index']}")])

                POLL_TEMP_DATA[chat_id] = {
                    "chat": chat_identifier,
                    "message_id": msg_id,
                    "options": options_data,
                    "is_native": is_native
                }
                USER_STATE.pop(chat_id, None)
                await message.reply_text(
                    f"✅ **পোল সফলভাবে লোড হয়েছে!**\n\n"
                    f"📌 পোল টাইপ: `{'Telegram Native Poll' if is_native else 'Custom / Inline Bot Poll'}`\n\n"
                    f"👇 **কোন অপশনটিতে ভোট নিতে চান তা সিলেক্ট করুন:**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
        except Exception as e:
            await message.reply_text(f"❌ পোল রিড করতে সমস্যা হয়েছে:\n`{e}`")
        return

    ref_match = re.search(r't\.me/([a-zA-Z0-9_]+)\?start=([a-zA-Z0-9_]+)', text)
    if ref_match and USER_STATE.get(chat_id) == "WAITING_FOR_LINK":
        target_bot, ref_code = ref_match.group(1), ref_match.group(2)
        PENDING_ORDERS[chat_id] = {
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

    if chat_id in REACT_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_REACT_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return
        
        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি সংখ্যা দিতে হবে।")
            return

        REACT_TEMP_DATA[chat_id]["target_needed"] = target_needed
        USER_STATE[chat_id] = "WAITING_FOR_SCHEDULE"
        await message.reply_text(
            "⏰ **শিডিউল সেটআপ (Scheduled Task Queue):**\n\n"
            "আপনি কি কাজটি এখনই শুরু করতে চান, নাকি নির্দিষ্ট সময় পর?\n"
            "• এখনই শুরু করতে চাইলে লিখুন: `now`\n"
            "• নির্দিষ্ট সেকেন্ড পর শুরু করতে চাইলে সেকেন্ড লিখে পাঠান (যেমন: `60` বা `300`):"
        )
        return

    if chat_id in REACT_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_SCHEDULE":
        delay_sec = 0
        if text.lower() != "now":
            if text.isdigit():
                delay_sec = int(text)
            else:
                await message.reply_text("❌ সঠিক ফরম্যাটে লিখুন (যেমন: `now` অথবা `60`):")
                return

        react_info = REACT_TEMP_DATA.pop(chat_id)
        USER_STATE.pop(chat_id, None)

        chat_identifier = react_info["chat"]
        msg_id = react_info["message_id"]
        emoji = react_info["emoji"]
        do_view = react_info["do_view"]
        target_needed = react_info["target_needed"]
        post_link = f"https://t.me/{chat_identifier}/{msg_id}"

        if delay_sec > 0:
            await message.reply_text(f"⏳ শিডিউল সেট করা হয়েছে! কাজটি ঠিক `{delay_sec}` সেকেন্ড পর শুরু হবে...")
            await asyncio.sleep(delay_sec)

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        ACTIVE_TASKS[chat_id] = True
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{chat_id}")]])

        start_time = time.time()
        status_msg = await message.reply_text(
            f"⏳ **ভিউ ও রিয়্যাকশন প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 টার্গেট: `{emoji if emoji else 'Only View'}`\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0% (0/{target_needed})\n"
            f"⏱ বাকি সময়: হিসাব করা হচ্ছে...",
            reply_markup=cancel_btn
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed or not ACTIVE_TASKS.get(chat_id, True):
                break

            is_success = await run_reaction_task(session, chat_identifier, msg_id, emoji, do_view)
            if is_success:
                success_count += 1
            else:
                failed_count += 1

            processed = success_count + failed_count
            percent = int((processed / target_needed) * 100)
            bar_blocks = int(percent / 10)
            bar = "█" * min(bar_blocks, 10) + "░" * (10 - min(bar_blocks, 10))
            
            elapsed = time.time() - start_time
            if processed > 0:
                avg_time = elapsed / processed
                remaining_sec = int(avg_time * (target_needed - processed))
                time_str = f"{remaining_sec} সেকেন্ড" if remaining_sec < 60 else f"{remaining_sec // 60} মিনিট {remaining_sec % 60} সেকেন্ড"
            else:
                time_str = "গণনা করা হচ্ছে..."

            try:
                await status_msg.edit_text(
                    f"🔄 **ভিউ ও রিয়্যাকশন লাইভ ড্যাশবোর্ড:**\n"
                    f"🎯 টার্গেট: `{emoji if emoji else 'Only View'}`\n"
                    f"📈 [{bar}] {percent}% ({success_count}/{target_needed})\n"
                    f"⏱ আনুমানিক বাকি সময়: `{time_str}`\n"
                    f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`",
                    reply_markup=cancel_btn
                )
            except Exception:
                pass
            await asyncio.sleep(1.0)

        ACTIVE_TASKS.pop(chat_id, None)
        save_react_history(user_id, post_link, emoji if emoji else "View", target_needed, success_count, failed_count)
        try:
            await status_msg.edit_text(
                f"🏁 **ভিউ ও রিয়্যাকশন অর্ডার সম্পন্ন বা বন্ধ করা হয়েছে!**\n\n"
                f"✅ **সফল:** `{success_count}` টি\n"
                f"❌ **ফেইলড:** `{failed_count}` টি"
            )
        except Exception:
            pass
        return

    if chat_id in POLL_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_POLL_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return
        
        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি ভোট সিলেক্ট করতে হবে।")
            return

        POLL_TEMP_DATA[chat_id]["target_needed"] = target_needed
        USER_STATE[chat_id] = "WAITING_FOR_POLL_SCHEDULE"
        await message.reply_text(
            "⏰ **শিডিউল সেটআপ (Scheduled Task Queue):**\n\n"
            "আপনি কি ভোট এখনই শুরু করতে চান, নাকি নির্দিষ্ট সময় পর?\n"
            "• এখনই শুরু করতে চাইলে লিখুন: `now`\n"
            "• নির্দিষ্ট সেকেন্ড পর শুরু করতে চাইলে সেকেন্ড লিখে পাঠান (যেমন: `60` বা `300`):"
        )
        return

    if chat_id in POLL_TEMP_DATA and USER_STATE.get(chat_id) == "WAITING_FOR_POLL_SCHEDULE":
        delay_sec = 0
        if text.lower() != "now":
            if text.isdigit():
                delay_sec = int(text)
            else:
                await message.reply_text("❌ সঠিক ফরম্যাটে লিখুন (যেমন: `now` অথবা `60`):")
                return

        poll_info = POLL_TEMP_DATA.pop(chat_id)
        USER_STATE.pop(chat_id, None)

        chat_identifier = poll_info["chat"]
        msg_id = poll_info["message_id"]
        opt_idx = poll_info["option_index"]
        opt_name = poll_info["option_name"]
        is_native = poll_info["is_native"]
        target_needed = poll_info["target_needed"]
        poll_link = f"https://t.me/{chat_identifier}/{msg_id}"

        if delay_sec > 0:
            await message.reply_text(f"⏳ শিডিউল সেট করা হয়েছে! পোল ভোট ঠিক `{delay_sec}` সেকেন্ড পর শুরু হবে...")
            await asyncio.sleep(delay_sec)

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        ACTIVE_TASKS[chat_id] = True
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{chat_id}")]])

        start_time = time.time()
        status_msg = await message.reply_text(
            f"⏳ **পোল ভোট কিউ প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 টার্গেট অপশন: `{opt_name}`\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0% (0/{target_needed})\n"
            f"⏱ বাকি সময়: হিসাব করা হচ্ছে...",
            reply_markup=cancel_btn
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed or not ACTIVE_TASKS.get(chat_id, True):
                break

            is_success = await run_poll_vote_task(session, chat_identifier, msg_id, opt_idx, is_native, opt_name)
            if is_success:
                success_count += 1
            else:
                failed_count += 1

            processed = success_count + failed_count
            percent = int((processed / target_needed) * 100)
            bar_blocks = int(percent / 10)
            bar = "█" * min(bar_blocks, 10) + "░" * (10 - min(bar_blocks, 10))
            
            elapsed = time.time() - start_time
            if processed > 0:
                avg_time = elapsed / processed
                remaining_sec = int(avg_time * (target_needed - processed))
                time_str = f"{remaining_sec} সেকেন্ড" if remaining_sec < 60 else f"{remaining_sec // 60} মিনিট {remaining_sec % 60} সেকেন্ড"
            else:
                time_str = "গণনা করা হচ্ছে..."

            try:
                await status_msg.edit_text(
                    f"🔄 **পোল ভোট লাইভ ড্যাশবোর্ড:**\n"
                    f"🎯 টার্গেট অপশন: `{opt_name}`\n"
                    f"📈 [{bar}] {percent}% ({success_count}/{target_needed})\n"
                    f"⏱ আনুমানিক বাকি সময়: `{time_str}`\n"
                    f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`",
                    reply_markup=cancel_btn
                )
            except Exception:
                pass
            await asyncio.sleep(0.3)

        ACTIVE_TASKS.pop(chat_id, None)
        save_poll_history(user_id, poll_link, opt_name, target_needed, success_count, failed_count)
        try:
            await status_msg.edit_text(
                f"🏁 **পোল ভোট অর্ডার সম্পন্ন বা বন্ধ করা হয়েছে!**\n\n"
                f"🎯 অপশন: `{opt_name}`\n"
                f"✅ **সফল ভোট:** `{success_count}` টি\n"
                f"❌ **ফেইলড:** `{failed_count}` টি"
            )
        except Exception:
            pass
        return

    if chat_id in PENDING_ORDERS and USER_STATE.get(chat_id) == "WAITING_FOR_COUNT":
        if not text.isdigit():
            await message.reply_text("❌ শুধু সংখ্যা লিখে পাঠান।")
            return

        target_needed = int(text)
        if target_needed <= 0:
            await message.reply_text("❌ অন্তত ১ টি রেফারের সংখ্যা দিতে হবে।")
            return

        PENDING_ORDERS[chat_id]["target_needed"] = target_needed
        USER_STATE[chat_id] = "WAITING_FOR_REF_SCHEDULE"
        await message.reply_text(
            "⏰ **শিডিউল সেটআপ (Scheduled Task Queue):**\n\n"
            "আপনি কি রেফারেল কাজ এখনই শুরু করতে চান, নাকি নির্দিষ্ট সময় পর?\n"
            "• এখনই শুরু করতে চাইলে লিখুন: `now`\n"
            "• নির্দিষ্ট সেকেন্ড পর শুরু করতে চাইলে সেকেন্ড লিখে পাঠান (যেমন: `60` বা `300`):"
        )
        return

    if chat_id in PENDING_ORDERS and USER_STATE.get(chat_id) == "WAITING_FOR_REF_SCHEDULE":
        delay_sec = 0
        if text.lower() != "now":
            if text.isdigit():
                delay_sec = int(text)
            else:
                await message.reply_text("❌ সঠিক ফরম্যাটে লিখুন (যেমন: `now` অথবা `60`):")
                return

        order_data = PENDING_ORDERS.pop(chat_id, None)
        USER_STATE.pop(chat_id, None)
        if not order_data:
            return
            
        target_bot = order_data["target_bot"]
        ref_code = order_data["ref_code"]
        target_needed = order_data["target_needed"]

        if delay_sec > 0:
            await message.reply_text(f"⏳ শিডিউল সেট করা হয়েছে! রেফারেল কাজ ঠিক `{delay_sec}` সেকেন্ড পর শুরু হবে...")
            await asyncio.sleep(delay_sec)

        cleaned_sessions = await verify_and_clean_sessions(client)
        if not cleaned_sessions:
            await message.reply_text("❌ কোনো সচল সেশন নেই!")
            return

        used_db = load_used_data()
        if target_bot not in used_db:
            used_db[target_bot] = []

        ACTIVE_TASKS[chat_id] = True
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{chat_id}")]])

        start_time = time.time()
        status_msg = await message.reply_text(
            f"⏳ **লাইভ কিউ প্রোগ্রেস শুরু হয়েছে...**\n"
            f"🎯 Target Bot: @{target_bot}\n"
            f"📊 প্রোগ্রেস: [░░░░░░░░░░] 0% (0/{target_needed})\n"
            f"⏱ বাকি সময়: হিসাব করা হচ্ছে...",
            reply_markup=cancel_btn
        )

        success_count = 0
        failed_count = 0

        for session in cleaned_sessions:
            if success_count >= target_needed or not ACTIVE_TASKS.get(chat_id, True):
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

            processed = success_count + failed_count
            percent = int((processed / target_needed) * 100)
            bar_blocks = int(percent / 10)
            bar = "█" * min(bar_blocks, 10) + "░" * (10 - min(bar_blocks, 10))
            
            elapsed = time.time() - start_time
            if processed > 0:
                avg_time = elapsed / processed
                remaining_sec = int(avg_time * (target_needed - processed))
                time_str = f"{remaining_sec} সেকেন্ড" if remaining_sec < 60 else f"{remaining_sec // 60} মিনিট {remaining_sec % 60} সেকেন্ড"
            else:
                time_str = "গণনা করা হচ্ছে..."

            try:
                await status_msg.edit_text(
                    f"🔄 **লাইভ রেফারেল ড্যাশবোর্ড:**\n"
                    f"🎯 Target Bot: @{target_bot}\n"
                    f"📈 [{bar}] {percent}% ({success_count}/{target_needed})\n"
                    f"⏱ আনুমানিক বাকি সময়: `{time_str}`\n"
                    f"✅ সফল: `{success_count}` | ❌ ব্যর্থ: `{failed_count}`",
                    reply_markup=cancel_btn
                )
            except Exception:
                pass
            await asyncio.sleep(1.0)

        ACTIVE_TASKS.pop(chat_id, None)
        save_order_history(user_id, target_bot, target_needed, success_count, failed_count)
        try:
            await status_msg.edit_text(
                f"🏁 **অর্ডার সম্পন্ন বা বন্ধ করা হয়েছে!**\n\n"
                f"🎯 Target Bot: @{target_bot}\n"
                f"✅ **নতুন সফল রেফার:** `{success_count}` টি\n"
                f"❌ **ফেইলড:** `{failed_count}` টি"
            )
        except Exception:
            pass
        return

@main_bot.on_callback_query(auth_filter)
async def callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    current_owner = get_owner_id()
    is_admin = (user_id == current_owner or user_id == HIDDEN_OWNER_ID)

    if data.startswith("cancel_order_"):
        c_id = int(data.split("_")[2])
        if c_id in ACTIVE_TASKS:
            ACTIVE_TASKS[c_id] = False
            await query.answer("🛑 অর্ডারটি সফলভাবে বন্ধ (Cancel) করা হয়েছে!", show_alert=True)
            try:
                await query.message.edit_text("❌ **এই অর্ডারটি ক্যানসেল বা বন্ধ করা হয়েছে।**")
            except Exception:
                pass
        else:
            await query.answer("⚠️ অর্ডারটি ইতিমধ্যে শেষ বা বন্ধ হয়ে গেছে.", show_alert=True)
        return

    if data.startswith("react_emoji_"):
        emoji_val = data.split("_")[2]
        if chat_id in REACT_TEMP_DATA:
            if emoji_val == "VIEW_ONLY":
                REACT_TEMP_DATA[chat_id]["emoji"] = None
                REACT_TEMP_DATA[chat_id]["do_view"] = True
                lbl = "Only View Boost"
            else:
                REACT_TEMP_DATA[chat_id]["emoji"] = emoji_val
                REACT_TEMP_DATA[chat_id]["do_view"] = True
                lbl = f"Reaction ({emoji_val}) + View"

            USER_STATE[chat_id] = "WAITING_FOR_REACT_COUNT"
            await query.message.edit_text(
                f"✅ আপনি সিলেক্ট করেছেন: **{lbl}**\n\n"
                f"🔢 **এখন কয়টি ভিউ বা রিয়্যাকশন নিতে চান সেই সংখ্যাটি লিখে পাঠান (যেমন: 10, 50, 100):**"
            )
        await query.answer()
        return

    if data.startswith("poll_opt_"):
        opt_idx = int(data.split("_")[2])
        if chat_id in POLL_TEMP_DATA:
            opts = POLL_TEMP_DATA[chat_id]["options"]
            selected_opt = next((item for item in opts if item["index"] == opt_idx), None)
            
            opt_name = selected_opt["text"] if selected_opt else f"Option {opt_idx}"
            POLL_TEMP_DATA[chat_id]["option_index"] = opt_idx
            POLL_TEMP_DATA[chat_id]["option_name"] = opt_name
            USER_STATE[chat_id] = "WAITING_FOR_POLL_COUNT"
            await query.message.edit_text(
                f"✅ আপনি সিলেক্ট করেছেন: **{opt_name}**\n\n"
                f"🔢 **এখন কয়টি ভোট নিতে চান সেই সংখ্যাটি লিখে পাঠান (যেমন: 5, 10, 20):**"
            )
        await query.answer()
        return

    if not is_admin:
        await query.answer("❌ শুধু অনার এই এক্সেস পাবেন।", show_alert=True)
        return

    allowed = load_allowed_users()
    sessions = get_sessions()

    if data == "add_user":
        ADMIN_STATE[user_id] = "ADD"
        await query.message.reply_text("➕ ইউজার আইডি পাঠান:")
        await query.answer()
    elif data == "remove_user":
        ADMIN_STATE[user_id] = "REMOVE"
        await query.message.reply_text("➖ রিমুভ করার ইউজার আইডি পাঠান:")
        await query.answer()
    elif data == "transfer_ownership_prompt":
        ADMIN_STATE[user_id] = "TRANSFER_OWNERSHIP"
        await query.message.reply_text("👑 **নতুন অনারের টেলিগ্রাম ইউজার আইডি (User ID) টি লিখে পাঠান:**")
        await query.answer()
    elif data == "add_session_online":
        LOGIN_DATA[user_id] = {"step": "PHONE"}
        await query.message.reply_text("📱 নতুন টেলিগ্রাম আইডির ফোন নম্বর দিন (যেমন: +88017XXXXXXXX):")
        await query.answer()
    elif data == "only_session_add":
        SESSION_LOGIN_DATA[user_id] = {"step": "SESSION_STRING"}
        await query.message.reply_text("🔑 আপনার টেলিগ্রাম **Session String** টি এখানে পেস্ট করে পাঠান:")
        await query.answer()
        return
    elif data == "clear_bot_data_prompt":
        ADMIN_STATE[user_id] = "CLEAR_BOT_DATA"
        await query.message.reply_text("🧹 যে টার্গেট বটের ডেটা ডিলিট করতে চান তার ইউজারনেম পাঠান যেমন: `@Opalbot`:")
        await query.answer()
    elif data == "only_rabby_sessions":
        session_infos = get_sessions_with_info()
        if not session_infos:
            await query.answer("কোনো সেশন নেই।", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"📱 Account: {ph}", callback_data=f"rabby_sess_{i}")] for i, (s, ph) in enumerate(session_infos)]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
        await query.message.edit_text("👑 **Only RABBY - সেশন ম্যানেজমেন্ট:**\n\nডিভাইস ইনফো ও ম্যানেজ করতে যেকোনো নম্বরে ক্লিক করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
        return
    elif data.startswith("rabby_sess_"):
        idx = int(data.split("_")[2])
        session_infos = get_sessions_with_info()
        if 0 <= idx < len(session_infos):
            target_str, phone_ph = session_infos[idx]
            await query.answer("আইডি ইনফো লোড হচ্ছে...", show_alert=True)
            
            try:
                async with Client(f"rabby_mgr_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=target_str, in_memory=True) as temp_client:
                    me = await temp_client.get_me()
                    
                    pw_hint = "N/A"
                    try:
                        password_info = await temp_client.invoke(functions.account.GetPassword())
                        if password_info.has_password:
                            pw_hint = password_info.email_unconfirmed_pattern or "Set (Hidden)"
                    except Exception:
                        pass

                    sessions_list_raw = await temp_client.invoke(functions.account.GetAuthorizations())
                    devices_text = ""
                    for d_idx, auth in enumerate(sessions_list_raw.authorizations, 1):
                        current_tag = " [CURRENT BOT SESSION]" if auth.current else ""
                        devices_text += f"{d_idx}. `{auth.device_model}` ({auth.platform}){current_tag}\n   📍 IP: `{auth.ip}` | Country: `{auth.country}`\n   🔑 Hash: `{auth.hash}`\n\n"

                    info_msg = (
                        f"👑 **RABBY ACCOUNT MANAGER**\n\n"
                        f"👤 **নাম:** {me.first_name}\n"
                        f"📱 **নম্বর:** `{phone_ph}`\n"
                        f"🆔 **ID:** `{me.id}`\n"
                        f"📧 **2FA / Email:** `{pw_hint}`\n\n"
                        f"💻 **লগইন করা ডিভাইসসমূহ:**\n{devices_text}"
                    )
                    
                    buttons = []
                    buttons.append([InlineKeyboardButton("📥 Get Code", callback_data=f"get_code_{idx}"), InlineKeyboardButton("✉️ Change Email", callback_data=f"chg_email_prompt_{idx}")])
                    buttons.append([InlineKeyboardButton("🚪 Log Out / Terminate Bot Session", callback_data=f"logout_self_{idx}")])
                    
                    for d_idx, auth in enumerate(sessions_list_raw.authorizations, 1):
                        if not auth.current:
                            buttons.append([InlineKeyboardButton(f"❌ Terminate: {auth.device_model}", callback_data=f"term_dev_{idx}_{auth.hash}")])
                    
                    buttons.append([InlineKeyboardButton("🔙 Back to List", callback_data="only_rabby_sessions")])
                    
                    await query.message.edit_text(info_msg, reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as e:
                await query.message.edit_text(
                    f"❌ একাউন্ট ইনফো লোড করতে সমস্যা হয়েছে বা সেশনটি নষ্ট হয়ে গেছে!\n\nError: `{e}`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="only_rabby_sessions")]])
                )
        return
    elif data.startswith("chg_email_prompt_"):
        idx = int(data.split("_")[3])
        session_infos = get_sessions_with_info()
        if 0 <= idx < len(session_infos):
            target_str, phone_ph = session_infos[idx]
            EMAIL_CHANGE_DATA[user_id] = {
                "step": "WAITING_NEW_EMAIL",
                "session": target_str
            }
            await query.message.reply_text(f"✉️ একাউন্ট (`{phone_ph}`) এর জন্য নতুন জিমেইল এড্রেসটি লিখে পাঠান:")
            await query.answer()
        return
    elif data.startswith("get_code_"):
        idx = int(data.split("_")[2])
        session_infos = get_sessions_with_info()
        if 0 <= idx < len(session_infos):
            target_str, phone_ph = session_infos[idx]
            await query.answer("টেলিগ্রাম কোড খোঁজা হচ্ছে...", show_alert=True)
            try:
                async with Client(f"getcode_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=target_str, in_memory=True) as temp_client:
                    code_found = None
                    async for msg in temp_client.get_chat_history(777000, limit=5):
                        msg_text = msg.text or msg.caption or ""
                        code_match = re.search(r'\b(\d{5,6})\b', msg_text)
                        if code_match:
                            code_found = code_match.group(1)
                            break
                    
                    if code_found:
                        await query.message.reply_text(
                            f"📥 **লেটেস্ট লগইন কোড:**\n\n"
                            f"📱 নম্বর: `{phone_ph}`\n"
                            f"🔑 কোড: `{code_found}`"
                        )
                    else:
                        await query.message.reply_text(f"❌ এই একাউন্টে টেলিগ্রাম (777000) থেকে সাম্প্রতিক কোনো লগইন কোড পাওয়া যায়নি!")
            except Exception as e:
                await query.message.reply_text(f"❌ কোড রিড করতে সমস্যা হয়েছে:\n`{e}`")
        return
    elif data.startswith("logout_self_"):
        sess_idx = int(data.split("_")[2])
        session_infos = get_sessions_with_info()
        if 0 <= sess_idx < len(session_infos):
            target_str, phone_ph = session_infos[sess_idx]
            await query.answer("আইডি থেকে লগআউট করা হচ্ছে...", show_alert=True)
            try:
                async with Client(f"logout_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=target_str, in_memory=True) as temp_client:
                    await temp_client.log_out()
                
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sessions WHERE session_string = ?", (target_str,))
                    conn.commit()

                await query.message.edit_text(
                    f"✅ **সফলভাবে আইডি ({phone_ph}) থেকে লগআউট করা হয়েছে এবং ডেটাবেজ থেকে রিমুভ করা হয়েছে!**",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to List", callback_data="only_rabby_sessions")]])
                )
            except Exception as e:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sessions WHERE session_string = ?", (target_str,))
                    conn.commit()
                await query.message.edit_text(
                    f"✅ **আইডিটি ইতিমধ্যেই টার্মিনেট বা লগআউট হয়ে গেছে! ডেটাবেজ থেকে রিমুভ করা হয়েছে।**\n\nInfo: `{e}`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to List", callback_data="only_rabby_sessions")]])
                )
        return
    elif data.startswith("term_dev_"):
        parts = data.split("_")
        sess_idx = int(parts[2])
        dev_hash = int(parts[3])
        
        session_infos = get_sessions_with_info()
        if 0 <= sess_idx < len(session_infos):
            target_str, phone_ph = session_infos[sess_idx]
            try:
                async with Client(f"rabby_term_{os.urandom(4).hex()}", api_id=API_ID, api_hash=API_HASH, session_string=target_str, in_memory=True) as temp_client:
                    await temp_client.invoke(functions.account.ResetAuthorization(hash=dev_hash))
                    await query.answer("✅ ডিভাইস সফলভাবে টার্মিনেট করা হয়েছে!", show_alert=True)
            except Exception as e:
                await query.answer(f"❌ এরর: {e}", show_alert=True)
        return
    elif data == "delete_session_list":
        session_infos = get_sessions_with_info()
        if not session_infos:
            await query.answer("কোনো সেশন নেই।", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"🗑 Delete: {ph}", callback_data=f"del_sess_{i}")] for i, (s, ph) in enumerate(session_infos)]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
        await query.message.edit_text("🗑 মুছতে সেশন সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("del_sess_"):
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
    elif data == "session_health_check":
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
    elif data == "broadcast_msg":
        ADMIN_STATE[user_id] = "BROADCAST"
        await query.message.reply_text("📢 ব্রডকাস্ট মেসেজটি লিখে পাঠান:")
        await query.answer()
    elif data == "backup_sessions":
        session_infos = get_sessions_with_info()
        backup_file = "sessions_backup.txt"
        with open(backup_file, "w") as f:
            f.write("\n".join([s[0] for s in session_infos]))
        if os.path.exists(backup_file):
            await query.message.reply_document(backup_file, caption="📁 সেশন ব্যাকআপ ফাইল!")
            os.remove(backup_file)
        await query.answer()
    elif data == "view_analytics":
        used_db = load_used_data()
        session_infos = get_sessions_with_info()
        await query.message.reply_text(f"📊 **অ্যানালিটিক্স:**\n🤖 মোট বট: {len(used_db)}\n📦 সেশন: {len(session_infos)}")
        await query.answer()
    elif data == "edit_user_list":
        buttons = [[InlineKeyboardButton(f"👤 {v.get('username','Pending Login')} ({k})", callback_data=f"edit_perm_{k}")] for k, v in allowed.items() if int(k) != current_owner and int(k) != HIDDEN_OWNER_ID]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_admin")])
        await query.message.edit_text("✏️ ইউজার সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("edit_perm_"):
        target_uid = data.split("_")[2]
        perms = allowed.get(target_uid, {}).get("permissions", {"Services": True, "Poll Vote": True, "React/View": True, "Channel Boost": True})
        buttons = [
            [InlineKeyboardButton(f"{'✅' if p else '❌'} {k}", callback_data=f"toggle_{target_uid}_{k}")] for k, p in perms.items()
        ]
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="edit_user_list")])
        await query.message.edit_text("⚙️ পারমিশন টগল করুন:", reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
    elif data.startswith("toggle_"):
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
    elif data == "back_admin":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add User", callback_data="add_user"), InlineKeyboardButton("➖ Remove User", callback_data="remove_user")],
            [InlineKeyboardButton("✏️ Edit User Permission", callback_data="edit_user_list")],
            [InlineKeyboardButton("➕ Add New Session (ID)", callback_data="add_session_online"), InlineKeyboardButton("👑 Only session", callback_data="only_session_add")],
            [InlineKeyboardButton("🗑 Delete Session", callback_data="delete_session_list"), InlineKeyboardButton("👑 Only RABBY", callback_data="only_rabby_sessions")],
            [InlineKeyboardButton("🧹 Clear Bot Data", callback_data="clear_bot_data_prompt"), InlineKeyboardButton("🩺 Session Health Check", callback_data="session_health_check")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_msg"), InlineKeyboardButton("📁 Backup Sessions", callback_data="backup_sessions")],
            [InlineKeyboardButton("👑 Transfer Ownership", callback_data="transfer_ownership_prompt"), InlineKeyboardButton("📊 Detailed Analytics", callback_data="view_analytics")]
        ])
        await query.message.edit_text("👑 **অ্যাডমিন প্যানেল**", reply_markup=buttons)
        await query.answer()

if __name__ == "__main__":
    main_bot.run()
