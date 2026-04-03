import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    lines = content.split('\n')

    # We need to find lines like:
    # if ('cancel' in msg_status.text or "".lower() or 'cᴀɴᴄᴇʟ' in ...): return await bot.send_message(...)
    # or
    # if ("cancel" in ...):
    #     return await bot.send_message(...)
    
    # Actually, the error introduced is exactly:
    # `('cancel' in msg_status.text or "".lower() or 'cᴀɴᴄᴇʟ' in msg_status.text or "".lower() or '⛔' in msg_status.text or "")`
    
    # We can match `if ('cancel' in <VAR>.text or "".lower() or 'cᴀɴᴄᴇʟ' in <VAR>.text or "".lower() or '⛔' in <VAR>.text or ""):`
    
    def replacer(m):
        var = m.group(1)
        # We need a strictly safe boolean expression:
        # `if var and getattr(var, "text", None) and any(x in var.text.lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔"]):`
        # But `var` might just be `msg_status`.
        return f"if getattr({var}, 'text', None) and any(x in {var}.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):"
        
    for i, line in enumerate(lines):
        # Match the broken regex insertion:
        m = re.search(r"if\s*\(\'cancel\'\s*in\s*([a-zA-Z0-9_]+)\.text\s*or\s*\"\"\.lower\(\).*?\):", line)
        if m:
            lines[i] = line[:m.start()] + replacer(m) + line[m.end():]
            continue
            
        m2 = re.search(r"elif\s*\(\'cancel\'\s*in\s*([a-zA-Z0-9_]+)\.text\s*or\s*\"\"\.lower\(\).*?\):", line)
        if m2:
            var = m2.group(1)
            new_cond = f"elif getattr({var}, 'text', None) and any(x in {var}.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):"
            lines[i] = line[:m2.start()] + new_cond + line[m2.end():]
            continue
            
        # Match my first script's broken output on `share_jobs.py:53`
        # `if not msg.text or ('cancel' in msg.text or "".lower() or ...):`
        # This one is tricky. Let's just fix the `('cancel' in VAR.text or "".lower() ...)` substring everywhere.
        
        # Substring replacement for the specific broken chunk:
        broken_chunk_match = re.search(r"\(\'cancel\'\s*in\s*([a-zA-Z0-9_]+)\.text\s*or\s*\"\"\.lower\(\)\s*or\s*\'cᴀɴᴄᴇʟ\'\s*in\s*[a-zA-Z0-9_]+\.text\s*or\s*\"\"\.lower\(\)\s*or\s*\'⛔\'\s*in\s*[a-zA-Z0-9_]+\.text\s*or\s*\"\"\)", line)
        if broken_chunk_match:
            var = broken_chunk_match.group(1)
            safe_expr = f"(getattr({var}, 'text', None) and any(x in {var}.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']))"
            lines[i] = line[:broken_chunk_match.start()] + safe_expr + line[broken_chunk_match.end():]

    content = '\n'.join(lines)
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed crashes in {filepath}")

for f in glob.glob("plugins/*.py"):
    process_file(f)
