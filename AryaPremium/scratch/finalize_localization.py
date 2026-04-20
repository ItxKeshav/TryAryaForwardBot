import os
import re

file_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\plugins\userbot\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Razorpay Verification Status Text
rzp_verify_pattern = r'm = await query\.message\.edit_text\(f"🛡️ <b>\{_sc\(\'VERIFYING PAYMENT\'\)\}...</b>\\n<i>\{_sc\(\'Checking with\'\)\} \{method\.capitalize\(\)\} \{_sc\(\'servers.\'\)\}</i>"\)'
new_rzp_verify = """
        if lang == 'hi':
            verify_txt = f"🛡️ <b>भुगतान की पुष्टि की जा रही है...</b>\\n<i>{method.capitalize()} सर्वर से चेक किया जा रहा है।</i>"
        else:
            verify_txt = f"🛡️ <b>{_sc('VERIFYING PAYMENT')}...</b>\\n<i>{_sc('Checking with')} {method.capitalize()} {(_sc('servers.'))}</i>"
        m = await query.message.edit_text(verify_txt)
"""
if 'if lang == \'hi\':' not in content:
    content = re.sub(rzp_verify_pattern, new_rzp_verify.strip(), content)

# 2. UPI Screenshot Upload Screen
# Handle upi_done replacement more robustly
upi_done_start = 'elif cmd == "upi_done":'
upi_done_end = 'await client.send_message(user_id, '
# We find the following block
# elif cmd == "upi_done":
#     ...
#     await client.send_message(user_id, ...)

new_upi_done = """elif cmd == "upi_done":
        s_id = data[2]
        from bson.objectid import ObjectId
        await db.db.premium_checkout.update_one(
            {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)},
            {"$set": {"status": "waiting_screenshot", "updated_at": datetime.utcnow()}}
        )
        await query.answer()
        if lang == 'hi':
            sub_txt = (
                "<b>☑️ भुगतान सबमिट किया गया</b>\\n\\n"
                "<blockquote expandable>"
                "<i>हमें आपके भुगतान को वेरीफाई करने की आवश्यकता है।</i>\\n"
                "<i>कृपया सफल भुगतान का स्क्रीनशॉट अभी यहां अपलोड करें।</i>\\n"
                "<i>सुनिश्चित करें कि ट्रांजैक्शन आईडी / UTR स्पष्ट रूप से दिखाई दे रहा हो।</i>\\n"
                "</blockquote>"
            )
        else:
            sub_txt = (
                f"<b>☑️ {_sc('PAYMENT SUBMITTED')}</b>\\n\\n"
                "<blockquote expandable>"
                f"<i>{_sc('Our system needs to verify your payment.')}</i>\\n"
                f"<i>{_sc('Please upload the successful payment screenshot here now.')}</i>\\n"
                f"<i>{_sc('Ensure the Transaction ID / UTR is clearly visible.')}</i>\\n"
                "</blockquote>"
            )
        await client.send_message(user_id, sub_txt)
"""

# Finding the block
current_upi_done = re.search(r'elif cmd == "upi_done":.*?await client\.send_message\(user_id,.*?\)', content, re.DOTALL)
if current_upi_done:
    content = content.replace(current_upi_done.group(0), new_upi_done.strip())

# 3. Verification Progress Timer
new_timer = """
                if lang == 'hi':
                    wait_txt = (f"⏳ <b>आपके भुगतान की पुष्टि की जा रही है</b>\\n"
                                 "<blockquote expandable>"
                                 f"<i>कृपया प्रतीक्षा करें (लगभग 5 मिनट)...</i>\\n\\n"
                                 f"<b>शेष समय :</b> {m:02d}:{s:02d}\\n"
                                 "</blockquote>")
                else:
                    wait_txt = (f"⏳ <b>{_sc('Your payment is being verified')}</b>\\n"
                                 "<blockquote expandable>"
                                 f"<i>{_sc('Please wait (approx 5 minutes)...')}</i>\\n\\n"
                                 f"<b>{_sc('Time Remaining')} :</b> {m:02d}:{s:02d}\\n"
                                 "</blockquote>")
                await target_msg.edit_text(wait_txt, reply_markup=InlineKeyboardMarkup(kb_user))
"""
content = re.sub(r'await target_msg\.edit_text\(.*?InlineKeyboardMarkup\(kb_user\)\s+\)', new_timer.strip(), content, flags=re.DOTALL)

# 4. Delivery Information Screen
new_delivery = """
    if lang == 'hi':
        del_txt = (
            "<b>✅ एक्सेस मिल गया है!</b>\\n\\n"
            f"<b>स्टोरी:</b> {s_name}\\n"
            + (f"<b>भुगतान तरीका:</b> {method_info}\\n" if method_info else "")
            + "\\n"
            + "<b>ℹ️ डिलीवरी की जानकारी</b>\\n\\n"
            + "<blockquote>• <b>DM डिलीवरी:</b> फाइलें सीधे यहां भेजी जाती हैं। उन्हें तुरंत सेव या फॉरवर्ड करें—वे कुछ समय बाद अपने आप डिलीट हो जाती हैं।</blockquote>\\n"
            + "<blockquote>• <b>चैनल लिंक:</b> एक वन-टाइम प्राइवेट इनवाइट लिंक जेनरेट किया जाता है। प्रत्येक स्टोरी के लिए केवल एक चैनल लिंक की अनुमति है।</blockquote>\\n"
            + "<blockquote>• <b>लाइफटाइम एक्सेस:</b> आप किसी भी खरीदी हुई स्टोरी को कभी भी <b>मुख्य मेनू ⟶ मेरी स्टोरीज</b> से एक्सेस कर सकते हैं।</blockquote>\\n"
            + "──────────────\\n\\n"
            + "आप अपनी फाइलें कैसे प्राप्त करना चाहेंगे?"
        )
        dm_btn_txt = "⤓ DM में प्राप्त करें"
        chan_btn_txt = "➦ चैनल लिंक प्राप्त करें"
        back_btn_txt = "« ❮ मुख्य मेनू"
    else:
        del_txt = (
            "<b>✅ Access Granted!</b>\\n\\n"
            f"<b>Product:</b> {s_name}\\n"
            + (f"<b>Method:</b> {method_info}\\n" if method_info else "")
            + "\\n"
            + "<b>ℹ️ Delivery Info</b>\\n\\n"
            + "<blockquote>• <b>DM Delivery:</b> Files are sent directly here. Save or forward them immediately—they auto-delete after some time.</blockquote>\\n"
            + "<blockquote>• <b>Channel Link:</b> A one-time private invite link is generated. Each story allows only one channel link per account.</blockquote>\\n"
            + "<blockquote>• <b>Lifetime Access:</b> You can re-access any purchased story anytime from <b>Main Menu ⟶ My Stories</b>.</blockquote>\\n"
            + "──────────────\\n\\n"
            + "How would you like to receive your files?"
        )
        dm_btn_txt = f"⤓ {_sc('RECEIVE IN DM')}"
        chan_btn_txt = f"➦ {_sc('ACCESS CHANNEL LINK')}"
        back_btn_txt = f"« ❮ {_sc('MAIN MENU')}"

    kb = [[InlineKeyboardButton(dm_btn_txt, callback_data=f"mb#deliver_dm#{story_id_str}")]]
    if can_use_channel:
        kb.append([InlineKeyboardButton(chan_btn_txt, callback_data=f"mb#deliver_channel#{story_id_str}")])
    kb.append([InlineKeyboardButton(back_btn_txt, callback_data="mb#main_back")])
"""
delivery_pattern = re.search(r'del_txt = \(.*?How would you like to receive your files\?\"\s+\).*?kb = \[.*?\]', content, re.DOTALL)
if delivery_pattern:
    content = content.replace(delivery_pattern.group(0), new_delivery.strip())

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Finished localization update")
