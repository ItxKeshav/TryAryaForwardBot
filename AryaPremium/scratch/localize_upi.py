import os

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_do_upi_msg = r'''        elif method == "upi":
            upi_id = await db.get_config("upi_id") or "heyjeetx@naviaxis"
            bt = await db.db.premium_bots.find_one({"id": client.me.id})
            bt_cfg = bt.get("config", {}) if bt else {}
            
            s_price = str(story["price"])
            s_name = story.get(f'story_name_{lang}', story.get('story_name_en', 'Story'))
            
            # Generate Premium UPI Card
            qr_card = None
            try:
                # Pass the configured payee name to match the official bank record
                p_name = (bt_cfg.get("upi_name") or "Merchant").strip()
                qr_card = generate_upi_card(upi_id, s_price, s_name, payee_name=p_name)
            except Exception as e:
                logger.error(f"UPI Card generation failed: {e}")
                qr_card = None

            upi_uri = _build_upi_uri(
                upi_id=upi_id,
                payee_name=(bt_cfg.get("upi_name") or "").strip(),
                amount=int(story["price"]),
                note=f"Payment for {s_name[:20]}"
            )

            slice_api_url = (getattr(Config, "SLICEURL_API_URL", "") or "").strip()
            slice_api_key = (getattr(Config, "SLICEURL_API_KEY", "") or "").strip()
            slice_direct = ""
            if slice_api_url and slice_api_key.startswith("slc_"):
                slice_direct = await _sliceurl_api_shorten(upi_uri)
            button_url = slice_direct

            await db.db.premium_checkout.update_one(
                {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)},
                {"$set": {
                    "status": "pending_gateway",
                    "bot_username": client.me.username,
                    "method": "upi",
                    "upi_uri": upi_uri,
                    "pay_link_copy": button_url,
                    "updated_at": datetime.utcnow(),
                }, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )

            p_name = (bt_cfg.get("upi_name") or "Merchant").strip()
            
            if lang == 'hi':
                txt = (
                    f"<b>⟦ {_sc('पेमेंट पूरा करें')} ⟧</b>\n\n"
                    f"<b>स्टेप 𝟷: ₹{s_price} का भुगतान करें</b>\n\n"
                    f"<blockquote>• QR कोड स्कैन करें या नीचे दिए गए विवरण का उपयोग करें:</blockquote>\n"
                    f"<blockquote><b>UPI ID:</b> <code>{upi_id}</code>\n"
                    f"<b>नाम:</b> <code>{p_name}</code>\n"
                    f"<b>राशि:</b> <code>₹{s_price}</code></blockquote>\n\n"
                    f"• सुनिश्चित करें कि राशि सही भरी गई है।\n\n"
                    f"<b>स्टेप य: भुगतान का सत्यापन</b>\n\n"
                    f"• भुगतान के बाद, अपना स्क्रीनशॉट अपलोड करने के लिए <b>पेमेंट हो गया</b> पर क्लिक करें।\n"
                    f"────────────────────"
                )
                kb = [
                    [InlineKeyboardButton("☑️ पेमेंट हो गया", callback_data=f"mb#upi_done#{s_id}")],
                    [InlineKeyboardButton("« ❮ वापस", callback_data=f"mb#pay_back#{s_id}")]
                ]
            else:
                txt = (
                    f"<b>⟦ {_sc('COMPLETE PAYMENT')} ⟧</b>\n\n"
                    f"<b>𝚂𝚝𝚎𝚙 𝟷: Pay ₹{s_price}</b>\n\n"
                    f"<blockquote>• Scan the QR code or pay using the details below:</blockquote>\n"
                    f"<blockquote><b>UPI ID:</b> <code>{upi_id}</code>\n"
                    f"<b>Name:</b> <code>{p_name}</code>\n"
                    f"<b>Amount:</b> <code>₹{s_price}</code></blockquote>\n\n"
                    f"• Make sure the amount is entered correctly.\n\n"
                    f"<b>𝚂𝚝𝚎𝚙 𝟸: Verify Payment</b>\n\n"
                    f"• After payment, click <b>PAYMENT DONE</b> to upload your screenshot.\n"
                    f"────────────────────"
                )
                kb = [
                    [InlineKeyboardButton(f"☑️ {_sc('PAYMENT DONE')}", callback_data=f"mb#upi_done#{s_id}")],
                    [InlineKeyboardButton(f"« ❮ {_sc('BACK')}", callback_data=f"mb#pay_back#{s_id}")]
                ]
            
            await query.message.delete()
            try:
                if qr_card:
                    await client.send_photo(user_id, photo=qr_card, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
                else:
                    import urllib.parse
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=900x900&margin=1&data={urllib.parse.quote(upi_uri)}"
                    await client.send_photo(user_id, photo=qr_url, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
            except Exception as e:
                logger.warning(f"UPI payment screen send failed: {e}")
                kb2 = [[InlineKeyboardButton(f"☑️ {'पेमेंट हो गया' if lang=='hi' else _sc('PAYMENT DONE')}", callback_data=f"mb#upi_done#{s_id}")]]
                await client.send_message(user_id, txt, reply_markup=InlineKeyboardMarkup(kb2))'''

new_upi_done_logic = r'''    elif cmd == "upi_done":
        s_id = data[2]
        from bson.objectid import ObjectId
        await db.db.premium_checkout.update_one(
            {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)},
            {"$set": {"status": "waiting_screenshot", "updated_at": datetime.utcnow()}}
        )
        if lang == 'hi':
            await query.answer("कृपया अपना स्क्रीनशॉट भेजें।", show_alert=True)
            await query.message.reply_text(
                "<b>📸 पेमेंट स्क्रीनशॉट भेजें</b>\n\n"
                "सत्यापन शुरू करने के लिए कृपया अपने सफल भुगतान का स्क्रीनशॉट यहाँ भेजें।",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« वापस", callback_data=f"mb#pay#upi#{s_id}")]])
            )
        else:
            await query.answer(_sc("Please send your screenshot."), show_alert=True)
            await query.message.reply_text(
                f"<b>📸 {_sc('SEND PAYMENT SCREENSHOT')}</b>\n\n"
                f"{_sc('Please send your successful payment screenshot here to begin verification.')}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"« {_sc('BACK')}", callback_data=f"mb#pay#upi#{s_id}")]])
            )'''

# Manual replacement for UPI page
start_idx = -1
end_idx = -1
for i in range(len(lines)):
    if 'elif method == "upi":' in lines[i]:
        start_idx = i
        # find where it ends
        for j in range(i+1, len(lines)):
            if 'elif cmd == "pay_back":' in lines[j] or 'elif cmd == "upi_done":' in lines[j]:
                end_idx = j
                break
        break

if start_idx != -1 and end_idx != -1:
    lines[start_idx:end_idx] = [new_do_upi_msg + "\n\n"]

# Manual replacement for upi_done
start_idx = -1
end_idx = -1
for i in range(len(lines)):
    if 'elif cmd == "upi_done":' in lines[i]:
        start_idx = i
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith("elif ") or lines[j].strip().startswith("#"):
                end_idx = j
                break
        break
if start_idx != -1 and end_idx != -1:
    lines[start_idx:end_idx] = [new_upi_done_logic + "\n\n"]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Updated UPI payment screen and confirmation localization.")
