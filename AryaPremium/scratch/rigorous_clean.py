import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False

dedup_signature = "unique_p = []"
dedup_end = "purchases = unique_p"

i = 0
while i < len(lines):
    line = lines[i]
    if "# Deduplicate for UI" in line or dedup_signature in line:
        # Check if we are already in a dedup block
        # Look ahead to see if it's the sequence
        block = []
        found_end = False
        k = i
        while k < len(lines) and not found_end:
            block.append(lines[k])
            if dedup_end in lines[k]:
                found_end = True
            k += 1
        
        if found_end:
            # We found a full block. 
            # Now skip ANY subsequent blocks of the same kind
            new_lines.append("    # Deduplicate for UI\n")
            new_lines.append("    unique_p = []\n")
            new_lines.append("    seen = set()\n")
            new_lines.append("    for p in purchases:\n")
            new_lines.append("        p_id = str(p)\n")
            new_lines.append("        if p_id not in seen:\n")
            new_lines.append("            unique_p.append(p)\n")
            new_lines.append("            seen.add(p_id)\n")
            new_lines.append("    purchases = unique_p\n")
            
            # Skip subsequent blocks
            next_i = k
            while next_i < len(lines):
                next_line = lines[next_i]
                if "# Deduplicate for UI" in next_line or dedup_signature in next_line or "`n" in next_line or next_line.strip() == "":
                    # Check if another full block follows
                    # If it's just garbage like `n# Deduplicate, skip it
                    next_i += 1
                else:
                    break
            i = next_i
            continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Seller.py cleaned rigorously.")
