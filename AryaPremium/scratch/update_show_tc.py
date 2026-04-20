import os

file_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\plugins\userbot\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_func = """async def _show_tc(client, user_id, story_id, lang='en'):
    # Use centralized helper for consistent text
    tc_text = _get_tc_text(lang)
    
    # Localized buttons
    accept_btn = "𝗜 𝗔𝗰𝗰𝗲𝗽𝘁" if lang == 'en' else "स्वीकार करें"
    reject_btn = "𝗥𝗲𝗷𝗲𝗰𝘁" if lang == 'en' else "अस्वीकार करें"
    back_btn = "‹ Back" if lang == 'en' else "‹ वापस"
    
    kb = [
        [InlineKeyboardButton(accept_btn, callback_data=f"mb#tc_accept_{story_id}")],
        [InlineKeyboardButton(reject_btn, callback_data="mb#tc_reject"),
         InlineKeyboardButton(back_btn, callback_data=f"mb#view_{story_id}")]
    ]
    from pyrogram import enums
    await client.send_message(user_id, tc_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)
"""

# Find the start of _show_tc and replace until the next definition
import re
start_match = re.search(r'async def _show_tc\(client, user_id, story_id, lang=\'en\'\):', content)
if start_match:
    start_pos = start_match.start()
    # Find the next def or end of file
    next_def = re.search(r'\n(async )?def ', content[start_pos + 20:])
    if next_def:
        end_pos = start_pos + 20 + next_def.start()
    else:
        end_pos = len(content)
        
    final_content = content[:start_pos] + new_func + content[end_pos:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print("Updated _show_tc successfully")
else:
    print("Could not find _show_tc")
