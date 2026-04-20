import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_story_profile = r'''async def _show_story_profile(client, user_id, story, lang):
    name = story.get(f'story_name_{lang}', story.get('story_name_en', 'Unknown'))
    status = story.get('status', 'Unknown')
    platform = story.get('platform', 'Unknown')
    genre = story.get('genre', 'Unknown')
    episodes = story.get('episodes', 'Unknown')
    image = story.get('image')

    if lang == 'hi':
        status_lbl = "स्टेटस"
        plat_lbl = "प्लेटफॉर्म"
        genre_lbl = "जौनर"
        ep_lbl = "एपिसोड्स"
        desc_lbl = "कहानी का विवरण"
        confirm_btn = "✅ आगे बढ़ें"
        back_btn = "❮ वापस"
        loading_txt = "प्रोफाइल लोड हो रही है..."
    else:
        status_lbl = "Status"
        plat_lbl = "Platform"
        genre_lbl = "Genre"
        ep_lbl = "Episodes"
        desc_lbl = "Story Description"
        confirm_btn = f"✅ {_sc('CONFIRM')}"
        back_btn = f"❮ {_sc('BACK')}"
        loading_txt = _sc("LOADING PROFILE...")

    desc = story.get('description', '').strip()
    header_txt = (
        f"<b>♨️ Story:</b> {to_mathbold(name)}\n"
        f"<b>🔰 {status_lbl}:</b> <b>{status}</b>\n"
        f"<b>🖥 {plat_lbl}:</b> <b>{platform}</b>\n"
        f"<b>🧩 {genre_lbl}:</b> <b>{genre}</b>\n"
        f"<b>🎬 {ep_lbl}:</b> <b>{episodes}</b>\n\n"
    )
    if desc and desc.lower() != "none":
        header_txt += (
            f"<b>{desc_lbl}</b>\n"
            f"<blockquote expandable>"
            f"-{to_mathbold(desc)}"
            f"</blockquote>\n"
        )
    txt = header_txt
        
    kb = [
        [InlineKeyboardButton(confirm_btn, callback_data=f"mb#show_tc#{str(story['_id'])}")],
        [InlineKeyboardButton(back_btn, callback_data="mb#return_main")]
    ]
    markup = InlineKeyboardMarkup(kb)
    
    from pyrogram import enums
    tmp = await client.send_message(user_id, f"<b>› › ⏳ {loading_txt}</b>", reply_markup=ReplyKeyboardRemove(), parse_mode=enums.ParseMode.HTML)
    
    try:
        if image:
            try:
                await client.send_photo(user_id, photo=image, caption=txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
                await tmp.delete()
                return
            except Exception: pass
        await client.send_message(user_id, txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        await tmp.delete()
    except Exception: pass'''

new_show_story_details = r'''async def _show_story_details(client, msg_or_query, story, lang, bot_cfg: dict = None):
    from pyrogram.types import Message
    is_msg = isinstance(msg_or_query, Message)
    bot_cfg = bot_cfg or {}

    name = story.get(f'story_name_{lang}', story.get('story_name_en', 'Unknown'))
    price = story.get('price', 1)
    
    if lang == 'hi':
        title = "⟦ चेकआउट ⟧"
        item_lbl = "आइटम"
        price_lbl = "कीमत"
        desc = "आप इस प्रीमियम कहानी को खरीदने जा रहे हैं। पेमेंट के बाद आपको तुरंत एक्सेस मिल जाएगा।"
        pay_gateway_btn = "पेमेंट गेटवे से भुगतान (Razorpay)"
        pay_upi_btn = "यूपीआई (Manual UPI)"
        unavailable_upi = "यूपीआई भुगतान अभी बंद है।"
        back_btn = "❮ वापस"
    else:
        title = "⟦ 𝗠𝗔𝗥𝗞𝗘𝗧𝗣𝗟𝗔𝗖𝗘 ⟧"
        item_lbl = "Item"
        price_lbl = "Price"
        desc = "𝖠𝗀𝗋𝖾𝖾𝖽 𝖺𝗇𝖽 𝖼𝗈𝗇𝖿𝗂𝗋𝗆𝖾𝖽. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗉𝗋𝗈𝖼𝖾𝖾𝖽 𝗐𝗂𝗍𝗁 𝗍𝗁𝖾 𝗉𝖺𝗒𝗆𝖾𝗇𝗍 𝗍𝗈 𝗎𝗇𝗅𝗈𝖼𝗄 𝗒𝗈𝗎𝗋 𝗌𝗍𝗈𝗋𝗒 𝗂𝗇𝗌𝗍𝖺𝗇𝗍𝗅𝗒."
        pay_gateway_btn = f"💳 {_sc('PAY VIA RAZORPAY')}"
        pay_upi_btn = f"🏦 {_sc('PAY VIA MANUAL UPI')}"
        unavailable_upi = "UPI Currently Unavailable"
        back_btn = f"❮ {_sc('BACK')}"

    txt = (
        f"<b>{title}</b>\n\n"
        f"<b>{item_lbl} :</b> <code>{name}</code>\n"
        f"<b>{price_lbl} :</b> <code>₹{price}</code>\n\n"
        f"{desc}"
    )

    kb = []
    # Razorpay row
    kb.append([InlineKeyboardButton(pay_gateway_btn, callback_data=f"mb#pay#razorpay#{str(story['_id'])}")])
    
    # UPI row
    from .market_seller import _is_upi_restricted
    upi_enabled = bot_cfg.get('upi_enabled', True)
    upi_restricted = _is_upi_restricted()
    if upi_enabled and not upi_restricted:
        kb.append([InlineKeyboardButton(pay_upi_btn, callback_data=f"mb#pay#upi#{str(story['_id'])}")])
    else:
        kb.append([InlineKeyboardButton(f"🚫 {unavailable_upi}", callback_data="mb#noop")])
        
    kb.append([InlineKeyboardButton(back_btn, callback_data="mb#return_main")])
    markup = InlineKeyboardMarkup(kb)

    if is_msg:
        await msg_or_query.reply_text(txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    else:
        await _safe_edit(msg_or_query.message, text=txt, markup=markup)'''

def apply_func(lines, name, content):
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(f"async def {name}"):
            start = i
            break
    if start == -1: return lines
    end = len(lines)
    for i in range(start+1, len(lines)):
        if lines[i].strip().startswith("async def ") or lines[i].strip().startswith("def ") or lines[i].strip().startswith("# ──────"):
            end = i
            break
    lines[start:end] = [content + "\n\n"]
    return lines

lines = apply_func(lines, "_show_story_profile", new_story_profile)
lines = apply_func(lines, "_show_story_details", new_show_story_details)

# Also fix the my_buys block in _process_callback
start_idx = -1
end_idx = -1
for i in range(len(lines)):
    if 'elif cmd == "my_buys" or cmd.startswith("my_buys_page_"):' in lines[i]:
        start_idx = i
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith("elif ") or lines[j].strip().startswith("#"):
                end_idx = j
                break
        break
if start_idx != -1 and end_idx != -1:
    # Just make it call _process_my_stories by simulating a message
    # Actually better to just use a simplified version for edit
    lines[start_idx:end_idx] = [r'''    elif cmd == "my_buys" or cmd.startswith("my_buys_page_"):
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
        purchases = [p for p in raw_purchases if str(p) in valid_ids_set]
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
                    en_name = st.get('story_name_en', 'Story')
                    hi_name = st.get('story_name_hi', en_name)
                    if lang == 'hi':
                        s_name = f"📖 {hi_name}" if hi_name == en_name else f"📖 {hi_name} ({en_name})"
                    else:
                        s_name = f"📖 {en_name}"
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
        await _safe_edit(query.message, text=txt_b, markup=InlineKeyboardMarkup(kb))
''' + "\n\n"]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Final massive localization applied.")
