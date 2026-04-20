import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I'll just fix the broken f-strings globally by replacing the literal newline + " with \n"
# Actually, that's risky. 

# Let's just fix the specific blocks using exact string matching.

# Fixing _show_story_details block
old_txt_block = r'''    txt = (
        f"<b>{checkout_title}</b>
"
        f"────────────────────
"
        f"<b>{item_label}</b> {name}
"
        f"<b>{amount_label}</b> ₹{price}
"
        f"────────────────────
"
        f"<b>{desc_title}</b>
"
        f"<blockquote expandable>{desc_content}</blockquote>
"
        f"────────────────────
"
        f"<i>{instruction}</i>"
    )'''

new_txt_block = r'''    txt = (
        f"<b>{checkout_title}</b>\n"
        f"────────────────────\n"
        f"<b>{item_label}</b> {name}\n"
        f"<b>{amount_label}</b> ₹{price}\n"
        f"────────────────────\n"
        f"<b>{desc_title}</b>\n"
        f"<blockquote expandable>{desc_content}</blockquote>\n"
        f"────────────────────\n"
        f"<i>{instruction}</i>"
    )'''

content = content.replace(old_txt_block, new_txt_block)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Manually fixed the unterminated string literal.")
