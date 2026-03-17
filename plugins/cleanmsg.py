"""
Clean MSG Plugin — Proper Implementation using bot.ask()
Flow:
  1. Select Account  (bot/userbot)
  2. Toggle-select Target Chats (multi-step ask loop)
  3. Select Message Type  (All / Audio / Video / Document / Photo / etc.)
  4. Confirm → Execute → Report

Key fix: Channels attribute messages to the channel, not the bot.
So we NEVER filter by sender — we iterate ALL messages and filter by type only.
  • Bot client  → iterate via get_messages(IDs) batches (bot-safe, no GetHistory)
  • Userbot     → get_chat_history() then filter by type
"""
import asyncio
from database import db
from .test import CLIENT, start_clone_bot
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageDeleteForbidden, ChatAdminRequired
from pyrogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)

_CLIENT = CLIENT()

# Pending confirm contexts  msg_id → dict
_pending_cleans: dict[int, dict] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def __parse_link(link: str):
    link = link.strip().rstrip('/')
    if "t.me/" not in link:
        return None, None
    parts = link.split('/')
    if not parts[-1].isdigit():
        return None, None
    msg_id = int(parts[-1])
    
    if "t.me/c/" in link:
        chat_id = int(f"-100{parts[-2]}")
    else:
        chat_id = parts[-2]
    return chat_id, msg_id

async def _safe_delete(client, chat_id, ids: list) -> int:
    if not ids:
        return 0
    try:
        await client.delete_messages(chat_id, ids)
        return len(ids)
    except (MessageDeleteForbidden, ChatAdminRequired):
        return 0
    except FloodWait as fw:
        await asyncio.sleep(fw.value + 2)
        try:
            await client.delete_messages(chat_id, ids)
            return len(ids)
        except Exception:
            return 0
    except Exception:
        return 0

async def _do_delete_range(client, chat_id, start_id: int, end_id: int, status_msg) -> int:
    total = [0]
    batch = []
    
    mn = min(start_id, end_id)
    mx = max(start_id, end_id)
    all_ids = list(range(mn, mx + 1))

    async def flush():
        nonlocal batch
        if batch:
            total[0] += await _safe_delete(client, chat_id, batch)
            batch = []
            try:
                await status_msg.edit_text(
                    f"<b>🗑 Cleaning… <code>{total[0]}</code> deleted so far.</b>"
                )
            except Exception:
                pass

    for i in all_ids:
        batch.append(i)
        if len(batch) >= 100:
            await flush()
            
    await flush()
    return total[0]


# ──────────────────────────────────────────────────────────────────────────────
# Settings callback entry point
# ──────────────────────────────────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r'^settings#cleanmsg$'))
async def clean_msg_from_settings(bot, query):
    await query.message.delete()
    await _cleanmsg_flow(bot, query.from_user.id)


# ──────────────────────────────────────────────────────────────────────────────
# Command entry point
# ──────────────────────────────────────────────────────────────────────────────
@Client.on_message(filters.private & filters.command("cleanmsg"))
async def cleanmsg_cmd(bot, message):
    await _cleanmsg_flow(bot, message.from_user.id)


# ──────────────────────────────────────────────────────────────────────────────
# Main interactive flow using bot.ask()
# ──────────────────────────────────────────────────────────────────────────────
async def _cleanmsg_flow(bot, user_id: int):

    # ── Step 1: Choose account ─────────────────────────────────────────────
    accounts = await db.get_bots(user_id)
    if not accounts:
        return await bot.send_message(
            user_id,
            "<b>❌ No accounts found. Add one in /settings → Accounts first.</b>"
        )

    acc_buttons = []
    for acc in accounts:
        label = "🤖 Bot" if acc.get('is_bot', True) else "👤 Userbot"
        name  = acc.get('username') or acc.get('name', 'Unknown')
        acc_buttons.append([KeyboardButton(f"{label}: {name} [{acc['id']}]")])
    acc_buttons.append([KeyboardButton("/cancel")])

    acc_reply = await bot.ask(
        user_id,
        "<b>🗑 Clean MSG — Step 1/3</b>\n\nChoose which account to use for deletion:",
        reply_markup=ReplyKeyboardMarkup(acc_buttons, resize_keyboard=True, one_time_keyboard=True)
    )
    if "/cancel" in acc_reply.text:
        return await acc_reply.reply("<b>Cancelled.</b>", reply_markup=ReplyKeyboardRemove())

    sel_acc = None
    if "[" in acc_reply.text and "]" in acc_reply.text:
        try:
            acc_id = int(acc_reply.text.split('[')[-1].split(']')[0])
            sel_acc = await db.get_bot(user_id, acc_id)
        except Exception:
            pass
    if not sel_acc:
        sel_acc = accounts[0]

    # ── Step 2: First target link ─────────────────
    msg_reply = await bot.ask(
        user_id,
        "<b>🗑 Clean MSG — Step 2/3</b>\n\nSend the <b>FIRST message link</b> (from where deletion should start):",
        reply_markup=ReplyKeyboardRemove()
    )
    if "/cancel" in msg_reply.text:
       return await msg_reply.reply("<b>Cancelled.</b>", reply_markup=ReplyKeyboardRemove())
       
    chat_id, start_id = __parse_link(msg_reply.text)
    if not chat_id:
        return await bot.send_message(user_id, "<b>❌ Invalid Telegram Message Link. Cancelled.</b>")

    # ── Step 3: Last target link ────────────────────────────────────────
    msg_reply2 = await bot.ask(
        user_id,
        "<b>🗑 Clean MSG — Step 3/3</b>\n\nSend the <b>LAST message link</b> (till where deletion should happen):"
    )
    if "/cancel" in (msg_reply2.text or ""):
        return await msg_reply2.reply("<b>Cancelled.</b>", reply_markup=ReplyKeyboardRemove())

    chat_id2, end_id = __parse_link(msg_reply2.text)
    if not chat_id2 or str(chat_id) != str(chat_id2):
        return await bot.send_message(user_id, "<b>❌ Invalid link or chats do not match. Cancelled.</b>")

    # ── Confirm ─────────────────────────────────────────────────────────────
    acc_label = "🤖 Bot" if sel_acc.get('is_bot', True) else "👤 Userbot"
    acc_name  = sel_acc.get('name', 'Unknown')

    confirm_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yes, Delete!", callback_data="cleanmsg#confirm"),
        InlineKeyboardButton("❌ Cancel",       callback_data="cleanmsg#abort")
    ]])
    confirm_msg = await bot.send_message(
        user_id,
        f"<b>⚠️ Confirm Deletion</b>\n\n"
        f"<b>Account:</b> {acc_label} — {acc_name}\n"
        f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"<b>Messages:</b> From ID <code>{start_id}</code> to <code>{end_id}</code>\n\n"
        f"<i>⚠️ This action is irreversible. Continue?</i>",
        reply_markup=confirm_markup
    )
    await msg_reply2.reply("<b>Confirm above ⬆️</b>", reply_markup=ReplyKeyboardRemove())

    # Store context
    _pending_cleans[confirm_msg.id] = {
        "user_id": user_id,
        "account": sel_acc,
        "chat_id": chat_id,
        "start_id": start_id,
        "end_id": end_id
    }


# ──────────────────────────────────────────────────────────────────────────────
# Confirm / Abort callbacks
# ──────────────────────────────────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r'^cleanmsg#confirm$'))
async def cleanmsg_confirm(bot, query):
    ctx = _pending_cleans.pop(query.message.id, None)
    if not ctx:
        return await query.answer("Session expired. Run /cleanmsg again.", show_alert=True)

    sel_acc       = ctx["account"]
    chat_id       = ctx["chat_id"]
    start_id      = ctx["start_id"]
    end_id        = ctx["end_id"]
    user_id       = ctx["user_id"]

    status_msg = await query.message.edit_text("<b>🗑 Starting Clean MSG… please wait.</b>")

    # Start forwarding client
    try:
        client = await start_clone_bot(_CLIENT.client(sel_acc))
    except Exception as e:
        return await status_msg.edit_text(f"<b>❌ Could not start account:</b>\n<code>{e}</code>")

    grand_total  = 0
    failed_chats = []

    try:
        await status_msg.edit_text(
            f"<b>🗑 Cleaning…\n✅ Deleted so far: <code>{grand_total}</code></b>"
        )
        grand_total = await _do_delete_range(client, chat_id, start_id, end_id, status_msg)
    except Exception as e:
        print(f"[CleanMSG] Chat {chat_id} error: {e}")
        failed_chats.append(str(chat_id))

    try:
        await client.stop()
    except Exception:
        pass

    from .settings import main_buttons
    result = (
        f"<b>✅ Clean MSG Complete!</b>\n\n"
        f"<b>Total deleted:</b> <code>{grand_total}</code> messages"
    )
    if failed_chats:
        result += f"\n\n<b>⚠️ Errors in:</b> {', '.join(failed_chats)}"

    await status_msg.edit_text(
        result,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("↩ Back to Settings", callback_data="settings#main")
        ]])
    )


@Client.on_callback_query(filters.regex(r'^cleanmsg#abort$'))
async def cleanmsg_abort(bot, query):
    _pending_cleans.pop(query.message.id, None)
    from .settings import main_buttons
    await query.message.edit_text(
        "<b>Cancelled.</b>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("↩ Back to Settings", callback_data="settings#main")
        ]])
    )
