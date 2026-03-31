import re

def to_smallcaps(text):
    return text.translate(str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
    ))

files = [
    'plugins/share_bot.py',
    'plugins/share_jobs.py',
    'plugins/commands.py',
    'plugins/settings.py',
    'plugins/lang.py',
    'plugins/multijob.py',
    'plugins/taskjob.py',
    'plugins/jobs.py'
]

def format_inline_button(m):
    # m.group(1) is the string content (e.g. '» Main Channel')
    original = m.group(1)
    if '{' in original or '\"' in original:
        return f"InlineKeyboardButton({original}"
    new_text = to_smallcaps(original)
    return f"InlineKeyboardButton({new_text}"

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # regex for InlineKeyboardButton('some string', or InlineKeyboardButton("some string",
    content = re.sub(r'InlineKeyboardButton\s*\(\s*([\'"][^\'"]*[\'"])', format_inline_button, content)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print('Button texts small-capped.')
