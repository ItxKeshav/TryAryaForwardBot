import os
import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 1681 to 1763 (0-indexed: 1680 to 1763)
# Check if it actually contains the dupe
target_start = 1680
target_end = 1763

if "elif cmd == \"noop\":" in lines[1764]:
    print("Noop found at expected location. Deleting dupe block.")
    del lines[target_start:target_end+1]

# Check for more dupes
# Let's perform a general deduplication based on handler start markers
new_lines = []
seen_handlers = set()
i = 0
while i < len(lines):
    line = lines[i]
    # Check for handler start: elif cmd == "...", elif action == "...", etc.
    match = re.search(r'elif (cmd|action) == "([^"]+)"', line)
    if match:
        h_type = match.group(1)
        h_name = match.group(2)
        key = f"{h_type}:{h_name}"
        
        if key in seen_handlers:
            # Skip this block until next handler or end of function
            print(f"Skipping duplicate handler: {key}")
            i += 1
            while i < len(lines):
                if re.search(r'elif (cmd|action) == "', lines[i]) or "async def" in lines[i]:
                    break
                i += 1
            continue
        else:
            seen_handlers.add(key)
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Seller.py final deduplication complete.")
