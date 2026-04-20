import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_do_channel_delivery_msg = r'''        # Result message
        if lang == 'hi':
            txt = (
                f"<b>आपका 1-टाइम एक्सेस लिंक तैयार है!</b>\n\n"
                f"<b>{s_name_h}</b>\n\n"
                f"{invite_link.invite_link}\n\n"
                "<blockquote>"
                f"<i>यह लिंक केवल 1 व्यक्ति के लिए है। एक बार उपयोग करने पर, यह एक्सपायर हो जाएगा।\n"
                f"भविष्य में इस स्टोरी को /mystories का उपयोग करके सीधे DM में प्राप्त किया जा सकता है।</i>\n"
                "</blockquote>"
                "<blockquote>"
                f"<i>⚠️ यह मैसेज 24 घंटे में अपने आप डिलीट हो जाएगा। "
                f"जैसे ही आप ज्वाइन करेंगे, प्राइवेसी के लिए लिंक को तुरंत रद्द कर दिया जाएगा।</i>\n"
                "</blockquote>"
            )
            back_btn_txt = "« ❮ मुख्य मेनू"
        else:
            txt = (
                f"<b>Your 1-Time Access Link is Ready!</b>\n\n"
                f"<b>{s_name_h}</b>\n\n"
                f"{invite_link.invite_link}\n\n"
                "<blockquote>"
                f"<i>This link works for exactly 1 person only. Once used, it expires.\n"
                f"Future access to this story will be via DM delivery only by using /mystories.</i>\n"
                "</blockquote>"
                "<blockquote>"
                f"<i>⚠️ This message will auto-delete in 24 hours. "
                f"Once you join, the link will be revoked automatically to ensure privacy.</i>\n"
                "</blockquote>"
            )
            back_btn_txt = f"« ❮ {_sc('MAIN MENU')}"

        kb_link = [[InlineKeyboardButton(back_btn_txt, callback_data="mb#main_back")]]
        msg = await client.send_message(user_id, txt, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(kb_link))
        _schedule_auto_delete(msg, 86400)'''

new_process_my_stories = r'''async def _process_my_stories(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    
    # Send a fresh "My Stories" menu
    purchases = user.get('purchases', [])
    from bson.objectid import ObjectId

    PAGE_SIZE = 5
    page = 0
    total = len(purchases)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page_purchases = purchases[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    kb = []
    for pid in page_purchases:
        try:
            st = await db.db.premium_stories.find_one({"_id": ObjectId(pid)})
            if st:
                # Optimized title: Show both Hindi and English if they differ
                en_name = st.get('story_name_en', 'Story')
                hi_name = st.get('story_name_hi', en_name)
                
                if lang == 'hi':
                    s_name = f"📖 {hi_name}" if hi_name == en_name else f"📖 {hi_name} ({en_name})"
                else:
                    s_name = f"📖 {en_name}"
                    
                kb.append([InlineKeyboardButton(s_name, callback_data=f"mb#purchased_view_{pid}")])
        except Exception:
            pass

    if lang == 'hi':
        title = "⟦ मेरी स्टोरीज ⟧"
        total_txt = "कुल स्टोरी ⟶"
        desc = "आपके अकाउंट में मौजूद सभी स्टोरीज नीचे दी गई हैं। किसी भी स्टोरी को देखने या दोबारा एक्सेस करने के लिए उसे चुनें।"
        next_btn = "आगे ❭"
        prev_btn = "❬ पीछे"
        back_btn = "« वापस मेनू"
        empty_txt = "कोई खरीद नहीं मिली। स्टोर देखें।"
        market_btn = "स्टोर खोलें"
    else:
        title = "⟦ 𝗠𝗬 𝗦𝗧𝗢𝗥𝗜𝗘𝗦 ⟧"
        total_txt = "ᴛᴏᴛᴀʟ ⟶"
        desc = "𝖠𝗅𝗅 𝗌𝗍𝗈𝗋𝗂𝖾𝗌 𝗅𝗂𝗌𝗍𝖾𝖽 𝖻𝖾𝗅𝗈𝗐 𝖺𝗋𝖾 𝖺𝗅𝗋𝖾𝖺𝖽𝗒 𝗈𝗇 𝗒𝗈𝗎𝗋 𝖺𝖼𝖼𝗈𝗎𝗇𝗍. 𝖲𝖾𝗅𝖾𝖼𝗍 𝖺𝗇𝗒 𝗌𝗍𝗈𝗋𝗒 𝗍𝗈 𝗏𝗂𝖾𝗐 𝖽𝖾𝗍𝖺𝗂𝗅𝗌."
        next_btn = "𝗡𝗲𝘅𝘁 ❭"
        prev_btn = "❬ 𝗣𝗿𝗲𝘃"
        back_btn = "Back to Menu"
        empty_txt = "ɴᴏ ᴘᴜʀᴄʜᴀꜱᴇꜱ ꜰᴏᴜɴᴅ."
        market_btn = "OPEN MARKETPLACE"

    if total_pages > 1:
        nav = []
        nav.append(InlineKeyboardButton(f"ᴘᴀɢᴇ 1/{total_pages}", callback_data="mb#noop"))
        nav.append(InlineKeyboardButton(next_btn, callback_data="mb#my_buys_page_1"))
        kb.append(nav)

    kb.append([InlineKeyboardButton(back_btn, callback_data="mb#main_back")])

    if total > 0:
        txt_b = (
            f"<b>{title}</b>\n\n"
            f"<b>{total_txt}</b> {total}\n\n"
            f"{desc}"
        )
    else:
        txt_b = (
            f"<b>{title}</b>\n\n"
            f"<b>{total_txt}</b> 0\n\n"
            f"{empty_txt}"
        )
        kb.insert(0, [InlineKeyboardButton(market_btn, callback_data="mb#main_marketplace")])

    await client.send_message(user_id, txt_b, reply_markup=InlineKeyboardMarkup(kb))'''

def apply_func(lines, name, content):
    start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(f"async def {name}"):
            start = i
            break
    if start == -1: return lines
    end = len(lines)
    for i in range(start+1, len(lines)):
        if lines[i].strip().startswith("async def ") or lines[i].strip().startswith("def ") or (name=="_do_channel_delivery" and "Revoker Helper" in lines[i]):
            end = i
            break
    lines[start:end] = [content + "\n\n"]
    return lines

lines = apply_func(lines, "_process_my_stories", new_process_my_stories)

# Manual fix for channel delivery msg
for i in range(len(lines)):
    if "txt = (" in lines[i] and "Your 1-Time Access Link is Ready!" in lines[i+1]:
        # Find where the block ends
        j = i + 1
        while j < len(lines) and "_schedule_auto_delete" not in lines[j]:
            j += 1
        lines[i:j+1] = [new_do_channel_delivery_msg + "\n"]
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Updated My Stories and Delivery Link localization.")
