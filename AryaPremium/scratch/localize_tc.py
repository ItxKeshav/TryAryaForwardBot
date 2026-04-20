import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_tc = r'''async def _show_tc(client, user_id, story_id, lang='en'):
    if lang == 'hi':
        tc_title = "<b>⟦ नियम और शर्तें ⟧</b>"
        tc_subtitle = "खरीदने से पहले, कृपया निम्नलिखित पढ़ें और सहमत हों:"
        missing_title = "• <b>गायब एपिसोड</b>"
        missing_desc = "यदि सार्वजनिक रूप से जारी नहीं किया गया तो 3-5 एपिसोड अनुपलब्ध हो सकते हैं। बाद में उपलब्ध होने पर, उन्हें अपने आप जोड़ दिया जाएगा। 5 से अधिक गायब? सहायता से संपर्क करें।"
        quality_title = "• <b>क्वालिटी</b>"
        quality_desc = "पुराने एपिसोड्स की क्वालिटी कम हो सकती है। हम 100% क्वालिटी की गारंटी नहीं दे सकते, लेकिन हमेशा सर्वश्रेष्ठ वर्जन प्रदान करेंगे।"
        order_title = "• <b>एपिसोड क्रम</b>"
        order_desc = "एपिसोड्स कभी-कभी क्रम से बाहर हो सकते हैं। सभी फाइलें आर्या बॉट द्वारा क्लीन और ब्रांडेड हैं।"
        refund_title = "• <b>कोई रिफंड नहीं</b>"
        refund_desc = "भुगतान की पुष्टि होने और डिलीवरी शुरू होने के बाद कोई रिफंड नहीं दिया जाएगा।"
        fake_title = "• <b>नकली स्क्रीनशॉट</b>"
        fake_desc = "नकली या अमान्य भुगतान प्रमाण भेजने पर स्थायी रूप से प्रतिबंध लगा दिया जाएगा।"
        accept_btn = "सहमत हूँ"
        reject_btn = "अस्वीकार"
        back_btn = "‹ वापस"
    else:
        tc_title = "<b>⟦ 𝗧𝗘𝗥𝗠𝗦 & 𝗖𝗢𝗡𝗗𝗜𝗧𝗜𝗢𝗡𝗦 ⟧</b>"
        tc_subtitle = "𝖡𝖾𝖿𝗈𝗋𝖾 𝗉𝗎𝗋𝖼𝗁𝖺𝗌𝗂𝗇𝗀, 𝗉𝗅𝖾𝖺𝗌𝖾 𝗋𝖾𝖺𝖽 𝖺𝗇𝖽 𝖺𝗀𝗋𝖾𝖾 𝗍𝗈 𝗍𝗁𝖾 𝖿𝗈𝗅𝗅𝗈𝗐𝗂𝗇𝗀:"
        missing_title = "• <b>𝗠𝗶𝘀𝘀𝗶𝗻𝗴 𝗘𝗽𝗶𝘀𝗼𝗱𝗲𝘀</b>"
        missing_desc = "𝟹–𝟻 𝖾𝗉𝗂𝗌𝗈𝖽𝖾𝗌 𝗆𝖺𝗒 𝖻𝖾 𝗎𝗇𝖺𝗏𝖺𝗂ʟ𝖺𝖻𝗅𝖾 𝗂𝖿 𝗇𝗈𝗍 𝗉𝗎𝖻𝗅𝗂𝖼𝗅𝗒 𝗋𝖾𝗅𝖾𝖺𝗌𝖾𝖽. 𝖨𝖿 𝖺𝗏𝖺𝗂ʟ𝖺𝖻𝗅𝖾 𝗅𝖺𝗍𝖾𝗋, 𝗍𝗁𝖾𝗒 𝗐𝗂𝗅𝗅 𝖻𝖾 𝖺𝖽𝖽𝖾𝖽 𝖺𝗎𝗍𝗈𝗆𝖺𝗍𝗂𝖼𝖺𝗅𝗅𝗒."
        quality_title = "• <b>𝗤𝘂𝗮𝗹𝗶𝘁𝘆</b>"
        quality_desc = "𝖲𝗈𝗆𝖾 𝗈𝗅𝖽𝖾𝗋 𝖾𝗉𝗂𝗌𝗈𝖽𝖾𝗌 𝗆𝖺𝗒 𝗁𝖺𝗏𝖾 𝗋𝖾𝖽𝗎𝖼𝖾𝖽 𝗊𝗎𝖺𝗅𝗂𝗍𝗒. 𝖶𝖾 𝖼𝖺𝗇𝗇𝗈𝗍 𝗀𝗎𝖺𝗋𝖺𝗇𝗍𝖾𝖾 𝟣𝟢𝟢% 𝗊𝗎𝖺𝗅𝗂𝗍𝗒, 𝖻𝗎𝗍 𝖺𝗅𝗐𝖺𝗒𝗌 𝗉𝗋𝗈𝗏𝗂𝖽𝖾 𝖻𝖾𝗌𝗍 𝗏𝖾𝗋𝗌𝗂𝗈𝗇."
        order_title = "• <b>𝗘𝗽𝗶𝘀𝗼𝗱𝗲 𝗢𝗿𝗱𝗲𝗿</b>"
        order_desc = "𝖤𝗉𝗂𝗌𝗈𝖽𝖾𝗌 𝗆𝖺𝗒 𝗋𝖺𝗋𝖾𝗅𝗒 𝖻𝖾 𝗈𝗎𝗍 𝗈𝖿 𝗌𝖾𝗊𝗎𝖾𝗇𝖼𝖾. 𝖠𝗅𝗅 𝖿𝗂𝗅𝖾𝗌 𝖺𝗋𝖾 𝖼𝗅𝖾𝖺𝗇𝖾𝖽 𝖺𝗇𝖽 𝖻𝗋𝖺𝗇𝖽𝖾𝖽 𝖻𝗒 𝖠𝗋𝗒𝖺 𝖡𝗈𝗍."
        refund_title = "• <b>𝗡𝗼 𝗥𝗲𝗳𝘂𝗻𝗱𝘀</b>"
        refund_desc = "𝖭𝗈 𝗋𝖾𝖿𝗎𝗇𝖽𝗌 𝗈𝗇𝖼𝖾 𝗉𝖺𝗒𝗆𝖾𝗇𝗍 𝗂𝗌 𝖼𝗈𝗇𝖿𝗂𝗋𝗆𝖾𝖽 𝖺𝗇𝖽 𝖽𝖾𝗅𝗂𝗏𝖾𝗋𝗒 𝗌𝗍𝖺𝗋𝗍𝗌."
        fake_title = "• <b>𝗙𝗮𝗸𝗲 𝗦𝗰𝗿𝗲𝗲𝗻𝘀𝗵𝗼𝘁𝘀</b>"
        fake_desc = "𝖥𝖺𝗄𝖾 𝗈𝗋 𝗂𝗇𝗏𝖺𝗅𝗂𝖽 𝗉𝖺𝗒𝗆𝖾𝗇𝗍 𝗉𝗋𝗈𝗈𝖿𝗌 𝗐𝗂𝗅𝗅 𝗅𝖾𝖺𝖽 𝗍𝗈 𝗉𝖾𝗋𝗆𝖺𝗇𝖾𝗇𝗍 𝖻𝖺𝗇."
        accept_btn = "𝗜 𝗔𝗰𝗰𝗲𝗽𝘁"
        reject_btn = "𝗥𝗲𝗷𝗲𝗰𝘁"
        back_btn = "‹ Back"

    tc_text = (
        f"{tc_title}\n\n"
        f"{tc_subtitle}\n\n"
        f"<blockquote expandable>{missing_title}\n{missing_desc}</blockquote>\n"
        f"<blockquote expandable>{quality_title}\n{quality_desc}</blockquote>\n"
        f"<blockquote expandable>{order_title}\n{order_desc}</blockquote>\n"
        f"<blockquote expandable>{refund_title}\n{refund_desc}</blockquote>\n"
        f"<blockquote expandable>{fake_title}\n{fake_desc}</blockquote>"
    )
    
    kb = [
        [InlineKeyboardButton(accept_btn, callback_data=f"mb#tc_accept_{story_id}")],
        [InlineKeyboardButton(reject_btn, callback_data="mb#tc_reject"),
         InlineKeyboardButton(back_btn, callback_data=f"mb#view_{story_id}")]
    ]
    from pyrogram import enums
    await client.send_message(user_id, tc_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)
'''

# Find _show_tc
start = -1
for i, line in enumerate(lines):
    if line.strip().startswith("async def _show_tc"):
        start = i
        break
if start != -1:
    # Find next function
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].strip().startswith("async def ") or lines[i].strip().startswith("def "):
            end = i
            break
    lines[start:end] = [new_tc + "\n"]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Localized T&C screen successfully.")
