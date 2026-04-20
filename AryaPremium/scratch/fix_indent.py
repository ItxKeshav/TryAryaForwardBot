import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the block starting at else: on line 2585
target_line = -1
for i, line in enumerate(lines):
    if line.strip() == 'else:' and i > 2550:
        # Check if child is not indented
        if i + 1 < len(lines) and 'if lang == \'hi\':' in lines[i+2]: # skip comment
             target_line = i
             break

if target_line != -1:
    # Indent lines from target_line + 1 until end of function
    j = target_line + 1
    while j < len(lines) and not lines[j].strip().startswith("except ") and not lines[j].strip().startswith("def "):
        if lines[j].strip():
            lines[j] = "    " + lines[j]
        j += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Indentation fixed.")
