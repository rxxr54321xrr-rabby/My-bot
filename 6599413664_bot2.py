import logging
import sqlite3
import html
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ২ নম্বর বট কনফিগারেশন ---
BOT_TOKEN = "8818736579:AAHe7GIZc0-U8XigxIfCf604llnp21U8MoE" # ২ নম্বর বটের টোকেন
PRIMARY_OWNER_ID = 6599413664 # মূল ওনার ১
SECONDARY_OWNER_ID = 7479085424 # মূল ওনার ২
PROTECTED_CHANNEL = "@MoneyPointtBD" # যে চ্যানেল মূল এডমিন ছাড়া কেউ রিমুভ করতে পারবে না
DB_NAME = "bot2_database.db" # ২য় বটের জন্য পৃথক ডাটাবেস

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# এডমিন ফিচার পারমিশনের তালিকা
ADMIN_PERMISSIONS_LIST = [
    ("adm_add_point", "➕ Add Point"),
    ("adm_sub_point", "➖ Deduct Point"),
    ("adm_user_details", "👤 User Details"),
    ("adm_search_user", "🔍 Search User"),
    ("adm_ban_user", "🚫 Ban User"),
    ("adm_unban_user", "✅ Unban User"),
    ("adm_banned_list", "📜 Banned List"),
    ("adm_send_gift", "🎁 Send Gift"),
    ("adm_set_dep_num", "📱 Set Deposit Number"),
    ("adm_set_support_id", "💬 Set Support ID"),
    ("adm_pay_cnl_menu", "💳 Payment CNL"),
    ("adm_add_ch", "➕ Add Channel"),
    ("adm_del_ch", "❌ Del Channel"),
    ("adm_list_ch", "📢 List Channels"),
    ("adm_clear_ch", "🔄 Clear Channels"),
    ("adm_add_admin", "👑 Add Admin"),
    ("adm_rem_admin", "❌ Remove Admin"),
    ("adm_refer_stats", "👥 Refer Stats"),
    ("adm_stats", "📊 Stats"),
    ("adm_pending_dep", "📥 Pending Deposits"),
    ("adm_pending_orders", "📤 Pending Orders"),
    ("adm_app_history", "✅ Approved History"),
    ("adm_rej_history", "❌ Rejected History"),
    ("adm_set_ref_pt", "⚙️ Set Refer Point"),
    ("adm_create_gift", "🎁 Create Gift Code"),
    ("adm_del_gift", "🗑 Delete Gift Code"),
    ("adm_list_gift", "📜 Active Gift Codes"),
    ("adm_broadcast", "📢 Broadcast"),
    ("adm_direct_msg", "✉ Direct Message"),
    ("adm_maint_mode", "🔒 Maintenance Mode"),
    ("adm_add_task", "➕ Add Task"),
    ("adm_manage_tasks", "📋 Manage Tasks"),
    ("adm_set_review_ch", "⚙️ Change Review Channel"),
    ("adm_refer_block", "🚫 Refer Block"),
    ("adm_set_min_order", "⚙️ Set Min Order Limit"),
    ("adm_owner_change", "👑 Owner Change")
]

# --- ডাটাবেস সেটআপ (২য় বট) ---
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    # ইউজার টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            points REAL DEFAULT 0,
            total_refers INTEGER DEFAULT 0,
            referred_by INTEGER,
            banned INTEGER DEFAULT 0,
            refer_blocked INTEGER DEFAULT 0
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN refer_blocked INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    # এডমিন টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY
        )
    ''')

    # এডমিন পারমিশন টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_permissions (
            user_id INTEGER,
            permission_key TEXT,
            is_allowed INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, permission_key)
        )
    ''')
    
    # অর্ডার টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_type TEXT,
            amount INTEGER,
            link TEXT,
            poll_name TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN poll_name TEXT")
    except sqlite3.OperationalError:
        pass
    
    # ডিপোজিট টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            deposit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            method TEXT,
            amount REAL,
            trx_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # সেটিংস টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # ফোর্সেড জয়েন চ্যানেল টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS force_channels (
            channel_name TEXT,
            channel_username TEXT PRIMARY KEY,
            channel_url TEXT
        )
    ''')

    # গিফট কোড টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gift_codes (
            code TEXT PRIMARY KEY,
            points REAL,
            max_uses INTEGER,
            used_count INTEGER DEFAULT 0
        )
    ''')

    # গিফট কোড ব্যবহারের রেকর্ড
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gift_claims (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )
    ''')

    # টাস্ক সিস্টেম টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            link TEXT,
            reward REAL,
            status TEXT DEFAULT 'Active'
        )
    ''')

    # টাস্ক সাবমিশন টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_submissions (
            sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_id INTEGER,
            photo_file_id TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("refer_point", "1")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("maint_mode", "off")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("pay_channel", "@Refer2votepayment")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("support_id", "RABBYBhAII")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("dep_bkash", "01968782512")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("dep_nagad", "01968782512")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("dep_rocket", "01968782512")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("review_channel", "-1002476532187")')
    cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("min_order_limit", "3")')
    
    cursor.execute('INSERT OR IGNORE INTO force_channels VALUES ("Channel 1", "@MoneyPointtBD", "https://t.me/MoneyPointtBD")')
    cursor.execute('INSERT OR IGNORE INTO force_channels VALUES ("Channel 2", "@Refer2votepayment", "https://t.me/Refer2votepayment")')

    conn.commit()
    conn.close()

init_db()

# --- হেল্পার ফাংশনসমূহ ---
def get_db():
    return sqlite3.connect(DB_NAME, timeout=10)

def is_owner(user_id: int) -> bool:
    if user_id in [PRIMARY_OWNER_ID, SECONDARY_OWNER_ID]:
        return True
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = "owner_id"')
    row = cursor.fetchone()
    conn.close()
    if row and str(user_id) == str(row[0]):
        return True
    return False

def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return True if row else False

def has_permission(user_id: int, perm_key: str) -> bool:
    if is_owner(user_id):
        return True
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_allowed FROM admin_permissions WHERE user_id = ? AND permission_key = ?', (user_id, perm_key))
    row = cursor.fetchone()
    conn.close()
    return True if row is None or row[0] == 1 else False

def set_permission(user_id: int, perm_key: str, is_allowed: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO admin_permissions (user_id, permission_key, is_allowed) VALUES (?, ?, ?)',
                   (user_id, perm_key, is_allowed))
    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, val):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(val)))
    conn.commit()
    conn.close()

def get_refer_point():
    try:
        return float(get_setting("refer_point", "1"))
    except:
        return 1.0

def get_pay_channel():
    return get_setting("pay_channel", "@Refer2votepayment")

def get_review_channel():
    return get_setting("review_channel", "-1002476532187")

def get_min_order_limit():
    try:
        return int(get_setting("min_order_limit", "3"))
    except:
        return 3

def get_user_point_source_emoji(user_id: int) -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM deposits WHERE user_id = ? AND status = "Approved"', (user_id,))
    dep_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT total_refers FROM users WHERE user_id = ?', (user_id,))
    u_row = cursor.fetchone()
    total_refers = u_row[0] if u_row else 0
    conn.close()

    if dep_count > 0:
        return "🟢👑"
    elif total_refers > 10:
        return "🔴"
    else:
        return "🟢🎭"

def get_or_create_user(user, referred_by=None, context=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, points, total_refers, banned, refer_blocked FROM users WHERE user_id = ?', (user.id,))
    row = cursor.fetchone()
    
    if not row:
        ref_pt = get_refer_point()
        cursor.execute('INSERT INTO users (user_id, first_name, username, points, total_refers, referred_by) VALUES (?, ?, ?, ?, ?, ?)',
                       (user.id, user.first_name, user.username, 0, 0, referred_by))
        
        if referred_by and referred_by != user.id:
            cursor.execute('SELECT refer_blocked FROM users WHERE user_id = ?', (referred_by,))
            ref_user_row = cursor.fetchone()
            is_ref_blocked = ref_user_row[0] if ref_user_row else 0

            if not is_ref_blocked:
                cursor.execute('UPDATE users SET points = points + ?, total_refers = total_refers + 1 WHERE user_id = ?', (ref_pt, referred_by))
                conn.commit()
                
                if context:
                    try:
                        app_async = context.bot
                        app_async.loop.create_task(
                            app_async.send_message(
                                chat_id=referred_by,
                                text=f"🎉 <b>নতুন রেফার জয়েন করেছে!</b>\n\n👤 নাম: {html.escape(user.first_name)}\n⭐ বোনাস পয়েন্ট: <b>+{ref_pt} Point</b>",
                                parse_mode="HTML"
                            )
                        )
                    except Exception:
                        pass
        
        conn.commit()
        cursor.execute('SELECT user_id, points, total_refers, banned, refer_blocked FROM users WHERE user_id = ?', (user.id,))
        row = cursor.fetchone()
    else:
        cursor.execute('UPDATE users SET first_name = ?, username = ? WHERE user_id = ?', (user.first_name, user.username, user.id))
        conn.commit()
        
    conn.close()
    return row

async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT channel_username FROM force_channels')
    channels = cursor.fetchall()
    conn.close()
    
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch[0], user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            pass
    return True

def get_join_keyboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT channel_name, channel_url FROM force_channels')
    channels = cursor.fetchall()
    conn.close()
    
    keyboard = []
    for ch in channels:
        keyboard.append([InlineKeyboardButton(f"📢 Join {ch[0]}", url=ch[1])])
    keyboard.append([InlineKeyboardButton("✅ Joined", callback_data="check_joined")])
    return InlineKeyboardMarkup(keyboard)

def get_main_keyboard(user_id: int):
    keyboard = [
        ['👤 প্রোফাইল', '🎯 Refer & Earn'],
        ['📢 Bot Refer Buy', '📦 Poll Vote Buy'],
        ['💰 Deposit', '📜 My Orders'],
        ['🏆 Leaderboard', '🎁 Gift Code'],
        ['🎯 Task', '💬 Support']
    ]
    if is_admin(user_id):
        keyboard.append(['👑 ADMIN PANEL'])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_panel_markup(user_id: int):
    keyboard = [
        [InlineKeyboardButton("➕ Add Point", callback_data="adm_add_point"), InlineKeyboardButton("➖ Deduct Point", callback_data="adm_sub_point")],
        [InlineKeyboardButton("👤 User Details", callback_data="adm_user_details"), InlineKeyboardButton("🔍 Search User", callback_data="adm_search_user")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="adm_ban_user"), InlineKeyboardButton("✅ Unban User", callback_data="adm_unban_user")],
        [InlineKeyboardButton("📜 Banned Users List", callback_data="adm_banned_list"), InlineKeyboardButton("🎁 Send Gift", callback_data="adm_send_gift")],
        
        [InlineKeyboardButton("📱 Set Deposit Number", callback_data="adm_set_dep_num"), InlineKeyboardButton("💬 Set Support ID", callback_data="adm_set_support_id")],
        [InlineKeyboardButton("💳 Payment CNL", callback_data="adm_pay_cnl_menu")],
        
        [InlineKeyboardButton("➕ Add Channel", callback_data="adm_add_ch"), InlineKeyboardButton("❌ Del Channel", callback_data="adm_del_ch")],
        [InlineKeyboardButton("📢 List Channels", callback_data="adm_list_ch"), InlineKeyboardButton("🔄 Clear Channels", callback_data="adm_clear_ch")],
        
        [InlineKeyboardButton("👑 Add Admin", callback_data="adm_add_admin"), InlineKeyboardButton("❌ Remove Admin", callback_data="adm_rem_admin")],
        [InlineKeyboardButton("👥 Refer Stats", callback_data="adm_refer_stats"), InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],

        [InlineKeyboardButton("📥 Pending Deposits", callback_data="adm_pending_dep"), InlineKeyboardButton("📤 Pending Orders", callback_data="adm_pending_orders")],
        [InlineKeyboardButton("✅ Approved History", callback_data="adm_app_history"), InlineKeyboardButton("❌ Rejected History", callback_data="adm_rej_history")],
        
        [InlineKeyboardButton("⚙️ Set Refer Point", callback_data="adm_set_ref_pt"), InlineKeyboardButton("🎁 Create Gift Code", callback_data="adm_create_gift")],
        [InlineKeyboardButton("🗑 Delete Gift Code", callback_data="adm_del_gift"), InlineKeyboardButton("📜 Active Gift Codes", callback_data="adm_list_gift")],
        
        [InlineKeyboardButton("➕ Add Task", callback_data="adm_add_task"), InlineKeyboardButton("📋 Manage Tasks", callback_data="adm_manage_tasks")],
        [InlineKeyboardButton("⚙️ Change Review Channel", callback_data="adm_set_review_ch"), InlineKeyboardButton("🚫 Refer Block", callback_data="adm_refer_block")],

        [InlineKeyboardButton("⚙️ Set Min Order Limit", callback_data="adm_set_min_order")],
        [InlineKeyboardButton("👑 Owner Change", callback_data="adm_owner_change")],

        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"), InlineKeyboardButton("✉ Direct Message", callback_data="adm_direct_msg")],
        [InlineKeyboardButton("🔒 Maintenance Mode", callback_data="adm_maint_mode")]
    ]
    
    if is_owner(user_id):
        keyboard.append([InlineKeyboardButton("👑 SPECIAL PANEL (Perms)", callback_data="adm_special_panel")])
        
    return InlineKeyboardMarkup(keyboard)

def get_subadmins_keyboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins WHERE user_id NOT IN (?, ?)', (PRIMARY_OWNER_ID, SECONDARY_OWNER_ID))
    admins = cursor.fetchall()
    conn.close()

    keyboard = []
    for a in admins:
        keyboard.append([InlineKeyboardButton(f"👤 Sub-Admin: {a[0]}", callback_data=f"sp_select_admin_{a[0]}")])
    return InlineKeyboardMarkup(keyboard)

def get_perm_manage_keyboard(target_admin_id: int):
    keyboard = []
    for key, label in ADMIN_PERMISSIONS_LIST:
        allowed = has_permission(target_admin_id, key)
        status = "✅ ON" if allowed else "❌ OFF"
        keyboard.append([InlineKeyboardButton(f"{label}: {status}", callback_data=f"sp_toggle_{target_admin_id}_{key}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Sub-Admins List", callback_data="adm_special_panel")])
    return InlineKeyboardMarkup(keyboard)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if get_setting("maint_mode") == "on" and not is_admin(user.id):
        await update.message.reply_text("🔒 <b>বট বর্তমানে মেইনটেন্যান্স মোডে রয়েছে। অনুগ্রহ করে পরে চেষ্টা করুন।</b>", parse_mode="HTML")
        return

    referred_by = None
    if context.args and context.args[0].isdigit():
        referred_by = int(context.args[0])
        
    u_data = get_or_create_user(user, referred_by, context)
    if u_data[3] == 1:
        await update.message.reply_text("🚫 আপনার অ্যাকাউন্টটি ব্যান করা হয়েছে।")
        return

    if not await is_user_joined(user.id, context):
        msg = "⚠️ <b>বটটি ব্যবহার করতে আমাদের চ্যানেলগুলোতে জয়েন করুন:</b>"
        await update.message.reply_text(msg, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    welcome_msg = f"হ্যালো {html.escape(user.first_name)}!\n\nআমাদের বটে আপনাকে স্বাগতম।"
    await update.message.reply_text(welcome_msg, reply_markup=get_main_keyboard(user.id))

# --- Admin Command ---
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ আপনি এডমিন নন!")
        return

    await update.message.reply_text("👑 <b>Admin Control Panel</b>\n\nনিচের অপশনগুলো বেছে নিন:", reply_markup=get_admin_panel_markup(user.id), parse_mode="HTML")

# --- Callbacks Handler ---
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "check_joined":
        if await is_user_joined(user_id, context):
            await query.message.delete()
            await context.bot.send_message(chat_id=user_id, text="✅ <b>ধন্যবাদ! আপনি সকল চ্যানেলে জয়েন করেছেন।</b>", reply_markup=get_main_keyboard(user_id), parse_mode="HTML")
        else:
            await query.answer("❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)

    elif data in ["dep_bkash", "dep_nagad", "dep_rocket"]:
        method_map = {
            "dep_bkash": ("bKash", "dep_bkash"),
            "dep_nagad": ("Nagad", "dep_nagad"),
            "dep_rocket": ("Rocket", "dep_rocket")
        }
        method_name, key_name = method_map[data]
        current_num = get_setting(key_name, "01968782512")
        
        context.user_data['dep_method'] = method_name
        context.user_data['state'] = 'DEP_AMOUNT'

        msg = (
            f"📱 <b>{method_name} Deposit</b>\n\n"
            f"📱 <b>{method_name} Number:</b>\n<code>{current_num}</code>\n\n"
            f"💰 Minimum Deposit: 10 টাকা\n\n"
            f"👉 কত টাকা Deposit করবেন লিখুন:"
        )
        await query.message.reply_text(msg, parse_mode="HTML")

    elif data.startswith("task_do_"):
        task_id = int(data.split("_")[2])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT title, description, link, reward FROM tasks WHERE task_id = ? AND status = "Active"', (task_id,))
        task = cursor.fetchone()
        conn.close()

        if not task:
            await query.answer("❌ এই টাস্কটি আর সক্রিয় নেই।", show_alert=True)
            return

        context.user_data['sub_task_id'] = task_id
        context.user_data['state'] = 'SUBMIT_TASK_SCREENSHOT'

        msg = (
            f"🎯 <b>Task: {html.escape(task[0])}</b>\n\n"
            f"📝 বিবরণ: {html.escape(task[1])}\n"
            f"🔗 লিংক: {task[2]}\n"
            f"⭐ পুরস্কার: {task[3]} Point\n\n"
            f"👉 টাস্ক সম্পন্ন করে কাজের প্রুফ হিসেবে একটি <b>স্ক্রিনশট (Screenshot)</b> ছবি পাঠান:"
        )
        await query.message.reply_text(msg, parse_mode="HTML")

    elif data.startswith("app_task_"):
        sub_id = int(data.split("_")[2])
        if not is_admin(user_id) or not has_permission(user_id, "adm_add_task"):
            await query.answer("❌ অনুমতি নেই!", show_alert=True)
            return

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, task_id, status FROM task_submissions WHERE sub_id = ?', (sub_id,))
        sub = cursor.fetchone()

        if not sub:
            await query.answer("❌ সাবমিশন পাওয়া যায়নি।", show_alert=True)
            conn.close()
            return

        target_user_id, task_id, current_status = sub

        if current_status == "Approved":
            await query.answer("⚠ এই টাস্কটি ইতিমধ্যে এপ্রুভ করা হয়েছে!", show_alert=True)
            conn.close()
            return

        cursor.execute('SELECT reward, title FROM tasks WHERE task_id = ?', (task_id,))
        t_data = cursor.fetchone()
        reward = t_data[0] if t_data else 0
        t_title = t_data[1] if t_data else "Task"

        cursor.execute('UPDATE task_submissions SET status = "Approved" WHERE sub_id = ?', (sub_id,))
        cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (reward, target_user_id))
        conn.commit()
        conn.close()

        try:
            old_caption = query.message.caption or ""
            new_caption = old_caption.replace("Status: Pending", "Status: Approved ✅")
            if "Status: Approved" not in new_caption:
                new_caption += "\n\n<b>Status: Approved ✅</b>"
            await query.message.edit_caption(caption=new_caption, parse_mode="HTML")
        except Exception:
            pass

        await query.answer("✅ টাস্ক সফলভাবে এপ্রুভ করা হয়েছে!")

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 <b>আপনার টাস্ক সাবমিশন এপ্রুভ হয়েছে!</b>\n\n🎯 Task: {t_title}\n⭐ বোনাস: <b>+{reward} Point</b> যোগ করা হয়েছে।",
                parse_mode="HTML"
            )
        except:
            pass

    elif data.startswith("rej_task_"):
        sub_id = int(data.split("_")[2])
        if not is_admin(user_id) or not has_permission(user_id, "adm_add_task"):
            await query.answer("❌ অনুমতি নেই!", show_alert=True)
            return

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, status FROM task_submissions WHERE sub_id = ?', (sub_id,))
        sub = cursor.fetchone()

        if not sub:
            await query.answer("❌ সাবমিশন পাওয়া যায়নি।", show_alert=True)
            conn.close()
            return

        target_user_id, current_status = sub
        if current_status == "Rejected":
            await query.answer("⚠ ইতিমধ্যে রিজেক্ট করা হয়েছে।", show_alert=True)
            conn.close()
            return

        cursor.execute('UPDATE task_submissions SET status = "Rejected" WHERE sub_id = ?', (sub_id,))
        conn.commit()
        conn.close()

        try:
            old_caption = query.message.caption or ""
            new_caption = old_caption.replace("Status: Pending", "Status: Rejected ❌")
            if "Status: Rejected" not in new_caption:
                new_caption += "\n\n<b>Status: Rejected ❌</b>"
            await query.message.edit_caption(caption=new_caption, parse_mode="HTML")
        except Exception:
            pass

        await query.answer("❌ টাস্ক রিজেক্ট করা হয়েছে!")

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ <b>আপনার টাস্ক সাবমিশন রিজেক্ট করা হয়েছে।</b> সঠিক প্রুফ দিয়ে আবার চেষ্টা করুন।",
                parse_mode="HTML"
            )
        except:
            pass

    # --- TASK MANAGEMENT CALLBACKS ---
    elif data.startswith("adm_mng_task_"):
        task_id = int(data.split("_")[3])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT title, description, link, reward, status FROM tasks WHERE task_id = ?', (task_id,))
        t = cursor.fetchone()
        conn.close()

        if not t:
            await query.answer("❌ টাস্ক পাওয়া যায়নি।", show_alert=True)
            return

        status_text = "🟢 Active" if t[4] == "Active" else "🔴 Inactive"
        toggle_text = "🔴 Turn Off" if t[4] == "Active" else "🟢 Turn On"

        msg = (
            f"📋 <b>Task Management</b>\n\n"
            f"🆔 ID: {task_id}\n"
            f"📌 Title: {html.escape(t[0])}\n"
            f"📝 Desc: {html.escape(t[1])}\n"
            f"🔗 Link: {t[2]}\n"
            f"⭐ Reward: {t[3]} Pts\n"
            f"📌 Status: {status_text}"
        )
        kbd = InlineKeyboardMarkup([
            [InlineKeyboardButton(toggle_text, callback_data=f"adm_ttoggle_{task_id}"),
             InlineKeyboardButton("🗑 Delete", callback_data=f"adm_tdel_{task_id}")],
            [InlineKeyboardButton("🔙 Back to Tasks List", callback_data="adm_manage_tasks")]
        ])
        await query.message.edit_text(msg, reply_markup=kbd, parse_mode="HTML")

    elif data.startswith("adm_ttoggle_"):
        task_id = int(data.split("_")[2])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM tasks WHERE task_id = ?', (task_id,))
        curr_status = cursor.fetchone()[0]
        new_status = "Inactive" if curr_status == "Active" else "Active"
        cursor.execute('UPDATE tasks SET status = ? WHERE task_id = ?', (new_status, task_id))
        conn.commit()
        conn.close()
        await query.answer(f"✅ টাস্ক স্ট্যাটাস পরিবর্তন করে {new_status} করা হয়েছে!")
        return

    elif data.startswith("adm_tdel_"):
        task_id = int(data.split("_")[2])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
        cursor.execute('DELETE FROM task_submissions WHERE task_id = ?', (task_id,))
        conn.commit()
        conn.close()
        await query.answer("🗑 টাস্কটি সফলভাবে ডিলিট করা হয়েছে!")
        await query.message.edit_text("🗑 <b>টাস্কটি সফলভাবে ডিলিট করা হয়েছে।</b>", parse_mode="HTML")
        return

    elif is_admin(user_id):
        # --- SPECIAL PANEL (MAIN ADMIN ONLY) ---
        if data == "adm_special_panel":
            if not is_owner(user_id):
                await query.answer("❌ এটি শুধুমাত্র মূল মালিকের (Owner) জন্য সংরক্ষিত!", show_alert=True)
                return
            kbd = get_subadmins_keyboard()
            if not kbd.inline_keyboard:
                await query.message.reply_text("👑 <b>SPECIAL PANEL</b>\n\nবর্তমানে কোনো সাব-এডমিন (Sub-Admin) নেই।", parse_mode="HTML")
            else:
                await query.message.reply_text("👑 <b>SPECIAL PANEL - Admin Permission Manager</b>\n\nযে এডমিনের পারমিশন কন্ট্রোল করতে চান তাকে সিলেক্ট করুন:", reply_markup=kbd, parse_mode="HTML")
            return

        elif data.startswith("sp_select_admin_"):
            if not is_owner(user_id):
                await query.answer("❌ অনুমতি নেই!", show_alert=True)
                return
            target_admin_id = int(data.split("_")[3])
            await query.message.reply_text(
                f"⚙️ <b>Sub-Admin:</b> <code>{target_admin_id}</code>\n\nবাটনের ওপর ক্লিক করে ON / OFF করুন:",
                reply_markup=get_perm_manage_keyboard(target_admin_id),
                parse_mode="HTML"
            )
            return

        elif data.startswith("sp_toggle_"):
            if not is_owner(user_id):
                await query.answer("❌ অনুমতি নেই!", show_alert=True)
                return
            parts = data.split("_")
            target_admin_id = int(parts[2])
            perm_key = "_".join(parts[3:])
            
            current_status = has_permission(target_admin_id, perm_key)
            new_status = 0 if current_status else 1
            set_permission(target_admin_id, perm_key, new_status)
            
            await query.edit_message_reply_markup(reply_markup=get_perm_manage_keyboard(target_admin_id))
            await query.answer("✅ পারমিশন আপডেট করা হয়েছে!")
            return

        # --- SUB-ADMIN PERMISSION CHECK ---
        if data in [p[0] for p in ADMIN_PERMISSIONS_LIST] or data in ["adm_set_pay_cnl", "adm_del_pay_cnl", "set_num_bkash", "set_num_nagad", "set_num_rocket"]:
            check_key = data
            if data in ["adm_set_pay_cnl", "adm_del_pay_cnl"]:
                check_key = "adm_pay_cnl_menu"
            elif data in ["set_num_bkash", "set_num_nagad", "set_num_rocket"]:
                check_key = "adm_set_dep_num"

            if not has_permission(user_id, check_key):
                await query.answer("🚫 এই ফিচারটি ব্যবহার করার অনুমতি আপনাকে দেওয়া হয়নি!", show_alert=True)
                return

        # --- STANDARD ADMIN ACTIONS ---
        if data == "adm_owner_change":
            if not is_owner(user_id):
                await query.answer("❌ শুধুমাত্র বর্তমান মূল ওনার (Owner) ওনারশিপ পরিবর্তন করতে পারবেন!", show_alert=True)
                return
            context.user_data['state'] = 'ADM_OWNER_CHANGE_INP'
            await query.message.reply_text("👑 <b>Owner Change</b>\n\nনতুন ওনার (Owner) বানাতে চান এমন ইউজারের <b>User ID</b> লিখে পাঠান:\n\n⚠️ <i>সতর্কতা: নতুন ওনার সেট করলে আপনার সমস্ত ওনার রাইটস নতুন ইউজারের কাছে চলে যাবে।</i>", parse_mode="HTML")

        elif data == "adm_pay_cnl_menu":
            curr_ch = get_pay_channel()
            kbd = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Set / Change Payment CNL", callback_data="adm_set_pay_cnl")],
                [InlineKeyboardButton("🗑 Delete Payment CNL", callback_data="adm_del_pay_cnl")]
            ])
            msg = f"💳 <b>Payment / Log Channel Settings</b>\n\n📌 <b>বর্তমান পেমেন্ট চ্যানেল:</b> {curr_ch if curr_ch else 'নেই (Not Set)'}"
            await query.message.reply_text(msg, reply_markup=kbd, parse_mode="HTML")

        elif data == "adm_set_pay_cnl":
            context.user_data['state'] = 'ADM_SET_PAY_CNL_INP'
            await query.message.reply_text("💳 <b>নতুন Payment Channel এর @username পাঠাও:</b>\n\nউদাহরণ:\n<code>@Refer2votepayment</code>", parse_mode="HTML")

        elif data == "adm_del_pay_cnl":
            set_setting("pay_channel", "")
            await query.message.reply_text("🗑️ <b>Payment Channel সফলভাবে মুছে ফেলা হয়েছে!</b>", parse_mode="HTML")

        elif data == "adm_set_support_id":
            context.user_data['state'] = 'ADM_SET_SUPPORT_INP'
            curr_supp = get_setting("support_id", "RABBYBhAII")
            await query.message.reply_text(f"💬 <b>বর্তমান সাপোর্ট আইডি:</b> @{curr_supp}\n\nনতুন সাপোর্ট Username ( @ ছাড়া ) লিখুন:", parse_mode="HTML")

        elif data == "adm_set_dep_num":
            keyboard = [
                [InlineKeyboardButton("💖 বিকাশ (bKash)", callback_data="set_num_bkash")],
                [InlineKeyboardButton("💚 নগদ (Nagad)", callback_data="set_num_nagad")],
                [InlineKeyboardButton("🚀 রকেট (Rocket)", callback_data="set_num_rocket")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📱 <b>কোন পেমেন্ট মেথডের নাম্বার পরিবর্তন করতে চান?</b>", reply_markup=reply_markup, parse_mode="HTML")

        elif data in ["set_num_bkash", "set_num_nagad", "set_num_rocket"]:
            method_key = data.replace("set_num_", "dep_")
            context.user_data['change_num_key'] = method_key
            context.user_data['state'] = 'ADM_SET_DEP_NUM_INP'
            method_name = method_key.replace("dep_", "").capitalize()
            await query.message.reply_text(f"✏️ <b>{method_name}</b> এর নতুন নাম্বারটি লিখে পাঠান:", parse_mode="HTML")

        elif data == "adm_add_point":
            context.user_data['state'] = 'ADM_ADD_PT_INP'
            await query.message.reply_text("➕ <b>User ID এবং Point স্পেস দিয়ে লিখুন:</b>\n\n<code>6599413664 100</code>", parse_mode="HTML")

        elif data == "adm_sub_point":
            context.user_data['state'] = 'ADM_SUB_PT_INP'
            await query.message.reply_text("➖ <b>User ID এবং কর্তনকৃত Point স্পেস দিয়ে লিখুন:</b>\n\n<code>6599413664 50</code>", parse_mode="HTML")

        elif data in ["adm_user_details", "adm_search_user"]:
            context.user_data['state'] = 'ADM_SEARCH_USR_INP'
            await query.message.reply_text("👤 <b>ইউজারের User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_ban_user":
            context.user_data['state'] = 'ADM_BAN_USR_INP'
            await query.message.reply_text("🚫 <b>ব্যান করতে চাওয়ার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_unban_user":
            context.user_data['state'] = 'ADM_UNBAN_USR_INP'
            await query.message.reply_text("✅ <b>আনব্যান করতে চাওয়ার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_banned_list":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, first_name FROM users WHERE banned = 1')
            b_users = cursor.fetchall()
            conn.close()
            txt = "📜 <b>Banned Users List:</b>\n\n"
            txt += "\n".join([f"• <code>{u[0]}</code> - {html.escape(str(u[1]))}" for u in b_users]) if b_users else "কোনো ব্যান ইউজার নেই।"
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_send_gift":
            context.user_data['state'] = 'ADM_SEND_GIFT_INP'
            await query.message.reply_text("🎁 <b>User ID এবং Gift Point স্পেস দিয়ে লিখুন:</b>\n\n<code>6599413664 20</code>", parse_mode="HTML")

        elif data == "adm_add_admin":
            if not is_owner(user_id):
                await query.message.reply_text("❌ শুধু মূল মালিক নতুন এডমিন যুক্ত করতে পারবেন!")
                return
            context.user_data['state'] = 'ADM_ADD_ADMIN_INP'
            await query.message.reply_text("👑 <b>Admin বানাতে চাওয়ার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_rem_admin":
            if not is_owner(user_id):
                await query.message.reply_text("❌ শুধু মূল মালিক এডমিন রিমুভ করতে পারবেন!")
                return
            context.user_data['state'] = 'ADM_REM_ADMIN_INP'
            await query.message.reply_text("❌ <b>Admin থেকে সরাতে চাওয়ার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_refer_stats":
            context.user_data['state'] = 'ADM_REF_STATS_INP'
            await query.message.reply_text("👥 <b>রেফারেল ডিটেইলস দেখতে চাওয়ার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_refer_block":
            context.user_data['state'] = 'ADM_REFER_BLOCK_INP'
            await query.message.reply_text("🚫 <b>যে ইউজারের রেফার ব্লক বা আনব্লক করবেন তার User ID লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_add_ch":
            context.user_data['state'] = 'ADM_ADD_CH_INP'
            await query.message.reply_text("➕ <b>নতুন চ্যানেল স্পেস দিয়ে লিখুন:</b>\n\n<code>Name @Username Link</code>", parse_mode="HTML")

        elif data == "adm_del_ch":
            context.user_data['state'] = 'ADM_DEL_CH_INP'
            await query.message.reply_text("❌ <b>যে চ্যানেল মুছবেন তার @username লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_list_ch":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT channel_name, channel_username FROM force_channels')
            channels = cursor.fetchall()
            conn.close()
            txt = "📢 <b>যুক্ত থাকা চ্যানেলসমূহ:</b>\n\n"
            txt += "\n".join([f"• {c[0]}: {c[1]}" for c in channels]) if channels else "কোনো চ্যানেল নেই।"
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_clear_ch":
            if not is_owner(user_id):
                await query.message.reply_text("❌ অনুমতি নেই!")
                return
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM force_channels')
            cursor.execute('INSERT OR IGNORE INTO force_channels VALUES ("Channel 1", ?, "https://t.me/MoneyPointtBD")', (PROTECTED_CHANNEL,))
            conn.commit()
            conn.close()
            await query.message.reply_text(f"🔄 চ্যানেলসমূহ রিমুভ করা হয়েছে (সুরক্ষিত চ্যানেল {PROTECTED_CHANNEL} ছাড়া)।")

        elif data == "adm_add_task":
            context.user_data['new_task'] = {}
            context.user_data['state'] = 'ADM_TASK_TITLE'
            await query.message.reply_text("➕ <b>নতুন টাস্ক তৈরি:</b>\n\nটাস্কের নাম (Title) লিখে পাঠান:", parse_mode="HTML")

        elif data == "adm_manage_tasks":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT task_id, title, status FROM tasks')
            all_tasks = cursor.fetchall()
            conn.close()

            if not all_tasks:
                await query.message.reply_text("📋 কোনো টাস্ক পাওয়া যায়নি।")
                return

            kbd = []
            for t in all_tasks:
                st_icon = "🟢" if t[2] == "Active" else "🔴"
                kbd.append([InlineKeyboardButton(f"{st_icon} {t[1]}", callback_data=f"adm_mng_task_{t[0]}")])

            await query.message.reply_text("📋 <b>Manage Tasks</b>\n\nযে টাস্কটি ম্যানেজ (Edit/Off/Delete) করতে চান তা সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(kbd), parse_mode="HTML")

        elif data == "adm_set_review_ch":
            context.user_data['state'] = 'ADM_SET_REVIEW_CH_INP'
            curr_rev = get_review_channel()
            await query.message.reply_text(
                f"⚙️ <b>বর্তমান টাস্ক রিভিউ চ্যানেল/লিংক:</b> {curr_rev}\n\n"
                f"নতুন রিভিউ চ্যানেল আইডি বা Username (@channel) লিখে পাঠান:",
                parse_mode="HTML"
            )

        elif data == "adm_set_min_order":
            context.user_data['state'] = 'ADM_SET_MIN_ORDER_INP'
            curr_limit = get_min_order_limit()
            await query.message.reply_text(
                f"⚙️ <b>বর্তমান সর্বনিম্ন অর্ডার লিমিট:</b> {curr_limit}\n\n"
                f"নতুন সর্বনিম্ন সংখ্যাটি (যেমন: 3 বা 5) লিখে পাঠান:",
                parse_mode="HTML"
            )

        elif data == "adm_pending_dep":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT deposit_id, user_id, method, amount, trx_id FROM deposits WHERE status = "Pending"')
            deps = cursor.fetchall()
            conn.close()
            if not deps:
                await query.message.reply_text("📥 কোনো পেন্ডিং ডিপোজিট নেই।")
            else:
                for d in deps:
                    kbd = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Approve", callback_data=f"app_dep_{d[0]}"),
                         InlineKeyboardButton("❌ Reject", callback_data=f"rej_dep_{d[0]}")]
                    ])
                    msg = f"📥 <b>Deposit #{d[0]}</b>\n👤 User: <code>{d[1]}</code>\n💳 Method: {d[2]}\n💰 Amount: {d[3]} Tk\n🧾 TrxID: <code>{d[4]}</code>"
                    await query.message.reply_text(msg, reply_markup=kbd, parse_mode="HTML")

        elif data.startswith("app_dep_"):
            dep_id = int(data.split("_")[2])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, amount FROM deposits WHERE deposit_id = ? AND status = "Pending"', (dep_id,))
            dep = cursor.fetchone()
            if dep:
                cursor.execute('UPDATE deposits SET status = "Approved" WHERE deposit_id = ?', (dep_id,))
                cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (dep[1], dep[0]))
                conn.commit()
                await query.message.reply_text(f"✅ Deposit #{dep_id} Approved & {dep[1]} Points added!")
                try:
                    await context.bot.send_message(chat_id=dep[0], text=f"🎉 আপনার Deposit #{dep_id} সফল হয়েছে! <b>{dep[1]} Point</b> যোগ করা হয়েছে।", parse_mode="HTML")
                except: pass
            conn.close()

        elif data.startswith("rej_dep_"):
            dep_id = int(data.split("_")[2])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM deposits WHERE deposit_id = ? AND status = "Pending"', (dep_id,))
            dep = cursor.fetchone()
            if dep:
                cursor.execute('UPDATE deposits SET status = "Rejected" WHERE deposit_id = ?', (dep_id,))
                conn.commit()
                await query.message.reply_text(f"❌ Deposit #{dep_id} Rejected!")
                try:
                    await context.bot.send_message(chat_id=dep[0], text=f"❌ আপনার Deposit #{dep_id} বাতিল করা হয়েছে।")
                except: pass
            conn.close()

        elif data == "adm_pending_orders":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT order_id, user_id, order_type, amount, link, poll_name FROM orders WHERE status = "Pending"')
            ords = cursor.fetchall()
            conn.close()
            if not ords:
                await query.message.reply_text("📤 কোনো পেন্ডিং অর্ডার নেই।")
            else:
                for o in ords:
                    kbd = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Complete", callback_data=f"cmp_ord_{o[0]}"),
                         InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cnl_ord_{o[0]}")]
                    ])
                    # অর্ডারকারী ইউজারের নাম ডাটাবেস থেকে ফেচ করা হচ্ছে
                    conn_u = get_db()
                    cur_u = conn_u.cursor()
                    cur_u.execute('SELECT first_name FROM users WHERE user_id = ?', (o[1],))
                    u_row = cur_u.fetchone()
                    conn_u.close()
                    order_user_name = u_row[0] if u_row and u_row[0] else "User"

                    p_name_info = f"\n🎯 Poll Name: {html.escape(str(o[5]))}" if o[5] else ""
                    emoji_tag = get_user_point_source_emoji(o[1])
                    msg = f"📤 <b>Order #{o[0]}</b>\n👤 User: <code>{o[1]}</code>\n👤 Name: {html.escape(str(order_user_name))} {emoji_tag}\n📦 Type: {o[2]}\n🔢 Amount: {o[3]}{p_name_info}\n🔗 Link: {o[4]}"
                    await query.message.reply_text(msg, reply_markup=kbd, parse_mode="HTML")

        elif data.startswith("cmp_ord_"):
            ord_id = int(data.split("_")[2])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM orders WHERE order_id = ? AND status = "Pending"', (ord_id,))
            ord_data = cursor.fetchone()
            if ord_data:
                cursor.execute('UPDATE orders SET status = "Completed" WHERE order_id = ?', (ord_id,))
                conn.commit()
                await query.message.reply_text(f"✅ Order #{ord_id} Completed!")
                try:
                    await context.bot.send_message(chat_id=ord_data[0], text=f"🎉 আপনার Order #{ord_id} সম্পন্ন করা হয়েছে!")
                except: pass
            conn.close()

        elif data.startswith("cnl_ord_"):
            ord_id = int(data.split("_")[2])
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, amount FROM orders WHERE order_id = ? AND status = "Pending"', (ord_id,))
            ord_data = cursor.fetchone()
            if ord_data:
                cursor.execute('UPDATE orders SET status = "Cancelled" WHERE order_id = ?', (ord_id,))
                cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (ord_data[1], ord_data[0]))
                conn.commit()
                await query.message.reply_text(f"❌ Order #{ord_id} Cancelled and {ord_data[1]} Points Refunded!")
                try:
                    await context.bot.send_message(chat_id=ord_data[0], text=f"❌ আপনার Order #{ord_id} বাতিল হয়েছে এবং <b>{ord_data[1]} Point</b> রিফান্ড করা হয়েছে।", parse_mode="HTML")
                except: pass
            conn.close()

        elif data == "adm_app_history":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT deposit_id, user_id, amount FROM deposits WHERE status = "Approved" ORDER BY deposit_id DESC LIMIT 5')
            deps = cursor.fetchall()
            conn.close()
            txt = "✅ <b>Approved Deposit History:</b>\n\n"
            txt += "\n".join([f"• Dep #{d[0]} | User: {d[1]} | {d[2]} Tk" for d in deps]) if deps else "কোনো তথ্য নেই।"
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_rej_history":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT deposit_id, user_id, amount FROM deposits WHERE status = "Rejected" ORDER BY deposit_id DESC LIMIT 5')
            deps = cursor.fetchall()
            conn.close()
            txt = "❌ <b>Rejected Deposit History:</b>\n\n"
            txt += "\n".join([f"• Dep #{d[0]} | User: {d[1]} | {d[2]} Tk" for d in deps]) if deps else "কোনো তথ্য নেই।"
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_set_ref_pt":
            context.user_data['state'] = 'ADM_SET_REF_PT_INP'
            await query.message.reply_text("⚙️ <b>প্রতি রেফারেলের জন্য কত Point দিতে চান লিখুন (যেমন: 1 বা 1.50):</b>", parse_mode="HTML")

        elif data == "adm_create_gift":
            context.user_data['state'] = 'ADM_CREATE_GIFT_INP'
            await query.message.reply_text("🎁 <b>Gift Code, Point এবং Max Uses স্পেস দিয়ে লিখুন:</b>\n\n<code>FREE100 50.5 100</code>", parse_mode="HTML")

        elif data == "adm_del_gift":
            context.user_data['state'] = 'ADM_DEL_GIFT_INP'
            await query.message.reply_text("🗑 <b>যে Gift Code মুছবেন তা লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_list_gift":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT code, points, max_uses, used_count FROM gift_codes')
            gifts = cursor.fetchall()
            conn.close()
            txt = "📜 <b>Active Gift Codes:</b>\n\n"
            txt += "\n".join([f"• Code: <code>{g[0]}</code> | Pts: {g[1]} | Used: {g[3]}/{g[2]}" for g in gifts]) if gifts else "কোনো সক্রিয় গিফট কোড নেই।"
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_broadcast":
            context.user_data['state'] = 'ADM_BROADCAST_INP'
            await query.message.reply_text("📢 <b>সকল ইউজারের উদ্দেশ্যে যে মেসেজ পাঠাতে চান তা লিখুন:</b>", parse_mode="HTML")

        elif data == "adm_direct_msg":
            context.user_data['state'] = 'ADM_DIRECT_MSG_INP'
            await query.message.reply_text("✉️ <b>User ID এবং মেসেজ স্পেস দিয়ে লিখুন:</b>\n\n<code>6599413664 আপনার অ্যাকাউন্ট এপ্রুভ হয়েছে।</code>", parse_mode="HTML")

        elif data == "adm_stats":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*), SUM(points) FROM users')
            u_count, total_pts = cursor.fetchone()
            cursor.execute('SELECT COUNT(*) FROM orders')
            o_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM deposits WHERE status = "Approved"')
            d_count = cursor.fetchone()[0]
            conn.close()
            
            txt = (
                f"📊 <b>Bot Overall Statistics:</b>\n\n"
                f"👤 Total Users: {u_count}\n"
                f"💰 Total User Points: {total_pts if total_pts else 0}\n"
                f"📦 Total Orders: {o_count}\n"
                f"📥 Total Approved Deposits: {d_count}"
            )
            await query.message.reply_text(txt, parse_mode="HTML")

        elif data == "adm_maint_mode":
            curr = get_setting("maint_mode")
            new_val = "off" if curr == "on" else "on"
            set_setting("maint_mode", new_val)
            await query.message.reply_text(f"🔒 Maintenance Mode: <b>{new_val.upper()}</b> করা হয়েছে।", parse_mode="HTML")

# --- Messages Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text if update.message else None
    
    if get_setting("maint_mode") == "on" and not is_admin(user.id):
        await update.message.reply_text("🔒 <b>বট বর্তমানে মেইনটেন্যান্স মোডে রয়েছে।</b>", parse_mode="HTML")
        return

    u_data = get_or_create_user(user, context=context)
    if u_data[3] == 1:
        return

    if not await is_user_joined(user.id, context):
        msg = "⚠️ <b>বটটি ব্যবহার করতে আমাদের সকল চ্যানেলে জয়েন থাকতে হবে!</b>"
        await update.message.reply_text(msg, reply_markup=get_join_keyboard(), parse_mode="HTML")
        return

    points = u_data[1]
    total_refers = u_data[2]
    state = context.user_data.get('state')

    # --- SCREENSHOT SUBMISSION FOR TASKS ---
    if state == 'SUBMIT_TASK_SCREENSHOT':
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            task_id = context.user_data.get('sub_task_id')

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO task_submissions (user_id, task_id, photo_file_id) VALUES (?, ?, ?)', (user.id, task_id, photo_file_id))
            sub_id = cursor.lastrowid
            
            cursor.execute('SELECT title, reward FROM tasks WHERE task_id = ?', (task_id,))
            t_data = cursor.fetchone()
            task_title = t_data[0] if t_data else "Task"
            reward_pts = t_data[1] if t_data else 0
            conn.commit()
            conn.close()

            await update.message.reply_text("✅ <b>আপনার টাস্কের স্ক্রিনশট সফলভাবে সাবমিট করা হয়েছে!</b>\n\n⌛ এডমিন যাচাই করার পর আপনার পয়েন্ট যোগ করা হবে।", parse_mode="HTML")

            review_ch = get_review_channel()
            if review_ch:
                rev_msg = (
                    f"🚀 <b>NEW TASK SUBMISSION</b>\n\n"
                    f"📸 <b>Screenshot:</b> ইউজারের পাঠানো ছবি\n\n"
                    f"📝 <b>Task:</b> {html.escape(task_title)}\n"
                    f"👤 <b>User Name:</b> {html.escape(user.first_name)}\n"
                    f"🔗 <b>Username:</b> @{user.username if user.username else 'N/A'}\n"
                    f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                    f"🎁 <b>Reward:</b> {reward_pts} Points\n\n"
                    f"📌 <b>Status: Pending</b>"
                )
                kbd = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approve", callback_data=f"app_task_{sub_id}"),
                     InlineKeyboardButton("❌ Reject", callback_data=f"rej_task_{sub_id}")]
                ])
                try:
                    await context.bot.send_photo(
                        chat_id=review_ch,
                        photo=photo_file_id,
                        caption=rev_msg,
                        reply_markup=kbd,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logging.error(f"Review Channel Error: {e}")
                    try:
                        await context.bot.send_message(
                            chat_id=PRIMARY_OWNER_ID,
                            text=f"⚠️ <b>Review Channel Error:</b>\nরিসেন্ট টাস্ক সাবমিশন রিভিউ চ্যানেলে পাঠানো যায়নি। অনুগ্রহ করে রিভিউ চ্যানেল আইডি বা বট পারমিশন চেক করুন।\n\nError: <code>{e}</code>",
                            parse_mode="HTML"
                        )
                    except: pass

            context.user_data['state'] = None
            return
        else:
            await update.message.reply_text("⚠️ অনুগ্রহ করে একটি স্ক্রিনশট (ছবি) পাঠান।")
            return

    if text == '👤 প্রোফাইল':
        msg = (
            f"👤 <b>আপনার প্রোফাইল</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"👤 নাম: {html.escape(user.first_name)}\n"
            f"🔗 Username: @{user.username if user.username else 'N/A'}\n\n"
            f"💰 Balance: {points} Point\n"
            f"👥 Total Refer: {total_refers}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    elif text == '🎯 Refer & Earn':
        bot_username = context.bot.username
        refer_link = f"https://t.me/{bot_username}?start={user.id}"
        ref_pt = get_refer_point()
        msg = (
            f"🎯 <b>Refer & Earn</b>\n\n"
            f"👥 <b>আপনার Referral Link:</b>\n\n"
            f"<code>{refer_link}</code>\n\n"
            f"👥 Total Refer: {total_refers}\n"
            f"⭐ Total Point: {points}\n\n"
            f"🎁 1 Referral = {ref_pt} Point"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    elif text == '👑 ADMIN PANEL':
        if is_admin(user.id):
            await update.message.reply_text("👑 <b>Admin Control Panel</b>\n\nনিচের অপশনগুলো বেছে নিন:", reply_markup=get_admin_panel_markup(user.id), parse_mode="HTML")
        else:
            await update.message.reply_text("❌ আপনি এডমিন নন!")
        return

    elif text == '🎁 Gift Code':
        context.user_data['state'] = 'CLAIM_GIFT_CODE'
        await update.message.reply_text("🎁 <b>আপনার Gift Code টি এখানে লিখে পাঠান:</b>", parse_mode="HTML")
        return

    elif text == '🎯 Task':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT task_id, title, reward FROM tasks 
            WHERE status = "Active" AND task_id NOT IN (
                SELECT task_id FROM task_submissions WHERE user_id = ? AND status IN ('Pending', 'Approved')
            )
        ''', (user.id,))
        tasks = cursor.fetchall()
        conn.close()

        if not tasks:
            await update.message.reply_text("🎯 এই মুহূর্তে আপনার জন্য কোনো নতুন টাস্ক নেই বা সবগুলো সম্পন্ন/পেন্ডিং রয়েছে।")
            return

        kbd = []
        for t in tasks:
            kbd.append([InlineKeyboardButton(f"🎯 {t[1]} ({t[2]} Pts)", callback_data=f"task_do_{t[0]}")])
        
        await update.message.reply_text("🎯 <b>অ্যাক্টিভ টাস্কসমূহ:</b>\n\nটাস্কে ক্লিক করে সম্পন্ন করুন এবং প্রুফ পাঠান:", reply_markup=InlineKeyboardMarkup(kbd), parse_mode="HTML")
        return

    elif text == '🏆 Leaderboard':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.user_id, u.first_name, SUM(d.amount) as total_dep 
            FROM users u JOIN deposits d ON u.user_id = d.user_id 
            WHERE d.status = 'Approved' 
            GROUP BY u.user_id 
            ORDER BY total_dep DESC LIMIT 3
        ''')
        top_depositors = cursor.fetchall()
        conn.close()

        msg = "🏆 <b>TOP 3 DEPOSITORS LEADERBOARD</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        if not top_depositors:
            msg += "এই মুহূর্তে কোনো ডিপোজিট রেকর্ড নেই।"
        else:
            for idx, dep in enumerate(top_depositors):
                msg += f"{medals[idx]} <b>Name:</b> {html.escape(dep[1])}\n🆔 <b>User ID:</b> <code>{dep[0]}</code>\n💰 <b>Total Deposit:</b> {dep[2]} Tk\n\n"
        
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    elif text == '📢 Bot Refer Buy':
        context.user_data['state'] = 'BOT_REF_LINK'
        min_limit = get_min_order_limit()
        await update.message.reply_text(f"📢 <b>Bot Refer Buy</b>\n\n🔗 যে বটের Referral নিতে চান, সেই Bot-এর Link পাঠান:\n\n⚠️ সর্বনিম্ন অর্ডার: <b>{min_limit} টি</b>", parse_mode="HTML")
        return

    elif text == '📦 Poll Vote Buy':
        context.user_data['state'] = 'POLL_VOTE_LINK'
        min_limit = get_min_order_limit()
        await update.message.reply_text(f"📢 <b>REFER TO VOT</b>\n\n🔗 আপনার Poll/Vote Link পাঠান:\n\n⚠️ সর্বনিম্ন অর্ডার: <b>{min_limit} টি</b>", parse_mode="HTML")
        return

    elif text == '📜 My Orders':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT order_id, order_type, amount, status, link, poll_name FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT 10', (user.id,))
        orders = cursor.fetchall()
        conn.close()

        if not orders:
            await update.message.reply_text("📜 আপনি এখনো কোনো অর্ডার করেননি।")
            return

        msg = "📜 <b>My Orders</b>\n\n"
        for o in orders:
            p_name_info = f"\n🎯 Poll Name: {html.escape(str(o[5]))}" if o[5] else ""
            msg += (
                f"🆔 <b>Order #{o[0]}</b>\n"
                f"📦 Type: {html.escape(str(o[1]))}\n"
                f"🔢 Amount: {o[2]}{p_name_info}\n"
                f"📌 Status: {html.escape(str(o[3]))}\n"
                f"🔗 Link: {html.escape(str(o[4]))}\n"
                "-----------------------------------\n"
            )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    elif text == '💰 Deposit':
        keyboard = [
            [InlineKeyboardButton("💖 বিকাশ", callback_data="dep_bkash"), InlineKeyboardButton("💚 নগদ", callback_data="dep_nagad")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            "💰 <b>DEPOSIT</b>\n\n"
            "⭐ Point কিনতে নিচের Payment Method নির্বাচন করুন。\n\n"
            "💖 বিকাশ অথবা 💚 নগদ নির্বাচন করুন。\n\n"
            "⚠️ Minimum Deposit: 10 টাকা"
        )
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")
        return

    elif text == '💬 Support':
        supp_id = get_setting("support_id", "RABBYBhAII")
        supp_id = supp_id.replace("@", "").strip()
        keyboard = [[InlineKeyboardButton("💬 CONTACT SUPPORT", url=f"https://t.me/{supp_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            "💬 <b>SUPPORT</b>\n\n"
            "কোনো সমস্যা হলে আমাদের Support-এ যোগাযোগ করুন。\n\n"
            f"🧑‍‍💻 Support: @{supp_id}\n\n"
            "⏰ আমরা আপনার সমস্যার সমাধান করার চেষ্টা করব।"
        )
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")
        return

    # --- USER PROCESS STATES ---
    if state == 'CLAIM_GIFT_CODE':
        code_input = text.strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT points, max_uses, used_count FROM gift_codes WHERE code = ?', (code_input,))
        gift = cursor.fetchone()

        if not gift:
            await update.message.reply_text("❌ ভুল বা অকার্যকর Gift Code!")
        else:
            pts, max_uses, used_count = gift
            cursor.execute('SELECT * FROM gift_claims WHERE user_id = ? AND code = ?', (user.id, code_input))
            already_claimed = cursor.fetchone()

            if already_claimed:
                await update.message.reply_text("⚠ আপনি ইতিমধ্যে এই Gift Code টি ব্যবহার করেছেন!")
            elif used_count >= max_uses:
                await update.message.reply_text("❌ দুঃখিত! এই Gift Code-এর ব্যবহারের লিমিট শেষ হয়ে গেছে।")
            else:
                cursor.execute('UPDATE gift_codes SET used_count = used_count + 1 WHERE code = ?', (code_input,))
                cursor.execute('INSERT INTO gift_claims (user_id, code) VALUES (?, ?)', (user.id, code_input))
                cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (pts, user.id))
                conn.commit()
                await update.message.reply_text(f"🎉 <b>অভিনন্দন!</b> আপনি Gift Code থেকে <b>{pts} Point</b> বোনাস পেয়েছেন।", parse_mode="HTML")

        conn.close()
        context.user_data['state'] = None
        return

    elif state == 'BOT_REF_LINK':
        context.user_data['order_link'] = text.strip()
        context.user_data['order_type'] = 'Bot Refer'
        context.user_data['state'] = 'ORDER_AMOUNT'
        min_limit = get_min_order_limit()
        await update.message.reply_text(f"🔢 <b>কতটি Refer নিতে চান তার সংখ্যা লিখুন:</b>\n(সর্বনিম্ন {min_limit} টি)", parse_mode="HTML")
        return

    elif state == 'POLL_VOTE_LINK':
        context.user_data['order_link'] = text.strip()
        context.user_data['order_type'] = 'Poll Vote'
        context.user_data['state'] = 'POLL_VOTE_NAME'
        await update.message.reply_text("আপনার poll এর নাম দিন:", parse_mode="HTML")
        return

    elif state == 'POLL_VOTE_NAME':
        context.user_data['poll_name'] = text.strip()
        context.user_data['state'] = 'ORDER_AMOUNT'
        min_limit = get_min_order_limit()
        await update.message.reply_text(f"🔢 <b>কতটি Vote নিতে চান তার সংখ্যা লিখুন:</b>\n(সর্বনিম্ন {min_limit} টি)", parse_mode="HTML")
        return

    elif state == 'ORDER_AMOUNT':
        if not text.isdigit():
            await update.message.reply_text("⚠️ সংখ্যা লিখুন।")
            return
        amount = int(text)
        min_limit = get_min_order_limit()

        if amount < min_limit:
            await update.message.reply_text(f"❌ সর্বনিম্ন অর্ডার সংখ্যা কমপক্ষে <b>{min_limit}</b> হতে হবে!", parse_mode="HTML")
            return

        if points < amount:
            await update.message.reply_text(f"❌ আপনার পর্যাপ্ত পয়েন্ট নেই! আপনার বর্তমান ব্যালেন্স: {points} Point।")
            context.user_data['state'] = None
            return
        
        ord_type = context.user_data.get('order_type')
        ord_link = context.user_data.get('order_link')
        poll_name = context.user_data.get('poll_name')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (amount, user.id))
        cursor.execute('INSERT INTO orders (user_id, order_type, amount, link, poll_name) VALUES (?, ?, ?, ?, ?)', (user.id, ord_type, amount, ord_link, poll_name))
        ord_id = cursor.lastrowid
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"🎉 <b>অর্ডার সফল হয়েছে!</b>\n\n"
            f"🆔 Order ID: #{ord_id}\n"
            f"📦 Type: {ord_type}\n"
            f"🔢 Amount: {amount}\n\n"
            f"⌛ এডমিন খুব শীঘ্রই সার্ভিসটি ডেলিভারি করবেন।",
            parse_mode="HTML"
        )

        pay_ch = get_pay_channel()
        if pay_ch:
            p_name_log = f"\n🎯 Poll Name: {html.escape(str(poll_name))}" if poll_name else ""
            emoji_tag = get_user_point_source_emoji(user.id)
            order_log_msg = f"""
REFER TO VOT OFFICIAL
📦 <b>NEW ORDER RECEIVED</b>

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🆔 <b>Order ID:</b> #{ord_id}
👤 <b>User ID:</b> <code>{user.id}</code>
👤 <b>Name:</b> {html.escape(user.first_name)} {emoji_tag}
📦 <b>Order Type:</b> {ord_type}
🔢 <b>Quantity/Amount:</b> {amount}{p_name_log}
🔗 <b>Link:</b> {html.escape(ord_link)}
📌 <b>Status:</b> Pending
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
"""
            try:
                await context.bot.send_message(chat_id=pay_ch, text=order_log_msg, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Order Channel Log Error: {e}")

        context.user_data['state'] = None
        return

    elif state == 'DEP_AMOUNT':
        try:
            amount = float(text.strip())
            context.user_data['dep_amount'] = amount
            context.user_data['state'] = 'DEP_TRX'
            
            await update.message.reply_text(
                f"✅ <b>Amount Accepted</b>\n\n"
                f"💰 Deposit Amount: {amount} টাকা\n\n"
                f"🧾 এখন আপনার Transaction ID (TrxID) পাঠান。\n\n"
                f"👉 উদাহরণ:\n<code>ABC123XYZ456</code>",
                parse_mode="HTML"
            )
        except ValueError:
            await update.message.reply_text("⚠ অনুগ্রহ করে সঠিক সংখ্যায় টাকা লিখুন (যেমন: 10)।")
        return

    elif state == 'DEP_TRX':
        trx_id = text.strip()
        dep_amount = context.user_data.get('dep_amount', 0)
        method = context.user_data.get('dep_method', 'bKash/Nagad')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO deposits (user_id, method, amount, trx_id) VALUES (?, ?, ?, ?)', (user.id, method, dep_amount, trx_id))
        deposit_id = cursor.lastrowid
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"⭐ Point: {dep_amount} Point\n\n"
            f"📌 Status: Pending\n\n"
            f"⌛ Admin যাচাই করার পর আপনার Point যোগ করা হবে।"
        )

        pay_ch = get_pay_channel()
        if pay_ch:
            channel_msg = f"""
REFER TO VOT OFFICIAL
💰 <b>NEW DEPOSIT REQUEST</b>

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
🆔 <b>Deposit ID:</b> #{deposit_id}
👤 <b>User ID:</b> <code>{user.id}</code>
👤 <b>Name:</b> {html.escape(user.first_name)}
💳 <b>Method:</b> {method}
💰 <b>Amount:</b> {dep_amount} টাকা
🧾 <b>Transaction ID:</b> <code>{html.escape(trx_id)}</code>
⭐ <b>Point to Add:</b> {dep_amount} Point
📌 <b>Status:</b> Pending
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
"""
            try:
                await context.bot.send_message(chat_id=pay_ch, text=channel_msg, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Deposit Channel Error: {e}")

        context.user_data['state'] = None
        return

    # --- ADMIN INPUT PROCESSORS ---
    if is_admin(user.id):
        if state == 'ADM_OWNER_CHANGE_INP':
            if not is_owner(user.id):
                await update.message.reply_text("❌ অনুমতি নেই!")
                context.user_data['state'] = None
                return
            try:
                new_owner_id = int(text.strip())
                set_setting("owner_id", str(new_owner_id))
                
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (new_owner_id,))
                conn.commit()
                conn.close()

                await update.message.reply_text(f"👑 সফলভাবে বট এর নতুন ওনার (Owner) হিসেবে <code>{new_owner_id}</code>-কে সেট করা হয়েছে!", parse_mode="HTML")
                try:
                    await context.bot.send_message(
                        chat_id=new_owner_id,
                        text="🎉 <b>অভিনন্দন!</b> আপনাকে এই বটের নতুন মূল মালিক (Owner) হিসেবে নিয়োগ দেওয়া হয়েছে। এখন থেকে আপনি সমস্ত ওনার কন্ট্রোল ও প্যানেল পরিচালনা করতে পারবেন।",
                        parse_mode="HTML"
                    )
                except:
                    pass
            except ValueError:
                await update.message.reply_text("❌ সঠিক User ID (সংখ্যায়) লিখুন।")
            context.user_data['state'] = None
            return

        elif state == 'ADM_TASK_TITLE':
            context.user_data['new_task']['title'] = text.strip()
            context.user_data['state'] = 'ADM_TASK_DESC'
            await update.message.reply_text("📝 টাস্কের বিবরণ (Description) লিখে পাঠান:", parse_mode="HTML")
            return

        elif state == 'ADM_TASK_DESC':
            context.user_data['new_task']['desc'] = text.strip()
            context.user_data['state'] = 'ADM_TASK_LINK'
            await update.message.reply_text("🔗 টাস্কের লিংক (Link) লিখে পাঠান:", parse_mode="HTML")
            return

        elif state == 'ADM_TASK_LINK':
            context.user_data['new_task']['link'] = text.strip()
            context.user_data['state'] = 'ADM_TASK_REWARD'
            await update.message.reply_text("⭐ পুরস্কারের পয়েন্ট (Reward Point, যেমন: 2 বা 2.5) লিখে পাঠান:", parse_mode="HTML")
            return

        elif state == 'ADM_TASK_REWARD':
            try:
                reward = float(text.strip())
                t_data = context.user_data.get('new_task', {})
                title = t_data.get('title')
                desc = t_data.get('desc')
                link = t_data.get('link')

                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO tasks (title, description, link, reward) VALUES (?, ?, ?, ?)', (title, desc, link, reward))
                conn.commit()
                conn.close()

                await update.message.reply_text(f"✅ নতুন টাস্ক সফলভাবে তৈরি ও যোগ করা হয়েছে!\n\n📌 <b>{title}</b> ({reward} Pts)", parse_mode="HTML")
            except ValueError:
                await update.message.reply_text("❌ পয়েন্ট অবশ্যই সংখ্যায় হতে হবে। টাস্ক তৈরি বাতিল হয়েছে। আবার চেষ্টা করুন।")
            
            context.user_data.pop('new_task', None)
            context.user_data['state'] = None
            return

        elif state == 'ADM_SET_PAY_CNL_INP':
            new_ch = text.strip()
            if not new_ch.startswith("@") and not new_ch.startswith("https://") and not new_ch.startswith("-100"):
                new_ch = "@" + new_ch
            set_setting("pay_channel", new_ch)
            await update.message.reply_text(f"✅ Payment Channel আপডেট করা হয়েছে: <code>{new_ch}</code>", parse_mode="HTML")
            context.user_data['state'] = None

        elif state == 'ADM_SET_SUPPORT_INP':
            new_supp = text.strip().replace("@", "")
            set_setting("support_id", new_supp)
            await update.message.reply_text(f"✅ সাপোর্ট আইডি পরিবর্তন করে <code>@{new_supp}</code> সেট করা হয়েছে!", parse_mode="HTML")
            context.user_data['state'] = None

        elif state == 'ADM_SET_DEP_NUM_INP':
            new_num = text.strip()
            key_name = context.user_data.get('change_num_key')
            
            if key_name:
                set_setting(key_name, new_num)
                method_name = key_name.replace("dep_", "").capitalize()
                await update.message.reply_text(f"✅ <b>{method_name}</b> এর ডিপোজিট নাম্বার পরিবর্তন হয়ে <code>{new_num}</code> সেট হয়েছে!", parse_mode="HTML")
            else:
                await update.message.reply_text("❌ সমস্যা দেখা দিয়েছে, আবার চেষ্টা করুন।")
            context.user_data['state'] = None

        elif state == 'ADM_ADD_ADMIN_INP':
            if not is_owner(user.id):
                await update.message.reply_text("❌ শুধু মূল মালিক নতুন এডমিন যুক্ত করতে পারবেন!")
                context.user_data['state'] = None
                return
            try:
                new_admin_id = int(text.strip())
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (new_admin_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"👑 User <code>{new_admin_id}</code>-কে Admin বানানো হয়েছে!", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ সঠিক User ID লিখুন।")
            context.user_data['state'] = None

        elif state == 'ADM_REM_ADMIN_INP':
            if not is_owner(user.id):
                await update.message.reply_text("❌ শুধু মূল মালিক এডমিন রিমুভ করতে পারবেন!")
                context.user_data['state'] = None
                return
            try:
                rem_admin_id = int(text.strip())
                if rem_admin_id in [PRIMARY_OWNER_ID, SECONDARY_OWNER_ID]:
                    await update.message.reply_text("❌ মূল ওনারকে এডমিন থেকে সরানো যাবে না!")
                    context.user_data['state'] = None
                    return
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM admins WHERE user_id = ?', (rem_admin_id,))
                cursor.execute('DELETE FROM admin_permissions WHERE user_id = ?', (rem_admin_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"❌ User <code>{rem_admin_id}</code>-কে Admin পদ থেকে সরানো হয়েছে।", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ সঠিক User ID লিখুন।")
            context.user_data['state'] = None

        elif state == 'ADM_REF_STATS_INP':
            try:
                target_id = int(text.strip())
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE referred_by = ?', (target_id,))
                referred_users = cursor.fetchall()
                conn.close()

                total_ref = len(referred_users)
                active_in_channels = 0
                left_channels = 0

                status_msg = await update.message.reply_text("⌛ রেফারেল ইউজারদের চ্যানেল জয়েন স্ট্যাটাস চেক করা হচ্ছে...")

                for r_user in referred_users:
                    if await is_user_joined(r_user[0], context):
                        active_in_channels += 1
                    else:
                        left_channels += 1

                txt = (
                    f"👥 <b>Referral Detailed Statistics</b>\n\n"
                    f"🆔 User ID: <code>{target_id}</code>\n"
                    f"📊 Total Referred Users: <b>{total_ref}</b>\n\n"
                    f"✅ Currently Joined All Channels: <b>{active_in_channels}</b>\n"
                    f"❌ Left/Not Joined Channels: <b>{left_channels}</b>"
                )
                await status_msg.edit_text(txt, parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text("❌ সঠিক User ID দিন।")
            context.user_data['state'] = None

        elif state == 'ADM_REFER_BLOCK_INP':
            try:
                target_id = int(text.strip())
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT refer_blocked FROM users WHERE user_id = ?', (target_id,))
                r_row = cursor.fetchone()
                
                if not r_row:
                    await update.message.reply_text("❌ ইউজারটি ডাটাবেজে পাওয়া যায়নি।")
                else:
                    curr_block = r_row[0]
                    new_block = 0 if curr_block else 1
                    cursor.execute('UPDATE users SET refer_blocked = ? WHERE user_id = ?', (new_block, target_id))
                    conn.commit()
                    
                    status_text = "ব্লক (Blocked)" if new_block else "আনব্লক (Unblocked)"
                    await update.message.reply_text(f"✅ User <code>{target_id}</code>-এর রেফার সিস্টেম সফলভাবে <b>{status_text}</b> করা হয়েছে!", parse_mode="HTML")
                conn.close()
            except:
                await update.message.reply_text("❌ সঠিক User ID দিন।")
            context.user_data['state'] = None

        elif state == 'ADM_ADD_PT_INP':
            try:
                parts = text.split()
                target_id = int(parts[0])
                pts = float(parts[1])
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (pts, target_id))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ User <code>{target_id}</code>-কে {pts} Point যোগ করা হয়েছে।", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ ভুল ফরম্যাট! উদাহরণ: `6599413664 100`", parse_mode="Markdown")
            context.user_data['state'] = None

        elif state == 'ADM_SUB_PT_INP':
            try:
                parts = text.split()
                target_id = int(parts[0])
                pts = float(parts[1])
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (pts, target_id))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ User <code>{target_id}</code> থেকে {pts} Point কেটে নেওয়া হয়েছে।", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ ভুল ফরম্যাট! উদাহরণ: `6599413664 50`", parse_mode="Markdown")
            context.user_data['state'] = None

        elif state == 'ADM_SEARCH_USR_INP':
            try:
                target_id = int(text.strip())
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('SELECT user_id, first_name, username, points, total_refers, banned, refer_blocked FROM users WHERE user_id = ?', (target_id,))
                u = cursor.fetchone()
                conn.close()
                if u:
                    msg = f"👤 <b>User Details:</b>\n\n🆔 ID: <code>{u[0]}</code>\n👤 Name: {u[1]}\n🔗 Username: @{u[2]}\n💰 Balance: {u[3]} Points\n👥 Refers: {u[4]}\n🚫 Banned: {'Yes' if u[5] else 'No'}\n🔒 Refer Blocked: {'Yes' if u[6] else 'No'}"
                    await update.message.reply_text(msg, parse_mode="HTML")
                else:
                    await update.message.reply_text("❌ কোনো ইউজার পাওয়া যায়নি।")
            except:
                await update.message.reply_text("❌ সঠিক User ID দিন।")
            context.user_data['state'] = None

        elif state == 'ADM_BAN_USR_INP':
            try:
                target_id = int(text.strip())
                if target_id in [PRIMARY_OWNER_ID, SECONDARY_OWNER_ID]:
                    await update.message.reply_text("❌ ওনারকে ব্যান করা যাবে না!")
                    context.user_data['state'] = None
                    return
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (target_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"🚫 User <code>{target_id}</code>-কে ব্যান করা হয়েছে।", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ সঠিক User ID দিন।")
            context.user_data['state'] = None

        elif state == 'ADM_UNBAN_USR_INP':
            try:
                target_id = int(text.strip())
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (target_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ User <code>{target_id}</code>-কে আনব্যান করা হয়েছে।", parse_mode="HTML")
            except:
                await update.message.reply_text("❌ সঠিক User ID দিন।")
            context.user_data['state'] = None

        elif state == 'ADM_SEND_GIFT_INP':
            try:
                parts = text.split()
                target_id = int(parts[0])
                pts = float(parts[1])
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (pts, target_id))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"🎁 User <code>{target_id}</code>-কে {pts} Gift Point পাঠানো হয়েছে।", parse_mode="HTML")
                try:
                    await context.bot.send_message(chat_id=target_id, text=f"🎁 <b>Admin আপনাকে {pts} Gift Point দিয়েছেন!</b>", parse_mode="HTML")
                except: pass
            except:
                await update.message.reply_text("❌ ভুল ফরম্যাট!")
            context.user_data['state'] = None

        elif state == 'ADM_ADD_CH_INP':
            try:
                parts = text.split()
                ch_name, ch_username, ch_url = parts[0], parts[1], parts[2]
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO force_channels VALUES (?, ?, ?)', (ch_name, ch_username, ch_url))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ চ্যানেল যোগ করা হয়েছে: {ch_name}")
            except:
                await update.message.reply_text("❌ ফরম্যাট ভুল! লিখুন: `Name @username URL`", parse_mode="Markdown")
            context.user_data['state'] = None

        elif state == 'ADM_DEL_CH_INP':
            ch_username = text.strip()
            
            if ch_username.lower() == PROTECTED_CHANNEL.lower() and not is_owner(user_id):
                await update.message.reply_text(f"🚫 <b>সুরক্ষা সতর্কতা:</b> <code>{PROTECTED_CHANNEL}</code> চ্যানেলটি ডিলিট করার অনুমতি শুধু বটের মূল মালিকের কাছে রয়েছে!", parse_mode="HTML")
            else:
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM force_channels WHERE channel_username = ?', (ch_username,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"❌ চ্যানেল ডিলিট করা হয়েছে: {ch_username}")
            context.user_data['state'] = None

        elif state == 'ADM_SET_REVIEW_CH_INP':
            new_rev = text.strip()
            set_setting("review_channel", new_rev)
            await update.message.reply_text(f"✅ টাস্ক রিভিউ চ্যানেল পরিবর্তন করে সেট করা হয়েছে: <code>{new_rev}</code>", parse_mode="HTML")
            context.user_data['state'] = None

        elif state == 'ADM_SET_MIN_ORDER_INP':
            try:
                min_val = int(text.strip())
                set_setting("min_order_limit", str(min_val))
                await update.message.reply_text(f"✅ সর্বনিম্ন অর্ডার লিমিট সফলভাবে <b>{min_val}</b> সেট করা হয়েছে!", parse_mode="HTML")
            except ValueError:
                await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন।")
            context.user_data['state'] = None

        elif state == 'ADM_SET_REF_PT_INP':
            try:
                ref_pt_val = float(text.strip())
                set_setting("refer_point", str(ref_pt_val))
                await update.message.reply_text(f"⚙ রেফারেল পয়েন্ট <b>{ref_pt_val} Point</b> সেট করা হয়েছে।", parse_mode="HTML")
            except ValueError:
                await update.message.reply_text("❌ সঠিক সংখ্যা (যেমন: 1 বা 1.50) লিখুন।")
            context.user_data['state'] = None

        elif state == 'ADM_CREATE_GIFT_INP':
            try:
                parts = text.split()
                code, pts, max_u = parts[0], float(parts[1]), int(parts[2])
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO gift_codes (code, points, max_uses) VALUES (?, ?, ?)', (code.strip(), pts, max_u))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"🎁 Gift Code <code>{code}</code> সফলভাবে তৈরি করা হয়েছে!", parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text("❌ ভুল ফরম্যাট! উদাহরণ: `FREE100 50 100`", parse_mode="Markdown")
            context.user_data['state'] = None

        elif state == 'ADM_DEL_GIFT_INP':
            code = text.strip()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM gift_codes WHERE code = ?', (code,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"🗑️ Gift Code <code>{code}</code> ডিলিট করা হয়েছে।", parse_mode="HTML")
            context.user_data['state'] = None

        elif state == 'ADM_BROADCAST_INP':
            msg = text.strip()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            conn.close()
            
            count = 0
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u[0], text=f"📢 <b>Announcement:</b>\n\n{msg}", parse_mode="HTML")
                    count += 1
                except: pass
            await update.message.reply_text(f"📢 ব্রডকাস্ট সম্পন্ন! মোট {count} জন ইউজারের কাছে মেসেজ পৌঁছেছে।")
            context.user_data['state'] = None

        elif state == 'ADM_DIRECT_MSG_INP':
            try:
                parts = text.split(maxsplit=1)
                target_id = int(parts[0])
                msg_text = parts[1]
                await context.bot.send_message(chat_id=target_id, text=f"📩 <b>Admin Message:</b>\n\n{msg_text}", parse_mode="HTML")
                await update.message.reply_text("✉️ মেসেজটি সফলভাবে পাঠানো হয়েছে।")
            except:
                await update.message.reply_text("❌ ভুল ফরম্যাট! উদাহরণ: `6599413664 আপনার মেসেজ`", parse_mode="Markdown")
            context.user_data['state'] = None

# --- Main App ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))

    print("Bot 2 is running successfully with dual owners and fixed Pending Orders...")
    app.run_polling()
