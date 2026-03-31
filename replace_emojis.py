import os
import re

files = [
    'plugins/share_bot.py',
    'plugins/share_jobs.py',
    'plugins/commands.py',
    'plugins/settings.py',
    'plugins/lang.py'
]

emoji_to_unicode = {
    '🚀': '» ', '💬': '» ', '📜': '» ', '⚙️': '» ', '📋': '» ', 
    '⚡': '» ', '🔗': '» ', '🙋‍♂️': '» ', '💁‍♂️': '» ',
    '📁': '» ', '❓': '» ', '🎥': '» ', '🔔': '» ', '◀️': '« ',
    '✅': '» ', '❌': '‣ ', '⏳': '» ', '📨': '» ', '📢': '» ', 
    '🔒': '‣ ', '✨': '‣ ', '👋': '» ', '🌵': '➤ ', '📚': '» ',
    '➜': '➲ ', '🛡️': '» ', '⚠️': '‣ ', '➕': '» ', '🔙': '« ',
    '📝': '» ', '▶️': '» ', 'ℹ️': '» ', '🔄': '» ', '🗑️': '» ',
    '🗃️': '» ', '📂': '» ', '🔍': '» ', '🤖': '» ', '👤': '» ',
    '✚': '» ', '━': ' ', '👨💻': '» ', '⏱': '» ', '⬇️': '» ',
    '⬆️': '» ', '💾': '» ', '📊': '» ', '📦': '» ', '👨': '» ',
    '🌐': '» ', '🗣️': '» ', '🆕': '» ', '↩': '« ', '🔆': '» ',
    '📌': '» ', '►': '➲ ', '1️⃣': '» ', '2️⃣': '» ', '3️⃣': '» ',
    '4️⃣': '» ', '5️⃣': '» ', '6️⃣': '» ', '📍': '» ', '📄': '» ',
    '⊸': ' ', '◈': ' ', '╭': '', '╰': '', '╮': '', '╯': '',
    '┣': '', '┃': '', '─': '', '❰': '', '❱': '', 
    '✦': '', '💥': '» ', '⚙': '» ', '💬': '» ', '▶': '» ', '🗑': '» '
}

def remove_emojis(text):
    for e, r in emoji_to_unicode.items():
        text = text.replace(e, r)
    return text

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    content = remove_emojis(content)
    content = content.replace('👨‍💻', '» ')
    content = content.replace('Share Batch Links', 'Batch Links')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print('Emojis replaced and Batch Links renamed.')
