import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update T Dictionary
new_t = """T = {
    "en": {
        "welcome": "Welcome to",
        "store": "Store",
        "intro": "Browse our premium collection. Tap Marketplace to explore stories by platform.",
        "tc_accept": "✅ I Accept the Terms",
        "tc_reject": "❌ I Reject",
        "no_stories": "No stories currently available.",
        "pay_upi": "Pay via UPI",
        "back": "❮ Back",
        "qr_msg": "<b>💳 Complete Payment</b>\\n\\n• Scan the QR code above.\\n• Amount: ₹{price}\\n\\n<b>After paying, send the successful payment screenshot here.</b>",
        "wait_ver": "⏳ Your payment is being verified, please wait (approx 5 minutes)...",
        "notify": "🔔 Notify Admin",
        "prof_title": "╔═⟦ 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 ⟧═╗",
        "prof_name": "ɴᴀᴍᴇ",
        "prof_uname": "ᴜꜱᴇʀɴᴀᴍᴇ",
        "prof_id": "ᴛɢ ɪᴅ",
        "prof_bought": "ᴘᴜʀᴄʜᴀꜱᴇꜱ",
        "prof_lang": "ʟᴀɴɢᴜᴀɢᴇ",
        "prof_join": "ᴊᴏɪɴᴇᴅ",
        "my_reqs": "📝 MY REQUESTS",
        "set_lang": "⚙️ Settings",
        "set_prompt": "<b>⚙️ Settings</b>\\n\\nSelect your language:",
        "req_main_title": "📝 My Story Requests",
        "req_click": "Click on any request to view its status:",
        "req_empty": "You haven't made any story requests yet.",
        "back_prof": "« BACK TO PROFILE",
        "back_reqs": "« BACK TO REQUESTS",
        "req_details": "📝 STORY REQUEST DETAILS",
        "req_name": "Name",
        "req_plat": "Platform",
        "req_type": "Type",
        "req_date": "Date",
        "req_status": "Status",
        "already_owned": "✅ You already own this story. Sending delivery options...",
        "wait_a_sec": "WAIT A SECOND...",
        "cant_find_btn": "🔍 CAN'T FIND? REQUEST NOW!",
        "req_search_prompt": "<b>🔍 SEARCH / REQUEST STORY</b>\\n\\nType the <b>Story Name</b> you want to search or request:",
        "req_cancel": "Process Cancelled.",
        "req_step1": "<b>Step 1/3:</b>\\nPlease enter the <b>Story Name</b> you want to request:",
        "req_step2": "<b>Step 2/3:</b>\\nChoose the <b>Platform</b> (e.g. Ullu, AltBalaji):",
        "req_step3": "<b>Step 3/3:</b>\\nHow would you like it? (e.g. Only Episodes, Full Movie, etc.):",
        "req_success": "✅ <b>Request Submitted!</b>\\n\\nOur team will search for this story and update you soon. Check status in <b>Profile -> My Requests</b>."
    },
    "hi": {
        "welcome": "स्वागत है",
        "store": "स्टोर",
        "intro": "प्रीमियम कलेक्शन ब्राउज़ करें। Marketplace पर टैप करें।",
        "tc_accept": "✅ मुझे शर्तें मंजूर हैं",
        "tc_reject": "❌ मैं अस्वीकार करता हूँ",
        "no_stories": "वर्तमान में कोई स्टोरी उपलब्ध नहीं है।",
        "pay_upi": "UPI से पेमेंट करें",
        "back": "❮ वापस",
        "qr_msg": "<b>💳 पेमेंट पूरा करें</b>\\n\\n• ऊपर QR स्कैन करें।\\n• राशि: ₹{price}\\n\\n<b>पेमेंट के बाद स्क्रीनशॉट यहाँ भेजें।</b>",
        "wait_ver": "⏳ आपके भुगतान का सत्यापन हो रहा है...",
        "notify": "🔔 एडमिन को सूचित करें",
        "prof_title": "╔═⟦ आपकी प्रोफाइल ⟧═╗",
        "prof_name": "नाम",
        "prof_uname": "यूज़रनेम",
        "prof_id": "आईडी",
        "prof_bought": "खरीदी गई स्टोरीज",
        "prof_lang": "भाषा",
        "prof_join": "जुड़े हुए",
        "my_reqs": "📝 मेरे अनुरोध (My Requests)",
        "set_lang": "⚙️ सेटिंग्स",
        "set_prompt": "<b>⚙️ सेटिंग्स</b>\\n\\nअपनी पसंदीदा भाषा चुनें:",
        "req_main_title": "📝 मेरे स्टोरी अनुरोध",
        "req_click": "किसी भी अनुरोध पर क्लिक करके उसका स्टेटस देखें:",
        "req_empty": "आपने अभी तक कोई स्टोरी अनुरोध नहीं किया है।",
        "back_prof": "« प्रोफाइल पर वापस",
        "back_reqs": "« अनुरोधों पर वापस",
        "req_details": "📝 स्टोरी अनुरोध विवरण",
        "req_name": "कहानी का नाम",
        "req_plat": "प्लेटफॉर्म",
        "req_type": "प्रकार (Type)",
        "req_date": "तारीख",
        "req_status": "स्टेटस",
        "already_owned": "✅ आप पहले ही इस स्टोरी को खरीद चुके हैं। डिलीवरी विकल्प भेजे जा रहे हैं...",
        "wait_a_sec": "कृपया प्रतीक्षा करें...",
        "cant_find_btn": "🔍 कहानी नहीं मिल रही? अनुरोध करें!",
        "req_search_prompt": "<b>🔍 स्टोरी खोजें / अनुरोध करें</b>\\n\\nउस <b>कहानी का नाम</b> लिखें जिसे आप खोजना या अनुरोध करना चाहते हैं:",
        "req_cancel": "प्रक्रिया रद्द कर दी गई।",
        "req_step1": "<b>स्टेप 1/3:</b>\\nकृपया उस <b>कहानी का नाम</b> लिखें जिसका आप अनुरोध करना चाहते हैं:",
        "req_step2": "<b>स्टेप 2/3:</b>\\n<b>प्लेटफॉर्म</b> चुनें (जैसे: Ullu, AltBalaji):",
        "req_step3": "<b>स्टेप 3/3:</b>\\nआपको यह कैसे चाहिए? (जैसे: केवल एपिसोड, पूरी फिल्म, आदि):",
        "req_success": "✅ <b>अनुरोध जमा हो गया!</b>\\n\\nहमारी टीम इस कहानी को खोजेगी और जल्द ही आपको अपडेट करेगी। स्टेटस देखने के लिए <b>प्रोफाइल -> मेरे अनुरोध</b> पर जाएं।"
    }
}"""

import re
content = re.sub(r'T = \{.*?\}', new_t, content, flags=re.DOTALL)

# 2. Update Profile Handler to use T
old_prof_block = r'''        elif action == "profile":
            u = query.from_user
            joined = user\.get\('joined_date', 'N/A'\)
            if isinstance\(joined, datetime\):
                joined = joined\.strftime\('%d %b %Y'\)
            purchases = user\.get\('purchases', \[\]\)
            uname = f"@{u\.username}" if u\.username else "N/A"
            lang_label = "English" if lang == 'en' else "हिंदी"
            name = f"{u\.first_name or ''} {u\.last_name or ''}"\.strip\(\) or "Unknown"
            txt_p = \(
                "<b>╔═⟦ 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 ⟧═╗</b>\n\n"
                f"<b>⧉ ɴᴀᴍᴇ        ⟶</b> {name}\n"
                f"<b>⧉ ᴜꜱᴇʀɴᴀᴍᴇ    ⟶</b> {uname}\n"
                f"<b>⧉ ᴛɢ ɪᴅ       ⟶</b> <code>{u\.id}</code>\n\n"
                "<b>╠══════════════════╣</b>\n\n"
                f"<b>⧉ ᴘᴜʀᴄʜᴀꜱᴇꜱ   ⟶</b> {len\(purchases\)}\n"
                f"<b>⧉ ʟᴀɴɢᴜᴀɢᴇ    ⟶</b> {lang_label}\n"
                f"<b>⧉ ᴊᴏɪɴᴇᴅ      ⟶</b> {joined}\n\n"
                "<b>╚══════════════════╝</b>"
            \)
            kb = \[
                \[InlineKeyboardButton\("📝 " \+ _sc\("MY REQUESTS"\), callback_data="mb#my_reqs_0"\)\],
                \[InlineKeyboardButton\(f"{_sc\('LANGUAGE'\)}", callback_data="mb#main_settings"\)\],
                \[InlineKeyboardButton\(f"{_sc\('BACK'\)}", callback_data="mb#main_back"\)\]
            \]
            await _safe_edit\(query\.message, text=txt_p, markup=InlineKeyboardMarkup\(kb\)\)
            return'''

new_prof_block = r'''        elif action == "profile":
            u = query.from_user
            joined = user.get('joined_date', 'N/A')
            if isinstance(joined, datetime):
                joined = joined.strftime('%d %b %Y')
            
            # Use unique stories only for purchase count
            raw_p = user.get('purchases', [])
            purchases = list(set(str(p) for p in raw_p))
            
            uname = f"@{u.username}" if u.username else "N/A"
            lang_label = "English" if lang == 'en' else "हिंदी"
            name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "Unknown"
            
            t = T[lang]
            txt_p = (
                f"<b>{t['prof_title']}</b>\n\n"
                f"<b>⧉ {t['prof_name']}        ⟶</b> {name}\n"
                f"<b>⧉ {t['prof_uname']}    ⟶</b> {uname}\n"
                f"<b>⧉ {t['prof_id']}       ⟶</b> <code>{u.id}</code>\n\n"
                "<b>╠══════════════════╣</b>\n\n"
                f"<b>⧉ {t['prof_bought']}   ⟶</b> {len(purchases)}\n"
                f"<b>⧉ {t['prof_lang']}    ⟶</b> {lang_label}\n"
                f"<b>⧉ {t['prof_join']}      ⟶</b> {joined}\n\n"
                "<b>╚══════════════════╝</b>"
            )
            kb = [
                [InlineKeyboardButton(t['my_reqs'], callback_data="mb#my_reqs_0")],
                [InlineKeyboardButton("⚙️ " + t['set_lang'], callback_data="mb#main_settings")],
                [InlineKeyboardButton("❮ " + t['back'], callback_data="mb#main_back")]
            ]
            await _safe_edit(query.message, text=txt_p, markup=InlineKeyboardMarkup(kb))
            return'''

# 3. Update My Requests List View
old_reqs_list = r'''    elif cmd\.startswith\("my_reqs_"\):
        page = int\(cmd\.replace\("my_reqs_", ""\)\)
        reqs = await db\.db\.premium_requests\.find\({"user_id": user_id, "bot_id": client\.me\.id}\)\.sort\("created_at", -1\)\.to_list\(length=None\)
        if not reqs:
            return await _safe_answer\(query, "You haven't made any story requests yet\.", show_alert=True\)
        items_per_page = 10
        total_pages = max\(1, \(len\(reqs\) \+ items_per_page - 1\) // items_per_page\)
        if page < 0: page = 0
        if page >= total_pages: page = total_pages - 1
        subset = reqs\[page\*items_per_page : \(page\+1\)\*items_per_page\]
        txt_req = f"<b>📝 My Story Requests \(Page {page\+1}/{total_pages}\)</b>\n\nClick on any request to view its status:"
        kb = \[\]
        for r in subset:
            sname = r\.get\('story_name', 'Unknown'\)
            if len\(sname\) > 25: sname = sname\[:22] \+ "\.\.\."
            status_emoji = \{"Sent": "📮", "Pending": "⏳", "Searching": "🔍", "Posting": "📤", "Posted": "✅", "Completed": "🎉"\}\.get\(r\.get\('status', 'Sent'\), "📌"\)
            kb\.append\(\[InlineKeyboardButton\(f"\{status_emoji\} \{sname\}", callback_data=f"mb#my_req_\{str\(r\['_id'\]\)\}"\)\]\)
        nav = \[\]
        if page > 0: nav\.append\(InlineKeyboardButton\("❬ Prev", callback_data=f"mb#my_reqs_\{page-1\}"\)\)
        if page < total_pages - 1: nav\.append\(InlineKeyboardButton\("Next ❭", callback_data=f"mb#my_reqs_\{page\+1\}"\)\)
        if nav: kb\.append\(nav\)
        kb\.append\(\[InlineKeyboardButton\("« " \+ _sc\("BACK TO PROFILE"\), callback_data="mb#main_profile"\)\]\)
        await _safe_edit\(query\.message, text=txt_req, markup=InlineKeyboardMarkup\(kb\)\)
        return'''

new_reqs_list = r'''    elif cmd.startswith("my_reqs_"):
        page = int(cmd.replace("my_reqs_", ""))
        # Look for requests for the current bot only
        reqs = await db.db.premium_requests.find({"user_id": user_id, "bot_id": client.me.id}).sort("created_at", -1).to_list(length=None)
        t = T[lang]
        if not reqs:
            return await _safe_answer(query, t['req_empty'], show_alert=True)
            
        items_per_page = 10
        total_pages = max(1, (len(reqs) + items_per_page - 1) // items_per_page)
        page = max(0, min(page, total_pages - 1))
        
        subset = reqs[page*items_per_page : (page+1)*items_per_page]
        txt_req = f"<b>{t['req_main_title']} (Page {page+1}/{total_pages})</b>\n\n{t['req_click']}"
        kb = []
        for r in subset:
            sname = r.get('story_name', 'Unknown')
            if len(sname) > 25: sname = sname[:22] + "..."
            status = r.get('status', 'Sent')
            if lang == 'hi':
                status_hi = {"Sent": "भेजा गया", "Pending": "लंबित", "Searching": "ढूंढ रहे हैं", "Posting": "अपलोड हो रहा है", "Posted": "अपलोड हो गया", "Completed": "पूरा हुआ"}.get(status, status)
                label = f"{sname} ({status_hi})"
            else:
                label = f"{sname} ({status})"
                
            status_emoji = {"Sent": "📮", "Pending": "⏳", "Searching": "🔍", "Posting": "📤", "Posted": "✅", "Completed": "🎉"}.get(status, "📌")
            kb.append([InlineKeyboardButton(f"{status_emoji} {label}", callback_data=f"mb#my_req_{str(r['_id'])}")])
        
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("❬ Prev" if lang=='en' else "❬ पीछे", callback_data=f"mb#my_reqs_{page-1}"))
        if page < total_pages - 1: nav.append(InlineKeyboardButton("Next ❭" if lang=='en' else "आगे ❭", callback_data=f"mb#my_reqs_{page+1}"))
        if nav: kb.append(nav)
        kb.append([InlineKeyboardButton(t['back_prof'], callback_data="mb#main_profile")])
        await _safe_edit(query.message, text=txt_req, markup=InlineKeyboardMarkup(kb))
        return'''

# 4. Update Marketplace Platforms View
old_market_block = r'''        if action == "marketplace":
            platforms = await db\.db\.premium_stories\.distinct\('platform', \{"bot_id": client\.me\.id\}\)
            kb = \[\]
            for i in range\(0, len\(platforms\), 2\):
                row = platforms\[i:i\+2\]
                kb\.append\(row\)
            if "Other" not in platforms:
                kb\.append\(\["Other"\]\)
            kb\.append\(\["« " \+ "𝗕𝗮𝗰𝗸 𝘁𝗼 𝗠𝗲𝗻𝘂"\]\)
            await query\.message\.delete\(\)
            await client\.send_message\(
                user_id,
                f"<b>🎧 Platform Selection</b>\n\nChoose a platform from the keyboard below:",
                reply_markup=ReplyKeyboardMarkup\(kb, resize_keyboard=True\)
            \)'''

new_market_block = r'''        if action == "marketplace":
            platforms = await db.db.premium_stories.distinct('platform', {"bot_id": client.me.id})
            t = T[lang]
            kb = []
            for i in range(0, len(platforms), 2):
                row = platforms[i:i+2]
                kb.append(row)
            if "Other" not in platforms:
                kb.append(["Other"])
            kb.append(["« " + ("𝗕𝗮𝗰𝗸 𝘁𝗼 𝗠𝗲𝗻𝘂" if lang=='en' else "वापस मेनू")])
            
            p_title = "🎧 Platform Selection" if lang == 'en' else "🎧 प्लेटफॉर्म चयन"
            p_desc = "Choose a platform from the keyboard below:" if lang == 'en' else "नीचे दिए गए कीबोर्ड से एक प्लेटफॉर्म चुनें:"
            
            await query.message.delete()
            await client.send_message(
                user_id,
                f"<b>{p_title}</b>\n\n{p_desc}",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
            )'''

# 5. Fix _process_text search/request logic
old_text_logic = r'''    if txt == "CAN'T FIND\? REQUEST NOW!":
        try:
            from utils import native_ask, log_arya_event
            sj = \{"user_id": user_id, "bot_id": client\.me\.id, "bot_username": client\.me\.username\}
            
            await message\.reply_text\("<b>? Request Process Started</b>", reply_markup=ReplyKeyboardRemove\(\)\)
            
            ans1 = await native_ask\(client, user_id, "<b>Step 1/3:</b>\nPlease enter the <b>Story Name</b> you want to request:", reply_markup=ReplyKeyboardMarkup\(\[\["« Cancel"\]\], resize_keyboard=True\)\)
            if getattr\(ans1, 'text', ""\) == "« Cancel": return await message\.reply_text\("Process Cancelled\."\)
            sj\["story_name"\] = ans1\.text'''

new_text_logic = r'''    t = T[lang]
    if txt == "CAN'T FIND? REQUEST NOW!" or txt == "🔍 कहानी नहीं मिल रही? अनुरोध करें!":
        try:
            from utils import native_ask, log_arya_event
            sj = {"user_id": user_id, "bot_id": client.me.id, "bot_username": client.me.username}
            
            cancel_btn = "« Cancel" if lang == 'en' else "« रद्द करें"
            await message.reply_text(f"<b>› › ⏳ {t['wait_a_sec']}</b>", reply_markup=ReplyKeyboardRemove())
            
            ans1 = await native_ask(client, user_id, t['req_step1'], reply_markup=ReplyKeyboardMarkup([[cancel_btn]], resize_keyboard=True))
            if not getattr(ans1, 'text', "") or cancel_btn in ans1.text: return await message.reply_text(t['req_cancel'])
            sj["story_name"] = ans1.text
            
            ans2 = await native_ask(client, user_id, t['req_step2'], reply_markup=ReplyKeyboardMarkup([[cancel_btn]], resize_keyboard=True))
            if not getattr(ans2, 'text', "") or cancel_btn in ans2.text: return await message.reply_text(t['req_cancel'])
            sj["platform"] = ans2.text
            
            ans3 = await native_ask(client, user_id, t['req_step3'], reply_markup=ReplyKeyboardMarkup([[cancel_btn]], resize_keyboard=True))
            if not getattr(ans3, 'text', "") or cancel_btn in ans3.text: return await message.reply_text(t['req_cancel'])
            sj["completion_type"] = ans3.text
            
            sj["status"] = "Sent"
            from datetime import datetime
            sj["created_at"] = datetime.now()
            
            await db.db.premium_requests.insert_one(sj)
            await message.reply_text(t['req_success'], reply_markup=None)
            await _send_main_menu(client, user_id, message.from_user, lang)
            return'''

# Apply replacements
content = re.sub(old_prof_block, new_prof_block, content, flags=re.DOTALL)
content = re.sub(old_reqs_list, new_reqs_list, content, flags=re.DOTALL)
content = re.sub(old_market_block, new_market_block, content, flags=re.DOTALL)
content = re.sub(old_text_logic, new_text_logic, content, flags=re.DOTALL)

# Also update the Search Prompt in _process_text
search_prompt_old = r'f"<b>? SEARCH / REQUEST STORY</b>\\n\\nType the <b>Story Name</b> you want to search or request:"'
search_prompt_new = r't["req_search_prompt"]'
content = content.replace(search_prompt_old, search_prompt_new)

# Update My Requests button text in Profile back to Menu handling
content = content.replace('kb.append(["« " + "𝗕𝗮𝗰𝗸 𝘁𝗼 𝗠𝗲𝗻𝘂"])', 'kb.append(["« " + ("𝗕𝗮𝗰𝗸 𝘁𝗼 𝗠𝗲𝗻𝘂" if lang==\'en\' else "वापस मेनू")])')

# Update already owned message
content = content.replace('msg = "✅ You already own this story. Sending delivery options..." if lang == \'en\' else "✅ आप पहले ही इस स्टोरी को खरीद चुके हैं। डिलीवरी विकल्प भेजे जा रहे हैं..."', 'msg = t["already_owned"]')

# Update "Can't find" button in platform view list
content = content.replace('kb.append([InlineKeyboardButton("? CAN\'T FIND? REQUEST NOW!", callback_data="mb#main_request")])', 'kb.append([InlineKeyboardButton(t["cant_find_btn"], callback_data="mb#main_request")])')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Seller.py fully localized and fixed.")
