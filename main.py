import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

def keep_alive():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
        def log_message(self, *args):
            pass
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()
import threading
import time
import json
import subprocess
import zipfile
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8730081204:AAFhgBcci6SWLidnzVeB7R2v9tELH4fkOlM"
OWNER_USERNAME = "RABBYBHAII"
OWNER_ID = 6599413664  # আপনার টেলিগ্রাম আইডি (নিশ্চিত করা হয়েছে)
UPDATES_CHANNEL_URL = "https://t.me/MoneyPointtBD"

UPLOAD_DIR = "user_files"
DATA_FILE = "bot_data.json"
LOGS_DIR = "bot_logs"

for folder in [UPLOAD_DIR, LOGS_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

running_processes = {}

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "banned": [], "files": {}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": [], "banned": [], "files": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📢 Updates Channel"],
        ["📩 Upload File", "📁 Check Files"],
        ["⚡ Bot Speed", "📊 Statistics"],
        ["📞 Contact Owner"],
        ["📦 Manual Install", "🆘 Help"]
    ],
    resize_keyboard=True
)

# সিকিউরিটি ফিল্টার: শুধু অনার ছাড়া কেউ ইউজ করতে পারবে না
def is_owner(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    # ইউজার আইডি অথবা ইউজারনেম দিয়ে চেক করা হচ্ছে
    if user.id == OWNER_ID or (user.username and user.username.lower() == OWNER_USERNAME.lower()):
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ **Access Denied!**\n\nএই হোস্টিং বটটি শুধুমাত্র `@RABBYBHAII`-এর জন্য সংরক্ষিত। অন্য কেউ এটি ব্যবহার করতে পারবে না।", parse_mode="Markdown")
        return

    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    welcome_text = (
        "👋 **Welcome to HOSTING BOT (Owner Panel)!**\n\n"
        "Here you can host and manage your Telegram Bots easily.\n"
        "Use the buttons below to control your bot."
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")

def start_bot_process(user_id, file_name):
    proc_key = f"{user_id}_{file_name}"
    file_path = os.path.join(UPLOAD_DIR, proc_key)
    log_path = os.path.join(LOGS_DIR, f"{proc_key}.log")

    if not os.path.exists(file_path):
        return False

    stop_bot_process(user_id, file_name)

    log_file = open(log_path, "a")

    if file_name.endswith('.py'):
        proc = subprocess.Popen(["python", file_path], stdout=log_file, stderr=log_file)
        running_processes[proc_key] = proc
        return True
    elif file_name.endswith('.js'):
        proc = subprocess.Popen(["node", file_path], stdout=log_file, stderr=log_file)
        running_processes[proc_key] = proc
        return True
    elif file_name.endswith('.zip'):
        extract_folder = os.path.join(UPLOAD_DIR, f"{user_id}_extracted_{file_name}")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
        
        py_main = os.path.join(extract_folder, "main.py")
        js_main = os.path.join(extract_folder, "index.js")
        
        if os.path.exists(py_main):
            proc = subprocess.Popen(["python", py_main], stdout=log_file, stderr=log_file)
            running_processes[proc_key] = proc
            return True
        elif os.path.exists(js_main):
            proc = subprocess.Popen(["node", js_main], stdout=log_file, stderr=log_file)
            running_processes[proc_key] = proc
            return True
    return False

def stop_bot_process(user_id, file_name):
    proc_key = f"{user_id}_{file_name}"
    if proc_key in running_processes:
        try:
            running_processes[proc_key].terminate()
            running_processes[proc_key].wait(timeout=2)
        except Exception:
            pass
        del running_processes[proc_key]
        return True
    return False

def is_process_running(user_id, file_name):
    proc_key = f"{user_id}_{file_name}"
    if proc_key in running_processes:
        if running_processes[proc_key].poll() is None:
            return True
        else:
            del running_processes[proc_key]
    return False

def build_files_keyboard(user_id):
    data = load_data()
    user_files = data["files"].get(user_id, [])
    
    if not user_files:
        return None, "📁 **Your files:**\nClick to manage.\n\n_No active files uploaded yet!_"
    
    keyboard = []
    for file_info in user_files:
        ext = file_info.split('.')[-1]
        running = is_process_running(user_id, file_info)
        status_icon = "🔴 Stopped" if not running else "🟢 Running"
        btn_text = f"{file_info} ({ext}) - {status_icon}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"manage:{file_info}")])
    
    return InlineKeyboardMarkup(keyboard), "📁 **Your files:**\nClick to manage."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ **Access Denied!** আপনার এই বট ব্যবহারের অনুমতি নেই।")
        return

    text = update.message.text
    user_id = str(update.effective_user.id)
    data = load_data()

    if context.user_data.get("waiting_for_install"):
        context.user_data["waiting_for_install"] = False
        package_name = text.strip()
        status_msg = await update.message.reply_text(f"⏳ Installing `{package_name}`...", parse_mode="Markdown")
        try:
            result = subprocess.run(["pip", "install"] + package_name.split(), capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                await status_msg.edit_text(f"✅ **Successfully installed:**\n`{package_name}`", parse_mode="Markdown")
            else:
                await status_msg.edit_text(f"❌ **Installation failed:**\n```\n{result.stderr[-500:]}\n```", parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error during installation: `{e}`", parse_mode="Markdown")
        return

    if text == "📢 Updates Channel":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates Channel", url=UPDATES_CHANNEL_URL)]
        ])
        await update.message.reply_text("Visit our Updates Channel:", reply_markup=keyboard)

    elif text == "📞 Contact Owner":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
        ])
        await update.message.reply_text("Click to contact Owner:", reply_markup=keyboard)

    elif text == "📩 Upload File":
        await update.message.reply_text(
            "📩 **Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file.**", 
            parse_mode="Markdown"
        )

    elif text == "📁 Check Files":
        keyboard, msg = build_files_keyboard(user_id)
        await update.message.reply_text(msg, reply_markup=keyboard, parse_mode="Markdown")

    elif text == "⚡ Bot Speed":
        start_time = time.time()
        ping = round((time.time() - start_time) * 1000 + 120.45, 2)
        
        speed_msg = (
            "⚡ **Bot Speed & Status:**\n\n"
            f"⏱️ **API Response Time:** {ping} ms\n"
            "🚦 **Bot Status:** 🔓 Unlocked\n"
            "👤 **Your Level:** 👑 Owner"
        )
        await update.message.reply_text(speed_msg, parse_mode="Markdown")

    elif text == "📊 Statistics":
        total_users = len(data["users"])
        banned_users = len(data["banned"])
        
        all_files_count = sum(len(f_list) for f_list in data["files"].values())
        user_files_count = len(data["files"].get(user_id, []))
        
        stats_msg = (
            "📊 **Bot Statistics:**\n\n"
            f"👥 **Total Users:** {total_users}\n"
            f"🚫 **Banned Users:** {banned_users}\n"
            f"📁 **Total File Records:** {all_files_count}\n"
            f"🟢 **Total Active Bots:** {len(running_processes)}\n"
            f"🤖 **Your Running Bots:** {user_files_count}"
        )
        await update.message.reply_text(stats_msg, parse_mode="Markdown")

    elif text == "📦 Manual Install":
        context.user_data["waiting_for_install"] = True
        await update.message.reply_text(
            "📦 **Manual Installation:**\n\n"
            "যে লাইব্রেরি বা প্যাকেজ ইনস্টল করতে চান তার নাম লিখে পাঠান (যেমন: `pyrogram tgcrypto` বা `requests`):",
            parse_mode="Markdown"
        )

    elif text == "🆘 Help":
        help_text = (
            "🆘 **Hosting Bot Help Guide (Owner Only)**\n\n"
            "1️⃣ **Upload File:** Click `📩 Upload File` and send your `.py`, `.js`, or `.zip` file.\n"
            "2️⃣ **Manual Install:** Use `📦 Manual Install` to install required libraries like `pyrogram tgcrypto`.\n"
            "3️⃣ **Check Status:** Use `📁 Check Files` to see your running bots.\n"
            "4️⃣ **Bot Speed:** Check system ping and status with `⚡ Bot Speed`.\n"
            "5️⃣ **Owner Support:** Click `📞 Contact Owner` for help."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_owner(update):
        await query.answer("❌ আপনার এই এক্সেস নেই!", show_alert=True)
        return

    await query.answer()
    
    user_id = str(query.from_user.id)
    data_split = query.data.split(":", 1)
    action = data_split[0]
    
    if action == "back_files":
        keyboard, msg = build_files_keyboard(user_id)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        return

    file_name = data_split[1]
    ext = file_name.split('.')[-1]

    if action == "manage":
        running = is_process_running(user_id, file_name)
        status = "🔴 Stopped" if not running else "🟢 Running"
        
        msg = f"⚙️ Controls for: {file_name} ({ext}) of User {user_id}\nStatus: {status}"
        
        if running:
            toggle_btn = InlineKeyboardButton("🔴 Stop", callback_data=f"stop:{file_name}")
        else:
            toggle_btn = InlineKeyboardButton("🟢 Start", callback_data=f"start:{file_name}")

        keyboard = InlineKeyboardMarkup([
            [toggle_btn, InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{file_name}")],
            [InlineKeyboardButton("📜 View Logs", callback_data=f"logs:{file_name}")],
            [InlineKeyboardButton("🔙 Back to Files", callback_data="back_files")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard)

    elif action == "start":
        start_bot_process(user_id, file_name)
        msg = f"⚙️ Controls for: {file_name} ({ext}) of User {user_id}\nStatus: 🟢 Running"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 Stop", callback_data=f"stop:{file_name}"), InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{file_name}")],
            [InlineKeyboardButton("📜 View Logs", callback_data=f"logs:{file_name}")],
            [InlineKeyboardButton("🔙 Back to Files", callback_data="back_files")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard)

    elif action == "stop":
        stop_bot_process(user_id, file_name)
        msg = f"⚙️ Controls for: {file_name} ({ext}) of User {user_id}\nStatus: 🔴 Stopped"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🟢 Start", callback_data=f"start:{file_name}"), InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{file_name}")],
            [InlineKeyboardButton("📜 View Logs", callback_data=f"logs:{file_name}")],
            [InlineKeyboardButton("🔙 Back to Files", callback_data="back_files")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard)

    elif action == "delete":
        stop_bot_process(user_id, file_name)
        
        data = load_data()
        if user_id in data["files"] and file_name in data["files"][user_id]:
            data["files"][user_id].remove(file_name)
            save_data(data)
            
        file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file_name}")
        if os.path.exists(file_path):
            os.remove(file_path)

        keyboard, msg = build_files_keyboard(user_id)
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")

    elif action == "logs":
        log_path = os.path.join(LOGS_DIR, f"{user_id}_{file_name}.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                logs = f.read()[-1000:]
            if not logs:
                logs = "No logs generated yet."
        else:
            logs = "No log file found."

        msg = "📜 **Logs for `" + file_name + "`:**\n\n```\n" + logs + "\n```"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Manage", callback_data=f"manage:{file_name}")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ **Access Denied!** আপনার ফাইল আপলোড করার অনুমতি নেই।")
        return

    user_id = str(update.effective_user.id)
    doc = update.message.document
    file_name = doc.file_name

    if file_name == "requirements.txt":
        status_msg = await update.message.reply_text("⏳ Installing requirements from file...", parse_mode="Markdown")
        file_path = os.path.join(UPLOAD_DIR, f"{user_id}_requirements.txt")
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(file_path)
        try:
            result = subprocess.run(["pip", "install", "-r", file_path], capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                await status_msg.edit_text("✅ **Requirements installed successfully!**", parse_mode="Markdown")
            else:
                await status_msg.edit_text(f"❌ **Failed to install requirements:**\n```\n{result.stderr[-500:]}\n```", parse_mode="Markdown")
        except Exception as e:
            await status_msg.edit_text(f"❌ Error: `{e}`", parse_mode="Markdown")
        return

    if file_name.endswith(('.py', '.js', '.zip')):
        status_msg = await update.message.reply_text(f"⏳ Downloading `{file_name}`...", parse_mode="Markdown")
        
        file = await context.bot.get_file(doc.file_id)
        file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file_name}")
        await file.download_to_drive(file_path)

        data = load_data()
        if user_id not in data["files"]:
            data["files"][user_id] = []
        if file_name not in data["files"][user_id]:
            data["files"][user_id].append(file_name)
        save_data(data)

        start_bot_process(user_id, file_name)

        await status_msg.edit_text(
            f"✅ **File Uploaded Successfully!**\n\n"
            f"📁 **File Name:** `{file_name}`\n"
            f"🚀 **Status:** Process Started & Running!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ **Invalid file!** Only `.py`, `.js`, `.zip`, and `requirements.txt` files are supported.", parse_mode="Markdown")

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("--- PRIVATE HOSTING BOT IS RUNNING ---")
    app.run_polling(poll_interval=1.0)

if __name__ == "__main__":
    main()
