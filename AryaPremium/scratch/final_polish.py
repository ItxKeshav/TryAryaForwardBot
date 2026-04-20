import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_dispatch = r'''async def dispatch_delivery_choice(client, user_id, story):
    """
    Called when Admin approves OR user already owns. Shows inline delivery options.
    """
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    story_id_str = str(story['_id'])

    used_channels = user.get("used_channels", [])
    mode = story.get("delivery_mode") or ("single" if story.get("channel_id") else "pool")
    fallback = await db.db.premium_channels.find_one({"type": "delivery"})
    pool = story.get("channel_pool") or []
    has_any_delivery = bool(story.get('channel_id') or pool or (fallback and fallback.get("channel_id")))
    can_use_channel = (story_id_str not in used_channels) and (mode != "dm_only") and has_any_delivery

    # Find purchase source to display
    from bson.objectid import ObjectId
    purchase = await db.db.premium_purchases.find_one({"user_id": int(user_id), "story_id": ObjectId(story_id_str)})
    method_info = "Verified Purchase"
    if purchase:
        src = str(purchase.get("source", "manual")).lower()
        if src == "razorpay": method_info = "💳 Razorpay"
        elif src == "easebuzz": method_info = "💸 Easebuzz"
        elif src == "upi": method_info = "🏦 Manual UPI"
        else: method_info = f"🛒 {src.capitalize()}"

    s_name = story.get(f'story_name_{lang}', story.get('story_name_en'))

    if lang == 'hi':
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
    kb.append([InlineKeyboardButton(back_btn_txt, callback_data="mb#main_back")])

    await client.send_message(user_id, del_txt, reply_markup=InlineKeyboardMarkup(kb))'''

# Localize screenshot handler and its timer
def find_and_localize(lines):
    # Localize _process_screenshot starter text
    for i in range(len(lines)):
        if "txt_user = (" in lines[i] and "Your payment is being verified" in lines[i+1]:
            lines[i+1:i+6] = [r'''        f"⏳ <b>{_sc('Your payment is being verified') if lang != 'hi' else 'आपके भुगतान की पुष्टि की जा रही है'}</b>\n"
        "<blockquote expandable>\n"
        f"<i>{_sc('Please wait (approx 5 minutes)...') if lang != 'hi' else 'कृपया प्रतीक्षा करें (लगभग 5 मिनट)...'}</i>\n\n"
        f"<b>{_sc('Time Remaining') if lang != 'hi' else 'शेष समय'} :</b> 05:00\n"
        "</blockquote>"\n''']
            break
    
    # Localize _live_timer loop text
    for i in range(len(lines)):
        if "f\"⏳ <b>{_sc('Your payment is being verified')}</b>\"" in lines[i]:
            lines[i:i+6] = [r'''                    (f"⏳ <b>{_sc('Your payment is being verified') if lang != 'hi' else 'आपके भुगतान की पुष्टि की जा रही है'}</b>\n"
                     "<blockquote expandable>\n"
                     f"<i>{_sc('Please wait (approx 5 minutes)...') if lang != 'hi' else 'कृपया प्रतीक्षा करें (लगभग 5 मिनट)...'}</i>\n\n"
                     f"<b>{_sc('Time Remaining') if lang != 'hi' else 'शेष समय'} :</b> {m:02d}:{s:02d}\n"
                     "</blockquote>"),\n''']
            break
    return lines

lines = find_and_localize(lines)

# Apply dispatch_delivery_choice
for i in range(len(lines)):
    if lines[i].strip().startswith("async def dispatch_delivery_choice"):
        # Find end of function (it ends before _do_dm_delivery)
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith("async def _do_dm_delivery"):
            j += 1
        lines[i:j] = [new_dispatch + "\n\n"]
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Localized delivery choice and screen timers successfully.")
