import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Update _show_story_profile for description localization
for i, line in enumerate(lines):
    if "desc = story.get('description', '').strip()" in line:
        lines[i] = "    desc = story.get(f'description_{lang}', story.get('description', '')).strip()\n"
        break

# 2. Update _process_callback for deduplication and language cleaning
# In my_buys block
start_b = -1
end_b = -1
for i, line in enumerate(lines):
    if 'elif cmd == "my_buys" or cmd.startswith("my_buys_page_"):' in line:
        start_b = i
        # find where it ends
        for j in range(i+1, len(lines)):
            if 'await _safe_edit(query.message, text=txt_b, markup=InlineKeyboardMarkup(kb))' in lines[j]:
                end_b = j + 1
                break
        break

new_my_buys = r'''    elif cmd == "my_buys" or cmd.startswith("my_buys_page_"):
        await query.answer()
        raw_purchases = user.get('purchases', [])
        from bson.objectid import ObjectId
        p_oids = []
        for p in raw_purchases:
            try: p_oids.append(ObjectId(p))
            except: pass
        
        valid_stories_cursor = db.db.premium_stories.find({"_id": {"$in": p_oids}})
        valid_stories = await valid_stories_cursor.to_list(length=1000)
        valid_ids_set = {str(s['_id']) for s in valid_stories}
        
        # DEDUPLICATION: Ensure one entry per unique story ID
        purchases = []
        seen = set()
        for p in raw_purchases:
            pid_str = str(p)
            if pid_str in valid_ids_set and pid_str not in seen:
                purchases.append(p)
                seen.add(pid_str)
        purchases.reverse()

        PAGE_SIZE = 5
        page = 0
        if cmd.startswith("my_buys_page_"):
            try: page = int(cmd.replace("my_buys_page_", ""))
            except: page = 0

        total = len(purchases)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        page_purchases = purchases[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

        kb = []
        for pid in page_purchases:
            try:
                st = next((s for s in valid_stories if str(s['_id']) == str(pid)), None)
                if st:
                    name_en = st.get('story_name_en', 'Story')
                    name_hi = st.get('story_name_hi', name_en)
                    # CLEAN DISPLAY: Only show the selected language version
                    s_name = f"📖 {name_hi if lang == 'hi' else name_en}"
                    kb.append([InlineKeyboardButton(s_name, callback_data=f"mb#purchased_view_{pid}")])
            except Exception: pass

        if lang == 'hi':
            title, total_txt, desc = "⟦ मेरी स्टोरीज ⟧", "कुल स्टोरी ⟶", "आपके अकाउंट में मौजूद सभी स्टोरीज नीचे दी गई हैं।"
            next_btn, prev_btn, back_btn = "आगे ❭", "❬ पीछे", "« वापस मेनू"
            empty_txt, market_btn_l = "कोई खरीद नहीं मिली।", "स्टोर खोलें"
        else:
            title, total_txt, desc = "⟦ 𝗠𝗬 𝗦𝗧𝗢𝗥𝗜𝗘𝗦 ⟧", "ᴛᴏᴛᴀʟ ⟶", "𝖠𝗅𝗅 𝗌𝗍𝗈𝗋𝗂𝖾𝗌 𝗅𝗂𝗌𝗍𝖾𝖽 𝖻𝖾𝗅𝗈𝗐 𝖺𝗋𝖾 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝗈𝗇 𝗒𝗈𝗎𝗋 𝖺𝖼𝖼𝗈𝗎𝗇ᴛ."
            next_btn, prev_btn, back_btn = "𝗡𝗲𝘅𝘁 ❭", "❬ 𝗣𝗿𝗲𝘃", _sc("BACK")
            empty_txt, market_btn_l = "ɴᴏ ᴘᴜʀᴄʜᴀꜱᴇꜱ ꜰᴏᴜɴᴅ.", _sc("OPEN MARKETPLACE")

        if total_pages > 1:
            nav = []
            if page > 0: nav.append(InlineKeyboardButton(prev_btn, callback_data=f"mb#my_buys_page_{page - 1}"))
            nav.append(InlineKeyboardButton(f"ᴘᴀɢᴇ {page + 1}/{total_pages}", callback_data="mb#noop"))
            if page < total_pages - 1: nav.append(InlineKeyboardButton(next_btn, callback_data=f"mb#my_buys_page_{page + 1}"))
            kb.append(nav)
        kb.append([InlineKeyboardButton(back_btn, callback_data="mb#main_back")])

        txt_b = f"<b>{title}</b>\n\n<b>{total_txt}</b> {total}\n\n{desc}" if total > 0 else f"<b>{title}</b>\n\n<b>{total_txt}</b> 0\n\n{empty_txt}"
        if total == 0: kb.insert(0, [InlineKeyboardButton(market_btn_l, callback_data="mb#main_marketplace")])
        await _safe_edit(query.message, text=txt_b, markup=InlineKeyboardMarkup(kb))'''

if start_b != -1 and end_b != -1:
    lines[start_b:end_b] = [new_my_buys + "\n"]

# 3. Update purchased_view_ localization
start_v = -1
end_v = -1
for i, line in enumerate(lines):
    if 'elif cmd.startswith("purchased_view_"):' in line:
        start_v = i
        for j in range(i+1, len(lines)):
            if 'await _safe_edit(query.message, text=txt_req, markup=InlineKeyboardMarkup(kb))' in lines[j]:
                end_v = j + 1
                break
        break

new_purchased_view = r'''    elif cmd.startswith("purchased_view_"):
        s_id = data[2] if len(data) > 2 else cmd.replace("purchased_view_", "")
        await query.answer()
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if story:
            purchase = await db.db.premium_purchases.find_one({"user_id": int(user_id), "story_id": ObjectId(s_id)})
            
            s_name = story.get(f'story_name_{lang}', story.get('story_name_en'))
            ep_count = abs(story.get('end_id', 0) - story.get('start_id', 0)) + 1 if story.get('end_id') else "?"

            # Clean payment label
            payment_label = "Verified"
            if purchase:
                src = str(purchase.get("source", "manual")).lower()
                amount_paid = purchase.get("amount", story.get('price', 0))
                payment_label = {
                    "razorpay":   f"Razorpay (₹{amount_paid})",
                    "easebuzz":   f"Easebuzz (₹{amount_paid})",
                    "upi":        f"Manual UPI (₹{amount_paid})",
                    "manual_upi": f"Manual UPI (₹{amount_paid})",
                }.get(src, f"{src.capitalize()} (₹{amount_paid})")

            if lang == 'hi':
                txt_req = (
                    "<b>⟦ स्टोरी विवरण ⟧</b>\n\n"
                    f"<b>{s_name}</b>\n\n"
                    "──────────────\n"
                    f"<b>प्लेटफॉर्म  ⟶</b> {story.get('platform', 'अन्य')}\n"
                    f"<b>एपिसोड्स   ⟶</b> {story.get('episodes', 'N/A')}\n"
                    f"<b>फाइलें     ⟶</b> {ep_count}\n"
                    f"<b>स्थिति     ⟶</b> आपकी अपनी (Owned)\n"
                    f"<b>पेमेंट      ⟶</b> {payment_label}\n"
                    "──────────────\n"
                    "अपनी फाइलें प्राप्त करने के लिए नीचे टैप करें।"
                )
                kb = [
                    [InlineKeyboardButton("डिलीवरी प्राप्त करें", callback_data=f"mb#access_{s_id}")],
                    [InlineKeyboardButton("« मेरी स्टोरीज पर वापस", callback_data="mb#my_buys")]
                ]
            else:
                txt_req = (
                    "<b>⟦ 𝗦𝗧𝗢𝗥𝗬 𝗠𝗘𝗧𝗔 ⟧</b>\n\n"
                    f"<b>{s_name}</b>\n\n"
                    "──────────────\n"
                    f"<b>ᴘʟᴀᴛꜰᴏʀᴍ ⟶</b> {story.get('platform', 'Other')}\n"
                    f"<b>ᴇᴘɪꜱᴏᴅᴇꜱ ⟶</b> {story.get('episodes', 'N/A')}\n"
                    f"<b>ꜰɪʟᴇꜱ    ⟶</b> {ep_count}\n"
                    f"<b>ꜱᴛᴀᴛᴜꜱ   ⟶</b> ᴏᴡɴᴇᴅ\n"
                    f"<b>ᴘᴀʏᴍᴇɴᴛ  ⟶</b> {payment_label}\n"
                    "──────────────\n"
                    "𝖳𝖺𝗉 𝖻𝖾𝗅𝗈𝗐 𝗍𝗈 𝗋𝖾𝖼𝖾𝗂𝗏𝖾 𝗒𝗈𝗎𝗋 𝖿𝗂𝗅𝖾𝗌."
                )
                kb = [
                    [InlineKeyboardButton(_bs("GET DELIVERY"), callback_data=f"mb#access_{s_id}")],
                    [InlineKeyboardButton(_bs("Back to My Stories"), callback_data="mb#my_buys")]
                ]
            await _safe_edit(query.message, text=txt_req, markup=InlineKeyboardMarkup(kb))'''

if start_v != -1 and end_v != -1:
    lines[start_v:end_v] = [new_purchased_view + "\n"]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Updated seller UI for localized description and deduplicated stories.")
