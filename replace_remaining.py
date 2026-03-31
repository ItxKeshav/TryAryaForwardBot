import os

files = ['plugins/multijob.py', 'plugins/taskjob.py', 'plugins/jobs.py', 'plugins/broadcast.py', 'main.py']

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
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = remove_emojis(file.read())
            content = content.replace('👨‍💻', '» ')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

print('Emojis processed in remaining files.')
