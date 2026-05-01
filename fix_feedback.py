#!/usr/bin/env python3
"""Fix feedback system in market_seller.py"""
import re

SELLER_FILE = "AryaPremium/plugins/userbot/market_seller.py"

with open(SELLER_FILE, "r", encoding="utf-8") as f:
    content = f.read()

original_len = len(content)

# ── CHANGE 1: Replace the big duplicated feedback block inside _process_text
# with a call to _submit_feedback helper. The old block starts at content_type = "text"
# and ends at the `return` statement.

OLD_FEEDBACK_BLOCK = '''        content_type = "text"
        if message.photo: content_type = "photo"
        elif message.video: content_type = "video"
        elif message.document: content_type = "document"
        from datetime import datetime, timezone as _tz
        fb_doc = {
            "user_id": user_id,
            "bot_id": client.me.id,
            "type": content_type,
            "text": txt,
            "status": "open",
            "created_at": datetime.now(_tz.utc),
            "user_name": f"{message.from_user.first_name or \'\'} {message.from_user.last_name or \'\'}".strip(),
            "username": message.from_user.username or "",
        }
        result = await db.db.premium_feedback.insert_one(fb_doc)
        fb_id = str(result.inserted_id)
        try:
            from config import Config
            admins = list(getattr(Config, \'SUDO_USERS\', None) or getattr(Config, \'OWNER_IDS\', []))
            admin_txt = (
                f"<b>📨 NEW FEEDBACK #{fb_id[:8]}</b>\\n"
                f"<b>User:</b> {fb_doc[\'user_name\']} | <code>{user_id}</code>\\n"
                f"<b>@:</b> @{fb_doc[\'username\'] or \'N/A\'}  |  <b>Type:</b> {content_type}\\n"
                f"<b>Message:</b> {txt[:800]}"
            )
            kb_admin = [[InlineKeyboardButton(f"✅ Resolve #{fb_id[:8]}", callback_data=f"mk#fbresv_{fb_id}"),
                         InlineKeyboardButton(f"💬 Reply", callback_data=f"mk#fbreply_{fb_id}_{user_id}")]]
            if hasattr(db, \'mgmt_client\') and db.mgmt_client:
                for admin_id in admins:
                    try:
                        if content_type == "photo":
                            await db.mgmt_client.send_photo(admin_id, photo=message.photo.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                        elif content_type == "video":
                            await db.mgmt_client.send_video(admin_id, video=message.video.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                        else:
                            await db.mgmt_client.send_message(admin_id, admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        pass
        except Exception:
            pass
        await db.update_user(user_id, {"state": None})
        if lang == \'hi\':
            confirm = "✅ <b>आपका फीडबैक सफलतापूर्वक भेजा गया!</b>\\n<i>हमारी टीम जल्द ही आपसे संपर्क करेगी।</i>"
        else:
            confirm = "✅ <b>Feedback submitted!</b>\\n<i>Our team will review it and get back to you shortly.</i>"
        await message.reply_text(
            confirm,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"« {_sc(\'MAIN MENU\')}", callback_data="mb#main_back")]]),
            parse_mode=enums.ParseMode.HTML
        )
        return'''

NEW_FEEDBACK_BLOCK_IN_TEXT = '''        # Only text feedback — media is handled by _process_media
        await _submit_feedback(client, message, user_id, user, lang, content_type="text", text=txt)
        return'''

if OLD_FEEDBACK_BLOCK in content:
    content = content.replace(OLD_FEEDBACK_BLOCK, NEW_FEEDBACK_BLOCK_IN_TEXT, 1)
    print("CHANGE 1: OK - replaced old feedback block with _submit_feedback call")
else:
    print("CHANGE 1: FAILED - could not find old block, checking manually...")
    # Try to find the key line to confirm file is restored
    if 'content_type = "text"' in content:
        print("  -> Found 'content_type = text' - old block exists but exact match failed")
        print("  -> Skipping this change, will fix manually")
    else:
        print("  -> Block not present at all")

# ── CHANGE 2: Add _submit_feedback helper + _process_media function
# We'll add them right before _process_my_stories function
INSERT_BEFORE = "async def _process_my_stories(client, message):"

NEW_FUNCTIONS = '''async def _submit_feedback(client, message, user_id: int, user: dict, lang: str, content_type: str, text: str):
    """Shared helper: saves feedback to DB and notifies admins. Handles text/photo/video/animation/document."""
    from datetime import datetime, timezone as _tz
    caption_or_text = text or (getattr(message, 'caption', None) or "")
    fb_doc = {
        "user_id": user_id,
        "bot_id": client.me.id,
        "type": content_type,
        "text": caption_or_text,
        "status": "open",
        "created_at": datetime.now(_tz.utc),
        "user_name": f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip(),
        "username": getattr(message.from_user, 'username', '') or "",
    }
    result = await db.db.premium_feedback.insert_one(fb_doc)
    fb_id = str(result.inserted_id)

    # ── Beautiful Admin Notification ──
    uname_str = f"@{fb_doc['username']}" if fb_doc['username'] else "No Username"
    type_icon = {"photo": "🖼", "video": "🎬", "animation": "🎞", "document": "📎"}.get(content_type, "💬")
    admin_txt = (
        f"<b>📨 New Feedback Received</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>👤 User:</b> {fb_doc['user_name']}\n"
        f"<b>🔗 Username:</b> {uname_str}\n"
        f"<b>🆔 User ID:</b> <code>{user_id}</code>\n"
        f"<b>{type_icon} Type:</b> {content_type.title()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>💬 Message:</b>\n"
        f"<blockquote>{caption_or_text[:800] if caption_or_text else '(media only)'}</blockquote>"
    )
    kb_admin = [[
        InlineKeyboardButton("✅ Resolve", callback_data=f"mk#fbresv_{fb_id}"),
        InlineKeyboardButton("💬 Reply", callback_data=f"mk#fbreply_{fb_id}_{user_id}")
    ]]

    try:
        from config import Config
        admins = list(getattr(Config, 'SUDO_USERS', None) or getattr(Config, 'OWNER_IDS', []))
        if hasattr(db, 'mgmt_client') and db.mgmt_client:
            for admin_id in admins:
                try:
                    if content_type == "photo":
                        await db.mgmt_client.send_photo(admin_id, photo=message.photo.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                    elif content_type == "video":
                        await db.mgmt_client.send_video(admin_id, video=message.video.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                    elif content_type == "animation":
                        await db.mgmt_client.send_animation(admin_id, animation=message.animation.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                    elif content_type == "document":
                        await db.mgmt_client.send_document(admin_id, document=message.document.file_id, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                    else:
                        await db.mgmt_client.send_message(admin_id, admin_txt, reply_markup=InlineKeyboardMarkup(kb_admin), parse_mode=enums.ParseMode.HTML)
                except Exception:
                    pass
    except Exception:
        pass

    await db.update_user(user_id, {"state": None})
    if lang == 'hi':
        confirm = "✅ <b>आपका फीडबैक सफलतापूर्वक भेजा गया!</b>\\n<i>हमारी टीम जल्द ही आपसे संपर्क करेगी।</i>"
    else:
        confirm = "✅ <b>Feedback submitted!</b>\\n<i>Our team will review it and get back to you shortly.</i>"
    await message.reply_text(
        confirm,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"« {_sc('MAIN MENU')}", callback_data="mb#main_back")]]),
        parse_mode=enums.ParseMode.HTML
    )


async def _process_media(client, message):
    """Handles photo/video/animation/document messages. Routes media feedback to _submit_feedback."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')

    # If user is in feedback_pending state, route to feedback system
    if user.get("state") == "feedback_pending":
        if message.photo:
            content_type = "photo"
        elif message.video:
            content_type = "video"
        elif message.animation:
            content_type = "animation"
        elif message.document:
            content_type = "document"
        else:
            content_type = "photo"
        caption = getattr(message, 'caption', None) or ""
        await _submit_feedback(client, message, user_id, user, lang, content_type=content_type, text=caption)
        return

    # Otherwise, fall through to screenshot handler (for UPI payment screenshots)
    await _process_screenshot(client, message)


'''

if INSERT_BEFORE in content:
    content = content.replace(INSERT_BEFORE, NEW_FUNCTIONS + INSERT_BEFORE, 1)
    print("CHANGE 2: OK - added _submit_feedback + _process_media functions")
else:
    print("CHANGE 2: FAILED - could not find insertion point")

# Write back
with open(SELLER_FILE, "w", encoding="utf-8") as f:
    f.write(content)

new_len = len(content)
print(f"File size: {original_len} -> {new_len} bytes (+{new_len - original_len})")
print("Done!")
