import os
import re
import glob

def fix_undo(directory):
    for f in glob.glob(os.path.join(directory, '*.py')):
        with open(f, 'r', encoding='utf-8') as h:
            content = h.read()
        
        orig = content
        
        # 1. Update Buttons
        content = re.sub(r'KeyboardButton\(\s*["\']/undo["\']\s*\)', 'KeyboardButton("↩️ Uɴᴅᴏ")', content)
        content = re.sub(r'KeyboardButton\(\s*["\']/cancel["\']\s*\)', 'KeyboardButton("⛔ Cᴀɴᴄᴇʟ")', content)
        
        # Array brackets lists: ["/undo", "/cancel"] -> ["↩️ Uɴᴅᴏ", "⛔ Cᴀɴᴄᴇʟ"]
        content = re.sub(r'\[\s*["\']/undo["\']\s*,\s*["\']/cancel["\']\s*\]', '["↩️ Uɴᴅᴏ", "⛔ Cᴀɴᴄᴇʟ"]', content)
        
        # 2. Update checks for msg.text == "/undo"
        # We'll use a robust regex for undo similarly to what we did for cancel.
        content = re.sub(
            r'if\s+\(\w+\.text\s+or\s+""\)\s*==\s*["\']/undo["\']\s*:',
            r'if getattr(\g<0>, "text", None) and any(x in \g<0>.lower() for x in ["/undo", "undo", "↩️"]):',
            content
        )
        content = re.sub(
            r'if\s+["\']/undo["\']\s+in\s+msg\w*\.text\s*:',
            r'if getattr(\g<0>, "text", None) and any(x in \g<0>.lower() for x in ["/undo", "undo", "↩️"]):',
            content
        )
        
        # Specifically target the messy if checks in share_jobs:
        # e.g., if (msg_status.text or "") == "/undo":
        # Let's just do a string replace for those.
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if '== "/undo":' in line and '(msg' in line and '.text' in line:
                # convert `if (msg_foo.text or "") == "/undo":` to `if getattr(msg_foo, "text", None) and any(x in msg_foo.text.lower() for x in ["/undo", "undo", "↩️"]):`
                var_match = re.search(r'\((\w+)\.text', line)
                if var_match:
                    var_name = var_match.group(1)
                    indent = line[:len(line) - len(line.lstrip())]
                    line = f'{indent}if getattr({var_name}, "text", None) and any(x in {var_name}.text.lower() for x in ["/undo", "undo", "uɴᴅᴏ", "↩️"]):'
            if '"/undo" in ' in line and '.text:' in line:
                var_match = re.search(r'in (\w+)\.text', line)
                if var_match:
                    var_name = var_match.group(1)
                    indent = line[:len(line) - len(line.lstrip())]
                    line = f'{indent}if getattr({var_name}, "text", None) and any(x in {var_name}.text.lower() for x in ["/undo", "undo", "uɴᴅᴏ", "↩️"]):'
            new_lines.append(line)
            
        content = '\n'.join(new_lines)
            
        if orig != content:
            with open(f, 'w', encoding='utf-8') as h:
                h.write(content)
            print(f"Fixed undo keys and logic in {f}")

fix_undo('plugins')
