import sys
try:
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    buttons.append([InlineKeyboardButton('Aᴅᴅ Cʜᴀɴɴᴇʟ', callback_data='settings#addchannel'),
                    InlineKeyboardButton('Mᴜʟᴛɪ-Dᴇʟᴇᴛᴇ', callback_data='settings#ch_multi'),
                    InlineKeyboardButton('Sʏɴᴄ Nᴀᴍᴇs', callback_data='settings#ch_sync')])
    InlineKeyboardMarkup(buttons)
    print('OK')
except ImportError:
    pass
except Exception as e:
    print('Error:', type(e).__name__, str(e))
