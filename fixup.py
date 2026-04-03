import os, re
path = r'plugins\settings.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

def fix_line(match):
    middle = match.group(0)
    new_middle = middle.replace('Iꜰ', 'if').replace('Eʟsᴇ', 'else')
    new_middle = new_middle.replace('Fɪʟᴛᴇʀs', 'filters').replace('Fɪʟᴛᴇʀ', 'filter')
    new_middle = new_middle.replace("['Fᴏʀᴡᴀʀᴅ_Tᴀɢ']", "['forward_tag']")
    new_middle = new_middle.replace("['Tᴇxᴛ']", "['text']")
    new_middle = new_middle.replace("['Dᴏᴄᴜᴍᴇɴᴛ']", "['document']")
    new_middle = new_middle.replace("['Vɪᴅᴇᴏ']", "['video']")
    new_middle = new_middle.replace("['Pʜᴏᴛᴏ']", "['photo']")
    new_middle = new_middle.replace("['Aᴜᴅɪᴏ']", "['audio']")
    new_middle = new_middle.replace("['Vᴏɪᴄᴇ']", "['voice']")
    new_middle = new_middle.replace("['Aɴɪᴍᴀᴛɪᴏɴ']", "['animation']")
    new_middle = new_middle.replace("['Sᴛɪᴄᴋᴇʀ']", "['sticker']")
    new_middle = new_middle.replace("['Dᴜᴘʟɪᴄᴀᴛᴇ']", "['duplicate']")
    new_middle = new_middle.replace("'' if", "'[ ON ]' if")
    new_middle = new_middle.replace("else ''", "else '[ OFF ]'")
    return new_middle

fixed_text = re.sub(r"InlineKeyboardButton\(''.*?Eʟsᴇ '',", fix_line, text)

# Just in case some others are messed up like: InlineKeyboardButton(' [V] ' Iꜰ ...
def fix_line2(match):
    middle = match.group(0)
    new_middle = middle.replace('Iꜰ', 'if').replace('Eʟsᴇ', 'else')
    new_middle = new_middle.replace('Fɪʟᴛᴇʀs', 'filters').replace('Fɪʟᴛᴇʀ', 'filter')
    return new_middle
fixed_text = re.sub(r"InlineKeyboardButton\('.*?' Iꜰ .*? Eʟsᴇ '.*?',", fix_line2, fixed_text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(fixed_text)
print("Done")
