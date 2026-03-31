import re

def safe_sc(text):
    out = ""
    in_tag = False
    in_brace = False
    skip_next = False
    for i, c in enumerate(text):
        if skip_next:
            out += c
            skip_next = False
            continue
        if c == '\\':
            out += c
            skip_next = True
            continue
            
        if c == '<': in_tag = True
        if c == '{': in_brace = True
        
        if not in_tag and not in_brace and c.isalpha() and c.isascii():
            out += c.translate(str.maketrans(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
            ))
        else:
            out += c
            
        if c == '>': in_tag = False
        if c == '}': in_brace = False
    return out

with open('plugins/lang.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_triple = False

for line in lines:
    if '"""' in line:
        if line.count('"""') % 2 != 0:
            in_triple = not in_triple
        new_lines.append(line)
        continue
    
    if in_triple:
        new_lines.append(line)
        continue

    def replacer(m):
        return '"' + safe_sc(m.group(1)) + '"'
    
    parts = line.split('#')[0]
    replaced = re.sub(r'"([^"]*)"', replacer, parts)
    
    if '#' in line:
        replaced += '#' + line.split('#', 1)[1]
    
    new_lines.append(replaced)

with open('plugins/lang.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Applied formatting to lang.py")
