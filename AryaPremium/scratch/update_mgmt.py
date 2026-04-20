import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\mgmt\\market_mgmt.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_add_story_section = r'''        # Meta Data
        msg_name_en = await native_ask(client, user_id, "<b>❪ STEP 5: STORY NAME ❫</b>\n\nEnter the story name (English):\n<i>(Hindi name will be automatically translated)</i>", reply_markup=cancel_kb)
        if getattr(msg_name_en, 'text', None) and "Cᴀɴᴄᴇʟ" in msg_name_en.text:
            return await client.send_message(user_id, "<i>Cancelled!</i>", reply_markup=ReplyKeyboardRemove())
        
        name_en = (msg_name_en.text or "").strip()
        sj['story_name_en'] = name_en
        
        waiting_msg = await client.send_message(user_id, "⏳ <i>Automatically translating name to Hindi...</i>")
        sj['story_name_hi'] = utils.translate_to_hindi(name_en)
        await waiting_msg.delete()

        msg_img = await native_ask(client, user_id, f"<b>❪ STEP 6: STORY IMAGE ❫</b>\n\n<b>EN:</b> {name_en}\n<b>HI:</b> {sj['story_name_hi']}\n\nSend the cover image for this story:", reply_markup=cancel_kb)
        if getattr(msg_img, 'text', None) and "Cᴀɴᴄᴇʟ" in msg_img.text:
            return await client.send_message(user_id, "<i>Cancelled!</i>", reply_markup=ReplyKeyboardRemove())
        if getattr(msg_img, 'photo', None):
            await client.send_message(user_id, "<i>Uploading image to store bot...</i>")
            try:
                from plugins.userbot.market_seller import market_clients
                store_cli = market_clients.get(str(sj["bot_id"]))
                dl = await client.download_media(msg_img.photo.file_id)
                ul = await store_cli.send_photo(user_id, photo=dl)
                sj['image'] = ul.photo.file_id
                import os; os.remove(dl)
            except Exception as e:
                sj['image'] = msg_img.photo.file_id # fallback
        else:
            sj['image'] = None

        msg_desc = await native_ask(
            client,
            user_id,
            "<b>❪ STEP 7: STORY DESCRIPTION ❫</b>\n\n"
            "<blockquote expandable='true'>"
            "Enter the description/synopsis of the story (English).\n\n"
            "Tip: This will be automatically translated to Hindi."
            "</blockquote>",
            reply_markup=cancel_kb
        )
        if getattr(msg_desc, 'text', None) and "Cᴀɴᴄᴇʟ" in msg_desc.text:
            return await client.send_message(user_id, "<i>Cancelled!</i>", reply_markup=ReplyKeyboardRemove())
        
        desc_en = (msg_desc.text or "None").strip()
        sj['description'] = desc_en
        
        waiting_msg = await client.send_message(user_id, "⏳ <i>Automatically translating description...</i>")
        sj['description_hi'] = utils.translate_to_hindi(desc_en)
        await waiting_msg.delete()'''

# Replace from line 1157 down to 1195 roughly
start_r = -1
end_r = -1
for i, line in enumerate(lines):
    if 'msg_name_en = await native_ask' in line and i > 1100:
        start_r = i
        # find where msg_desc assignment ends
        for j in range(i+1, len(lines)):
            if "sj['description'] =" in lines[j]:
                end_r = j + 1
                break
        break

if start_r != -1 and end_r != -1:
    lines[start_r:end_r] = [new_add_story_section + "\n"]

# Update Name Edit (line 1393)
for i, line in enumerate(lines):
    if 'elif action == "name":' in line:
        lines[i+1] = '            name_hi = utils.translate_to_hindi(msg.text)\n'
        lines[i+2] = '            await db.db.premium_stories.update_one({"_id": s_id_obj}, {"$set": {"story_name_en": msg.text, "story_name_hi": name_hi}})\n'
        break

# Update Desc Edit (line 1413)
for i, line in enumerate(lines):
    if 'elif action == "desc":' in line:
        lines[i+1] = '            desc_hi = utils.translate_to_hindi(msg.text)\n'
        lines[i+2] = '            await db.db.premium_stories.update_one({"_id": s_id_obj}, {"$set": {"description": msg.text, "description_hi": desc_hi}})\n'
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Updated management flow with auto-translation.")
