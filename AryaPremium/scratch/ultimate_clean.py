import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
last_added_block_idx = -100

# Signature lines of the bloat block
signatures = [
    "unique_p = []",
    "seen = set()",
    "for p in purchases:",
    "p_id = str(p)",
    "if p_id not in seen:",
    "unique_p.append(p)",
    "seen.add(p_id)",
    "purchases = unique_p",
    "# Deduplicate for UI"
]

i = 0
while i < len(lines):
    line = lines[i].strip()
    is_bloat = any(sig in line for sig in signatures)
    
    if is_bloat:
        # Check if we should allow this bloat line
        # We allow it if it's the first one in a long time OR if it's part of a legit block we want to keep one of.
        # Actually, let's just keep ONE full block per function.
        
        # Simple heuristic: if we see more than 3 bloat lines in 5 lines, it's a bloat zone.
        lookahead = lines[i:i+10]
        bloat_count = sum(1 for l in lookahead if any(sig in l for sig in signatures))
        
        if bloat_count > 3:
            # We are in a bloat zone.
            # Have we added a clean version recently?
            if i - last_added_block_idx > 50:
                # Add ONE clean block
                indent = "    "
                new_lines.append(f"{indent}# Deduplicate for UI\n")
                new_lines.append(f"{indent}unique_p = []\n")
                new_lines.append(f"{indent}seen = set()\n")
                new_lines.append(f"{indent}for p in purchases:\n")
                new_lines.append(f"{indent}    p_id = str(p)\n")
                new_lines.append(f"{indent}    if p_id not in seen:\n")
                new_lines.append(f"{indent}        unique_p.append(p)\n")
                new_lines.append(f"{indent}        seen.add(p_id)\n")
                new_lines.append(f"{indent}purchases = unique_p\n")
                last_added_block_idx = i
            
            # Skip until we exit the bloat zone
            k = i
            while k < len(lines):
                if any(sig in lines[k] for sig in signatures) or lines[k].strip() == "":
                    k += 1
                else:
                    break
            i = k
            continue

    new_lines.append(lines[i])
    i += 1

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Seller.py cleaned and restored.")
