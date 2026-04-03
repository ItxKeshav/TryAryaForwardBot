import os
import re
import glob

sc_map = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ',
    'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ',
    'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ',
    'p': 'ᴘ', 'q': 'Q', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ',
    'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ',
    'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ',
    'P': 'ᴘ', 'Q': 'Q', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
    'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ',
}

# The user wants "Back" button ONLY to be replaced by "❮ Bᴀᴄᴋ"
# For settings buttons, remove emojis and '>' '»', '«', '‣'
# For Multi Job, Live Job, Batch Links, Merger Mode -> keep emojis, apply small caps, remove '>' '»', '‣'.

def clean_text(text, remove_emojis=False):
    # Remove '»', '«', '‣', '>'
    for c in ['»', '«', '‣', '>', '—']:
        text = text.replace(c, '')
        
    if remove_emojis:
        # Simple heuristic to remove unicode symbols that act like emojis or bullets
        new_text = []
        for char in text:
            if ord(char) < 127: # ascii
                new_text.append(char)
            elif char in sc_map.values(): # small caps
                new_text.append(char)
            elif char in ['❮', ' ']: # allow specific unicode 
                new_text.append(char)
            # Remove high surrogates / emojis
        text = "".join(new_text)
    
    # squeeze out double spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def to_mixed_small_caps(text):
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
                if char in ['-', '_', '[']:
                    first_letter = True
        res.append("".join(new_w))
    return " ".join(res)

import ast

def process_file(filepath, remove_emojis_flag):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will do regex replacement on literal strings inside InlineKeyboardButton
    # Regex pattern: (InlineKeyboardButton\(\s*)(f?(["']))(.*?)(["'])(\s*,\s*callback_data=|\s*,\s*url=)
    # Wait, the 1st argument can be single string or f-string.
    # It's better to just do line-by-line regex if it matches InlineKeyboardButton.
    
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if "InlineKeyboardButton(" in line:
            # check string literal
            # find first string literal inside InlineKeyboardButton
            match = re.search(r'(InlineKeyboardButton\(\s*)(f?["\'])(.*?)(["\'])(\s*,)', line)
            
            if match:
                prefix = match.group(1)
                qnt = match.group(2) # quote type or f"
                text = match.group(3)
                qnt2 = match.group(4)
                suffix = match.group(5)
                
                # Check if it's the "Back" button globally
                if 'back' in text.lower() or '❮ ʙᴀᴄᴋ' in text.lower():
                    # entirely replace with ❮ Bᴀᴄᴋ
                    cleaned = clean_text("❮ Bᴀᴄᴋ", remove_emojis=True)
                    line = line[:match.start()] + prefix + qnt + cleaned + qnt2 + suffix + line[match.end():]
                else:
                    # check if the text contains {var} for f-strings
                    # we should not parse inside {}
                    # But replacing letters around {} is fine.
                    
                    def repl_non_f(m):
                        s = m.group(1)
                        if '{' in s or '}' in s:
                            return s # better to skip f-string formatting if it contains {
                        
                        s = clean_text(s, remove_emojis=remove_emojis_flag)
                        s = to_mixed_small_caps(s)
                        return s
                    
                    if '{' in text and qnt.startswith('f'):
                        # Process parts outside of {}
                        parts = re.split(r'(\{.*?\})', text)
                        for i in range(len(parts)):
                            if not parts[i].startswith('{'):
                                parts[i] = clean_text(parts[i], remove_emojis=remove_emojis_flag)
                                parts[i] = to_mixed_small_caps(parts[i])
                        new_text = "".join(parts)
                    else:
                        new_text = clean_text(text, remove_emojis=remove_emojis_flag)
                        new_text = to_mixed_small_caps(new_text)

                    line = line[:match.start()] + prefix + qnt + new_text + qnt2 + suffix + line[match.end():]
        new_lines.append(line)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))


print("Testing regex on line")
test_line = 'InlineKeyboardButton("«  " + _sc("❮ Bᴀᴄᴋ"), callback_data="sbd#back")'
match = re.search(r'(InlineKeyboardButton\(\s*)(.*?)(,\s*(callback_data|url)=)', test_line)
if match:
    # Actually if there is a variable concatenating like "«  " + _sc("...") it's trickier.
    print(match.groups())

