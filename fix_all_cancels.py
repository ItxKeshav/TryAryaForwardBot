import os, re, glob

# Regex patterns that identify a cancellation check
CANCEL_CHECKS_REGEX = [
    r'if\s+["\']/cancel["\']\s+in\s+(\w+)\.text(?:\.lower\(\))?\s*:',
    r'if\s+(\w+)\.text\s+and\s+(\w+)\.text\.strip\(\)(?:\.lower\(\))?\s*(?:in|==)\s*(?:\([^\)]*["\']/cancel["\'][^\)]*\)|["\']/cancel["\'])\s*:',
    r'if\s+getattr\((\w+),\s*["\']text["\'],\s*["\']["\']\)\s+and\s+str\((\w+)\.text\)\.strip\(\)\s*==\s*["\']/cancel["\']\s*:',
    r'if\s+["\']/cancel["\']\s+in\s+\(([\w\.]+)\s+or\s+["\']["\']\)\s*:',
    r'if\s+["\']/cancel["\']\s+not\s+in\s+(\w+)\.text\.lower\(\)\s*:',
    r'if\s+["\']⛔["\']\s+in\s+(\w+)\s+or\s+["\']Cᴀɴᴄᴇʟ["\']\s+in\s+(\w+)\s+or\s+(\w+)\.startswith\([^)]+\)\s*:',
]

CANCEL_REPLACEMENT = r'if getattr(\g<1>, "text", None) and any(x in str(\g<1>.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):'

for f in glob.glob('plugins/*.py'):
    with open(f, 'r', encoding='utf-8') as h:
        content = h.read()
    orig = content
    
    # 1. First, replace any remaining Inline keyboards /cancel with "⛔ Cᴀɴᴄᴇʟ" 
    # (actually /cancel in reply keyboard was already replaced, except array combinations like ["/cancel"] or ["skip", "/cancel"]
    content = re.sub(r'\[\s*["\']/cancel["\']\s*\]', '["⛔ Cᴀɴᴄᴇʟ"]', content)
    content = re.sub(r'KeyboardButton\(\s*["\']/cancel["\']\s*\)', 'KeyboardButton("⛔ Cᴀɴᴄᴇʟ")', content)
    
    # Let's cleanly replace the exact patterns of `if "/cancel" in txt:` with the robust one:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        # Clean msg cancel:
        if 'if "/cancel" in' in line and '.text' in line:
            # find variable name before .text
            match = re.search(r'in\s+([a-zA-Z0-9_]+)\.text', line)
            if match:
                var = match.group(1)
                indent = line[:len(line) - len(line.lstrip())]
                lines[i] = f'{indent}if getattr({var}, "text", None) and any(x in str({var}.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):'
        
        # if r.text and r.text.strip() == "/cancel"
        elif '== "/cancel"' in line or 'in ("/cancel", "cancel")' in line:
            match = re.search(r'([a-zA-Z0-9_]+)\.text', line)
            if match:
                var = match.group(1)
                indent = line[:len(line) - len(line.lstrip())]
                if 'not in' in line or '!=' in line:
                    lines[i] = f'{indent}if not (getattr({var}, "text", None) and any(x in str({var}.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"])):'
                else:
                    lines[i] = f'{indent}if getattr({var}, "text", None) and any(x in str({var}.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):'

    content = "\n".join(lines)
    
    if orig != content:
        with open(f, 'w', encoding='utf-8') as h:
            h.write(content)
        print(f"Fixed unprotected cancels in {f}")
