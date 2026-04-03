import os
import glob
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Replace `"cancel" in (X).lower()` with `('cancel' in (X).lower() or 'cᴀɴᴄᴇʟ' in (X).lower() or '⛔' in (X))`
    
    def replacer(m):
        x = m.group(1)
        return f"('cancel' in {x}.lower() or 'cᴀɴᴄᴇʟ' in {x}.lower() or '⛔' in {x})"
        
    content = re.sub(r'\"cancel\"\s*in\s*((?:[A-Za-z0-9_]+(?:\.text)?(?:\s*or\s*(?:\"\"|''))?))\.lower\(\)', replacer, content)

    # Some might use 'cancel' instead of "cancel"
    content = re.sub(r'\'cancel\'\s*in\s*((?:[A-Za-z0-9_]+(?:\.text)?(?:\s*or\s*(?:\"\"|''))?))\.lower\(\)', replacer, content)

    # Note: we need to handle the case where it captured `(msg.text or "")` with the parentheses
    # Let's use a simpler approach:
    # First revert any broken ones if any? No.
    # regex to match `"cancel" in (<variable part>).lower()`
    # Let's just match `"cancel" in <STUFF>.lower()`
    
    def replacer2(m):
        stuff = m.group(1)
        return f"('cancel' in {stuff}.lower() or 'cᴀɴᴄᴇʟ' in {stuff}.lower() or '⛔' in {stuff})"
        
    content = re.sub(r'\"cancel\"\s*in\s*\((.*?)\)\.lower\(\)', replacer2, content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated cancel logic string match in {filepath}")

for f in glob.glob("plugins/*.py"):
    process_file(f)
