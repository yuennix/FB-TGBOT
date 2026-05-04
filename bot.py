import os
import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

import main as fb

_executor = ThreadPoolExecutor(max_workers=32)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID  = int(os.getenv("OWNER_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

user_data       = {}   # uid -> session dict
seen_users      = set()
approved_users  = set()
pending_users   = {}   # uid -> {name, username}
stop_flags      = {}   # uid -> bool
unlocked_domains= {}   # uid -> set of domain keys
created_accounts= []   # list of {name,email,password,uid,by}
user_credits    = {}   # uid -> int  (OWNER_ID is unlimited)
owner_action    = {}   # OWNER_ID -> {action, target, prompt_msg_id}
creating_msg    = {}   # uid -> message_id of the "⚡ Creating …" banner

USERS_FILE = "users.json"

def load_users():
    global seen_users, approved_users, user_credits, pending_users, unlocked_domains, created_accounts
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
        seen_users     = set(data.get("seen_users", []))
        approved_users = set(data.get("approved_users", []))
        user_credits   = {int(k): v for k, v in data.get("user_credits", {}).items()}
        for uid_str, info in data.get("pending_users", {}).items():
            uid = int(uid_str)
            if uid not in pending_users:
                pending_users[uid] = info
        for uid_str, domains in data.get("unlocked_domains", {}).items():
            unlocked_domains[int(uid_str)] = set(domains)
        created_accounts = data.get("created_accounts", [])
    except Exception:
        pass

def save_users():
    try:
        with open(USERS_FILE, "w") as f:
            json.dump({
                "seen_users":       list(seen_users),
                "approved_users":   list(approved_users),
                "user_credits":     {str(k): v for k, v in user_credits.items()},
                "pending_users":    {str(k): v for k, v in pending_users.items()},
                "unlocked_domains": {str(k): list(v) for k, v in unlocked_domains.items()},
                "created_accounts": created_accounts,
            }, f)
    except Exception:
        pass

DOMAINS = {
    "1": "1secmail",
    "2": "yopmail.com",
    "3": "harakirimail.com",
    "4": "weyn.store",
    "5": "jhames.shop",
    "6": "jakulan.site",
}

DOMAIN_PASSWORDS = {
    "1": "1sec123",
    "2": "yop123",
    "3": "hara123",
    "4": "yuennix",
    "5": "yuennix",
    "6": "yuennix",
}

# ================== KEYBOARDS ==================

def make_start_kb(uid=0):
    is_owner = (uid == OWNER_ID)
    rows = [[InlineKeyboardButton(text="🚀 Start Creating Accounts", callback_data="menu:create")]]
    rows.append([
        InlineKeyboardButton(text="📋 My Accounts",  callback_data="menu:myaccs"),
        InlineKeyboardButton(text="🌐 Bot Accounts", callback_data="menu:botaccs"),
    ])
    if not is_owner:
        rows.append([InlineKeyboardButton(text="💳 My Credits", callback_data="menu:mycredits")])
    if is_owner:
        rows.append([InlineKeyboardButton(text="⚙️ Owner Menu", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def make_name_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇵🇭 Filipino Names", callback_data="name:1")],
        [InlineKeyboardButton(text="🔥 RPW Names",       callback_data="name:2")],
    ])

def make_gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Male",  callback_data="gender:1")],
        [InlineKeyboardButton(text="👩 Female",callback_data="gender:2")],
        [InlineKeyboardButton(text="⚧ Mixed", callback_data="gender:3")],
    ])

def make_domain_kb():
    rows = []
    for k, v in DOMAINS.items():
        rows.append([InlineKeyboardButton(text=f"{k} • {v}", callback_data=f"domain:{k}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

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

def make_credit_give_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5",          callback_data=f"credits:give:{user_id}:5"),
            InlineKeyboardButton(text="10",         callback_data=f"credits:give:{user_id}:10"),
            InlineKeyboardButton(text="20",         callback_data=f"credits:give:{user_id}:20"),
        ],
        [
            InlineKeyboardButton(text="50",         callback_data=f"credits:give:{user_id}:50"),
            InlineKeyboardButton(text="100",        callback_data=f"credits:give:{user_id}:100"),
            InlineKeyboardButton(text="✏️ Custom",  callback_data=f"credits:give:{user_id}:custom"),
        ],
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
            info    = pending_users.get(u, {})
            label   = info.get("name", str(u))
            credits = user_credits.get(u, 0)
            rows.append([InlineKeyboardButton(
                text=f"👤 {label} ({u})  💳 {credits} credits",
                callback_data="noop"
            )])
            rows.append([
                InlineKeyboardButton(text="➕ Add Credits", callback_data=f"credits:add:{u}"),
                InlineKeyboardButton(text="🚫 Revoke",      callback_data=f"revoke:{u}"),
            ])
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def make_accounts_kb():
    rows = []
    if created_accounts:
        rows.append([InlineKeyboardButton(
            text=f"🗑 Clear All ({len(created_accounts)} accs)",
            callback_data="accounts:clear"
        )])
    else:
        rows.append([InlineKeyboardButton(text="— No accounts yet —", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def is_allowed(uid):
    return uid == OWNER_ID or uid in approved_users

async def _del(chat_id, msg_id, delay=0):
    try:
        if delay:
            await asyncio.sleep(delay)
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

# ================== /start ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid        = message.from_user.id
    first_name = message.from_user.first_name or "there"
    username   = f"@{message.from_user.username}" if message.from_user.username else "no username"

    user_data.pop(uid, None)
    owner_action.pop(uid, None)
    # Delete any lingering "⚡ Creating..." banner
    banner_id = creating_msg.pop(uid, None)
    if banner_id:
        asyncio.create_task(_del(uid, banner_id))

    if uid == OWNER_ID:
        approved_users.add(uid)

    # Show welcome only the very first time ever
    if uid not in seen_users:
        seen_users.add(uid)
        save_users()
        await message.answer(
            f"👋 *Welcome, {first_name}!*\n\n"
            f"This bot lets you automatically create Facebook accounts with custom names, gender, email domain, and more.\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📌 *How to use:*\n"
            f"1️⃣ Tap *Start Creating Accounts*\n"
            f"2️⃣ Choose name style\n"
            f"3️⃣ Choose gender\n"
            f"4️⃣ Choose email domain\n"
            f"5️⃣ Enter domain password _(only once per domain)_\n"
            f"6️⃣ Type how many accounts\n"
            f"7️⃣ Get results instantly!\n"
            f"━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )

    # Already approved → go straight to menu
    if is_allowed(uid):
        await message.answer(
            "🤖 *Facebook Auto Creator*\n\nSelect options step by step 👇",
            parse_mode="Markdown",
            reply_markup=make_start_kb(uid)
        )
        return

    # Already waiting for approval → remind, don't re-send request
    if uid in pending_users:
        await message.answer(
            "⏳ Your access request is still *pending approval*. Please wait.",
            parse_mode="Markdown"
        )
        return

    # First time requesting access
    pending_users[uid] = {"name": first_name, "username": username}
    save_users()
    req_msg = await message.answer(
        "🔒 *Access Required*\n\n"
        "This bot requires approval to use.\n"
        "Your request has been sent to the owner.\n\n"
        "Please wait for approval ⏳",
        parse_mode="Markdown"
    )
    pending_users[uid]["req_msg_id"] = req_msg.message_id
    try:
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
    except Exception:
        pass

# ================== /credits COMMAND ==================
@dp.message(Command("credits"))
async def cmd_credits(message: types.Message):
    uid = message.from_user.id
    # Delete any lingering "⚡ Creating..." banner
    banner_id = creating_msg.pop(uid, None)
    if banner_id:
        asyncio.create_task(_del(uid, banner_id))
    if uid == OWNER_ID:
        await message.answer("👑 You have *unlimited credits* as owner.", parse_mode="Markdown")
        return
    if not is_allowed(uid):
        return
    credits = user_credits.get(uid, 0)
    await message.answer(
        f"💳 *Your Credits*\n\n"
        f"Available: *{credits}* credit(s)\n"
        f"_(1 credit = 1 account created)_",
        parse_mode="Markdown"
    )

# ================== /stats COMMAND ==================
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != OWNER_ID:
        await message.answer("🔒 Owner only.")
        return
    total_seen      = len(seen_users)
    total_approved  = len([u for u in approved_users if u != OWNER_ID])
    total_pending   = len(pending_users)
    total_credits_remaining = sum(user_credits.values())
    total_accounts  = len(created_accounts)
    await message.answer(
        f"📊 *Bot Statistics*\n\n"
        f"👥 Total Users Seen: *{total_seen}*\n"
        f"✅ Approved Users: *{total_approved}*\n"
        f"⏳ Pending Requests: *{total_pending}*\n\n"
        f"💳 Total Credits Used: *{total_accounts}*\n"
        f"💰 Total Credits Remaining: *{total_credits_remaining}*\n\n"
        f"🤖 Total Accounts Created: *{total_accounts}*",
        parse_mode="Markdown"
    )

# ================== OWNER: APPROVE/DENY ==================
@dp.callback_query(lambda c: c.data.startswith("access:"))
async def cb_approval(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("You are not the owner.", show_alert=True)
        return

    parts     = callback.data.split(":")
    action    = parts[1]
    target_id = int(parts[2])
    user_info = pending_users.get(target_id, {})
    name      = user_info.get("name", "User")

    if action == "ok":
        approved_users.add(target_id)
        pending_users.pop(target_id, None)
        await callback.message.edit_text(
            f"✅ *Approved!*  👤 {name} (`{target_id}`)\n\n"
            f"💳 *How many credits to give this user?*\n"
            f"_(1 credit = 1 account)_",
            parse_mode="Markdown",
            reply_markup=make_credit_give_kb(target_id)
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

# ================== GIVE CREDITS (approval or add) ==================
@dp.callback_query(lambda c: c.data.startswith("credits:give:"))
async def cb_give_credits(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return

    parts     = callback.data.split(":")   # credits:give:{uid}:{amount}
    target_id = int(parts[2])
    amount    = parts[3]

    if amount == "custom":
        owner_action[OWNER_ID] = {
            "action":       "add_credits",
            "target":       target_id,
            "prompt_msg_id": callback.message.message_id,
        }
        await callback.message.edit_text(
            f"✏️ *Type the number of credits to give* 👤 `{target_id}`:\n\n"
            f"_(Send a number, e.g. 30)_",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    amount = int(amount)
    user_credits[target_id] = user_credits.get(target_id, 0) + amount
    total = user_credits[target_id]
    save_users()

    target_info = pending_users.get(target_id, {})
    name = target_info.get("name", str(target_id))

    await callback.message.edit_text(
        f"✅ *Credits given!*\n"
        f"👤 {name} (`{target_id}`) now has *{total}* credit(s).",
        parse_mode="Markdown"
    )
    try:
        req_msg_id = pending_users.get(target_id, {}).get("req_msg_id")
        if req_msg_id:
            asyncio.create_task(_del(target_id, req_msg_id))
        await bot.send_message(
            target_id,
            f"✅ *Your access has been approved!*\n\n"
            f"💳 You've been given *{amount}* credit(s).\n"
            f"_(1 credit = 1 account)_\n\n"
            f"Tap below to start 👇",
            parse_mode="Markdown",
            reply_markup=make_start_kb(target_id)
        )
    except Exception:
        pass
    await callback.answer(f"✅ Gave {amount} credits!", show_alert=True)

# ================== ADD CREDITS TO EXISTING USER ==================
@dp.callback_query(lambda c: c.data.startswith("credits:add:"))
async def cb_add_credits(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    target_id = int(callback.data.split(":")[2])
    info  = pending_users.get(target_id, {})
    name  = info.get("name", str(target_id))
    total = user_credits.get(target_id, 0)
    await callback.message.edit_text(
        f"💳 *Add Credits*\n"
        f"👤 {name} (`{target_id}`) — current: *{total}* credit(s)\n\n"
        f"How many to add?",
        parse_mode="Markdown",
        reply_markup=make_credit_give_kb(target_id)
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
    uid = callback.from_user.id
    await callback.message.edit_text(
        "🤖 *Facebook Auto Creator*\n\nSelect options step by step 👇",
        parse_mode="Markdown",
        reply_markup=make_start_kb(uid)
    )
    await callback.answer()

# ── Approved Users panel ──
@dp.callback_query(lambda c: c.data == "menu:users")
async def cb_menu_users(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    users  = [u for u in approved_users if u != OWNER_ID]
    header = f"👥 *Approved Users* — {len(users)} user(s)\n\nManage credits & access:"
    await callback.message.edit_text(header, parse_mode="Markdown", reply_markup=make_users_kb())
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("revoke:"))
async def cb_revoke(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Owner only.", show_alert=True)
        return
    target = int(callback.data.split(":")[1])
    approved_users.discard(target)
    user_credits.pop(target, None)
    save_users()
    try:
        await bot.send_message(target, "🚫 Your access to this bot has been revoked.")
    except Exception:
        pass
    users  = [u for u in approved_users if u != OWNER_ID]
    header = f"👥 *Approved Users* — {len(users)} user(s)\n\nManage credits & access:"
    await callback.message.edit_text(header, parse_mode="Markdown", reply_markup=make_users_kb())
    await callback.answer(f"🚫 Revoked access for {target}", show_alert=True)

# ── Created Accounts panel (owner sees all) ──
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
    save_users()
    await callback.message.edit_text(
        f"🗑 *Cleared!* {count} account record(s) removed.\n\n📋 *Created Accounts*\n\nNo accounts yet.",
        parse_mode="Markdown",
        reply_markup=make_accounts_kb()
    )
    await callback.answer("✅ Cleared!", show_alert=True)

# ── My Accounts panel (regular user sees only their own) ──
@dp.callback_query(lambda c: c.data == "menu:myaccs")
async def cb_my_accounts(callback: types.CallbackQuery):
    uid  = callback.from_user.id
    if not is_allowed(uid):
        await callback.answer("No access.", show_alert=True)
        return
    mine = [a for a in created_accounts if a.get("by") == uid]
    if not mine:
        text = "📋 *My Created Accounts*\n\nYou haven't created any accounts yet."
    else:
        lines = []
        for i, acc in enumerate(mine, 1):
            lines.append(
                f"*{i}.* 👤 `{acc['name']}`\n"
                f"    📧 `{acc['email']}`\n"
                f"    🔑 `{acc['password']}`\n"
                f"    🆔 `{acc['uid']}`"
            )
        body = "\n\n".join(lines)
        text = f"📋 *My Created Accounts* — {len(mine)} total\n\n{body}"
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated_"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu:back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_kb)
    await callback.answer()

# ── Bot Accounts panel (own accounts for users, all accounts for owner) ──
@dp.callback_query(lambda c: c.data == "menu:botaccs")
async def cb_bot_accounts(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if not is_allowed(uid):
        await callback.answer("No access.", show_alert=True)
        return
    is_owner = (uid == OWNER_ID)
    mine = created_accounts if is_owner else [a for a in created_accounts if a.get("by") == uid]
    label = "🌐 *Bot Accounts*" if is_owner else "📋 *My Accounts*"
    if not mine:
        text = f"{label}\n\nNo accounts created yet."
    else:
        lines = []
        for i, acc in enumerate(mine, 1):
            by_line = f"\n    👤 by `{acc.get('by', '?')}`" if is_owner else ""
            lines.append(
                f"*{i}.* 👤 `{acc['name']}`\n"
                f"    📧 `{acc['email']}`\n"
                f"    🔑 `{acc['password']}`\n"
                f"    🆔 `{acc['uid']}`{by_line}"
            )
        body = "\n\n".join(lines)
        text = f"{label} — {len(mine)} account(s)\n\n{body}"
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated_"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu:back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_kb)
    await callback.answer()

# ── /myaccs command ──
@dp.message(Command("myaccs"))
async def cmd_myaccs(message: types.Message):
    uid = message.from_user.id
    if not is_allowed(uid):
        await message.answer("🔒 No access.")
        return
    mine = [a for a in created_accounts if a.get("by") == uid]
    if not mine:
        text = "📋 *My Created Accounts*\n\nYou haven't created any accounts yet."
    else:
        lines = []
        for i, acc in enumerate(mine, 1):
            lines.append(
                f"*{i}.* 👤 `{acc['name']}`\n"
                f"    📧 `{acc['email']}`\n"
                f"    🔑 `{acc['password']}`\n"
                f"    🆔 `{acc['uid']}`"
            )
        body = "\n\n".join(lines)
        text = f"📋 *My Created Accounts* — {len(mine)} total\n\n{body}"
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated_"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Menu", callback_data="menu:back")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=back_kb)

# ── /botaccs command ──
@dp.message(Command("botaccs"))
async def cmd_botaccs(message: types.Message):
    uid = message.from_user.id
    if not is_allowed(uid):
        await message.answer("🔒 No access.")
        return
    is_owner_user = (uid == OWNER_ID)
    accs = created_accounts if is_owner_user else [a for a in created_accounts if a.get("by") == uid]
    label = "🌐 *Bot Accounts*" if is_owner_user else "📋 *My Accounts*"
    if not accs:
        text = f"{label}\n\nNo accounts created yet."
    else:
        lines = []
        for i, acc in enumerate(accs, 1):
            by_line = f"\n    👤 by `{acc.get('by', '?')}`" if is_owner_user else ""
            lines.append(
                f"*{i}.* 👤 `{acc['name']}`\n"
                f"    📧 `{acc['email']}`\n"
                f"    🔑 `{acc['password']}`\n"
                f"    🆔 `{acc['uid']}`{by_line}"
            )
        body = "\n\n".join(lines)
        text = f"{label} — {len(accs)} account(s)\n\n{body}"
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated_"
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Menu", callback_data="menu:back")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=back_kb)

# ── My Credits panel ──
@dp.callback_query(lambda c: c.data == "menu:mycredits")
async def cb_my_credits(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if not is_allowed(uid):
        await callback.answer("No access.", show_alert=True)
        return
    credits = user_credits.get(uid, 0)
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="menu:back")]
    ])
    await callback.message.edit_text(
        f"💳 *My Credits*\n\n"
        f"Available: *{credits}* credit(s)\n"
        f"_(1 credit = 1 account created)_",
        parse_mode="Markdown",
        reply_markup=back_kb
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()

# ================== START CREATE ==================
@dp.callback_query(lambda c: c.data == "menu:create")
async def cb_name_style(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("⛔ You don't have access. Use /start to request.", show_alert=True)
        return
    await callback.message.edit_text(
        "📛 Choose *Name Style*:", parse_mode="Markdown", reply_markup=make_name_kb()
    )
    await callback.answer()

# ================== NAME ==================
@dp.callback_query(lambda c: c.data.startswith("name:"))
async def cb_gender(callback: types.CallbackQuery):
    uid = callback.from_user.id
    user_data[uid] = {"name": callback.data.split(":")[1]}
    await callback.message.edit_text(
        "⚤ Choose *Gender*:", parse_mode="Markdown", reply_markup=make_gender_kb()
    )
    await callback.answer()

# ================== GENDER ==================
@dp.callback_query(lambda c: c.data.startswith("gender:"))
async def cb_domain(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    user_data[uid]["gender"] = callback.data.split(":")[1]
    await callback.message.edit_text(
        "📧 Choose *Email Domain*:", parse_mode="Markdown", reply_markup=make_domain_kb()
    )
    await callback.answer()

# ================== DOMAIN → ASK PASSWORD ==================
@dp.callback_query(lambda c: c.data.startswith("domain:"))
async def cb_domain_pass(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    domain_key  = callback.data.split(":")[1]
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

    user_data[uid]["awaiting"]       = "domain_pass"
    user_data[uid]["prompt_msg_id"]  = callback.message.message_id
    await callback.message.edit_text(
        f"🔑 *Domain Password Required*\n\n"
        f"Domain: `{domain_name}`\n\n"
        f"Type the password for this domain:",
        parse_mode="Markdown"
    )
    await callback.answer()

# ================== ACCOUNT PASSWORD CHOICE ==================
@dp.callback_query(lambda c: c.data.startswith("accpass:"))
async def cb_acc_pass(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if uid not in user_data:
        await callback.answer("Session expired. Use /start", show_alert=True)
        return
    choice = callback.data.split(":")[1]
    if choice == "random":
        user_data[uid]["password"]      = None
        user_data[uid]["awaiting"]      = "count"
        user_data[uid]["prompt_msg_id"] = callback.message.message_id
        await callback.message.edit_text(
            "🔢 *How many accounts do you want to create?*\n\n"
            "_(Type a number, e.g. 5)_",
            parse_mode="Markdown"
        )
    else:
        user_data[uid]["awaiting"]      = "custom_pass"
        user_data[uid]["prompt_msg_id"] = callback.message.message_id
        await callback.message.edit_text(
            "🔑 *Type your custom password for the accounts:*\n\n_(minimum 6 characters)_",
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
    creating_msg.pop(uid, None)
    await callback.answer("🛑 Stopping after current account finishes...", show_alert=True)
    # Delete the "⚡ Creating..." banner (this IS the banner message)
    try:
        await callback.message.delete()
    except Exception:
        try:
            await callback.message.edit_text("🛑 *Stopped.*", parse_mode="Markdown", reply_markup=None)
        except Exception:
            pass

# ================== TEXT INPUT HANDLER ==================
@dp.message()
async def handle_text(message: types.Message):
    uid      = message.from_user.id
    chat_id  = message.chat.id
    entered  = (message.text or "").strip()

    # ── Owner typing credits amount ──
    if uid == OWNER_ID and uid in owner_action:
        act = owner_action.pop(uid)
        if act.get("action") == "add_credits":
            target_id      = act["target"]
            prompt_msg_id  = act.get("prompt_msg_id")
            asyncio.create_task(_del(chat_id, message.message_id))
            if prompt_msg_id:
                asyncio.create_task(_del(chat_id, prompt_msg_id))
            if not entered.isdigit() or int(entered) <= 0:
                err = await bot.send_message(
                    chat_id, "⚠️ Enter a valid positive number.", parse_mode="Markdown"
                )
                asyncio.create_task(_del(chat_id, err.message_id, delay=3))
                return
            amount = int(entered)
            user_credits[target_id] = user_credits.get(target_id, 0) + amount
            total = user_credits[target_id]
            save_users()
            info  = pending_users.get(target_id, {})
            name  = info.get("name", str(target_id))
            conf = await bot.send_message(
                chat_id,
                f"✅ Added *{amount}* credits to 👤 {name} (`{target_id}`).\n"
                f"New total: *{total}* credit(s).",
                parse_mode="Markdown"
            )
            asyncio.create_task(_del(chat_id, conf.message_id, delay=5))
            try:
                await bot.send_message(
                    target_id,
                    f"💳 *{amount} credit(s) added to your account!*\n"
                    f"New total: *{total}* credit(s).\n"
                    f"_(1 credit = 1 account)_",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        return

    data     = user_data.get(uid)
    awaiting = data.get("awaiting") if data else None

    if not data or awaiting not in ("domain_pass", "custom_pass", "count"):
        return

    prompt_msg_id = data.pop("prompt_msg_id", None)

    # Always delete user's typed message
    asyncio.create_task(_del(chat_id, message.message_id))

    # ── Custom account password ──
    if awaiting == "custom_pass":
        if prompt_msg_id:
            asyncio.create_task(_del(chat_id, prompt_msg_id))
        if len(entered) < 6:
            err = await message.answer(
                "⚠️ Password too short _(min 6 chars)_. Try again:", parse_mode="Markdown"
            )
            asyncio.create_task(_del(chat_id, err.message_id, delay=4))
            # Restore awaiting so user can try again
            user_data[uid]["awaiting"]      = "custom_pass"
            user_data[uid]["prompt_msg_id"] = err.message_id
            return
        user_data[uid]["password"] = entered
        user_data[uid].pop("awaiting", None)
        prompt = await message.answer(
            "✅ *Custom password set!*\n\n"
            "🔢 *How many accounts do you want to create?*\n\n"
            "_(Type a number, e.g. 5)_",
            parse_mode="Markdown"
        )
        user_data[uid]["awaiting"]      = "count"
        user_data[uid]["prompt_msg_id"] = prompt.message_id
        return

    # ── Domain password ──
    if awaiting == "domain_pass":
        if prompt_msg_id:
            asyncio.create_task(_del(chat_id, prompt_msg_id))
        domain_key = data.get("domain")
        correct    = DOMAIN_PASSWORDS.get(domain_key, "")
        if entered != correct:
            user_data.pop(uid, None)
            err = await message.answer(
                "❌ *Wrong domain password.* Access denied.\nUse /start to try again.",
                parse_mode="Markdown"
            )
            asyncio.create_task(_del(chat_id, err.message_id, delay=5))
            return
        if uid not in unlocked_domains:
            unlocked_domains[uid] = set()
        unlocked_domains[uid].add(domain_key)
        save_users()
        user_data[uid].pop("awaiting", None)
        await message.answer(
            "✅ *Domain unlocked!* _(won't ask again)_\n\n🔑 *Set a password for the created accounts:*",
            parse_mode="Markdown",
            reply_markup=make_acc_pass_kb()
        )
        return

    # ── Count ──
    if awaiting == "count":
        if prompt_msg_id:
            asyncio.create_task(_del(chat_id, prompt_msg_id))
        if not entered.isdigit() or int(entered) <= 0:
            err = await message.answer(
                "⚠️ Please type a *valid number* (e.g. 5).", parse_mode="Markdown"
            )
            asyncio.create_task(_del(chat_id, err.message_id, delay=4))
            user_data[uid]["awaiting"]      = "count"
            user_data[uid]["prompt_msg_id"] = err.message_id
            return
        count = int(entered)
        # Credit check for non-owners
        if uid != OWNER_ID:
            available = user_credits.get(uid, 0)
            if available <= 0:
                err = await message.answer(
                    "❌ *You have no credits left.*\n"
                    "Contact the owner to get more credits.",
                    parse_mode="Markdown"
                )
                asyncio.create_task(_del(chat_id, err.message_id, delay=6))
                user_data.pop(uid, None)
                return
            if count > available:
                count = available
                note = await message.answer(
                    f"⚠️ You only have *{available}* credit(s). Creating *{available}* account(s).",
                    parse_mode="Markdown"
                )
                asyncio.create_task(_del(chat_id, note.message_id, delay=5))

        data = user_data.pop(uid)
        await _start_creation(uid, count, data, message.chat.id)

# ================== CREATION ENGINE ==================
async def _start_creation(uid, count, data, chat_id):
    stop_flags[uid] = False

    banner = await bot.send_message(
        chat_id,
        f"⚡ *Creating {count} account(s)...*\nResults appear one by one 👇",
        parse_mode="Markdown",
        reply_markup=make_stop_kb(uid)
    )
    creating_msg[uid] = banner.message_id

    fb.CUSTOM_PASS = data.get("password", None)
    loop       = asyncio.get_event_loop()
    domain_val = str(data.get("domain", ""))
    name_val   = str(data.get("name", "1"))
    gender_val = str(data.get("gender", "1"))

    if not domain_val:
        await bot.send_message(chat_id, "❌ Session error: domain not set. Use /start to try again.")
        creating_msg.pop(uid, None)
        return

    def _register():
        return fb.register_account(
            domain_choice=domain_val,
            name_option=name_val,
            gender_option=gender_val
        )

    CONCURRENCY = 32
    success     = 0
    lock        = asyncio.Lock()
    stopped     = False

    async def _worker():
        nonlocal success, stopped
        while True:
            async with lock:
                if stopped or success >= count:
                    return
            if stop_flags.get(uid):
                async with lock:
                    stopped = True
                return
            try:
                result = await loop.run_in_executor(_executor, _register)
            except Exception as e:
                logging.exception(e)
                continue
            if result:
                async with lock:
                    if success >= count:
                        return
                    success += 1
                    current = success
                    # Deduct credit for non-owners
                    if uid != OWNER_ID:
                        user_credits[uid] = max(0, user_credits.get(uid, 0) - 1)
                created_accounts.append({
                    "name":     result["name"],
                    "email":    result["email"],
                    "password": result["password"],
                    "uid":      result["uid"],
                    "by":       uid,
                })
                save_users()
                credits_left = "" if uid == OWNER_ID else f"\n💳 Credits left: *{user_credits.get(uid, 0)}*"
                await bot.send_message(
                    chat_id,
                    f"✅ *Account {current}/{count} Created!*\n\n"
                    f"👤 *Name:* `{result['name']}`\n"
                    f"📧 *Email:* `{result['email']}`\n"
                    f"🔑 *Password:* `{result['password']}`\n"
                    f"🆔 *UID:* `{result['uid']}`"
                    f"{credits_left}",
                    parse_mode="Markdown"
                )
                if current >= count:
                    return
            elif stop_flags.get(uid):
                async with lock:
                    stopped = True
                return

    workers = [asyncio.create_task(_worker()) for _ in range(min(count, CONCURRENCY))]
    await asyncio.gather(*workers)

    # Delete the "⚡ Creating..." banner
    banner_id = creating_msg.pop(uid, None)
    if banner_id:
        asyncio.create_task(_del(chat_id, banner_id))

    if stopped or stop_flags.get(uid):
        await bot.send_message(chat_id, "🛑 *Creation stopped.*", parse_mode="Markdown")

    stop_flags.pop(uid, None)
    credits_summary = (
        "" if uid == OWNER_ID
        else f"\n💳 Credits remaining: *{user_credits.get(uid, 0)}*"
    )
    if success == 0 and not stopped:
        await bot.send_message(
            chat_id,
            "❌ *No accounts were created.*\n\n"
            "Facebook may be blocking registrations from this server's IP. "
            "Try again later or contact the owner.",
            parse_mode="Markdown"
        )
    else:
        await bot.send_message(
            chat_id,
            f"🎉 *Done!* {success}/{count} accounts created.{credits_summary}\n\nType /start to create more.",
            parse_mode="Markdown"
        )

async def main():
    print("🤖 Bot is now running...")
    logging.basicConfig(level=logging.INFO)
    load_users()

    await bot.set_my_commands([
        types.BotCommand(command="start",    description="🚀 Start the bot"),
        types.BotCommand(command="myaccs",   description="📋 My created accounts"),
        types.BotCommand(command="credits",  description="💳 Check your credits"),
    ])

    await bot.set_my_commands(
        [
            types.BotCommand(command="start",    description="🚀 Start the bot"),
            types.BotCommand(command="myaccs",   description="📋 My created accounts"),
            types.BotCommand(command="botaccs",  description="🌐 All bot accounts"),
            types.BotCommand(command="credits",  description="💳 Credits info"),
            types.BotCommand(command="stats",    description="📊 Bot statistics"),
            types.BotCommand(command="menu",     description="⚙️ Owner menu"),
        ],
        scope=types.BotCommandScopeChat(chat_id=OWNER_ID)
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
