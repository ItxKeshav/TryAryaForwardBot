import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to catch the repeated blocks regardless of minor variations in spacing/newlines
pattern = r'(    # Deduplicate for UI.*?purchases = unique_p\s*)+'
clean_code = '''    # Deduplicate for UI
    unique_p = []
    seen = set()
    for p in purchases:
        p_id = str(p)
        if p_id not in seen:
            unique_p.append(p)
            seen.add(p_id)
    purchases = unique_p
'''

# Use sub to replace all occurrences of the pattern with just one block
# We do it cautiously.
new_content = re.sub(pattern, clean_code, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Seller.py cleaned from redundant deduplication blocks.")
