import os
import re

file_path = r'c:\\Users\\User\\Downloads\\AryaBotNew\\TryAryaBot\\AryaPremium\\plugins\\userbot\\market_seller.py'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# --- 1. Replace _menu_card_text ---
new_menu_func = """def _menu_card_text(user, bt_cfg: dict, bot_name: str, lang: str = 'en') -> str:
    from utils import translate_to_hindi
    u_mention = f'<a href="tg://user?id={user.id}">{html.escape((user.first_name or "User").strip())}</a>'
    
    # --- DEFAULTS ---
    DEFAULT_WELCOME_EN = \"\"\"›› ʜᴇʏ, {name} | {bot_name}
ʙʀᴏᴡꜱᴇ ᴘʀᴇᴍɪᴜᴍ ꜱᴛᴏʀɪᴇꜱ ꜰʀᴏᴍ pocket fm, kuku fm, headphone & more.\"\"\"
    DEFAULT_ABOUT_EN = \"\"\"ᴛᴀᴘ marketplace ᴛᴏ ᴇxᴘʟᴏʀᴇ ꜱᴛᴏʀɪᴇꜱ ʙʏ platform.\"\"\"
    DEFAULT_QUOTE_EN = \"\"\"ǫᴜᴀʟɪᴛʏ ꜱᴛᴏʀɪᴇꜱ • ɪɴꜱᴛᴀɴᴛ ᴅᴇʟɪᴠᴇʀʏ • ᴀᴜᴛᴏᴍᴀᴛᴇᴅ\"\"\"
    DEFAULT_AUTHOR_EN = \"\"\"— ᴀʀʏᴀ ᴘʀᴇᴍɪᴜᴍ\"\"\"
    
    DEFAULT_WELCOME_HI = \"\"\"›› ʜᴇʏ, {name} | {bot_name}
pocket fm, kuku fm, headphone और अन्य से प्रीमियम कहानियाँ ब्राउज़ करें।\"\"\"
    DEFAULT_ABOUT_HI = \"\"\"प्लेटफ़ॉर्म के अनुसार कहानियों को देखने के लिए marketplace पर टैप करें।\"\"\"
    DEFAULT_QUOTE_HI = \"\"\"गुणवत्ता वाली कहानियाँ • तत्काल वितरण • स्वचालित\"\"\"
    DEFAULT_AUTHOR_HI = \"\"\"— आर्या प्रीमियम\"\"\"

    # --- 1. Welcome Section ---
    text_en = bt_cfg.get("welcome")
    if text_en and text_en.lower() == "disable":
        welcome = ""
    else:
        if not text_en:
            text_en = DEFAULT_WELCOME_EN
        
        if lang == 'hi':
            if text_en == DEFAULT_WELCOME_EN:
                welcome = DEFAULT_WELCOME_HI
            else:
                welcome = translate_to_hindi(text_en)
        else:
            welcome = text_en
        
        welcome = welcome.replace("{name}", u_mention).replace("{bot_name}", bot_name).replace("{user}", u_mention).replace("{first_name}", u_mention)

    # --- 2. About Section ---
    text_en = bt_cfg.get("about")
    if text_en and text_en.lower() == "disable":
        about = ""
    else:
        if not text_en:
            text_en = DEFAULT_ABOUT_EN
        
        if lang == 'hi':
            if text_en == DEFAULT_ABOUT_EN:
                about = DEFAULT_ABOUT_HI
            else:
                about = translate_to_hindi(text_en)
        else:
            about = text_en

    # --- 3. Quote Section ---
    text_en = bt_cfg.get("quote")
    if text_en and text_en.lower() == "disable":
        quote = ""
    else:
        if not text_en:
            text_en = DEFAULT_QUOTE_EN
        
        if lang == 'hi':
            if text_en == DEFAULT_QUOTE_EN:
                quote = DEFAULT_QUOTE_HI
            else:
                quote = translate_to_hindi(text_en)
        else:
            quote = text_en

    # --- 4. Author Section ---
    text_en = bt_cfg.get("quote_author")
    if text_en and text_en.lower() == "disable":
        author = ""
    else:
        if not text_en:
            text_en = DEFAULT_AUTHOR_EN
        
        if lang == 'hi':
            if text_en == DEFAULT_AUTHOR_EN:
                author = DEFAULT_AUTHOR_HI
            else:
                author = translate_to_hindi(text_en)
        else:
            author = text_en
        
    blocks = []
    
    # Block 1: Welcome + About
    b1_content = []
    if welcome.strip(): b1_content.append(welcome.strip())
    if about.strip(): b1_content.append(about.strip())
    
    if b1_content:
        blocks.append(f'<blockquote expandable="true">{"\\n".join(b1_content)}</blockquote>')
        
    # Block 2: Quote + Author
    b2_content = []
    if quote.strip(): b2_content.append(quote.strip())
    if author.strip(): b2_content.append(f"<b>{author.strip()}</b>")
    
    if b2_content:
        # User wants them grouped. 
        blocks.append(f'<blockquote expandable="true">{"\\n".join(b2_content)}</blockquote>')
        
    return "\\n\\n".join(blocks)
"""

text = re.sub(r'def _menu_card_text\(user, bt_cfg: dict, bot_name: str, lang: str = \'en\'\) -> str:.*?return "\\n".join\(blocks\)', new_menu_func, text, flags=re.DOTALL)

# --- 2. Update lang Handler ---
old_lang = """    # ── Language ──
    elif cmd == "lang":
        new_lang = data[2]
        await db.update_user(user_id, {"lang": new_lang})
        await query.answer("Language Updated!")
        await _edit_main_menu_in_place(client, query, query.from_user, new_lang)"""

new_lang = """    # ── Language ──
    elif cmd == "lang":
        new_lang = data[2]
        await query.answer("✓ Updates applied!", show_alert=False)
        m = await client.send_message(user_id, "<b>› › Yup, Bro updating... ⏳</b>")
        await asyncio.sleep(2)
        await db.update_user(user_id, {"lang": new_lang})
        try: await m.delete()
        except: pass
        await _edit_main_menu_in_place(client, query, query.from_user, new_lang)"""

text = text.replace(old_lang, new_lang)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Menu text corrected and lang switch improved.")
