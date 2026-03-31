"""
Comprehensive fix script for all UI issues.
Run this once, then push to GitHub.
"""
import re

# ── 1. FIX share_bot.py (delivery bot) ────────────────────────────────────────
with open('plugins/share_bot.py', 'r', encoding='utf-8') as f:
    sb = f.read()

# Fix _get_base_header: replace the bloated one with a clean "Hey UserName" header
old_header = '''def _get_base_header(user) -> str:
    u_name = user.first_name or "User"
    return (
        f"›› {_sc('Hey')} <a href='tg://user?id={user.id}'>{u_name}</a>\\n"
        
        
        f"\\n"
    )'''

new_header = '''def _get_base_header(user) -> str:
    u_name = user.first_name or "User"
    last = (" " + user.last_name) if getattr(user, "last_name", None) else ""
    return f"›› ʜᴇʏ, <a href=\'tg://user?id={user.id}\'>{u_name}{last}</a>\\n\\n"'''

sb = sb.replace(old_header, new_header)

# Fix the welcome text - simpler, no example text
old_welcome = '''def _get_welcome_text(user, bot_name, custom_wel=None) -> str:
    if custom_wel:
        return format_msg(custom_wel, user)
    return _get_base_header(user) + _sc(
        "I am a permanent file store bot — users can access stored messages\\n"
        "by using a shareable link created for them.\\n\\n"
        "Click a link button from the channel to receive your files directly here.\\n"
        "To know more, click the Help button below."
    )'''

new_welcome = '''def _get_welcome_text(user, bot_name, custom_wel=None) -> str:
    if custom_wel:
        return format_msg(custom_wel, user)
    return (
        _get_base_header(user) +
        f"<b>»  {_sc('Welcome to')} {bot_name}!</b>\\n\\n" +
        _sc(
            "I am a file delivery bot. Tap any link button from the channel "
            "and I will send you the files directly here.\\n\\n"
            "Click Help for more info."
        )
    )'''

sb = sb.replace(old_welcome, new_welcome)

# Fix the cancel button text (had emoji)
sb = sb.replace('"🚫 Dᴏᴡɴʟᴏᴀᴅ Cᴀɴᴄᴇʟʟᴇᴅ."', '"‣  Dᴏᴡɴʟᴏᴀᴅ Cᴀɴᴄᴇʟʟᴇᴅ."')

with open('plugins/share_bot.py', 'w', encoding='utf-8') as f:
    f.write(sb)
print("✅ share_bot.py fixed")

# ── 2. FIX commands.py (main Arya bot) — revert to original emojis, fix menu ──
with open('plugins/commands.py', 'r', encoding='utf-8') as f:
    cmd = f.read()

# Replace the entire _main_buttons function with the original emoji version + only Batch Links
old_main_buttons = '''async def _main_buttons(user_id: int):
    lang = await db.get_language(user_id)
    return [
        [InlineKeyboardButton('»  ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ',   url='https://t.me/MeJeetX')],
        [
            InlineKeyboardButton('»  ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
            InlineKeyboardButton('»  ꜱᴛᴀᴛᴜꜱ',       callback_data='status'),
        ],
        [
            InlineKeyboardButton(_tx(lang, 'btn_help'),  callback_data='help'),
            InlineKeyboardButton(_tx(lang, 'btn_about'), callback_data='about'),
        ],
        [
            InlineKeyboardButton(_tx(lang, 'btn_settings'), callback_data='settings#main'),
            InlineKeyboardButton(_tx(lang, 'btn_jobs'),     callback_data='job#list'),
        ],
        [
            InlineKeyboardButton('»  ᴍᴜʟᴛɪ ᴊᴏʙ',    callback_data='mj#list'),
            InlineKeyboardButton('»  ꜱʜᴀʀᴇ ʙᴀᴛᴄʜ ʟɪɴᴋꜱ', callback_data='sl#start'),
        ],
    ]'''

new_main_buttons = '''async def _main_buttons(user_id: int):
    lang = await db.get_language(user_id)
    return [
        [InlineKeyboardButton('📢 Main Channel',   url='https://t.me/MeJeetX')],
        [
            InlineKeyboardButton('💬 Support Group', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
            InlineKeyboardButton('🔔 Status',         callback_data='status'),
        ],
        [
            InlineKeyboardButton(_tx(lang, 'btn_help'),  callback_data='help'),
            InlineKeyboardButton(_tx(lang, 'btn_about'), callback_data='about'),
        ],
        [
            InlineKeyboardButton(_tx(lang, 'btn_settings'), callback_data='settings#main'),
            InlineKeyboardButton(_tx(lang, 'btn_jobs'),     callback_data='job#list'),
        ],
        [
            InlineKeyboardButton('»  Mᴜʟᴛɪ Jᴏʙ',    callback_data='mj#list'),
            InlineKeyboardButton('»  Bᴀᴛᴄʜ Lɪɴᴋs',  callback_data='sl#start'),
        ],
    ]'''

cmd = cmd.replace(old_main_buttons, new_main_buttons)

# Fix _STATIC_BUTTONS too
old_static = '''_STATIC_BUTTONS = [
    [InlineKeyboardButton('»  ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ',   url='https://t.me/MeJeetX')],
    [
        InlineKeyboardButton('»  ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
        InlineKeyboardButton('»  ꜱᴛᴀᴛᴜꜱ',       callback_data='status'),
    ],
    [
        InlineKeyboardButton('»  ʜᴇʟᴘ',  callback_data='help'),
        InlineKeyboardButton('»  ᴀʙᴏᴜᴛ', callback_data='about'),
    ],
    [
        InlineKeyboardButton('»  ꜱᴇᴛᴛɪɴɢꜱ » ', callback_data='settings#main'),
        InlineKeyboardButton('»  ʟɪᴠᴇ ᴊᴏʙꜱ',    callback_data='job#list'),
    ],
    [
        InlineKeyboardButton('»  ᴍᴜʟᴛɪ ᴊᴏʙ',    callback_data='mj#list'),
        InlineKeyboardButton('»  ꜱʜᴀʀᴇ ʙᴀᴛᴄʜ ʟɪɴᴋꜱ', callback_data='sl#start'),
    ],
]'''

new_static = '''_STATIC_BUTTONS = [
    [InlineKeyboardButton('📢 Main Channel',   url='https://t.me/MeJeetX')],
    [
        InlineKeyboardButton('💬 Support Group', url='https://t.me/+1p2hcQ4ZaupjNjI1'),
        InlineKeyboardButton('🔔 Status',         callback_data='status'),
    ],
    [
        InlineKeyboardButton('🙋 Help',  callback_data='help'),
        InlineKeyboardButton('💁 About', callback_data='about'),
    ],
    [
        InlineKeyboardButton('⚙️ Settings', callback_data='settings#main'),
        InlineKeyboardButton('📋 Live Jobs', callback_data='job#list'),
    ],
    [
        InlineKeyboardButton('»  Mᴜʟᴛɪ Jᴏʙ',   callback_data='mj#list'),
        InlineKeyboardButton('»  Bᴀᴛᴄʜ Lɪɴᴋs', callback_data='sl#start'),
    ],
]'''

cmd = cmd.replace(old_static, new_static)

with open('plugins/commands.py', 'w', encoding='utf-8') as f:
    f.write(cmd)
print("✅ commands.py fixed")

# ── 3. FIX lang.py — broken setlang_cb + fix btn_ keys ──────────────────────
with open('plugins/lang.py', 'r', encoding='utf-8') as f:
    lang = f.read()

# Fix broken setlang_cb (small caps map keys)
old_setlang = '''    label_map = {"ᴇɴ": "ᴇɴɢʟɪꜱʜ 🇺🇸", "ʜɪ": "हिंदी 🇮🇳", "ʜɪɴɢʟɪꜱʜ": "ʜɪɴɢʟɪꜱʜ » "}
    await query.answer(f"ʟᴀɴɢᴜᴀɢᴇ ꜱᴇᴛ ᴛᴏ {label_map[lang]}!", show_alert=False)
    await query.message.edit_text(
        _tx(lang, "ʟᴀɴɢ_ꜱᴇᴛ"),
        reply_markup=_lang_keyboard(lang)
    )'''

new_setlang = '''    label_map = {"en": "English 🇺🇸", "hi": "हिंदी 🇮🇳", "hinglish": "Hinglish"}
    label = label_map.get(lang, lang)
    await query.answer(f"Language set to {label}!", show_alert=False)
    await query.message.edit_text(
        _tx(lang, "lang_set"),
        reply_markup=_lang_keyboard(lang)
    )'''

lang = lang.replace(old_setlang, new_setlang)

# Fix btn_ keys to use proper strings
lang = lang.replace(
    '_S["btn_settings"] = {"en": "»  Settings", "hi": "»  सेटिंग्स", "hinglish": "»  Settings"}',
    '_S["btn_settings"] = {"en": "⚙️  Settings", "hi": "⚙️  सेटिंग्स", "hinglish": "⚙️  Settings"}'
)
lang = lang.replace(
    '_S["btn_jobs"] = {"en": "»  Lɪᴠᴇ Jᴏʙs", "hi": "»  लाइव जॉब्स", "hinglish": "»  Lɪᴠᴇ Jᴏʙs"}',
    '_S["btn_jobs"] = {"en": "📋  Live Jobs", "hi": "📋  लाइव जॉब्स", "hinglish": "📋  Live Jobs"}'
)
lang = lang.replace(
    '_S["btn_help"] = {"en": "»  Help", "hi": "»  संसथान", "hinglish": "»  Help"}',
    '_S["btn_help"] = {"en": "🙋  Help", "hi": "🙋  संसथान", "hinglish": "🙋  Help"}'
)
lang = lang.replace(
    '_S["btn_about"] = {"en": "»  About", "hi": "»  बारे में", "hinglish": "»  About"}',
    '_S["btn_about"] = {"en": "💁  About", "hi": "💁  बारे में", "hinglish": "💁  About"}'
)

with open('plugins/lang.py', 'w', encoding='utf-8') as f:
    f.write(lang)
print("✅ lang.py fixed")

# ── 4. RESTORE emojis in jobs.py and multijob.py ────────────────────────────
for fname in ['plugins/jobs.py', 'plugins/multijob.py']:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()

    # Restore job status emojis that were stripped
    content = content.replace(
        '"running": "🟢", "stopped": "🔴", "error": "‣ "',
        '"running": "🟢", "stopped": "🔴", "error": "❌"'
    )
    # Restore live job progress message emojis
    content = content.replace(
        '"» " if current_lang == code else ""',
        '"✅ " if current_lang == code else ""'
    )
    # Restore "✅ Multi Job Complete!" text
    content = content.replace(
        'f"» ✅\\"',
        'f"  ✅\\"'
    )
    # Restore jobs check marks in empty list
    content = content.replace(
        '"»  All source types (public, private, DMs, topics)\\n"',
        '"✅ All source types (public, private, DMs, topics)\\n"'
    )
    content = content.replace(
        '"»  Dual destinations\\n"',
        '"✅ Dual destinations\\n"'
    )
    content = content.replace(
        '"»  Multiple jobs run simultaneously\\n"',
        '"✅ Multiple jobs run simultaneously\\n"'
    )
    content = content.replace(
        '"»  Pause / Resume support\\n"',
        '"✅ Pause / Resume support\\n"'
    )
    content = content.replace(
        '"»  Survives bot restarts\\n\\n"',
        '"✅ Survives bot restarts\\n\\n"'
    )
    content = content.replace(
        '"»  Batch mode: copy old messages first, then watch live\\n"',
        '"✅ Batch mode: copy old messages first, then watch live\\n"'
    )
    content = content.replace(
        '"»  Dual destinations: send to 2 channels simultaneously\\n"',
        '"✅ Dual destinations: send to 2 channels simultaneously\\n"'
    )
    content = content.replace(
        '"»  Per-job size limit\\n\\n"',
        '"✅ Per-job size limit\\n\\n"'
    )
    content = content.replace(
        '"»  Create your first job below!"',
        '"👇 Create your first job below!"'
    )
    content = content.replace(
        '"»  Create your first Multi Job below!"',
        '"👇 Create your first Multi Job below!"'
    )
    # Restore green/red dots in status lines  
    content = content.replace(
        '"»  ✅\\"', '"  ✅\\"'
    )
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ jobs.py + multijob.py emoji restored")

# ── 5. FIX _mj_emoji to use proper emojis ─────────────────────────────────────
with open('plugins/multijob.py', 'r', encoding='utf-8') as f:
    mj = f.read()

old_emoji = '''    return {
        "running": "🟢", "paused": "⏸",
        "stopped": "🔴", "done": "✅", "error": "‣ "
    }.get(status, "» ")'''

new_emoji = '''    return {
        "running": "🟢", "paused": "⏸",
        "stopped": "🔴", "done": "✅", "error": "❌"
    }.get(status, "⭘")'''

mj = mj.replace(old_emoji, new_emoji)

with open('plugins/multijob.py', 'w', encoding='utf-8') as f:
    f.write(mj)

print("✅ multijob emoji fixed")

# ── 6. FIX jobs.py _status_emoji ─────────────────────────────────────────────
with open('plugins/jobs.py', 'r', encoding='utf-8') as f:
    jb = f.read()

old_status = '    return {"running": "🟢", "stopped": "🔴", "error": "‣ "}.get(status, "» ")'
new_status = '    return {"running": "🟢", "stopped": "🔴", "error": "❌"}.get(status, "⭘")'
jb = jb.replace(old_status, new_status)

with open('plugins/jobs.py', 'w', encoding='utf-8') as f:
    f.write(jb)

print("✅ jobs.py status emoji fixed")

print("\n✅ All fixes applied!")
