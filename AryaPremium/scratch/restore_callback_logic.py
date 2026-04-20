import os
import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add joined_check handler to _process_callback
joined_check_code = r'''    # ── Joined Check ──
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
if 'cmd == "joined_check"' not in content:
    content = content.replace('cmd = data[1]', 'cmd = data[1]\n' + joined_check_code)

# 2. Localize Profile and Settings blocks in _process_callback
profile_block = r'''        if action == "profile":
            u = query.from_user
            joined = user.get('joined_date', 'N/A')
            if isinstance(joined, datetime):
                joined = joined.strftime('%d %b %Y')
            purchases = user.get('purchases', [])
            uname = f"@{u.username}" if u.username else "N/A"
            lang_label = "English" if lang == 'en' else "हिंदी"
            name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "Unknown"
            
            if lang == 'hi':
                txt_p = (
                    "<b>╔═⟦ प्रोफाइल ⟧═╗</b>\n\n"
                    f"<b>⧉ नाम        ⟶</b> {name}\n"
                    f"<b>⧉ यूजरनेम    ⟶</b> {uname}\n"
                    f"<b>⧉ टेलीग्राम आईडी ⟶</b> <code>{u.id}</code>\n\n"
                    "<b>╠══════════════════╣</b>\n\n"
                    f"<b>⧉ कुल खरीदारी   ⟶</b> {len(purchases)}\n"
                    f"<b>⧉ भाषा        ⟶</b> {lang_label}\n"
                    f"<b>⧉ शामिल हुए     ⟶</b> {joined}\n\n"
                    "<b>╚══════════════════╝</b>"
                )
                kb = [
                    [InlineKeyboardButton("📝 मेरी रिक्वेस्ट", callback_data="mb#my_reqs_0")],
                    [InlineKeyboardButton("भाषा बदलें", callback_data="mb#main_settings")],
                    [InlineKeyboardButton("वापस जाएं", callback_data="mb#main_back")]
                ]
            else:
                txt_p = (
                    "<b>╔═⟦ 𝗣𝗥𝗢𝗙𝗜𝗟𝗘 ⟧═╗</b>\n\n"
                    f"<b>⧉ ɴᴀᴍᴇ        ⟶</b> {name}\n"
                    f"<b>⧉ ᴜꜱᴇʀɴᴀᴍᴇ    ⟶</b> {uname}\n"
                    f"<b>⧉ ᴛɢ ɪᴅ       ⟶</b> <code>{u.id}</code>\n\n"
                    "<b>╠══════════════════╣</b>\n\n"
                    f"<b>⧉ ᴘᴜʀᴄʜᴀꜱᴇꜱ   ⟶</b> {len(purchases)}\n"
                    f"<b>⧉ ʟᴀɴɢᴜᴀɢᴇ    ⟶</b> {lang_label}\n"
                    f"<b>⧉ ᴊᴏɪɴᴇᴅ      ⟶</b> {joined}\n\n"
                    "<b>╚══════════════════╝</b>"
                )
                kb = [
                    [InlineKeyboardButton("📝 " + _sc("MY REQUESTS"), callback_data="mb#my_reqs_0")],
                    [InlineKeyboardButton(f"{_sc('LANGUAGE')}", callback_data="mb#main_settings")],
                    [InlineKeyboardButton(f"{_sc('BACK')}", callback_data="mb#main_back")]
                ]
            await _safe_edit(query.message, text=txt_p, markup=InlineKeyboardMarkup(kb))
            return'''

old_profile_pattern = re.search(r'if action == "profile":.*?await _safe_edit\(query\.message, text=txt_p, markup=InlineKeyboardMarkup\(kb\)\)\s+return', content, re.DOTALL)
if old_profile_pattern:
    content = content.replace(old_profile_pattern.group(0), profile_block)

# 3. Localize Gateway Verification in _process_callback
gateway_check_localize = r'''        m_txt = f"🛡️ <b>पुगतान की पुष्टि की जा रही है...</b>\\n<i>{method.capitalize()} सर्वर से चेक किया जा रहा है।</i>" if lang == 'hi' else f"🛡️ <b>{_sc('VERIFYING PAYMENT')}...</b>\\n<i>{_sc('Checking with')} {method.capitalize()} {_sc('servers.')}</i>"
        m = await query.message.edit_text(m_txt)'''
content = re.sub(r'm = await query\.message\.edit_text\(f"🛡️ <b>\{_sc\(\'VERIFYING PAYMENT\'\)\}...</b>\\n<i>\{_sc\(\'Checking with\'\)\} \{method\.capitalize\(\)\} \{_sc\(\'servers.\'\)\}</i>"\)', gateway_check_localize.replace('\\n', '\n'), content)

# 4. Localize upi_done sub_txt
upi_done_localize = r'''        if lang == 'hi':
            sub_txt = (
                "<b>☑️ भुगतान सबमिट किया गया</b>\n\n"
                "<blockquote expandable>"
                "<i>हमें आपके भुगतान को वेरीफाई करने की आवश्यकता है।</i>\n"
                "<i>कृपया सफल भुगतान का स्क्रीनशॉट अभी यहां अपलोड करें।</i>\n"
                "<i>सुनिश्चित करें कि ट्रांजैक्शन आईडी / UTR स्पष्ट रूप से दिखाई दे रहा हो।</i>\n"
                "</blockquote>"
            )
        else:
            sub_txt = (
                f"<b>☑️ {_sc('PAYMENT SUBMITTED')}</b>\n\n"
                "<blockquote expandable>"
                f"<i>{_sc('Our system needs to verify your payment.')}</i>\n"
                f"<i>{_sc('Please upload the successful payment screenshot here now.')}</i>\n"
                f"<i>{_sc('Ensure the Transaction ID / UTR is clearly visible.')}</i>\n"
                "</blockquote>"
            )
        await client.send_message(user_id, sub_txt)'''
content = re.sub(r'await client\.send_message\(\s+user_id,\s+f"<b>☑️ \{_sc\(\'PAYMENT SUBMITTED\'\)\}</b>.*?<\/blockquote>"\s+\)', upi_done_localize, content, flags=re.DOTALL)

# 5. Localize Delivery choice
delivery_localize = r'''    if lang == 'hi':
        del_txt = (
            "<b>✅ एक्सेस मिल गया है!</b>\n\n"
            f"<b>स्टोरी:</b> {s_name}\n"
            + (f"<b>भुगतान तरीका:</b> {method_info}\n" if method_info else "")
            + "\n"
            + "<b>ℹ️ डिलीवरी की जानकारी</b>\n\n"
            + "<blockquote>• <b>DM डिलीवरी:</b> फाइलें सीधे यहां भेजी जाती हैं। उन्हें तुरंत सेव या फॉरवर्ड करें—वे कुछ समय बाद अपने आप डिलीट हो जाती हैं।</blockquote>\n"
            + "<blockquote>• <b>चैनल लिंक:</b> एक वन-टाइम प्राइवेट इनवाइट लिंक जेनरेट किया जाता है। प्रत्येक स्टोरी के लिए केवल एक चैनल लिंक की अनुमति है।</blockquote>\n"
            + "<blockquote>• <b>लाइफटाइम एक्सेस:</b> आप किसी भी खरीदी हुई स्टोरी को कभी भी <b>मुख्य मेनू ⟶ मेरी स्टोरीज</b> से एक्सेस कर सकते हैं।</blockquote>\n"
            + "──────────────\n\n"
            + "आप अपनी फाइलें कैसे प्राप्त करना चाहेंगे?"
        )
        dm_btn_txt = "⤓ DM में प्राप्त करें"
        chan_btn_txt = "➦ चैनल लिंक प्राप्त करें"
        back_btn_txt = "« ❮ मुख्य मेनू"
    else:
        del_txt = (
            "<b>✅ Access Granted!</b>\n\n"
            f"<b>Product:</b> {s_name}\n"
            + (f"<b>Method:</b> {method_info}\n" if method_info else "")
            + "\n"
            + "<b>ℹ️ Delivery Info</b>\n\n"
            + "<blockquote>• <b>DM Delivery:</b> Files are sent directly here. Save or forward them immediately—they auto-delete after some time.</blockquote>\n"
            + "<blockquote>• <b>Channel Link:</b> A one-time private invite link is generated. Each story allows only one channel link per account.</blockquote>\n"
            + "<blockquote>• <b>Lifetime Access:</b> You can re-access any purchased story anytime from <b>Main Menu ⟶ My Stories</b>.</blockquote>\n"
            + "──────────────\n\n"
            + "How would you like to receive your files?"
        )
        dm_btn_txt = f"⤓ {_sc('RECEIVE IN DM')}"
        chan_btn_txt = f"➦ {_sc('ACCESS CHANNEL LINK')}"
        back_btn_txt = f"« ❮ {_sc('MAIN MENU')}"

    kb = [[InlineKeyboardButton(dm_btn_txt, callback_data=f"mb#deliver_dm#{story_id_str}")]]
    if can_use_channel:
        kb.append([InlineKeyboardButton(chan_btn_txt, callback_data=f"mb#deliver_channel#{story_id_str}")])
    kb.append([InlineKeyboardButton(back_btn_txt, callback_data="mb#main_back")])'''

old_delivery_pattern = re.search(r'del_txt = \(.*?How would you like to receive your files\?\"\s+\).*?kb = \[.*?\]', content, re.DOTALL)
if old_delivery_pattern:
    content = content.replace(old_delivery_pattern.group(0), delivery_localize)

# 6. Localize Timer screen
timer_localize = r'''                if lang == 'hi':
                    wait_txt = (f"⏳ <b>आपके भुगतान की पुष्टि की जा रही है</b>\n"
                                 "<blockquote expandable>\n"
                                 f"<i>कृपया प्रतीक्षा करें (लगभग 5 मिनट)...</i>\n\n"
                                 f"<b>शेष समय :</b> {m:02d}:{s:02d}\n"
                                 "</blockquote>")
                else:
                    wait_txt = (f"⏳ <b>{_sc('Your payment is being verified')}</b>\n"
                                 "<blockquote expandable>\n"
                                 f"<i>{_sc('Please wait (approx 5 minutes)...')}</i>\n\n"
                                 f"<b>{_sc('Time Remaining')} :</b> {m:02d}:{s:02d}\n"
                                 "</blockquote>")
                await target_msg.edit_text(wait_txt, reply_markup=InlineKeyboardMarkup(kb_user))'''
content = re.sub(r'await target_msg\.edit_text\(.*?InlineKeyboardMarkup\(kb_user\)\s+\)', timer_localize, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Final localization and Join logic restoration complete.")
