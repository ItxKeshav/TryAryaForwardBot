import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_process_callback_header = r'''async def _process_callback(client, query):
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    data = query.data.split('#')
    cmd = data[1]

    # ── Joined Check ──
    if cmd == "joined_check":
        try:
            from pyrogram import enums
            chat_member = await client.get_chat_member("@AryaPremiumTG", user_id)
            if chat_member.status not in (enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT):
                msg = "✓ Joined Success!" if lang == 'en' else "✓ आपने सफलतापूर्वक ज्वाइन कर लिया है!"
                await query.answer(msg, show_alert=True)
                try: await query.message.delete()
                except: pass
                return await _send_main_menu(client, user_id, query.from_user, lang)
            else:
                msg = "Aapne abhi tak join nahi kiya hai। Kripya join karein aur phir check karein।" if lang == 'hi' else "You haven't joined yet. Please join the channel first."
                return await query.answer(msg, show_alert=True)
        except Exception:
            return await query.answer("Error checking status. Make sure you joined.", show_alert=True)
'''

# Find _process_callback
for i, line in enumerate(lines):
    if line.strip().startswith("async def _process_callback"):
        # Replace the first 6 lines of the function (header)
        lines[i:i+6] = [new_process_callback_header + "\n"]
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Restored joined_check handler to _process_callback.")
