import os
import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix the syntax error at upi_done end
content = content.replace('await client.send_message(user_id, sub_txt))', 'await client.send_message(user_id, sub_txt)')

# 2. Localize Gateway Checkout (Razorpay/Easebuzz)
gateway_checkout_block = r'''if lang == 'hi':
                check_txt = (
                    f"<b>🛍️ चेकआउट</b>\\n"
                    f"────────────────────\\n"
                    f"<b>📦 स्टोरी :</b> {story.get(f'story_name_{lang}', story.get('story_name_en'))}\\n"
                    f"<b>💰 राशि :</b> ₹{price}\\n"
                    f"────────────────────\\n"
                    f"आप इस प्रीमियम कहानी के लिए भुगतान कर रहे हैं।\\n"
                    f"तुरंत वेरिफिकेशन और डिलीवरी।\\n"
                    f"────────────────────\\n"
                    f"<i>भुगतान करने के लिए नीचे क्लिक करें। पूरा होने के बाद, वेरीफाई पर टैप करें।</i>"
                )
                kb = [
                    [InlineKeyboardButton(f"💳 {method.upper()} द्वारा भुगतान", url=url)],
                    [InlineKeyboardButton(f"✅ भुगतान वेरीफाई करें", callback_data=f"mb#{method}_check#{s_id}")],
                    [InlineKeyboardButton(f"« ❮ वापस", callback_data="mb#return_main")]
                ]
            else:
                kb = [
                    [InlineKeyboardButton(f"💳 {_sc('PAY VIA')} {_sc(method.upper())}", url=url)],
                    [InlineKeyboardButton(f"✅ {_sc('VERIFY PAYMENT')}", callback_data=f"mb#{method}_check#{s_id}")],
                    [InlineKeyboardButton(f"« ❮ {_sc('BACK')}", callback_data="mb#return_main")]
                ]
                check_txt = (
                    f"<b>🛍️ {_sc('CHECKOUT')}</b>\\n"
                    f"────────────────────\\n"
                    f"<b>📦 {_sc('Item')} :</b> {story.get('story_name_en', 'Premium Story')}\\n"
                    f"<b>💰 {_sc('Amount')} :</b> ₹{price}\\n"
                    f"────────────────────\\n"
                    f"{_sc('You are paying for this premium story.')}\\n"
                    f"{_sc('Instant verification & delivery.')}\\n"
                    f"────────────────────\\n"
                    f"<i>{_sc('Click below to pay. Once done, tap Verify.')}</i>"
                )
            await query.message.edit_text(check_txt, reply_markup=InlineKeyboardMarkup(kb))'''

old_gateway_pattern = re.search(r'kb = \[.*?\]\s+check_txt = \(.*?\)\s+await query\.message\.edit_text\(check_txt, reply_markup=InlineKeyboardMarkup\(kb\)\)', content, re.DOTALL)
if old_gateway_pattern:
    content = content.replace(old_gateway_pattern.group(0), gateway_checkout_block.replace('\\n', '\n'))

# 3. Final polish on _process_start (Unicode formatting)
# I want to ensure the 'Joined' status check is blocking and has the right title.
# I already did this in fix_newlines, but let's make sure INVITE_CHANNEL is correct.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied final fixes and gateway localization")
