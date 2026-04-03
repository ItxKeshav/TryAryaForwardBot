import glob

def replace_if_line(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        # 1. msg.text == "/undo"
        if 'if ' in line and '.text == "/undo":' in line:
            indent = line[:len(line) - len(line.lstrip())]
            var_name = line.split('.text')[0].split('if ')[-1].strip()
            lines[i] = f'{indent}if getattr({var_name}, "text", None) and any(x in {var_name}.text.lower() for x in ["/undo", "undo", "uɴᴅᴏ", "↩️"]): \n'
            
        # 2. if not msg.text or "/cancel" in msg.text:
        elif 'if not ' in line and '.text or "/cancel" in ' in line.lower():
            indent = line[:len(line) - len(line.lstrip())]
            var_name = line.split('.text')[0].split('not ')[-1].strip()
            if var_name:
                lines[i] = f'{indent}if not {var_name}.text or (getattr({var_name}, "text", None) and any(x in {var_name}.text.lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"])): \n'
                
        # 3. if not msg.text or "/cancel" in msg.text.lower():
        elif 'if not ' in line and '.text' in line and '"/cancel"' in line and 'lower()' in line:
            indent = line[:len(line) - len(line.lstrip())]
            match = re.search(r'not (\w+)\.text', line)
            if match:
                var = match.group(1)
                lines[i] = f'{indent}if not {var}.text or (getattr({var}, "text", None) and any(x in {var}.text.lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"])): \n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

for f in glob.glob('plugins/*.py'):
    replace_if_line(f)
