import os
import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

import main as fb

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}
seen_users = set()
approved_users = set()
pending_users = {}
stop_flags = {}
unlocked_domains = {}   # uid -> set of unlocked domain keys
created_accounts = []   # list of dicts: {name, email, password, uid, by}

DOMAINS = {
    "1": "jemm.site",
    "2": "yopmail.com",
    "3": "weyn.store",
    "4": "astheia.shop",
    "5": "jhames.shop",
    "6": "lilearyth.shop",
    "7": "miztyxmm.store",
    "8": "jakulan.site",
    "9": "pleasenospam.email",
    "10": "lovesiobhan.shop",
    "11": "rimuru.store",
}

DOMAIN_PASSWORDS = {
    "1": "jemm123",
    "2": "yop123",
    "3": "yuennix",
    "4": "astheia123",
    "5": "yuennix",
    "6": "astheia123",
    "7": "shaishai@22",
    "8": "yuennix",
    "9": "meggg123",
    "10": "3490_sio8aN",
    "11": "9382",
}

# ================== KEYBOARDS ==================

def make_start_kb(is_owner=False):
    rows = [[InlineKeyboardButton(text="🚀 Start Creating Accounts", callback_data="menu:create")]]
    if is_owner:
        rows.append([InlineKeyboardButton(text="⚙️ Owner Menu", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def make_name_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇵🇭 Filipino Names", callback_data="name:1")],
        [InlineKeyboardButton(text="🔥 RPW Names", callback_data="name:2")],
    ])

def make_gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Male", callback_data="gender:1")],
        [InlineKeyboardButton(text="👩 Female", callback_data="gender:2")],
        [InlineKeyboardButton(text="⚧ Mixed", callback_data="gender:3")],
    ])

def make_domain_kb():
    rows = []
    for k, v in DOMAINS.items():
        rows.append([InlineKeyboardButton(text=f"{k} • {v}", callback_data=f"domain:{k}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def make_count_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1",  callback_data="count:1"),
            InlineKeyboardButton(text="2",  callback_data="count:2"),
            InlineKeyboardButton(text="3",  callback_data="count:3"),
            InlineKeyboardButton(text="5",  callback_data="count:5"),
        ],
        [
            InlineKeyboardButton(text="10", callback_data="count:10"),
            InlineKeyboardButton(text="15", callback_data="count:15"),
            InlineKeyboardButton(text="20", callback_data="count:20"),
        ],
    ])

def make_acc_pass_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Set Custom Password", callback_data="accpass:custom")],
        [InlineKeyboardButton(text="🎲 Use Random Password",  callback_data="accpass:random")],
    ])

def make_stop_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛑 Stop Creation", callback_data=f"stop:{uid}")]
    ])

def make_approval_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"access:ok:{user_id}"),
            InlineKeyboardButton(text="❌ Deny",    callback_data=f"access:no:{user_id}"),
        ]
    ])

def make_admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Approved Users",   callback_data="menu:users")],
        [InlineKeyboardButton(text="📋 Created Accounts", callback_data="menu:accounts")],
        [InlineKeyboardButton(text="🔙 Back",             callback_data="menu:back")],
    ])

def make_users_kb():
    rows = []
    users = [u for u in approved_users if u != OWNER_ID]
    if not users:
        rows.append([InlineKeyboardButton(text="— No approved users —", callback_data="noop")])
    else:
        for u in users:
            info = pending_users.get(u, {})
            label = info.get("name", str(u))
            rows.append([
                InlineKeyboardButton(text=f"👤 {label} ({u})", callback_data="noop"),
                InlineKeyboardButton(text="🚫 Revoke",         callback_data=f"revoke:{u}"),
            ])
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def make_accounts_kb():
    rows = []
    if created_accounts:
        rows.append([InlineKeyboardButton(text=f"🗑 Clear All ({len(created_accounts)} accs)", callback_data="accounts:clear")])
    else:
        rows.append([InlineKeyboardButton(text="— No accounts yet —", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def is_allowed(uid):
    return uid == OWNER_ID or uid in approved_users

# ================== /start ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    user_data.pop(uid, None)
    first_name = message.from_user.first_name or "there"
    username = f"@{message.from_user.username}" if message.from_user.username else "no username"

    if uid == OWNER_ID:
        approved_users.add(uid)

    if uid not in seen_users:
        seen_users.add(uid)
        await message.answer(
            f"👋 *Welcome, {first_name}!*\n\n"
            f"This bot lets you automatically create Facebook accounts with custom names, gender, email domain, and more.\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📌 *How to use:*\n"
            f"1️⃣ Tap *Start Creating Accounts*\n"
            f"2️⃣ Choose name style\n"
            f"3️⃣ Choose gender\n"
            f"4️⃣ Choose email domain\n"
            f"5️⃣ Enter domain password\n"
            f"6️⃣ Choose how many accounts\n"
            f"7️⃣ Get results instantly!\n"
            f"━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )

    if is_allowed(uid):
        await message.answer(
            "🤖 *Facebook Auto Creator*\n\nSelect options step by step 👇",
            parse_mode="Markdown",
            reply_markup=make_start_kb(is_owner=(uid == OWNER_ID))
        )
        return

    if uid in pending_users:
        await message.answer("⏳ Your access request is still *pending approval*. Please wait.", parse_mode="Markdown")
        return

    pending_users[uid] = {"name": first_name, "username": username}
    await message.answer(
        "🔒 *Access Required*\n\n"
        "This bot requires approval to use.\n"
        "Your request has been sent to the owner.\n\n"
        "Please wait for approval ⏳",
        parse_mode="Markdown"
    )
    await bot.send_message(
        OWNER_ID,
        f"🔔 *New Access Request*\n\n"
        f"👤 Name: *{first_name}*\n"
        f"🆔 User ID: `{uid}`\n"
        f"📛 Username: {username}\n\n"
        f"Approve or deny below:",
        parse_mode="Markdown",
        reply_markup=make_approval_kb(uid)
    )

# ================== OWNER: APPROVE/DENY ==================
@dp.callback_query(lambda c: c.data.startswith("access:"))
async def cb_approval(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("You are not the owner.", show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]
    target_id = int(parts[2])
    user_info = pending_users.get(target_id, {})
    name = user_info.get("name", "User")

    if action == "ok":
        approved_users.add(target_id)
        pending_users.pop(target_id, None)
        await callback.message.edit_text(
            f"✅ *Approved!*\n👤 {name} (`{target_id}`) has been granted access.",
            parse_mode="Markdown"
        )
        await bot.send_message(
            target_id,
            "✅ *Your access has been approved!*\n\nYou can now use the bot. Tap below to start 👇",
            parse_mode="Markdown",
            reply_markup=make_start_kb()
        )
    else:
        pending_users.pop(target_id, None)
        await callback.message.edit_text(
            f"❌ *Denied.*\n👤 {name} (`{target_id}`) has been rejected.",
            parse_mode="Markdown"
        )
        await bot.send_message(
            target_id,
            "❌ *Your access request was denied.*\n\nContact the owner if you think this is a mistake.",
            parse_mode="Markdown"
        )
    await callback.answer()

# ================== /menu COMMAND ==================
@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer(
        "⚙️ *Owner Menu*\n\nChoose a section:",
        parse_mode="Markdown",
        reply_markup=make_admin_menu_kb()
    )

# ================== OWNER MENU ==================
@dp.callback_query(lambda c: c.data == "menu:admin")
async def cb_admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    await callback.message.edit_text(
        "⚙️ *Owner Menu*\n\nChoose a section:",
        parse_mode="Markdown",
        reply_markup=make_admin_menu_kb()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "menu:back")
async def cb_menu_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🤖 *Facebook Auto Creator*\n\nSelect options step by step 👇",
        parse_mode="Markdown",
        reply_markup=make_start_kb(is_owner=(callback.from_user.id == OWNER_ID))
    )
    await callback.answer()

# ── Approved Users panel ──
@dp.callback_query(lambda c: c.data == "menu:users")
async def cb_menu_users(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    users = [u for u in approved_users if u != OWNER_ID]
    header = f"👥 *Approved Users* — {len(users)} user(s)\n\nTap Revoke to remove access:"
    await callback.message.edit_text(header, parse_mode="Markdown", reply_markup=make_users_kb())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("revoke:"))
async def cb_revoke(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    target = int(callback.data.split(":")[1])
    approved_users.discard(target)
    try:
        await bot.send_message(target, "🚫 Your access to this bot has been revoked.")
    except Exception:
        pass
    users = [u for u in approved_users if u != OWNER_ID]
    header = f"👥 *Approved Users* — {len(users)} user(s)\n\nTap Revoke to remove access:"
    await callback.message.edit_text(header, parse_mode="Markdown", reply_markup=make_users_kb())
    await callback.answer(f"🚫 Revoked access for {target}", show_alert=True)

# ── Created Accounts panel ──
@dp.callback_query(lambda c: c.data == "menu:accounts")
async def cb_menu_accounts(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    if not created_accounts:
        text = "📋 *Created Accounts*\n\nNo accounts have been created yet."
    else:
        lines = []
        for i, acc in enumerate(created_accounts, 1):
            lines.append(
                f"*{i}.* 👤 `{acc['name']}`\n"
                f"    📧 `{acc['email']}`\n"
                f"    🔑 `{acc['password']}`\n"
                f"    🆔 `{acc['uid']}`"
            )
        body = "\n\n".join(lines)
        text = f"📋 *Created Accounts* — {len(created_accounts)} total\n\n{body}"
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated, use Clear to reset_"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=make_accounts_kb())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "accounts:clear")
async def cb_accounts_clear(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    count = len(created_accounts)
    created_accounts.clear()
    await callback.message.edit_text(
        f"🗑 *Cleared!* {count} account record(s) removed.\n\n📋 *Created Accounts*\n\nNo accounts yet.",
        parse_mode="Markdown",
        reply_markup=make_accounts_kb()
    )
    await callback.answer("✅ Cleared!", show_alert=True)

@dp.callback_query(lambda c: c.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()

# ================== START CREATE ==================
@dp.callback_query(lambda c: c.data == "menu:create")
async def cb_name_style(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("⛔ You don't have access. Use /start to request.", show_alert=True)
        return
    await callback.message.edit_text("📛 Choose *Name Style*:", parse_mode="Markdown", reply_markup=make_name_kb())
    await callback.answer()

# ================== NAME ==================
@dp.callback_query(lambda c: c.data.startswith("name:"))
async def cb_gender(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_data[uid] = {"name": callback.data.split(":")[1]}
    await callback.message.edit_text("⚤ Choose *Gender*:", parse_mode="Markdown", reply_markup=make_gender_kb())
    await callback.answer()

# ================== GENDER ==================
@dp.callback_query(lambda c: c.data.startswith("gender:"))
async def cb_domain(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    user_data[uid]["gender"] = callback.data.split(":")[1]
    await callback.message.edit_text("📧 Choose *Email Domain*:", parse_mode="Markdown", reply_markup=make_domain_kb())
    await callback.answer()

# ================== DOMAIN → ASK PASSWORD ==================
@dp.callback_query(lambda c: c.data.startswith("domain:"))
async def cb_domain_pass(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    domain_key = callback.data.split(":")[1]
    user_data[uid]["domain"] = domain_key
    domain_name = DOMAINS.get(domain_key, domain_key)

    if domain_key in unlocked_domains.get(uid, set()):
        await callback.message.edit_text(
            f"✅ *Domain `{domain_name}` already unlocked!*\n\n🔑 *Set a password for the created accounts:*",
            parse_mode="Markdown",
            reply_markup=make_acc_pass_kb()
        )
        await callback.answer()
        return

    user_data[uid]["awaiting"] = "domain_pass"
    await callback.message.edit_text(
        f"🔑 *Domain Password Required*\n\n"
        f"Domain: `{domain_name}`\n\n"
        f"Type the password for this domain:",
        parse_mode="Markdown"
    )
    await callback.answer()

# ================== STOP BUTTON ==================
@dp.callback_query(lambda c: c.data.startswith("stop:"))
async def cb_stop(callback: types.CallbackQuery):
    uid = int(callback.data.split(":")[1])
    if callback.from_user.id != uid and callback.from_user.id != OWNER_ID:
        await callback.answer("Not your session.", show_alert=True)
        return
    stop_flags[uid] = True
    await callback.answer("🛑 Stopping after current account finishes...", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

# ================== TEXT INPUT HANDLER ==================
@dp.message()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    data = user_data.get(uid)
    awaiting = data.get("awaiting") if data else None

    if not data or awaiting not in ("domain_pass", "custom_pass"):
        return

    entered = message.text.strip()

    # Delete the password message immediately so it vanishes from chat
    try:
        await message.delete()
    except Exception:
        pass

    if awaiting == "custom_pass":
        if len(entered) < 6:
            await message.answer("⚠️ Password must be at least *6 characters*. Try again:", parse_mode="Markdown")
            return
        user_data[uid]["password"] = entered
        user_data[uid].pop("awaiting")
        await message.answer(
            f"✅ *Custom password set!*\n\n🔢 How many accounts?",
            parse_mode="Markdown",
            reply_markup=make_count_kb()
        )
        return

    domain_key = data.get("domain")
    correct = DOMAIN_PASSWORDS.get(domain_key, "")

    if entered != correct:
        user_data.pop(uid, None)
        await message.answer(
            "❌ *Wrong domain password!*\n\nAccess denied for this domain.\nUse /start to try again.",
            parse_mode="Markdown"
        )
        return

    if uid not in unlocked_domains:
        unlocked_domains[uid] = set()
    unlocked_domains[uid].add(domain_key)

    user_data[uid].pop("awaiting")
    await message.answer(
        "✅ *Domain password correct!* _(won't ask again)_\n\n🔑 *Set a password for the created accounts:*",
        parse_mode="Markdown",
        reply_markup=make_acc_pass_kb()
    )

# ================== ACCOUNT PASSWORD CHOICE ==================
@dp.callback_query(lambda c: c.data.startswith("accpass:"))
async def cb_acc_pass(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    choice = callback.data.split(":")[1]
    if choice == "random":
        user_data[uid]["password"] = None
        await callback.message.edit_text("🔢 *How many accounts?*", parse_mode="Markdown", reply_markup=make_count_kb())
    else:
        user_data[uid]["awaiting"] = "custom_pass"
        await callback.message.edit_text(
            "🔑 *Type your custom password for the accounts:*\n\n_(minimum 6 characters)_",
            parse_mode="Markdown"
        )
    await callback.answer()

# ================== COUNT → CREATE ==================
@dp.callback_query(lambda c: c.data.startswith("count:"))
async def cb_create(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return

    count = int(callback.data.split(":")[1])
    data = user_data.pop(uid)
    stop_flags[uid] = False

    await callback.message.answer(
        f"⚡ *Creating {count} account(s)...*\nResults appear one by one 👇",
        parse_mode="Markdown",
        reply_markup=make_stop_kb(uid)
    )
    await callback.answer()

    fb.CUSTOM_PASS = data.get("password", None)
    loop = asyncio.get_event_loop()

    domain_val = str(data.get("domain", ""))
    name_val   = str(data.get("name", "1"))
    gender_val = str(data.get("gender", "1"))

    if not domain_val:
        await callback.message.answer("❌ Session error: domain not set. Use /start to try again.")
        return

    def _register():
        return fb.register_account(
            domain_choice=domain_val,
            name_option=name_val,
            gender_option=gender_val
        )

    success = 0
    while success < count:
        if stop_flags.get(uid):
            await callback.message.answer("🛑 *Creation stopped.*", parse_mode="Markdown")
            break
        try:
            result = await loop.run_in_executor(None, _register)
            if result:
                success += 1
                created_accounts.append({
                    "name":     result["name"],
                    "email":    result["email"],
                    "password": result["password"],
                    "uid":      result["uid"],
                    "by":       uid,
                })
                await callback.message.answer(
                    f"✅ *Account {success}/{count} Created!*\n\n"
                    f"👤 *Name:* `{result['name']}`\n"
                    f"📧 *Email:* `{result['email']}`\n"
                    f"🔑 *Password:* `{result['password']}`\n"
                    f"🆔 *UID:* `{result['uid']}`",
                    parse_mode="Markdown"
                )
            # if result is None here it means STOP_FLAG was set inside register_account
            elif stop_flags.get(uid):
                await callback.message.answer("🛑 *Creation stopped.*", parse_mode="Markdown")
                break
        except Exception as e:
            logging.exception(e)

    stop_flags.pop(uid, None)
    await callback.message.answer(
        f"🎉 *Done!* {success}/{count} accounts created.\n\nType /start to create more.",
        parse_mode="Markdown"
    )

async def main():
    print("🤖 Bot is now running...")
    logging.basicConfig(level=logging.INFO)

    # Commands visible to all users via ≡ Menu button
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🚀 Start the bot"),
    ])

    # Extra commands visible only to the owner via ≡ Menu button
    await bot.set_my_commands(
        [
            types.BotCommand(command="start",    description="🚀 Start the bot"),
            types.BotCommand(command="menu",     description="⚙️ Owner menu"),
        ],
        scope=types.BotCommandScopeChat(chat_id=OWNER_ID)
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
