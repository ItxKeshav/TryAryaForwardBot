"""
Fix the channels display block in settings.py to add:
- Channel count (X/40)
- Sync button
- Search hint message
"""

content = open('plugins/settings.py', 'r', encoding='utf-8').read()

old_channels_block = '''   elif type=="channels":
     buttons = []
     channels = await db.get_user_channels(user_id)
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"settings#editchannels_{channel['chat_id']}")])
     buttons.append([InlineKeyboardButton('Aᴅᴅ Cʜᴀɴɴᴇʟ',
                      callback_data="settings#addchannel"),
                    InlineKeyboardButton('🗑 Mᴜʟᴛɪ-Dᴇʟᴇᴛᴇ',
                      callback_data="settings#ch_multi")])
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ',
                      callback_data="settings#main")])
     await query.message.edit_text(
       "<b><u>My Channels</u></b>\\n\\n<b>you can manage your target chats in here</b>",
       reply_markup=InlineKeyboardMarkup(buttons))'''

new_channels_block = '''   elif type=="channels":
     buttons = []
     channels = await db.get_user_channels(user_id)
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"settings#editchannels_{channel['chat_id']}")])
     ch_count = len(channels)
     buttons.append([InlineKeyboardButton('Add Channel', callback_data="settings#addchannel"),
                     InlineKeyboardButton('Multi-Delete', callback_data="settings#ch_multi"),
                     InlineKeyboardButton('Sync Names', callback_data="settings#ch_sync")])
     buttons.append([InlineKeyboardButton('Back', callback_data="settings#main")])
     await query.message.edit_text(
       f"<b><u>My Channels</u></b>  (<code>{ch_count}/40</code>)\\n\\n"
       "<b>Manage your source / destination chats here.</b>\\n"
       "<i>Tip: Use <b>Sync Names</b> to refresh all channel names from Telegram.</i>",
       reply_markup=InlineKeyboardMarkup(buttons))'''

if old_channels_block in content:
    content = content.replace(old_channels_block, new_channels_block, 1)
    open('plugins/settings.py', 'w', encoding='utf-8').write(content)
    print("SUCCESS: channels block updated")
else:
    print("NOT FOUND - checking partial match...")
    idx = content.find('elif type=="channels":')
    print(repr(content[idx:idx+500]))
