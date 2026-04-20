import os
import re

file_path = r'c:\Users\User\Downloads\AryaBotNew\TryAryaBot\AryaPremium\plugins\userbot\market_seller.py'

# Cleanly rewrite the problematic functions with correct escaping
new_start_func = r'''async def _process_start(client, message):
    user_id = message.from_user.id
    from pyrogram import enums
    
    is_new = await db.db.users.count_documents({"id": int(user_id)}) == 0
    if is_new:
        from utils import log_arya_event
        asyncio.create_task(log_arya_event(
            event_type="NEW USER JOIN",
            user_id=user_id,
            user_info={"first_name": message.from_user.first_name, "last_name": getattr(message.from_user, "last_name", ""), "username": getattr(message.from_user, "username", "")},
            details="User started the Premium Store bot for the first time."
        ))
        
    user = await db.get_user(user_id)
    args = message.command

    if 'lang' not in user:
        lang_prompt = (
            "<b>⟦ 𝗦𝗘𝗟𝗘𝗖𝗧 𝗟𝗔𝗡𝗚𝗨𝗔𝗚𝗘 ⟧</b>\n\n"
            "<blockquote expandable>"
            "<i>Choose your preferred language to continue.\n"
            "अपनी भाषा चुनें और आगे बढ़ें।</i>"
            "</blockquote>"
        )
        kb = [[InlineKeyboardButton("• English", callback_data="mb#lang#en"),
               InlineKeyboardButton("• हिंदी", callback_data="mb#lang#hi")]]
        return await message.reply_text(lang_prompt, reply_markup=InlineKeyboardMarkup(kb))

    lang = user.get('lang', 'en')

    # ── Force Join Logic (Unicode only, no emojis) ──
    INVITE_CHANNEL = "https://t.me/AryaPremiumTG"
    try:
        chat_member = await client.get_chat_member("@AryaPremiumTG", user_id)
        if chat_member.status in (enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT):
            raise Exception("Not joined")
    except Exception:
        if lang == 'hi':
            join_title = "𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥𝗘𝗡"
            join_txt = (
                "𝗕𝗼𝘁 𝗸𝗼 𝘂𝘀𝗲 𝗸𝗮𝗿𝗻𝗲 𝗸𝗲 𝗹𝗶𝘆𝗲 𝗮𝗮𝗽𝗸𝗼 𝗵𝘂𝗺𝗮𝗿𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗶𝗻 𝗷𝗼𝗶𝗻 𝗵𝗼𝗻𝗮 𝗵𝗼𝗴𝗮।\n\n"
                "<blockquote expandable>"
                "𝗝𝗼𝗶𝗻 𝗸𝗮𝗿𝗻𝗲 𝗸𝗲 𝗯𝗮𝗮𝗱 '𝗝𝗼𝗶𝗻𝗲𝗱' 𝗽𝗮𝗿 𝗰𝗹𝗶𝗰𝗸 𝗸𝗮𝗿𝗲𝗻। 𝗜𝘀𝘀𝗲 𝗮𝗮𝗽𝗸𝗼 𝘀𝗮𝗯𝗵𝗶 𝗮𝗱𝘃𝗮𝗻𝗰𝗲𝗱 𝗳𝗲𝗮𝘁𝘂𝗿𝗲𝘀 𝗮𝘂𝗿 𝘂𝗽𝗱𝗮𝘁𝗲𝘀 𝗺𝗶𝗹𝘁𝗲 𝗿𝗮𝗵𝗲𝗻𝗴𝗲।\n"
                "</blockquote>"
            )
            join_btn = "✓ 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟"
            joined_btn = "✓ 𝗝𝗢𝗜𝗡 𝗞𝗔𝗥 𝗟𝗜𝗬𝗔"
        else:
            join_title = "𝗝𝗢𝗜𝗡 𝗢𝗨𝗥 𝗖𝗛𝗔𝗡𝗡𝗘𝗟"
            join_txt = (
                "𝗬𝗼𝘂 𝗺𝘂𝘀𝘁 𝗷𝗼𝗶𝗻 𝗼𝘂𝗿 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗯𝗼𝘁.\n\n"
                "<blockquote expandable>"
                "𝗔𝗳𝘁𝗲𝗿 𝗷𝗼𝗶𝗻𝗶𝗻𝗴, 𝗰𝗹𝗶𝗰𝗸 '𝗝𝗼𝗶𝗻𝗲𝗱' 𝘁𝗼 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗲. 𝗬𝗼𝘂 𝘄𝗶𝗹𝗹 𝗴𝗲𝘁 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗮𝗹𝗹 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝘀𝘁𝗼𝗿𝗶𝗲𝘀 𝗮𝗻𝗱 𝗶𝗻𝘀𝘁𝗮𝗻𝘁 ᴅᴇʟɪᴠᴇʀʏ."
                "</blockquote>"
            )
            join_btn = "✓ 𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟"
            joined_btn = "✓ 𝗝𝗢𝗜𝗡Ｅᴅ"

        join_kb = [
            [InlineKeyboardButton(join_btn, url=INVITE_CHANNEL)],
            [InlineKeyboardButton(joined_btn, callback_data="mb#joined_check")]
        ]
        return await message.reply_text(f"<b>{join_title}</b>\n\n{join_txt}", reply_markup=InlineKeyboardMarkup(join_kb))

    # ── Deep Link Handler ──
    if len(args) > 1 and args[1].startswith("buy_"):
        story_id = args[1].replace("buy_", "")
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(story_id)})
        if story:
            has_paid = await db.has_purchase(user_id, story_id)
            if has_paid:
                msg = "✅ You already own this story. Sending delivery options..." if lang == 'en' else "✅ आप पहले ही इस स्टोरी को खरीद चुके हैं। डिलीवरी विकल्प भेजे जा रहे हैं..."
                await message.reply_text(msg)
                return await dispatch_delivery_choice(client, user_id, story)
            return await _show_story_profile(client, user_id, story, lang)

    # Standard Main Menu
    wait_msg_txt = "WAIT A SECOND..." if lang == 'en' else "कृपया प्रतीक्षा करें..."
    wait_msg = await message.reply_text(f"<b>› › ⏳ {wait_msg_txt}</b>", parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(0.4)
    await wait_msg.delete()

    await _send_main_menu(client, user_id, message.from_user, lang, reply_to_message_id=message.id)'''

new_story_details_func = r'''async def _show_story_details(client, msg_or_query, story, lang, bot_cfg: dict = None):
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

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Using raw replacement to avoid escaping issues
content = re.sub(r'async def _process_start\(client, message\):.*?(\n(?=async def|def|#))', new_start_func + "\n", content, flags=re.DOTALL)
content = re.sub(r'async def _show_story_details\(client, msg_or_query, story, lang, bot_cfg: dict = None\):.*?(\n(?=async def|def|#))', new_story_details_func + "\n", content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed functions in market_seller.py")
