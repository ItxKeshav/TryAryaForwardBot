import os
import glob
import re

TARGET_MSG = "<i>Process Cancelled Successfully!</i>"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Replace "Cancelled." or "<b>Cancelled.</b>"
    # Matches: "Cancelled.", 'Cancelled', "<b>Cancelled.</b>", etc.
    content = re.sub(
        r'(["\'])(?:<b>)?Cancelled\.?(?:</b>)?\1',
        r'\g<1>' + TARGET_MSG + r'\g<1>',
        content,
        flags=re.IGNORECASE
    )

    # 2. Fix restrictive Cancel checks
    # Replace:
    # if (msg_status.text or "") == "/cancel":
    # if msg.text == "/cancel":
    # if getattr(..., "text", "") == "/cancel":
    # with:
    # if "cancel" in (msg_status.text or "").lower():
    
    # We can match `== "/cancel"` or `== '/cancel'` and change the whole condition to a safer `in` check.
    # Just look for checking against "/cancel". This won't touch other logic because '/cancel' is quite unique.
    
    # Match pattern like: (var.text or "") == "/cancel"
    # Or msg.text.lower() == '/cancel'
    def fix_cancel_cond(m):
        prefix = m.group(1) # e.g. "if " or "elif "
        var_part = m.group(2) # e.g. "(msg.text or "")"
        # we will just do: prefix + '"cancel" in (' + var_part + ' or "").lower()'
        return prefix + '"cancel" in (' + var_part.strip() + ' or " " + str(' + var_part.strip() + ')).lower()'
    
    # Let's use a simpler safe regex that replaces == "/cancel"
    # This specifically targets Pyrogram's text check.
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"/cancel"' in line or "'/cancel'" in line:
            # specifically replace strict equality
            if '==' in line and 'cancel' in line.lower():
                # Extract the variable being compared
                # usually `xxx.text` or `xxx`
                # Let's just blindly replace `xxx == "/cancel"` with `"cancel" in (xxx or "").lower()`
                # A bit risky to regex blindly. Instead let's match exact common patterns
                line = re.sub(r'\(\s*([A-Za-z0-9_]+(?:\[.+?\])?\.text|\w+)\s+or\s+""\s*\)\s*==\s*["\']/cancel["\']', r'"cancel" in (\1 or "").lower()', line)
                line = re.sub(r'\(\s*([A-Za-z0-9_]+(?:\[.+?\])?\.text|\w+)\s+or\s+\'\'\s*\)\s*==\s*["\']/cancel["\']', r'"cancel" in (\1 or "").lower()', line)
                line = re.sub(r'([A-Za-z0-9_]+(?:\[.+?\])?\.text)\s*==\s*["\']/cancel["\']', r'"cancel" in (\1 or "").lower()', line)
                line = re.sub(r'([A-Za-z0-9_]+(?:\[.+?\])?\.text\.lower\(\))\s*==\s*["\']/cancel["\']', r'"cancel" in \1', line)
                lines[i] = line
                
        # Also fix: if "cancel" in msg.text:  -> msg.text could be None!
        # Handled carefully:
        if 'in ' in line and '.text' in line and 'lower()' not in line and '"cancel"' in line.lower():
            # e.g. if "Cancel" in msg.text:
            m = re.search(r'["\']cancel["\']\s+in\s+([a-zA-Z0-9_]+)\.text', line, re.IGNORECASE)
            if m:
                var = m.group(1)
                lines[i] = line.replace(f'in {var}.text', f'in ({var}.text or "").lower()').replace('"Cancel"','"cancel"').replace("'Cancel'","'cancel'")

    content = '\n'.join(lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

for f in glob.glob("plugins/*.py"):
    process_file(f)
