import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_details = r'''async def _show_story_details(client, msg_or_query, story, lang, bot_cfg: dict = None):
    from pyrogram.types import Message
    is_msg = isinstance(msg_or_query, Message)
    bot_cfg = bot_cfg or {}

    name = story.get(f'story_name_{lang}', story.get('story_name_en'))
    price = story.get('price', 0)

    upi_enabled = bot_cfg.get('upi_enabled', True)
    upi_restricted = _is_upi_restricted()
    show_upi = upi_enabled and not upi_restricted

    if lang == 'hi':
        checkout_title = "🛍️ चेकआउट"
        item_label = "📦 स्टोरी :"
        amount_label = "💰 राशि :"
        desc_title = "भविष्य के अपडेट और गाइड"
        desc_content = (
            "इस प्रीमियम कहानी को खरीदने के बाद आपको इसके भविष्य के सभी अपडेट्स मिलते रहेंगे। "
            "साथ ही, आपको बॉट का उपयोग करने और कहानियों को आसानी से एक्सेस करने का एक विस्तृत गाइड भी मिलेगा।"
        )
        instruction = "भुगतान करने के लिए नीचे क्लिक करें। पूरा होने के बाद, वेरीफाई पर टैप करें।"
        pay_now_btn = "𝗥𝗮𝘇𝗼𝗿𝗽𝗮𝘆 → अभी भुगतान करें"
        upi_manual_btn = "𝗨𝗣𝗜 → मैन्युअल भुगतान"
        back_btn = "« ❮ वापस"
    else:
        checkout_title = "🛍️ 𝗖𝗛𝗘𝗖𝗞𝗢𝗨𝗧"
        item_label = "📦 𝗜𝘁𝗲𝗺 :"
        amount_label = "💰 𝗔𝗺𝗼𝘂𝗻𝘁 :"
        desc_title = "Future Updates & Guide"
        desc_content = (
            "You are paying for this premium story. You will receive all future updates for this story automatically. "
            "A complete guide on how to use the bot and access your stories will also be provided after purchase."
        )
        instruction = "Click below to pay. Once done, tap verify."
        pay_now_btn = "𝗥𝗮𝘇𝗼𝗿𝗽𝗮𝘆 → 𝗣𝗔𝗬 𝗡𝗢𝗪"
        upi_manual_btn = "𝗨𝗣𝗜 → 𝗠𝗔𝗡𝗨𝗔𝗟 𝗣𝗔𝗬𝗠𝗘𝗡𝗧"
        back_btn = "« ❮ 𝗕𝗔𝗖𝗞"

    txt = (
        f"<b>{checkout_title}</b>\n"
        f"────────────────────\n"
        f"<b>{item_label}</b> {name}\n"
        f"<b>{amount_label}</b> ₹{price}\n"
        f"────────────────────\n"
        f"<b>{desc_title}</b>\n"
        f"<blockquote expandable>{desc_content}</blockquote>\n"
        f"────────────────────\n"
        f"<i>{instruction}</i>"
    )

    kb = [
        [InlineKeyboardButton(pay_now_btn, callback_data=f"mb#pay#razorpay#{str(story['_id'])}")],
    ]
    if show_upi:
        kb.append([InlineKeyboardButton(upi_manual_btn, callback_data=f"mb#pay#upi#{str(story['_id'])}")])
    kb.append([InlineKeyboardButton(back_btn, callback_data="mb#return_main")])

    if is_msg:
        await msg_or_query.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await msg_or_query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb))'''

new_upi = r'''async def _show_upi_payment_screen(client, user_id, story, lang, bot_cfg, upi_id, qr_card, upi_uri, button_url):
    s_price = str(story["price"])
    p_name = (bot_cfg.get("upi_name") or "Merchant").strip()
    s_id = str(story['_id'])

    if lang == 'hi':
        title = "⟦ भुगतान पूरा करें ⟧"
        step1 = f"स्टेप १: ₹{s_price} का भुगतान करें"
        scan_txt = "QR कोड स्कैन करें या नीचे दिए गए विवरण का उपयोग करें:"
        upi_label = "UPI आईडी:"
        name_label = "नाम:"
        amount_label = "राशि:"
        warn_txt = "कृपया सुनिश्चित करें कि राशि सही है।"
        step2 = "स्टेप २: भुगतान वेरीफाई करें"
        done_txt = "भुगतान करने के बाद, स्क्रीनशॉट अपलोड करने के लिए 'पेमेंट कर दिया' पर क्लिक करें।"
        done_btn = "☑️ पेमेंट कर दिया"
        back_btn = "« वापस"
    else:
        title = "⟦ 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 ⟧"
        step1 = f"𝗦𝘁𝗲𝗽 𝟭: 𝗣𝗮𝘆 ₹{s_price}"
        scan_txt = "Scan the QR code or pay using the details below:"
        upi_label = "𝗨𝗣𝗜 𝗜𝗗:"
        name_label = "𝗡𝗮𝗺𝗲:"
        amount_label = "𝗔𝗺𝗼𝘂𝗻𝘁:"
        warn_txt = "Please ensure the amount is exact."
        step2 = "𝗦𝘁𝗲𝗽 𝟮: 𝗩𝗲𝗿𝗶𝗳𝘆 𝗣𝗮𝘆𝗺𝗲𝗻𝘁"
        done_txt = "After paying, click 'Payment Done' to upload your screenshot."
        done_btn = "✅ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗗𝗢𝗡𝗘"
        back_btn = "« 𝗕𝗔𝗖𝗞"

    txt = (
        f"<b>{title}</b>\n\n"
        f"<b>{step1}</b>\n"
        f"────────────────────\n"
        f"<i>{scan_txt}</i>\n\n"
        f"<b>{upi_label}</b> <code>{upi_id}</code>\n"
        f"<b>{name_label}</b> {p_name}\n"
        f"<b>{amount_label}</b> <code>₹{s_price}</code>\n\n"
        f"⚠️ <i>{warn_txt}</i>\n"
        f"────────────────────\n\n"
        f"<b>{step2}</b>\n"
        f"<i>{done_txt}</i>"
    )

    kb = [
        [InlineKeyboardButton(done_btn, callback_data=f"mb#upi_done#{s_id}")],
        [InlineKeyboardButton(back_btn, callback_data=f"mb#pay_back#{s_id}")]
    ]
    
    try:
        if qr_card:
            await client.send_photo(user_id, photo=qr_card, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            import urllib.parse
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=900x900&margin=1&data={urllib.parse.quote(upi_uri)}"
            await client.send_photo(user_id, photo=qr_url, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        await client.send_message(user_id, txt, reply_markup=InlineKeyboardMarkup(kb))'''

def replace_func(c, name, new_b):
    start_m = f"async def {name}"
    end_m = "async def"
    parts = c.split(start_m)
    second = parts[1].split(end_m, 1)
    return parts[0] + new_b + "\n\n" + end_m + second[1]

content = replace_func(content, "_show_story_details", new_details)
content = replace_func(content, "_show_upi_payment_screen", new_upi)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied details and upi screens successfully.")
