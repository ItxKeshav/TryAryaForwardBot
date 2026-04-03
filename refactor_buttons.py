import os
import re
import unicodedata

sc_map = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
    'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
    'p': 'ᴘ', 'q': 'Q', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
}

unicode_to_ascii = {
    'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ꜰ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'Q': 'q', 'ʀ': 'r', 's': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x', 'ʏ': 'y', 'ᴢ': 'z', 'ꜱ': 's', 'Ʀ': 'r'
}

def is_emoji(char):
    if char in ['❮']: return False
    name = unicodedata.name(char, "")
    if "EMOJI" in name or "SYMBOL" in name or name.startswith("BLACK ") or name.startswith("WHITE ") or name.startswith("HEAVY CHECK"):
        if char == '❮': return False
        if char == ' ' or char == '_': return False
        if char in sc_map.values(): return False
        return True
    cp = ord(char)
    if cp >= 0x1F600 and cp <= 0x1F64F: return True
    if cp >= 0x1F300 and cp <= 0x1F5FF: return True
    if cp >= 0x1F680 and cp <= 0x1F6FF: return True
    if cp >= 0x1F700 and cp <= 0x1F77F: return True
    if cp >= 0x1F780 and cp <= 0x1F7FF: return True
    if cp >= 0x1F800 and cp <= 0x1F8FF: return True
    if cp >= 0x1F900 and cp <= 0x1F9FF: return True
    if cp >= 0x1FA00 and cp <= 0x1FA6F: return True
    if cp >= 0x1FA70 and cp <= 0x1FAFF: return True
    if cp >= 0x2600 and cp <= 0x26FF: return True
    if cp >= 0x2700 and cp <= 0x27BF: return True
    if cp >= 0x2300 and cp <= 0x23FF: return True
    return False

def clean_text(text, remove_emojis=False):
    for c in ['»', '«', '‣', '>', '—']:
        text = text.replace(c, '')
        
    if remove_emojis:
        new_text = []
        for char in text:
            if not is_emoji(char):
                new_text.append(char)
        text = "".join(new_text)
    
    if 'back' in text.lower() or 'ʙᴀᴄᴋ' in text:
        return '❮ Bᴀᴄᴋ'
        
    text = re.sub(r' +', ' ', text)
    return text.strip()

def to_plain_ascii(text):
    res = ""
    for char in text:
        if char in unicode_to_ascii:
            res += unicode_to_ascii[char]
        else:
            res += char.lower() if char.isalpha() and char.isascii() else char
    return res

def to_mixed_small_caps(text):
    text = to_plain_ascii(text)
    words = text.split(' ')
    res = []
    for w in words:
        if not w:
            res.append(w)
            continue
        first_letter = True
        new_w = []
        for char in w:
            if char.isalpha() and char.isascii():
                if first_letter:
                    new_w.append(char.upper())
                    first_letter = False
                else:
                    new_w.append(sc_map.get(char, char))
            else:
                new_w.append(char)
                if not char.isalnum() and char not in ['\'']:
                    first_letter = True
        res.append("".join(new_w))
    return " ".join(res)

def process_file(filepath, remove_emojis=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    def replacer(match):
        prefix = match.group(1)
        qnt = match.group(2)
        text = match.group(3)
        suffix = match.group(4)
        
        if 'back' in text.lower() or 'ʙᴀᴄᴋ' in text:
            return f"{prefix}{qnt}❮ Bᴀᴄᴋ{suffix}"
            
        def process_str(s):
            if '{' in s:
                parts = re.split(r'(\{.*?\})', s)
                for i in range(len(parts)):
                    if not parts[i].startswith('{'):
                        parts[i] = clean_text(parts[i], remove_emojis)
                        parts[i] = to_mixed_small_caps(parts[i])
                return "".join(parts)
            else:
                s = clean_text(s, remove_emojis)
                return to_mixed_small_caps(s)
                
        new_text = process_str(text)
        return f"{prefix}{qnt}{new_text}{suffix}"
        
    new_content = re.sub(r"(InlineKeyboardButton\(\s*)([f]?['\"])(.*?)(['\"]\s*,)", replacer, content)
    
    new_content = re.sub(r'InlineKeyboardButton\("«  " \+ _sc\("❮ Bᴀᴄᴋ"\),\s*callback_data=', r'InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=', new_content)
    new_content = re.sub(r'InlineKeyboardButton\("«  " \+ _sc\("❮ Bᴀᴄᴋ"\),\s*callback_data=', r'InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=', new_content)
    new_content = new_content.replace('InlineKeyboardButton("" + _sᴄ("ᴜᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ"), Uʀʟ=ᴜᴘᴅᴀᴛᴇ_ʟɪɴᴋ)', 'InlineKeyboardButton("Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ", url=UPDATE_LINK)')
    if remove_emojis:
        new_content = new_content.replace('active_mark = "✔️ " if b.get(\'active\') else " "', 'active_mark = "" if b.get(\'active\') else ""')
        new_content = new_content.replace('"{active_mark} {b[\'name\']}"', '"{active_mark}{b[\'name\']}"')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)


files = [
    ('plugins/settings.py', True),
    ('plugins/multijob.py', False),
    ('plugins/jobs.py', False),
    ('plugins/share_jobs.py', False),
    ('plugins/merger.py', False),
    ('plugins/cleanmsg.py', False),
    ('plugins/taskjob.py', False),
    ('plugins/share_bot.py', False),
]

for fp, rm_emo in files:
    if os.path.exists(fp):
        process_file(fp, rm_emo)
        print("Processed", fp)
