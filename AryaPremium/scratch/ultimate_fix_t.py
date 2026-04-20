import os

file_path = r'AryaPremium/plugins/userbot/market_seller.py'

# The clean T dictionary
clean_t = """T = {
    "en": {
        "welcome": "Welcome to",
        "store": "Store",
        "intro": "Browse our premium collection. Tap Marketplace to explore stories by platform.",
        "tc_accept": "✅ I Accept the Terms",
        "tc_reject": "❌ I Reject",
        "no_stories": "No stories currently available.",
        "pay_upi": "Pay via UPI",
        "back": "❮ Back",
        "qr_msg": \"\"\"<b>💳 Complete Payment</b>

• Scan the QR code above.
• Amount: ₹{price}

<b>After paying, send the successful payment screenshot here.</b>\"\"\",
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
        "set_prompt": \"\"\"<b>⚙️ Settings</b>

Select your language:\"\"\",
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
        "req_search_prompt": \"\"\"<b>🔍 SEARCH / REQUEST STORY</b>

Type the <b>Story Name</b> you want to search or request:\"\"\",
        "req_cancel": "Process Cancelled.",
        "req_step1": \"\"\"<b>Step 1/3:</b>
Please enter the <b>Story Name</b> you want to request:\"\"\",
        "req_step2": \"\"\"<b>Step 2/3:</b>
Choose the <b>Platform</b> (e.g. Ullu, AltBalaji):\"\"\",
        "req_step3": \"\"\"<b>Step 3/3:</b>
How would you like it? (e.g. Only Episodes, Full Movie, etc.):\"\"\",
        "req_success": \"\"\"✅ <b>Request Submitted!</b>

Our team will search for this story and update you soon. Check status in <b>Profile -> My Requests</b>.\"\"\"
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
        "qr_msg": \"\"\"<b>💳 पेमेंट पूरा करें</b>

• ऊपर QR स्कैन करें।
• राशि: ₹{price}

<b>पेमेंट के बाद स्क्रीनशॉट यहाँ भेजें।</b>\"\"\",
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
        "set_prompt": \"\"\"<b>⚙️ सेटिंग्स</b>

अपनी पसंदीदा भाषा चुनें:\"\"\",
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
        "req_search_prompt": \"\"\"<b>🔍 स्टोरी खोजें / अनुरोध करें</b>

उस <b>कहानी का नाम</b> लिखें जिसे आप खोजना या अनुरोध करना चाहते हैं:\"\"\",
        "req_cancel": "प्रक्रिया रद्द कर दी गई।",
        "req_step1": \"\"\"<b>स्टेप 1/3:</b>
कृपया उस <b>कहानी का नाम</b> लिखें जिसका आप अनुरोध करना चाहते हैं:\"\"\",
        "req_step2": \"\"\"<b>स्टेप 2/3:</b>
<b>प्लेटफॉर्म</b> चुनें (जैसे: Ullu, AltBalaji):\"\"\",
        "req_step3": \"\"\"<b>स्टेप 3/3:</b>
आपको यह कैसे चाहिए? (जैसे: केवल एपिसोड, पूरी फिल्म, आदि):\"\"\",
        "req_success": \"\"\"✅ <b>अनुरोध जमा हो गया!</b>

हमारी टीम इस कहानी को खोजेगी और जल्द ही आपको अपडेट करेगी। स्टेटस देखने के लिए <b>प्रोफाइल -> मेरे अनुरोध</b> पर जाएं।\"\"\"
    }
}
"""

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
added = False

for i, line in enumerate(lines):
    # Detect start of T dictionary
    if line.strip().startswith('T = {'):
        if not added:
            new_lines.append(clean_t + "\n")
            added = True
        skip = True
        continue
    
    # Detect end of the mess by looking for the next function definition
    if skip and (line.strip().startswith('def _get_main_menu') or line.strip().startswith('def _get_start_buttons')):
        skip = False
    
    if not skip:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("T dictionary mess cleaned and restored.")
