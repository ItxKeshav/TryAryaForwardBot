import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i in range(len(lines)):
    line = lines[i]
    # If a line ends with a double quote and a newline, and the next line starts with a newline...
    # Or specifically for the f-strings I broke:
    # 773:             "<b>⟦ 𝗦𝗘𝗟𝗘𝗖𝗧 𝗟𝗔𝗡𝗚𝗨𝗔𝗚𝗘 ⟧</b>
    # 774: 
    # 775: "
    # These should be combined into "<b>...</b>\n\n"
    
    # Let's fix the specific patterns:
    # Pattern 1: Unterminated f" string line
    if line.strip().startswith('f"') and not line.strip().endswith('"') and not '"""' in line:
        # Check if next lines can complete it
        j = i + 1
        combined = line.rstrip('\r\n')
        while j < len(lines) and not combined.endswith('"'):
            combined += "\\n" + lines[j].strip()
            j += 1
        # This is too complex. 
        pass

# SIMPLER APPROACH:
# The regex replacement messed up. I will just re-read the file from the PREVIOUS GOOD STATE if possible?
# I have 'git'.
# But I already made many changes.

# I will use 'git checkout plugins/userbot/market_seller.py' to get the clean file.
# Then I will apply the changes using ONLY replace_file_content (no scripts with re.sub).

with open('restore_v2.bat', 'w') as f:
    f.write('git checkout plugins/userbot/market_seller.py')

os.system('restore_v2.bat')
print("File restored from git. Now applying changes cleanly.")
