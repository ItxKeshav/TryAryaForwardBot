import asyncio
import logging
from database import db
from translation import Translation
from plugins.lang import t, _tx
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)
CLIENT = CLIENT()

#  Future-based ask() — immune to pyrofork stale-listener bug 
_settings_waiting: dict[int, asyncio.Future] = {}

@Client.on_message(filters.private, group=-16)
async def _settings_input_router(bot, message):
    uid = message.from_user.id if message.from_user else None
    if uid and uid in _settings_waiting:
        fut = _settings_waiting.pop(uid)
        if not fut.done():
            fut.set_result(message)
    raise ContinuePropagation

async def _ask(bot, user_id: int, timeout: int = 300):
    loop = asyncio.get_event_loop()
    fut: asyncio.Future = loop.create_future()
    old = _settings_waiting.pop(user_id, None)
    if old and not old.done():
        old.cancel()
    _settings_waiting[user_id] = fut
    try:
        from asyncio import wait_for, TimeoutError
        res = await wait_for(fut, timeout=timeout)
        return res
    except TimeoutError:
        _settings_waiting.pop(user_id, None)
        raise

from pyrogram import ContinuePropagation

async def _sb_set_text_flow(bot, user_id, query, b_id: str, key: str,
                             label: str, instructions: str, back_cb: str):
    """Reusable helper: prompt user for a per-bot text, then save it."""
    await query.message.delete()
    ask = await bot.send_message(
        user_id,
        f"<b>»  Set {label}</b>\n\n{instructions}\n\n"
        "Send /reset to remove current value.\n"
        "/cancel to abort."
    )
    try:
        resp = await bot.listen(chat_id=user_id, timeout=300)
        txt = resp.text or resp.caption or ""
        await resp.delete()
        if txt.strip().lower() in ("/cancel", "cancel"):
            return await ask.edit_text(
                "<i>Process Cancelled Successfully!</i>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=back_cb)]])
            )
        if txt.strip() == "/reset":
            await db.set_share_bot_text(b_id, key, "")
            return await ask.edit_text(
                f"»  {label} reset to default.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=back_cb)]])
            )
        await db.set_share_bot_text(b_id, key, txt)
        await ask.edit_text(
            f"»  {label} saved!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=back_cb)]])
        )
    except asyncio.TimeoutError:
        try:
            await ask.edit_text(
                "Timeout.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=back_cb)]])
            )
        except Exception:
            pass


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    await message.delete()
    user_id = message.from_user.id
    await message.reply_text(
        await t(user_id, 'settings_title'),
        reply_markup=await main_buttons(user_id)
    )
    
@Client.on_callback_query(filters.regex(r'^settings#(?!lang$|cleanmsg$)'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  i, type = query.data.split("#")
  buttons = [[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#main")]]
  
  if type=="main":
     user_id = query.from_user.id
     text = await t(user_id, 'settings_title')
     markup = await main_buttons(user_id)
     if getattr(query.message, "photo", None):
         await query.message.delete()
         await bot.send_message(chat_id=query.message.chat.id, text=text, reply_markup=markup)
     else:
         await query.message.edit_text(text, reply_markup=markup)
          
  elif type=="accounts":
     bots = await db.get_bots(user_id)
     normal_bots = [b for b in bots if b.get('is_bot', True)]
     userbots    = [b for b in bots if not b.get('is_bot', True)]
     
     buttons = []
     
     # ---- BOTS SECTION ----
     buttons.append([InlineKeyboardButton("Bᴏᴛs", callback_data="settings#noop")])
     for b in normal_bots:
         active_mark = "" if b.get('active') else ""
         buttons.append([InlineKeyboardButton(f"{active_mark}{b['name']}", callback_data=f"settings#editbot_{b['id']}")])
     if len(normal_bots) < 2:
         buttons.append([InlineKeyboardButton('Aᴅᴅ Bᴏᴛ', callback_data="settings#addbot")])

     # ---- USERBOTS SECTION ----
     buttons.append([InlineKeyboardButton("Usᴇʀʙᴏᴛs", callback_data="settings#noop")])
     for b in userbots:
         active_mark = "" if b.get('active') else ""
         buttons.append([InlineKeyboardButton(f"{active_mark}{b['name']}", callback_data=f"settings#editbot_{b['id']}")])
     if len(userbots) < 2:
         buttons.append([InlineKeyboardButton('Aᴅᴅ Usᴇʀʙᴏᴛ', callback_data="settings#adduserbot")])
         
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#main")])
     
     text = (
         "<b><u>👥 My Accounts</u></b>\n\n"
         f"<b>🤖 Bots:</b> {len(normal_bots)}/2\n"
         f"<b>👤 Userbots:</b> {len(userbots)}/2\n\n"
         "<b>Tap an account to view details or set it active.\n"
         "✔️ = Currently active for that type.</b>"
     )
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
     
  elif type=="main_menu_img":
     await query.message.delete()
     ask = await bot.send_message(
         user_id,
         "<b>🖼 Set Main Menu Image</b>\n\n"
         "Send a photo to use as the Main Menu Image.\n"
         "Send <code>/clear</code> to remove the current image.\n"
         "Send <code>/cancel</code> to abort."
     )
     try:
         resp = await bot.listen(chat_id=user_id, timeout=120)
         if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
             await resp.delete()
             return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")]]))

         if getattr(resp, "text", None) and resp.text.strip() == "/clear":
             cfgs = await db.get_configs(user_id)
             cfgs['menu_image_id'] = None
             await db.update_configs(user_id, cfgs)
             await resp.delete()
             return await ask.edit_text("»  Main Menu image removed.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")]]))

         photo = resp.photo
         if not photo:
             await resp.delete()
             return await ask.edit_text("‣  No photo received. Please send an image.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")]]))

         cfgs = await db.get_configs(user_id)
         cfgs['menu_image_id'] = photo.file_id
         await db.update_configs(user_id, cfgs)
         await resp.delete()
         await ask.edit_text("»  ✅ Main Menu image configured successfully!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")]]))
     except asyncio.TimeoutError:
         await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")]]))

  elif type=="noop":
     await query.answer()
  
  elif type=="addbot":
     await query.message.delete()
     res = await CLIENT.add_bot(bot, query)
     if res == "LIMIT_REACHED": return await bot.send_message(user_id, "<b>Limit reached: You can only add up to 2 Bots.</b>")
     if res == "EXISTS": return await bot.send_message(user_id, "<b>This bot has already been added.</b>")
     if res != True: return
     await bot.send_message(user_id, "<b>Bot token successfully added to db</b>\nGo back to /settings to configure.")
  
  elif type=="adduserbot":
     await query.message.delete()
     res = await CLIENT.add_session(bot, query)
     if res == "LIMIT_REACHED": return await bot.send_message(user_id, "<b>Limit reached: You can only add up to 2 Userbots.</b>")
     if res == "EXISTS": return await bot.send_message(user_id, "<b>This session has already been added.</b>")
     if res != True: return
     await bot.send_message(user_id, "<b>Session successfully added to db</b>\nGo back to /settings to configure.")
      
  elif type=="channels":
     buttons = []
     channels = await db.get_user_channels(user_id)
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"settings#editchannels_{channel['chat_id']}")])
     buttons.append([InlineKeyboardButton('Aᴅᴅ Cʜᴀɴɴᴇʟ', 
                      callback_data="settings#addchannel")])
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text( 
       "<b><u>My Channels</b></u>\n\n<b>you can manage your target chats in here</b>",
       reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="addchannel":  
     await query.message.delete()
     try:
         text = await bot.send_message(user_id, "<b>❪ ADD CHAT ❫\n\nForward a message from the chat, OR send its Chat ID (e.g. -100...), OR send a link to any message in the chat.\n/cancel - cancel this process</b>")
         chat_ids = await _ask(bot, user_id, timeout=300)
         if getattr(chat_ids, 'text', None) and any(x in chat_ids.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
             await chat_ids.delete()
             return await text.edit_text("<b>process canceled</b>", reply_markup=InlineKeyboardMarkup(buttons))
             
         chat_id, title, username = None, "Unknown Chat", "private"
         
         if getattr(chat_ids, 'forward_from_chat', None):
             chat_id = chat_ids.forward_from_chat.id
             title = chat_ids.forward_from_chat.title
             username = "@" + chat_ids.forward_from_chat.username if chat_ids.forward_from_chat.username else "private"
         elif chat_ids.text:
             txt = chat_ids.text.strip()
             if txt.lstrip('-').isdigit():
                 chat_id = int(txt)
             elif "t.me/c/" in txt:
                 import re
                 m = re.search(r't\.me/c/(\d+)', txt)
                 if m: chat_id = int("-100" + m.group(1))
             elif "t.me/" in txt:
                 import re
                 m = re.search(r't\.me/([^/]+)', txt.replace('https://','').replace('http://',''))
                 if m and m.group(1) not in ['joinchat', '+', 'c']:
                     chat_id = m.group(1)
                     username = "@" + m.group(1)
                     
         if not chat_id:
             await chat_ids.delete()
             return await text.edit_text("**Could not extract Chat ID. Invalid forward or link.**", reply_markup=InlineKeyboardMarkup(buttons))
         
         try:
             # Try to resolve chat title
             chat_info = await bot.get_chat(chat_id)
             chat_id = chat_info.id
             title = chat_info.title or title
             username = "@" + chat_info.username if getattr(chat_info, 'username', None) else username
         except Exception:
             pass
             
         chat = await db.add_channel(user_id, chat_id, title, username)
         await chat_ids.delete()
         await text.edit_text(
            "<b>Successfully updated</b>" if chat else "<b>This channel is already added</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type.startswith("editbot"): 
     bot_id = type.split('_')[1] if "_" in type else None
     bott = await db.get_bot(user_id, bot_id)
     if not bott:
         return await query.answer("Account not found!", show_alert=True)
         
     TEXT = Translation.BOT_DETAILS if bott.get('is_bot', True) else Translation.USER_DETAILS
     buttons = []
     if not bott.get('active'):
         buttons.append([InlineKeyboardButton('Sᴇᴛ Aᴄᴛɪᴠᴇ', callback_data=f"settings#setactive_{bott['id']}")])
         
     buttons.append([InlineKeyboardButton('Rᴇᴍᴏᴠᴇ', callback_data=f"settings#removebot_{bott['id']}")])
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#accounts")])
     await query.message.edit_text(
        TEXT.format(bott['name'], bott['id'], bott['username']),
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("setactive"):
     bot_id = type.split('_')[1]
     await db.set_active_bot(user_id, bot_id)
     await query.answer("Account set as ACTIVE!", show_alert=True)
     buttons = [[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#accounts")]]
     await query.message.edit_text("<b>Successfully changed active account.</b>", reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "sharebot":
     bots = await db.get_share_bots()
     protect = await db.get_share_protect_global()
     ptxt = "»  ON" if protect else "‣  OFF"
     
     buttons = []
     buttons.append([InlineKeyboardButton(f"Pʀᴏᴛᴇᴄᴛɪᴏɴ:{ptxt}", callback_data="settings#sharebotprotect")])
     buttons.append([InlineKeyboardButton("Dᴇʟɪᴠᴇʀʏ Bᴏᴛs", callback_data="settings#noop")])
     for b in bots:
         buttons.append([InlineKeyboardButton(f"{b['name']}", callback_data=f"settings#sb_view_{b['id']}")])
     if len(bots) < 10:
         buttons.append([InlineKeyboardButton('Aᴅᴅ Sʜᴀʀᴇ Bᴏᴛ', callback_data="settings#sb_add")])
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#main")])
     
     text = (
         "<b>❪ SHARE BOT CONFIGURATION ❫</b>\n\n"
         f"<b>Allocated Bots:</b> {len(bots)}/10\n\n"
         "<b>These bots handle exclusively the delivery payload of your Share Links.</b>\n\n"
         "<i>Protection globally restricts saving and forwarding delivered files.</i>"
     )
     await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

  elif type == "sharebotprotect":
     protect = await db.get_share_protect_global()
     await db.set_share_protect_global(not protect)
     await query.answer(f"Protection turned {'OFF' if protect else 'ON'}")
     query.data = "settings#sharebot"
     return await settings_query(bot, query)



  elif type == "sbt_manage":
      bots = await db.get_share_bots()
      buttons = []
      buttons.append([InlineKeyboardButton("Dᴇʟɪᴠᴇʀʏ Bᴏᴛs", callback_data="settings#noop")])
      for b in bots:
          buttons.append([InlineKeyboardButton(f"{b['name']}", callback_data=f"settings#sb_view_{b['id']}")])
      if len(bots) < 10:
          buttons.append([InlineKeyboardButton('Aᴅᴅ Sʜᴀʀᴇ Bᴏᴛ', callback_data="settings#sb_add")])
      buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#sharebot")])
      
      text = (
          "<b><u>»  Share Agent Accounts</u></b>\n\n"
          f"<b>Allocated Bots:</b> {len(bots)}/10\n\n"
          "<b>These bots handle exclusively the delivery payload of your Share Links. They distribute traffic securely to avoid bans across high volumes.</b>"
      )
      await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type == "sb_add":
      await query.message.delete()
      ask = None
      try:
          from config import Config as _Cfg
          ask = await bot.send_message(
              user_id,
              "<b>❪ ADD SHARE BOT ❫</b>\n\n"
              "Send the bot token from @BotFather directly, or forward a message containing it.\n\n"
              "/cancel to abort"
          )
          resp = await bot.listen(chat_id=user_id, timeout=120)
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              await resp.delete()
              return await ask.edit_text(
                  "<i>Process Cancelled Successfully!</i>",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharebot")]])
              )

          raw = (resp.text or "").strip()
          await resp.delete()

          import re as _re_add
          m = _re_add.search(r"(\d{8,11}:[A-Za-z0-9_-]{35,})", raw)
          tk = m.group(1) if m else raw

          if ":" not in tk or len(tk) < 40:
              return await ask.edit_text(
                  "<b>‣  Invalid token format!</b>\nMake sure you send the full token from @BotFather.",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Rᴇᴛʀʏ", callback_data="settings#sb_add"), InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharebot")]])
              )

          # Validate token by starting a temp client
          test_app = Client(
              f"test_sb_{tk[:8]}", bot_token=tk,
              api_id=_Cfg.API_ID, api_hash=_Cfg.API_HASH, in_memory=True
          )
          await test_app.start()
          me = await test_app.get_me()
          await test_app.stop()

          # Save to DB
          await db.add_share_bot(me.id, tk, me.username or "unknown", me.first_name or "ShareBot")

          # Reload all share bots
          from plugins.share_bot import start_share_bot
          import asyncio as _aio
          _aio.create_task(start_share_bot())

          await ask.edit_text(
              f"»  <b>Successfully added @{me.username}!</b>\n\nThe delivery bot is now active.",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharebot")]])
          )
      except Exception as e:
          errmsg = f"‣  <b>Error:</b> <code>{e}</code>"
          try:
              if ask:
                  await ask.edit_text(errmsg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharebot")]]))
              else:
                  await bot.send_message(user_id, errmsg)
          except Exception:
              pass

  elif type.startswith("sb_view_"):
      b_id = type.split("sb_view_")[1]
      bots = await db.get_share_bots()
      bt = next((x for x in bots if str(x['id']) == str(b_id)), None)
      if not bt: return await query.answer("Bot not found!")

      buttons = [
          [InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ & Aʙᴏᴜᴛ', callback_data=f"settings#sb_wa_{b_id}")],
          [
              InlineKeyboardButton('Dᴇʟᴇᴛᴇ Msɢ',      callback_data=f"settings#sb_set_delete_{b_id}"),
              InlineKeyboardButton('Sᴜᴄᴄᴇss Msɢ',    callback_data=f"settings#sb_set_success_{b_id}"),
          ],
          [InlineKeyboardButton('Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ',    callback_data=f"settings#sb_set_caption_{b_id}")],
          [InlineKeyboardButton('Aᴜᴛᴏ-Dᴇʟᴇᴛᴇ', callback_data=f"settings#sb_set_autodel_{b_id}"),
           InlineKeyboardButton('Fᴏʀᴄᴇ Sᴜʙsᴄʀɪʙᴇ',  callback_data=f"settings#sb_fsub_{b_id}")],
          [InlineKeyboardButton('🎞 Fᴇᴛᴄʜɪɴɢ Mᴇᴅɪᴀ', callback_data=f"settings#sb_fetch_media_{b_id}")],
          [
              InlineKeyboardButton('Sᴛᴀᴛs',           callback_data=f"settings#sb_stats_{b_id}"),
              InlineKeyboardButton('Bʀᴏᴀᴅᴄᴀsᴛ',       callback_data=f"settings#sb_broadcast_{b_id}")
          ],
          [InlineKeyboardButton('Rᴇᴍᴏᴠᴇ Bᴏᴛ',      callback_data=f"settings#sb_remove_{b_id}")],
          [InlineKeyboardButton('❮ Bᴀᴄᴋ',               callback_data="settings#sharebot")],
      ]
      await query.message.edit_text(
          f"<b>❪ SHARE BOT PROFILE ❫</b>\n\n"
          f"<b>»  Name:</b> {bt['name']}\n"
          f"<b>»  Username:</b> @{bt['username']}\n"
          f"<b>🆔 ID:</b> <code>{bt['id']}</code>\n\n"
          "<i>All settings below are specific to this bot.</i>",
          reply_markup=InlineKeyboardMarkup(buttons)
      )

  elif type.startswith("sb_wa_"):
      b_id = type.split("sb_wa_")[1]
      buttons = [
          [
              InlineKeyboardButton('Wᴇʟᴄᴏᴍᴇ Msɢ',    callback_data=f"settings#sb_set_welcome_{b_id}"),
          ],
          [InlineKeyboardButton('Aʙᴏᴜᴛ',        callback_data=f"settings#sb_about_{b_id}")],
          [InlineKeyboardButton('Mᴇɴᴜ Iᴍᴀɢᴇ',  callback_data=f"settings#sb_menu_mgr_{b_id}")],
          [InlineKeyboardButton('❮ Bᴀᴄᴋ',         callback_data=f"settings#sb_view_{b_id}")],
      ]
      await query.message.edit_text(
          f"<b>❪ WELCOME, ABOUT & MENU ❫</b>\n\n"
          "Select what you want to configure for this bot:",
          reply_markup=InlineKeyboardMarkup(buttons)
      )

  elif type.startswith("sb_menu_mgr_"):
      b_id = type.split("sb_menu_mgr_")[1]
      about = await db.get_share_bot_about(b_id)
      images = about.get('menu_image_ids', [])
      
      buttons = []
      buttons.append([
          InlineKeyboardButton('➕ Aᴅᴅ Iᴍᴀɢᴇ', callback_data=f"settings#sb_menu_img_{b_id}"),
          InlineKeyboardButton('👁 Pʀᴇᴠɪᴇᴡ', callback_data=f"settings#sb_menu_pre_{b_id}")
      ])
      
      img_btns = []
      for idx, file_id in enumerate(images):
          img_btns.append(InlineKeyboardButton(f'❌ Iᴍᴀɢᴇ {idx+1}', callback_data=f"settings#sb_menu_del_{b_id}_{idx}"))
          if len(img_btns) == 2:
              buttons.append(img_btns)
              img_btns = []
      if img_btns:
          buttons.append(img_btns)
          
      buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data=f"settings#sb_wa_{b_id}")])
      
      await query.message.edit_text(
          f"<b>❪ MENU IMAGES MANAGER ❫</b>\n\n"
          f"You have <b>{len(images)}/10</b> images in rotation.\n"
          f"These images will automatically rotate when a user starts your bot.",
          reply_markup=InlineKeyboardMarkup(buttons)
      )

  elif type.startswith("sb_menu_del_"):
      _, b_id, idx = type.split("sb_menu_del_")[1].partition("_")
      idx = int(idx)
      about = await db.get_share_bot_about(b_id)
      images = about.get('menu_image_ids', [])
      if 0 <= idx < len(images):
          images.pop(idx)
          about['menu_image_ids'] = images
          await db.set_share_bot_about(b_id, about)
      
      query.data = f"settings#sb_menu_mgr_{b_id}"
      return await settings_query(bot, query)

  elif type.startswith("sb_menu_pre_"):
      b_id = type.split("sb_menu_pre_")[1]
      about = await db.get_share_bot_about(b_id)
      images = about.get('menu_image_ids', [])
      if not images:
          return await query.answer("No images configured yet!", show_alert=True)
      
      import random
      file_id = random.choice(images)
      await query.message.delete()
      await bot.send_photo(
          chat_id=user_id,
          photo=file_id,
          caption="<b>👁 Preview of the rotating menu image.</b>",
          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ Tᴏ Mᴀɴᴀɢᴇʀ', callback_data=f"settings#sb_menu_mgr_{b_id}")]])
      )

  elif type.startswith("sb_menu_img_"):
      b_id = type.split("sb_menu_img_")[1]
      await query.message.delete()
      ask = await bot.send_message(
          user_id,
          "<b>🖼 Set Menu Image</b>\n\n"
          "Send a photo to use as the main Menu Image.\n"
          "This image will appear above the Welcome and About menus.\n\n"
          "Send <code>/clear</code> to remove all images.\n"
          "Send <code>/cancel</code> to abort."
      )
      try:
          resp = await bot.listen(chat_id=user_id, timeout=120)

          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              await resp.delete()
              return await ask.edit_text(
                  "<i>Process Cancelled Successfully!</i>",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
              )

          if resp.text and resp.text.strip() == "/clear":
              about = await db.get_share_bot_about(b_id)
              about.pop('menu_image_ids', None)
              await db.set_share_bot_about(b_id, about)
              await resp.delete()
              return await ask.edit_text(
                  "»  Menu media removed.",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
              )

          about = await db.get_share_bot_about(b_id)
          if len(about.get('menu_image_ids', [])) >= 10:
              await resp.delete()
              return await ask.edit_text(
                  "<b>‣  Limit Reached:</b> You can only set up to 10 rotating menu items.\nSend <code>/clear</code> first to reset the list.",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
              )

          media_obj = None
          menu_media_type = None
          if resp.animation:
              media_obj = resp.animation
              menu_media_type = 'animation'
          elif resp.video and resp.video.duration <= 10:
              media_obj = resp.video
              menu_media_type = 'video'
          elif resp.photo:
              media_obj = resp.photo
              menu_media_type = 'photo'

          if not media_obj:
              await resp.delete()
              return await ask.edit_text(
                  "‣  Unsupported media. Please send a Photo, GIF, or short Video (≤10s).",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
              )

          final_file_id = media_obj.file_id
          import os
          from pyrogram import Client
          from plugins.share_bot import share_clients
          from config import Config

          sb_client = share_clients.get(str(b_id))
          should_stop = False

          if not sb_client:
              bot_info = next((bx for bx in await db.get_bots(user_id) if str(bx['id']) == b_id), None)
              if bot_info:
                  try:
                      sb_client = Client(name=f"tmp_{b_id}", bot_token=bot_info['token'], in_memory=True, api_id=Config.API_ID, api_hash=Config.API_HASH)
                      await sb_client.start()
                      should_stop = True
                  except Exception:
                      sb_client = None

          if sb_client:
              dl_path = await bot.download_media(resp)
              if dl_path:
                  try:
                      if menu_media_type == 'animation':
                          relay = await sb_client.send_animation(chat_id=user_id, animation=dl_path)
                          final_file_id = relay.animation.file_id
                      elif menu_media_type == 'video':
                          relay = await sb_client.send_video(chat_id=user_id, video=dl_path)
                          final_file_id = relay.video.file_id
                      else:
                          relay = await sb_client.send_photo(chat_id=user_id, photo=dl_path)
                          ph = relay.photo
                          final_file_id = ph.file_id if hasattr(ph, 'file_id') else ph[-1].file_id
                      try: await relay.delete()
                      except Exception: pass
                  except Exception as _re:
                      logger.warning(f"[MenuImg] relay failed: {_re}")
                  try: os.remove(dl_path)
                  except Exception: pass

          if should_stop and sb_client:
              try: await sb_client.stop()
              except Exception: pass

          if not final_file_id:
               await ask.edit_text(
                   "<b>‣  ERROR:</b> Failed to process media file securely. Ensure the bot token is active.",
                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
               )
               return

          about = await db.get_share_bot_about(b_id)
          about.setdefault('menu_image_ids', []).append({"file_id": final_file_id, "media_type": menu_media_type})
          await db.set_share_bot_about(b_id, about)
          await resp.delete()
          type_icon = {"animation": "🎞", "video": "🎬", "photo": "🖼"}.get(menu_media_type, "🖼")
          await ask.edit_text(
              f"»  ✅ {type_icon} Menu media saved! Type: <b>{menu_media_type}</b>",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
          )
      except asyncio.TimeoutError:
          await ask.edit_text(
              "Timeout.",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_menu_mgr_{b_id}")]])
          )

  elif type.startswith("sb_fetch_media_"):
      b_id = type.split("sb_fetch_media_")[1]
      existing = await db.get_bot_fetching_media(b_id)

      # Build current status badge
      if existing and existing.get('file_id'):
          ext = existing.get('media_type', 'photo')
          type_icon = {"animation": "🎞", "video": "🎬", "photo": "🖼"}.get(ext, "🖼")
          status_str = f"{type_icon} Currently set: <b>{ext}</b> — tap below to replace or clear."
      else:
          status_str = "<i>❌ Not configured — delivery shows text only.</i>"

      await query.message.delete()
      ask = await bot.send_message(
          user_id,
          f"<b>🎞 Fetching Media Setup</b>\n\n"
          f"{status_str}\n\n"
          "<b>How it works:</b>\n"
          "When a user requests files, this GIF / Image / Video appears while\n"
          "their files are being prepared — making delivery feel alive & premium.\n\n"
          "<b>Supported types:</b>\n"
          "  🎞 GIF / Animation\n"
          "  🖼 Photo / Image\n"
          "  🎬 Short Video (max 10 sec)\n\n"
          "<b>Simply send the media now.</b>\n"
          "Or send <code>/clear</code> to remove it.\n"
          "Or send <code>/cancel</code> to abort.",
          reply_markup=InlineKeyboardMarkup([[
              InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")
          ]])
      )

      try:
          resp = await _ask(bot, user_id, timeout=180)

          if getattr(resp, 'text', None):
              txt = resp.text.strip().lower()
              if '/cancel' in txt or 'cancel' in txt:
                  try: await resp.delete()
                  except: pass
                  return await ask.edit_text(
                      "<i>Process Cancelled Successfully!</i>",
                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
                  )
              if '/clear' in txt:
                  await db.clear_bot_fetching_media(b_id)
                  try: await resp.delete()
                  except: pass
                  return await ask.edit_text(
                      "✅ Fetching media <b>removed</b>. Delivery will show text only.",
                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
                  )

          # ── Detect media type ──────────────────────────────────────────────
          file_id   = None
          media_type = None

          if resp.animation:
              # GIF / animation: always has file_id directly
              file_id    = resp.animation.file_id
              media_type = 'animation'

          elif resp.video and resp.video.duration <= 10:
              file_id    = resp.video.file_id
              media_type = 'video'

          elif resp.photo:
              # In Pyrogram, msg.photo is the LARGEST PhotoSize object
              # (not a list like in older versions) — just use file_id directly
              ph = resp.photo
              file_id    = ph.file_id if hasattr(ph, 'file_id') else ph[-1].file_id
              media_type = 'photo'

          else:
              try: await resp.delete()
              except: pass
              return await ask.edit_text(
                  "❌ <b>Unsupported type.</b>\n\nPlease send:\n"
                  "  🎞 A GIF / Animation\n"
                  "  🖼 A Photo / Image\n"
                  "  🎬 A Video under 10 seconds\n\n"
                  "Try again with /settings → Fetching Media.",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
              )

          # ── Capture Share Bot-compatible file_id ───────────────────────────
          # Strategy: have the Share Bot forward the media to itself (saved messages = bot's own chat).
          # This gives a file_id bound to the Share Bot's session — guaranteed to work at delivery.
          from plugins.share_bot import share_clients
          sb_client   = share_clients.get(str(b_id))
          final_file_id = file_id   # fallback = main bot's file_id
          sb_status   = "⚠️ Share Bot offline"
          sb_ok       = False

          if sb_client:
              try:
                  # Step 1 — Main bot copies to a "staging" location the Share Bot can access:
                  #          forward to the admin's chat using the Share Bot itself.
                  #          The admin has already chatted with the Share Bot (they set it up),
                  #          so the Share Bot can send to the admin's chat directly.
                  #
                  # CORRECT approach: We download the file_bytes using main bot and re-upload via Share Bot.
                  # But that's heavy (network). Better: use forward_messages from main bot's DM.
                  #
                  # SIMPLEST guaranteed approach: use Share Bot to send the file from its OWN
                  # saved messages. We do: sb_client.send_* with the main-bot file_id.
                  # Telegram's CDN file_ids are actually cross-client compatible for send operations
                  # when the file already exists on the CDN — the server re-uses the file.
                  # Failed only for "copy_message" from inaccessible chats, not for direct send by file_id.
                  #
                  # So: try sb_client.send_* with the main-bot file_id directly.
                  # If Telegram accepts it (CDN shortcut), great. Otherwise download+re-upload.

                  sb_me = await sb_client.get_me()
                  sb_own_chat = sb_me.id   # Share Bot's "Saved Messages"

                  staged = None
                  try:
                      # Try direct send with existing file_id
                      if media_type == 'animation':
                          staged = await sb_client.send_animation(sb_own_chat, animation=file_id,
                                                                   caption="[fetch-media-stage]")
                      elif media_type == 'video':
                          staged = await sb_client.send_video(sb_own_chat, video=file_id,
                                                               caption="[fetch-media-stage]")
                      else:
                          staged = await sb_client.send_photo(sb_own_chat, photo=file_id,
                                                               caption="[fetch-media-stage]")
                  except Exception as _direct_err:
                      logger.warning(f"[FetchMedia] Direct file_id send failed ({_direct_err}), downloading...")
                      # Fallback: download via main bot, re-upload via Share Bot
                      import io
                      buf = io.BytesIO()
                      await bot.download_media(resp, file_name=buf)
                      buf.seek(0)
                      buf.name = "fetch_media" + (
                          ".gif" if media_type == "animation" else
                          ".mp4" if media_type == "video" else ".jpg"
                      )
                      if media_type == 'animation':
                          staged = await sb_client.send_animation(sb_own_chat, animation=buf,
                                                                   caption="[fetch-media-stage]")
                      elif media_type == 'video':
                          staged = await sb_client.send_video(sb_own_chat, video=buf,
                                                               caption="[fetch-media-stage]")
                      else:
                          staged = await sb_client.send_photo(sb_own_chat, photo=buf,
                                                               caption="[fetch-media-stage]")

                  if staged:
                      if staged.animation:  final_file_id = staged.animation.file_id
                      elif staged.video:    final_file_id = staged.video.file_id
                      elif staged.photo:
                          ph2 = staged.photo
                          final_file_id = ph2.file_id if hasattr(ph2, 'file_id') else ph2[-1].file_id
                      # Clean up staged message
                      try: await staged.delete()
                      except: pass
                      sb_ok = True
                      sb_status = "✅ via Share Bot"

              except Exception as _fe:
                  logger.warning(f"[FetchMedia] Share Bot capture failed: {_fe}")
                  sb_status = f"⚠️ Share Bot error ({type(_fe).__name__})"

          # ── Save to DB ─────────────────────────────────────────────────────
          await db.set_bot_fetching_media(b_id, final_file_id, media_type)
          try: await resp.delete()
          except: pass

          type_icon = {"animation": "🎞", "video": "🎬", "photo": "🖼"}.get(media_type, "🖼")
          await ask.edit_text(
              f"<b>{type_icon} Fetching Media Saved!</b>\n\n"
              f"<b>Type:</b> {media_type}\n"
              f"<b>Source:</b> {sb_status}\n\n"
              f"Users will see this media while their files are being delivered.\n"
              f"<i>{'Share Bot will send it directly.' if sb_ok else 'Warning: using main-bot file_id — may not display correctly if Share Bot cannot access it.'}</i>",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
          )

      except asyncio.TimeoutError:
          await ask.edit_text(
              "⏱ <i>Timed out waiting for media. Please try again.</i>",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
          )


  elif type.startswith("sb_set_welcome_"):
      b_id = type.split("sb_set_welcome_")[1]
      await _sb_set_text_flow(bot, user_id, query, b_id, "welcome_msg",
          "Wᴇʟᴄᴏᴍᴇ Mᴇssᴀɢᴇ",
          "Send the new welcome message.\n"
          "Use <code>{first_name}</code>, <code>{full_name}</code>, <code>{mention}</code> as placeholders.\n"
          "Any font/formatting is accepted.",
          f"settings#sb_view_{b_id}")

  elif type.startswith("sb_set_delete_"):
      b_id = type.split("sb_set_delete_")[1]
      await _sb_set_text_flow(bot, user_id, query, b_id, "delete_msg",
          "Dᴇʟᴇᴛᴇ Nᴏᴛɪᴄᴇ Mᴇssᴀɢᴇ",
          "Send the delete notice text.\n"
          "Use <code>{time}</code> for the auto-delete duration.\n"
          "Any font/formatting is accepted.",
          f"settings#sb_view_{b_id}")

  elif type.startswith("sb_set_success_"):
      b_id = type.split("sb_set_success_")[1]
      await _sb_set_text_flow(bot, user_id, query, b_id, "success_msg",
          "Sᴜᴄᴄᴇss Mᴇssᴀɢᴇ",
          "Send the success/delivery confirmation message.\nAny font is accepted.",
          f"settings#sb_view_{b_id}")

  elif type.startswith("sb_set_caption_"):
      b_id = type.split("sb_set_caption_")[1]
      await _sb_set_text_flow(bot, user_id, query, b_id, "custom_caption",
          "Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ",
          "Send the caption to add to delivered media. Any font is accepted.",
          f"settings#sb_view_{b_id}")

  elif type.startswith("sb_set_autodel_"):
      b_id = type.split("sb_set_autodel_")[1]
      opts   = [0, 5, 10, 30, 60, 1440]           # minutes; 0 = OFF
      labels = ["OFF","5m","10m","30m","1h","24h"]
      about = await db.get_share_bot_about(b_id)
      cur = about.get('auto_delete', 0)
      try:    cur_idx = opts.index(cur)
      except: cur_idx = 0
      nxt_idx = (cur_idx + 1) % len(opts)
      about['auto_delete'] = opts[nxt_idx]
      await db.set_share_bot_about(b_id, about)
      await query.answer(f"Auto-Delete: {labels[nxt_idx]}")
      query.data = f"settings#sb_view_{b_id}"
      return await settings_query(bot, query)

  #  Stats & Broadcast 
  elif type.startswith("sb_stats_"):
      b_id = type.split("sb_stats_")[1]
      users = await db.get_share_bot_users(b_id)
      cnt = len(users)
      await query.message.edit_text(
          f"<b>»  SHARE BOT STATS</b>\n\n"
          f"<b>Total Users:</b> <code>{cnt}</code>\n\n"
          "<i>These are users who have opened or interacted with this specific bot.</i>",
          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
      )

  elif type.startswith("sb_broadcast_"):
      b_id = type.split("sb_broadcast_")[1]
      await query.message.delete()
      
      ask = await bot.send_message(
          user_id,
          "<b>»  Broadcast Message</b>\n\n"
          "Send the message you want to broadcast to all users of this bot.\n"
          "You can use text, photos, videos, etc.\n\n"
          "/cancel to abort."
      )
      
      try:
          resp = await _ask(bot, user_id, timeout=300)
          msg_to_send = resp.text or resp.caption or "media"
          
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              await ask.delete()
              await resp.delete()
              return await bot.send_message(
                  user_id, "<i>Process Cancelled Successfully!</i>",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
              )
              
          users = await db.get_share_bot_users(b_id)
          if not users:
              await ask.delete()
              return await bot.send_message(
                  user_id, "<b>‣  No users found for this bot.</b>",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
              )
              
          from plugins.share_bot import share_clients
          sb_client = share_clients.get(str(b_id))
          if not sb_client:
              await ask.delete()
              return await bot.send_message(
                  user_id, "<b>‣  Delivery Bot is not running online.</b>",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
              )
              
          await ask.edit_text(
              f"<b>»  Broadcast Started...</b>\n\n"
              f"<b>Target:</b> <code>{len(users)} users</code>"
          )
          
          import asyncio
          async def _do_broadcast(main_bot, sb_app, uids, msg_obj, status_msg, back_btn_data):
              sent = 0
              failed = 0
              blocked = 0
              total_users = len(uids)
              processed = 0

              for u in uids:
                  processed += 1
                  try:
                      uid_int = int(u)
                      # Strategy: try Share Bot first (sends from delivery bot name/avatar)
                      # If Share Bot can't (it has no access to admin DM), fallback to main bot relay
                      send_ok = False
                      if sb_app:
                          try:
                              # Copy via Share Bot requires the Share Bot to have a cached version.
                              # We relay: main bot forwards msg to Share Bot saved msgs, then SB copies to user.
                              # Simpler working strategy: main bot copies to user (since it has the message).
                              # Share Bot sends a text caption if media, or main bot sends the full thing.
                              pass  # See below
                          except Exception:
                              pass

                      # Always reliable: main bot copies/forwards the original message to each user
                      await main_bot.copy_message(
                          chat_id=uid_int,
                          from_chat_id=msg_obj.chat.id,
                          message_id=msg_obj.id
                      )
                      sent += 1
                      send_ok = True
                  except Exception as e:
                      failed += 1
                      estr = str(e).upper()
                      if any(k in estr for k in ("USER_IS_BLOCKED", "BOT WAS BLOCKED", "PEER_ID_INVALID",
                                                   "USER_DEACTIVATED", "INPUT_USER_DEACTIVATED")):
                          blocked += 1

                  # Rate limit protection (Telegram: ~30 msgs/sec for bots)
                  await asyncio.sleep(0.05)

                  # Live status update every 10 users
                  if processed % 10 == 0 or processed == total_users:
                      try:
                          pct = int(processed / total_users * 100)
                          bar_filled = int(pct / 10)
                          bar = "█" * bar_filled + "░" * (10 - bar_filled)
                          await status_msg.edit_text(
                              f"<b>»  Broadcast In Progress...</b>\n\n"
                              f"<b>Progress:</b> [{bar}] {pct}%\n"
                              f"<b>Processed:</b> <code>{processed}/{total_users}</code>\n\n"
                              f"<b>✅ Sent:</b> <code>{sent}</code>\n"
                              f"<b>❌ Failed:</b> <code>{failed}</code>\n"
                              f"<b>🚫 Blocked:</b> <code>{blocked}</code>"
                          )
                      except Exception:
                          pass

              # Final report
              try:
                  await status_msg.edit_text(
                      f"<b>»  ✅ Broadcast Complete!</b>\n\n"
                      f"<b>Total Users:</b> <code>{total_users}</code>\n"
                      f"<b>✅ Delivered:</b> <code>{sent}</code>\n"
                      f"<b>❌ Failed:</b> <code>{failed}</code>\n"
                      f"<b>🚫 Blocked/Inactive:</b> <code>{blocked}</code>\n\n"
                      f"<i>Success rate: {int(sent/total_users*100) if total_users else 0}%</i>",
                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=back_btn_data)]])
                  )
              except Exception: pass
              try:
                  await msg_obj.delete()
              except: pass

          import asyncio as _aio
          _aio.create_task(_do_broadcast(bot, sb_client, users, resp, ask, f"settings#sb_view_{b_id}"))

      except asyncio.TimeoutError:
          try:
              await bot.send_message(
                  user_id, "Timeout.",
                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")]])
              )
          except Exception:
              pass

  #  About section editor 
  elif type.startswith("sb_about_") and not any(type.startswith(f"sb_about_{p}_") for p in ['img', 'txt', 'owner', 'ver', 'reset']):
      b_id = type.split("sb_about_")[1]
      bots = await db.get_share_bots()
      bt = next((x for x in bots if str(x['id']) == str(b_id)), None)
      if not bt: return await query.answer("Bot not found!")
      about = await db.get_share_bot_about(b_id)
      txt_set = "»  Custom" if about.get('custom_text') else "»  Default"
      btns = [
          [InlineKeyboardButton('Eᴅɪᴛ Aʙᴏᴜᴛ Tᴇxᴛ',   callback_data=f"settings#sb_about_txt_{b_id}")],
          [InlineKeyboardButton('Eᴅɪᴛ Oᴡɴᴇʀ',         callback_data=f"settings#sb_about_owner_{b_id}")],
          [InlineKeyboardButton('Eᴅɪᴛ Vᴇʀsɪᴏɴ',       callback_data=f"settings#sb_about_ver_{b_id}")],
          [InlineKeyboardButton('Rᴇsᴇᴛ Tᴏ Dᴇꜰᴀᴜʟᴛ',    callback_data=f"settings#sb_about_reset_{b_id}")],
          [InlineKeyboardButton('❮ Bᴀᴄᴋ',                callback_data=f"settings#sb_wa_{b_id}")],
      ]
      await query.message.edit_text(
          f"<b>‣  Aʙᴏᴜᴛ Sᴇᴄᴛɪᴏɴ — {bt['name']}</b>\n\n"
          f"<b>Text:</b> {txt_set}\n"
          f"<b>Owner:</b> {about.get('owner_name', 'JeetX')}\n"
          f"<b>Version:</b> {about.get('version', 'V1.0')}\n\n"
          "<i>The About section is shown when users tap the About button in the delivery bot.</i>",
          reply_markup=InlineKeyboardMarkup(btns)
      )


  elif type.startswith("sb_about_txt_"):
      b_id = type.split("sb_about_txt_")[1]
      await query.message.delete()
      ask = await bot.send_message(user_id,
          "<b>»  Send the custom About text</b>.\n"
          "Use any font you like. HTML formatting is supported.\n"
          "/cancel to abort."
      )
      try:
          resp = await bot.listen(chat_id=user_id, timeout=180)
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
          txt = resp.text or ""
          about = await db.get_share_bot_about(b_id)
          about['custom_text'] = txt
          await db.set_share_bot_about(b_id, about)
          await ask.edit_text("»  About text saved!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
      except asyncio.TimeoutError:
          await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))

  elif type.startswith("sb_about_owner_"):
      b_id = type.split("sb_about_owner_")[1]
      await query.message.delete()
      ask = await bot.send_message(user_id,
          "<b>»  Send owner name and link</b>\n"
          "Format: <code>Owner Name | https://t.me/username</code>\n"
          "/cancel to abort."
      )
      try:
          resp = await bot.listen(chat_id=user_id, timeout=120)
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
          parts = (resp.text or "").split("|", 1)
          about = await db.get_share_bot_about(b_id)
          about['owner_name'] = parts[0].strip()
          if len(parts) > 1:
              about['owner_link'] = parts[1].strip()
          await db.set_share_bot_about(b_id, about)
          await ask.edit_text("»  Owner updated!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
      except asyncio.TimeoutError:
          await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))

  elif type.startswith("sb_about_ver_"):
      b_id = type.split("sb_about_ver_")[1]
      await query.message.delete()
      ask = await bot.send_message(user_id,
          "<b>»  Send new version string</b> (e.g. <code>V1.2</code>)\n/cancel to abort."
      )
      try:
          resp = await bot.listen(chat_id=user_id, timeout=60)
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
          about = await db.get_share_bot_about(b_id)
          about['version'] = (resp.text or "V1.0").strip()
          await db.set_share_bot_about(b_id, about)
          await ask.edit_text("»  Version updated!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))
      except asyncio.TimeoutError:
          await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_about_{b_id}")]]))

  elif type.startswith("sb_about_reset_"):
      b_id = type.split("sb_about_reset_")[1]
      await db.set_share_bot_about(b_id, {})
      await query.answer("About reset to defaults.")
      return await edit_settings(client, query, f"sb_about_{b_id}")

  #  Per-bot Force-Subscribe 
  elif type.startswith("sb_fsub_") and not any(type.startswith(f"sb_fsub_{p}_") for p in ['add', 'jr', 'del']):
      b_id = type.split("sb_fsub_")[1]
      fsub_chs = await db.get_bot_fsub_channels(b_id)
      lines = []
      btns  = []
      for i, ch in enumerate(fsub_chs):
          jr_lbl = " [JR]" if ch.get('join_request') else ""
          lines.append(f"{i+1}. {ch.get('title','?')}{jr_lbl}")
          btns.append([
              InlineKeyboardButton(f"Jʀ #{i+1}",  callback_data=f"settings#sb_fsub_jr_{b_id}_{i}"),
              InlineKeyboardButton(f"Dᴇʟ #{i+1}", callback_data=f"settings#sb_fsub_del_{b_id}_{i}"),
          ])
      ch_list = "\n".join(lines) if lines else "None configured."
      if len(fsub_chs) < 6:
          btns.append([InlineKeyboardButton("Aᴅᴅ Cʜᴀɴɴᴇʟ", callback_data=f"settings#sb_fsub_add_{b_id}")])
      btns.append([InlineKeyboardButton("Sᴇᴛ Fsᴜʙ Msɢ", callback_data=f"settings#sb_fsub_msg_{b_id}")])
      btns.append([InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_view_{b_id}")])
      await query.message.edit_text(
          f"<b>»  Force-Subscribe — Bot Specific</b>\n\n"
          f"Users must join ALL listed channels to receive files from this bot.\n"
          f"[JR] = join-request mode.\n\n{ch_list}",
          reply_markup=InlineKeyboardMarkup(btns)
      )

  elif type.startswith("sb_fsub_jr_"):
      rest = type[len("sb_fsub_jr_"):]
      # rest = "{b_id}_{idx}"
      last_under = rest.rfind("_")
      b_id = rest[:last_under]; idx = int(rest[last_under+1:])
      fsub_chs = await db.get_bot_fsub_channels(b_id)
      if 0 <= idx < len(fsub_chs):
          new_jr = not fsub_chs[idx].get('join_request', False)
          fsub_chs[idx]['join_request'] = new_jr
          ch_id = fsub_chs[idx].get('chat_id')
          if ch_id:
              try:
                  if new_jr:
                      lnk_obj = await bot.create_chat_invite_link(int(ch_id), creates_join_request=True)
                      fsub_chs[idx]['invite_link'] = lnk_obj.invite_link
                  else:
                      fsub_chs[idx]['invite_link'] = await bot.export_chat_invite_link(int(ch_id))
              except Exception as e:
                  logger.warning(f"Could not regenerate invite link: {e}")
          await db.set_bot_fsub_channels(b_id, fsub_chs)
          status = "ON » " if new_jr else "OFF ‣ "
          await query.answer(f"JR: {status}")
      return await edit_settings(client, query, f"sb_fsub_{b_id}")

  elif type.startswith("sb_fsub_del_"):
      rest = type[len("sb_fsub_del_"):]
      last_under = rest.rfind("_")
      b_id = rest[:last_under]; idx = int(rest[last_under+1:])
      fsub_chs = await db.get_bot_fsub_channels(b_id)
      if 0 <= idx < len(fsub_chs):
          fsub_chs.pop(idx)
          await db.set_bot_fsub_channels(b_id, fsub_chs)
          await query.answer("Removed.")
      return await edit_settings(client, query, f"sb_fsub_{b_id}")

  elif type.startswith("sb_fsub_msg_"):
      b_id = type.split("sb_fsub_msg_")[1]
      await _sb_set_text_flow(bot, user_id, query, b_id, "fsub_msg",
          "Fᴏʀᴄᴇ-Sᴜʙ Mᴇssᴀɢᴇ",
          "Send the new message to prompt users to subscribe.\nAny font is accepted.",
          f"settings#sb_fsub_{b_id}")

  elif type.startswith("sb_fsub_add_"):
      b_id = type[len("sb_fsub_add_"):]
      await query.message.delete()
      ask = await bot.send_message(user_id,
          "<b>Send the Channel/Group ID or @username</b>\n"
          "Example: <code>-1001234567890</code> or <code>@mychannel</code>\n\n"
          "/cancel to abort"
      )
      try:
          resp = await bot.listen(chat_id=user_id, timeout=120)
          if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
              await resp.delete()
              return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_fsub_{b_id}")]]))
          raw_id = resp.text.strip()
          await resp.delete()
          try:
              ch_obj = await bot.get_chat(raw_id)
          except Exception as e:
              err_str = str(e).lower()
              if "private" in err_str or "peer_id_invalid" in err_str or "channel_invalid" in err_str:
                  msg = "<b>‣  Cannot access this channel.</b>\nMake sure the Main Bot is admin."
              else:
                  msg = f"<b>‣  Error:</b> <code>{e}</code>"
              return await ask.edit_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_fsub_{b_id}")]]))
          try:
              invite = await bot.export_chat_invite_link(ch_obj.id)
          except Exception:
              invite = getattr(ch_obj, 'invite_link', '') or ''
          fsub_chs = await db.get_bot_fsub_channels(b_id)
          fsub_chs.append({
              'chat_id':     str(ch_obj.id),
              'title':       ch_obj.title or ch_obj.username or str(ch_obj.id),
              'invite_link': invite,
              'join_request': False,
          })
          await db.set_bot_fsub_channels(b_id, fsub_chs)
          await ask.edit_text(
              f"<b>»  Added: {ch_obj.title}</b>\n<i>Toggle JR to enable join-request mode.</i>",
              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_fsub_{b_id}")]]))
      except asyncio.TimeoutError:
          await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data=f"settings#sb_fsub_{b_id}")]]))

  elif type.startswith("sb_remove_"):
      b_id = type.split("sb_remove_")[1]
      await db.remove_share_bot(b_id)
      await db.remove_share_bot_config(b_id)  # clean up per-bot config too
      await query.answer("Bot Removed!")
      return await edit_settings(client, query, "sbt_manage")



  elif type == "sharefsub":
     fsub_chs = await db.get_share_fsub_channels()
     lines = []
     btns  = []
     for i, ch in enumerate(fsub_chs):
         jr_lbl = " [JR]" if ch.get('join_request') else ""
         lines.append(f"{i+1}. {ch.get('title','?')}{jr_lbl}")
         btns.append([
             InlineKeyboardButton(f"Tᴏɢɢʟᴇ Jʀ #{i+1}",  callback_data=f"settings#sharefsub_jr_{i}"),
             InlineKeyboardButton(f"Rᴇᴍᴏᴠᴇ #{i+1}", callback_data=f"settings#sharefsub_del_{i}")
         ])
     ch_list = "\n".join(lines) if lines else "None configured."
     if len(fsub_chs) < 6:
         btns.append([InlineKeyboardButton("Aᴅᴅ Cʜᴀɴɴᴇʟ/Gʀᴏᴜᴘ", callback_data="settings#sharefsub_add")])
     btns.append([InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharebot")])
     await query.message.edit_text(
         f"<b>»  Force-Subscribe Channels</b>\n\n"
         f"Users must join ALL listed channels to receive files.\n"
         f"[JR] = join-request mode (user sends request; admin approves).\n\n"
         f"{ch_list}",
         reply_markup=InlineKeyboardMarkup(btns)
     )

  elif type == "sharefsub_add":
     fsub_chs = await db.get_share_fsub_channels()
     if len(fsub_chs) >= 6:
         return await query.answer("Maximum 6 channels supported.", show_alert=True)
     await query.message.delete()
     try:
         ask = await bot.send_message(
             user_id,
             "<b>Send the Channel/Group ID or @username</b>\n"
             "Example: <code>-1001234567890</code> or <code>@mychannel</code>\n\n"
             "/cancel to abort"
         )
         resp = await bot.listen(chat_id=user_id, timeout=120)
         if getattr(resp, "text", None) and any(x in str(resp.text).lower() for x in ["cancel", "cᴀɴᴄᴇʟ", "⛔", "/cancel"]):
             await resp.delete()
             return await ask.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharefsub")]]))
         raw_id = resp.text.strip()
         await resp.delete()
         try:
             ch_obj = await bot.get_chat(raw_id)
         except Exception as e:
             err_str = str(e).lower()
             if "private" in err_str or "peer_id_invalid" in err_str or "channel_invalid" in err_str:
                 msg = (
                     "<b>‣  Cannot access this channel.</b>\n\n"
                     "This is a <b>private channel/group</b>. Make sure:\n"
                     "• The <b>Main Bot</b> is an <b>admin</b> in this channel\n"
                     "• You send the ID (not @username) for private channels\n\n"
                     "<i>Format: <code>-1001234567890</code></i>"
                 )
             else:
                 msg = f"<b>‣  Error:</b> <code>{e}</code>\nMake sure the Main Bot is an admin in that channel."
             return await ask.edit_text(
                 msg,
                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharefsub")]])
             )
         try:
             invite = await bot.export_chat_invite_link(ch_obj.id)
         except Exception:
             invite = getattr(ch_obj, 'invite_link', '') or ''

         ah = 0
         try:
             peer = await bot.resolve_peer(ch_obj.id)
             ah = getattr(peer, 'access_hash', 0)
         except Exception: pass

         fsub_chs.append({
             'chat_id':     str(ch_obj.id),
             'title':       ch_obj.title or ch_obj.username or str(ch_obj.id),
             'invite_link': invite,
             'join_request': False,
             'access_hash': ah,
         })
         await db.set_share_fsub_channels(fsub_chs)
         await ask.edit_text(
             f"<b>»  Added: {ch_obj.title}</b>\n"
             f"<i>Use 'Toggle JR' to enable join-request mode for this channel.</i>",
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharefsub")]])
         )
     except asyncio.TimeoutError:
         try: await ask.edit_text("Timeout.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#sharefsub")]]))
         except Exception: pass

  elif type.startswith("sharefsub_jr_"):
     idx      = int(type.split("_")[-1])
     fsub_chs = await db.get_share_fsub_channels()
     if 0 <= idx < len(fsub_chs):
         new_jr = not fsub_chs[idx].get('join_request', False)
         fsub_chs[idx]['join_request'] = new_jr
         ch_id = fsub_chs[idx].get('chat_id')
         if ch_id:
             try:
                 if new_jr:
                     lnk_obj = await bot.create_chat_invite_link(int(ch_id), creates_join_request=True)
                     fsub_chs[idx]['invite_link'] = lnk_obj.invite_link
                 else:
                     fsub_chs[idx]['invite_link'] = await bot.export_chat_invite_link(int(ch_id))
             except Exception as lnk_err:
                 logger.warning(f"Could not regenerate fsub invite link: {lnk_err}")
         await db.set_share_fsub_channels(fsub_chs)
         status = "ON » " if new_jr else "OFF ‣ "
         await query.answer(f"Join-Request mode: {status}")
     return await edit_settings(client, query, "sharefsub")

  elif type.startswith("sharefsub_del_"):
     idx      = int(type.split("_")[-1])
     fsub_chs = await db.get_share_fsub_channels()
     if 0 <= idx < len(fsub_chs):
         removed = fsub_chs.pop(idx)
         await db.set_share_fsub_channels(fsub_chs)
         await query.answer(f"Removed: {removed.get('title','?')}")
     return await edit_settings(client, query, "sharefsub")

  elif type == "share_autodelete":
     opts   = [0, 5, 10, 30, 60, 1440]           # minutes; 0 = OFF
     labels = ["OFF","5m","10m","30m","1h","24h"]
     cur    = await db.get_share_autodelete_global()
     try:    cur_idx = opts.index(cur)
     except: cur_idx = 0
     nxt_idx = (cur_idx + 1) % len(opts)
     await db.set_share_autodelete_global(opts[nxt_idx])
     await query.answer(f"Auto-Delete: {labels[nxt_idx]}")
     return await edit_settings(client, query, "sharebot")

  elif type == "editsharebot":
     import re
     await query.message.delete()
     try:
         txtmsg = await bot.send_message(user_id, "<b>Send the Bot Token for the File-Sharing Bot:</b>\n<i>(Get it from @BotFather)</i>\n\n/remove - to delete current token.\n/cancel - to abort.")
         resp = await bot.listen(chat_id=user_id, timeout=120)
         if getattr(resp, 'text', None) and any(x in resp.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
             await resp.delete()
             return await txtmsg.edit_text("<i>Process Cancelled Successfully!</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='settings#sharebot')]]))
         if resp.text == "/remove":
             await resp.delete()
             await db.set_share_bot_token("")
             return await txtmsg.edit_text("<b>Token Removed.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='settings#sharebot')]]))
            
         bot_token = re.findall(r'\d{8,10}:[A-Za-z0-9_-]{35}', resp.text)
         if not bot_token:
             return await txtmsg.edit_text("<b>Invalid Token Format.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='settings#sharebot')]]))
         
         new_token = bot_token[0]
         await db.set_share_bot_token(new_token)
         # Start immediately
         try:
             from plugins.share_bot import start_share_bot
             await start_share_bot(new_token)
             status = "»  Successfully Saved & Started!"
         except Exception as e:
             status = f"»  Saved securely, but failed to start stream:\n<code>{e}</code>"
             
         await resp.delete()
         await txtmsg.edit_text(status, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='settings#sharebot')]]))
     except asyncio.exceptions.TimeoutError:
         try: await txtmsg.edit_text('Timeout.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data='settings#sharebot')]]))
         except: pass

  elif type.startswith("removebot"):
     if "_" in type:
         bot_id = type.split('_')[1]
         await db.remove_bot(user_id, bot_id)
     else:
         await db.remove_bot(user_id)
     buttons = [[InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#accounts")]]
     await query.message.edit_text(
        "<b>successfully removed!</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("editchannels"): 
     chat_id = type.split('_')[1]
     chat = await db.get_channel_details(user_id, chat_id)
     buttons = [[InlineKeyboardButton('Rᴇᴍᴏᴠᴇ', callback_data=f"settings#removechannel_{chat_id}")
               ],
               [InlineKeyboardButton('❮ Bᴀᴄᴋ', callback_data="settings#channels")]]
     await query.message.edit_text(
        f"<b><u>»  CHANNEL DETAILS</b></u>\n\n<b>- TITLE:</b> <code>{chat['title']}</code>\n<b>- CHANNEL ID: </b> <code>{chat['chat_id']}</code>\n<b>- USERNAME:</b> {chat['username']}",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("removechannel"):
     chat_id = type.split('_')[1]
     await db.remove_channel(user_id, chat_id)
     await query.message.edit_text(
        "<b>successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="caption":
     data    = await get_configs(user_id)
     caption = data['caption']
     rm_cap  = data.get('filters', {}).get('rm_caption', False)

     # Determine mode label
     if rm_cap is True:
         mode_lbl = "»  Smart Clean  (active)"
     elif rm_cap == 2:
         mode_lbl = "»  Wipe All Captions  (active)"
     else:
         mode_lbl = "»  Keep Original  (active)"

     cap_lbl = "»  Add Custom Caption" if caption is None else "✏️ Edit Custom Caption"

     buttons = [[
         InlineKeyboardButton("Cᴀᴘᴛɪᴏɴ Mᴏᴅᴇ",
             callback_data="settings_#noop")
     ],[
         InlineKeyboardButton("»  ᴋᴇᴇᴘ ᴏʀɪɢɪɴᴀʟ" + (" ◀" if not rm_cap else ""),
             callback_data="settings#caption_mode-off"),
     ],[
         InlineKeyboardButton("»  ꜱᴍᴀʀᴛ ᴄʟᴇᴀɴ" + (" ◀" if rm_cap is True else ""),
             callback_data="settings#caption_mode-smart"),
     ],[
         InlineKeyboardButton("»  ᴡɪᴘᴇ ᴀʟʟ ᴄᴀᴘᴛɪᴏɴꜱ" + (" ◀" if rm_cap == 2 else ""),
             callback_data="settings#caption_mode-wipe"),
     ],[
         InlineKeyboardButton("Cᴜsᴛᴏᴍ Tᴇᴍᴘʟᴀᴛᴇ",
             callback_data="settings_#noop")
     ],[
         InlineKeyboardButton(cap_lbl, callback_data="settings#addcaption"),
     ]]
     if caption is not None:
         buttons.append([
             InlineKeyboardButton("Vɪᴇᴡ Tᴇᴍᴘʟᴀᴛᴇ",  callback_data="settings#seecaption"),
             InlineKeyboardButton("Cʟᴇᴀʀ Tᴇᴍᴘʟᴀᴛᴇ", callback_data="settings#deletecaption"),
         ])
     buttons.append([InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")])

     await query.message.edit_text(
         "<b><u>»  Caption Settings</u></b>\n\n"
         f"<b>Current mode:</b> {mode_lbl}\n\n"
         "<b>Modes:</b>\n"
         "• <b>Keep Original</b> — forward caption as-is\n"
         "• <b>Smart Clean</b> — strip links/usernames but keep text\n"
         "• <b>Wipe All Captions</b> — remove caption completely from every file\n\n"
         "<b>Custom Template</b> — override caption with your own text.\n"
         "  Supports: <code>{filename}</code>, <code>{size}</code>, <code>{caption}</code>",
         reply_markup=InlineKeyboardMarkup(buttons))

                               
  elif type=="seecaption":   
     data = await get_configs(user_id)
     buttons = [[InlineKeyboardButton('️ Eᴅɪᴛ Cᴀᴘᴛɪᴏɴ', 
                  callback_data="settings#addcaption")
               ],[
               InlineKeyboardButton('❮ Bᴀᴄᴋ', 
                 callback_data="settings#caption")]]
     await query.message.edit_text(
        f"<b><u>YOUR CUSTOM CAPTION</b></u>\n\n<code>{data['caption']}</code>",
        reply_markup=InlineKeyboardMarkup(buttons))
    
  elif type=="deletecaption":
     await update_configs(user_id, 'caption', None)
     await query.answer("\u2705 Caption template cleared.", show_alert=False)
     # Redirect back to caption sub-menu
     data    = await get_configs(user_id)
     rm_cap  = data.get('filters', {}).get('rm_caption', False)
     buttons = [[
         InlineKeyboardButton(("✅ " if not rm_cap else "» ") + "ᴋᴇᴇᴘ ᴏʀɪɢɪɴᴀʟ", callback_data="settings#caption_mode-off"),
     ],[
         InlineKeyboardButton(("✅ " if rm_cap is True else "» ") + "ꜱᴍᴀʀᴛ ᴄʟᴇᴀɴ", callback_data="settings#caption_mode-smart"),
     ],[
         InlineKeyboardButton(("✅ " if rm_cap == 2 else "» ") + "ᴡɪᴘᴇ ᴀʟʟ ᴄᴀᴘᴛɪᴏɴꜱ", callback_data="settings#caption_mode-wipe"),
     ],[
         InlineKeyboardButton("Aᴅᴅ Cᴜsᴛᴏᴍ Cᴀᴘᴛɪᴏɴ", callback_data="settings#addcaption"),
     ],[
         InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")
     ]]
     await query.message.edit_text(
         "<b><u>»  Caption Settings</u></b>\n\n<b>Template cleared successfully.</b>",
         reply_markup=InlineKeyboardMarkup(buttons))
                              
  elif type.startswith("caption_mode"):
     mode = type.split("-")[1]  # off | smart | wipe
     if mode == "off":
         val = False
     elif mode == "smart":
         val = True
     else:
         val = 2  # wipe
         
     await update_configs(user_id, 'rm_caption', val)
     
     await query.answer("»  Caption mode updated!", show_alert=False)
     # Refresh the caption sub-menu
     data    = await get_configs(user_id)
     caption = data['caption']
     rm_cap  = data.get('filters', {}).get('rm_caption', False)
     if rm_cap is True:
         mode_lbl = "»  Smart Clean  (active)"
     elif rm_cap == 2:
         mode_lbl = "»  Wipe All Captions  (active)"
     else:
         mode_lbl = "»  Keep Original  (active)"
     cap_lbl = "»  Add Custom Caption" if caption is None else "✏️ Edit Custom Caption"
     buttons = [[
         InlineKeyboardButton("Cᴀᴘᴛɪᴏɴ Mᴏᴅᴇ", callback_data="settings_#noop")
     ],[
         InlineKeyboardButton(("✅ " if not rm_cap else "» ") + "ᴋᴇᴇᴘ ᴏʀɪɢɪɴᴀʟ", callback_data="settings#caption_mode-off"),
     ],[
         InlineKeyboardButton(("✅ " if rm_cap is True else "» ") + "ꜱᴍᴀʀᴛ ᴄʟᴇᴀɴ", callback_data="settings#caption_mode-smart"),
     ],[
         InlineKeyboardButton(("✅ " if rm_cap == 2 else "» ") + "ᴡɪᴘᴇ ᴀʟʟ ᴄᴀᴘᴛɪᴏɴꜱ", callback_data="settings#caption_mode-wipe"),
     ],[
         InlineKeyboardButton("Cᴜsᴛᴏᴍ Tᴇᴍᴘʟᴀᴛᴇ", callback_data="settings_#noop")
     ],[
         InlineKeyboardButton(cap_lbl, callback_data="settings#addcaption"),
     ]]
     if caption is not None:
         buttons.append([
             InlineKeyboardButton("Vɪᴇᴡ Tᴇᴍᴘʟᴀᴛᴇ",  callback_data="settings#seecaption"),
             InlineKeyboardButton("Cʟᴇᴀʀ Tᴇᴍᴘʟᴀᴛᴇ", callback_data="settings#deletecaption"),
         ])
     buttons.append([InlineKeyboardButton("❮ Bᴀᴄᴋ", callback_data="settings#main")])
     await query.message.edit_text(
         "<b><u>»  Caption Settings</u></b>\n\n"
         f"<b>Current mode:</b> {mode_lbl}\n\n"
         "<b>Modes:</b>\n"
         "• <b>Keep Original</b> — forward caption as-is\n"
         "• <b>Smart Clean</b> — strip links/usernames but keep text\n"
         "• <b>Wipe All Captions</b> — remove caption completely from every file\n\n"
         "<b>Custom Template</b> — override caption with your own text.\n"
         "  Supports: <code>{filename}</code>, <code>{size}</code>, <code>{caption}</code>",
         reply_markup=InlineKeyboardMarkup(buttons))

  elif type=="addcaption":
     await query.message.delete()
     try:
         text = await bot.send_message(query.message.chat.id, "Send your custom caption\n/cancel - <code>cancel this process</code>")
         caption = await bot.listen(chat_id=user_id, timeout=300)
         if getattr(caption, 'text', None) and any(x in caption.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
            await caption.delete()
            return await text.edit_text(
                  "<b>process canceled !</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
         try:
            caption.text.format(filename='', size='', caption='')
         except KeyError as e:
            await caption.delete()
            return await text.edit_text(
               f"<b>wrong filling {e} used in your caption. change it</b>",
               reply_markup=InlineKeyboardMarkup(buttons))
         await update_configs(user_id, 'caption', caption.text)
         await caption.delete()
         await text.edit_text(
            "<b>successfully updated</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="button":
     buttons = []
     button = (await get_configs(user_id))['button']
     if button is None:
        buttons.append([InlineKeyboardButton('Aᴅᴅ Bᴜᴛᴛᴏɴ', 
                      callback_data="settings#addbutton")])
     else:
        buttons.append([InlineKeyboardButton('Sᴇᴇ Bᴜᴛᴛᴏɴ', 
                      callback_data="settings#seebutton")])
        buttons[-1].append(InlineKeyboardButton('Rᴇᴍᴏᴠᴇ Bᴜᴛᴛᴏɴ', 
                      callback_data="settings#deletebutton"))
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>CUSTOM BUTTON</b></u>\n\n<b>You can set a inline button to messages.</b>\n\n<b><u>FORMAT:</b></u>\n`[Forward bot][buttonurl:https://t.me/devgaganbot]`\n",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbutton":
     await query.message.delete()
     try:
         txt = await bot.send_message(user_id, text="**Send your custom button.\n\nFORMAT:**\n`[forward bot][buttonurl:https://t.me/devgaganbot]`\n")
         ask = await bot.listen(chat_id=user_id, timeout=300)
         button = parse_buttons(ask.text.html)
         if not button:
            await ask.delete()
            return await txt.edit_text("**INVALID BUTTON**")
         await update_configs(user_id, 'button', ask.text.html)
         await ask.delete()
         await txt.edit_text("**Successfully button added**",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await txt.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seebutton":
      button = (await get_configs(user_id))['button']
      button = parse_buttons(button, markup=False)
      button.append([InlineKeyboardButton("❮ Bᴀᴄᴋ", "settings#button")])
      await query.message.edit_text(
         "**YOUR CUSTOM BUTTON**",
         reply_markup=InlineKeyboardMarkup(button))
      
  elif type=="deletebutton":
     await update_configs(user_id, 'button', None)
     await query.message.edit_text(
        "**Successfully button deleted**",
        reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="database":
     buttons = []
     db_uri = (await get_configs(user_id))['db_uri']
     if db_uri is None:
        buttons.append([InlineKeyboardButton('Aᴅᴅ Uʀʟ', 
                      callback_data="settings#addurl")])
     else:
        buttons.append([InlineKeyboardButton('Sᴇᴇ Uʀʟ', 
                      callback_data="settings#seeurl")])
        buttons[-1].append(InlineKeyboardButton('Rᴇᴍᴏᴠᴇ Uʀʟ', 
                      callback_data="settings#deleteurl"))
     buttons.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>DATABASE</u>\n\nDatabase is required for store your duplicate messages permenant. other wise stored duplicate media may be disappeared when after bot restart.</b>",
        reply_markup=InlineKeyboardMarkup(buttons))

  elif type=="addurl":
     await query.message.delete()
     uri = await bot.ask(user_id, "<b>please send your mongodb url.</b>\n\n<i>get your Mongodb url from [here](https://mongodb.com)</i>", disable_web_page_preview=True)
     if getattr(uri, 'text', None) and any(x in uri.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
        return await uri.reply_text(
                  "<b>process canceled !</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
     if not uri.text.startswith("mongodb+srv://") and not uri.text.endswith("majority"):
        return await uri.reply("<b>Invalid Mongodb Url</b>",
                   reply_markup=InlineKeyboardMarkup(buttons))
     await update_configs(user_id, 'db_uri', uri.text)
     await uri.reply("**Successfully database url added**",
             reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seeurl":
     db_uri = (await get_configs(user_id))['db_uri']
     await query.answer(f"DATABASE URL: {db_uri}", show_alert=True)
  
  elif type=="deleteurl":
     await update_configs(user_id, 'db_uri', None)
     await query.message.edit_text(
        "**Successfully your database url deleted**",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="filters":
     await query.message.edit_text(
        "<b><u>💠 CUSTOM FILTERS 💠</b></u>\n\n**configure the type of messages which you want forward**",
        reply_markup=await filters_buttons(user_id))
  
  elif type=="nextfilters":
     await query.edit_message_reply_markup( 
        reply_markup=await next_filters_buttons(user_id))
   
  elif type.startswith("updatefilter"):
     i, key, value = type.split('-')
     
     if key == 'rm_caption':
         # Three states: False (Remove), True (Smart Clean), 2 (Keep Original)
         if value == "False":
             await update_configs(user_id, key, True)
         elif value == "True":
             await update_configs(user_id, key, 2)
         else:
             await update_configs(user_id, key, False)
     else:
         if value == "True":
            await update_configs(user_id, key, False)
         else:
            await update_configs(user_id, key, True)
            
     if key in ['poll', 'protect', 'download', 'rm_caption', 'links']:
        return await query.edit_message_reply_markup(
           reply_markup=await next_filters_buttons(user_id)) 
     await query.edit_message_reply_markup(
        reply_markup=await filters_buttons(user_id))
        
  elif type == "set_duration":
    await query.message.delete()
    dur_msg = await bot.ask(user_id, text="**Please send your duration in seconds (between forwards):**")
    if getattr(dur_msg, 'text', None) and any(x in dur_msg.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
       return await dur_msg.reply_text("<b>process canceled</b>", reply_markup=await next_filters_buttons(user_id))
    try:
        duration = int(dur_msg.text)
        await update_configs(user_id, 'duration', duration)
        await dur_msg.reply_text(f"**successfully updated duration to {duration} seconds**", reply_markup=await next_filters_buttons(user_id))
    except ValueError:
        await dur_msg.reply_text("<b>invalid duration, process canceled</b>", reply_markup=await next_filters_buttons(user_id))
   
  elif type.startswith("file_size"):
    settings = await get_configs(user_id)
    size = settings.get('file_size', 0)
    i, limit = size_limit(settings['size_limit'])
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
       reply_markup=size_button(size))
  
  elif type.startswith("update_size"):
    size = int(query.data.split('-')[1])
    if 0 < size > 2000:
      return await query.answer("size limit exceeded", show_alert=True)
    await update_configs(user_id, 'file_size', size)
    i, limit = size_limit((await get_configs(user_id))['size_limit'])
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {limit} `{size} MB` will forward</b>',
       reply_markup=size_button(size))
  
  elif type.startswith('update_limit'):
    i, limit, size = type.split('-')
    limit, sts = size_limit(limit)
    await update_configs(user_id, 'size_limit', limit) 
    await query.message.edit_text(
       f'<b><u>SIZE LIMIT</b></u><b>\n\nyou can set file size limit to forward\n\nStatus: files with {sts} `{size} MB` will forward</b>',
       reply_markup=size_button(int(size)))
      
  elif type == "add_extension":
    await query.message.delete() 
    ext = await bot.ask(user_id, text="**please send your extensions (seperete by space)**")
    if getattr(ext, 'text', None) and any(x in ext.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
       return await ext.reply_text(
                  "<b>process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    extensions = ext.text.split(" ")
    extension = (await get_configs(user_id))['extension']
    if extension:
        for extn in extensions:
            extension.append(extn)
    else:
        extension = extensions
    await update_configs(user_id, 'extension', extension)
    await ext.reply_text(
        f"**successfully updated**",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type == "get_extension":
    extensions = (await get_configs(user_id))['extension']
    btn = extract_btn(extensions)
    btn.append([InlineKeyboardButton('Aᴅᴅ', 'settings#add_extension')])
    btn.append([InlineKeyboardButton('Rᴇᴍᴏᴠᴇ Aʟʟ', 'settings#rmve_all_extension')])
    btn.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>EXTENSIONS</u></b>\n\n**Files with these extiontions will not forward**',
        reply_markup=InlineKeyboardMarkup(btn))
  
  elif type == "rmve_all_extension":
    await update_configs(user_id, 'extension', None)
    await query.message.edit_text(text="**successfully deleted**",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  elif type == "add_keyword":
    await query.message.delete()
    ask = await bot.ask(user_id, text="**please send the keywords (seperete by space)**")
    if getattr(ask, 'text', None) and any(x in ask.text.lower() for x in ['cancel', 'cᴀɴᴄᴇʟ', '⛔']):
       return await ask.reply_text(
                  "<b>process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    keywords = ask.text.split(" ")
    keyword = (await get_configs(user_id))['keywords']
    if keyword:
        for word in keywords:
            keyword.append(word)
    else:
        keyword = keywords
    await update_configs(user_id, 'keywords', keyword)
    await ask.reply_text(
        f"**successfully updated**",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type == "get_keyword":
    keywords = (await get_configs(user_id))['keywords']
    btn = extract_btn(keywords)
    btn.append([InlineKeyboardButton('Aᴅᴅ', 'settings#add_keyword')])
    btn.append([InlineKeyboardButton('Rᴇᴍᴏᴠᴇ Aʟʟ', 'settings#rmve_all_keyword')])
    btn.append([InlineKeyboardButton('❮ Bᴀᴄᴋ', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>KEYWORDS</u></b>\n\n**File with these keywords in file name will forwad**',
        reply_markup=InlineKeyboardMarkup(btn))
      
  elif type == "rmve_all_keyword":
    await update_configs(user_id, 'keywords', None)
    await query.message.edit_text(text="**successfully deleted**",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  elif type.startswith("alert"):
    alert = type.split('_')[1]
    await query.answer(alert, show_alert=True)

  elif type == "toggle_mode":
    data = await get_configs(user_id)
    current = data.get('bot_mode', 'forward')
    new_mode = 'merger' if current == 'forward' else 'forward'
    await update_configs(user_id, 'bot_mode', new_mode)
    mode_lbl = "🔀 Merger" if new_mode == 'merger' else "📤 Forward"
    await query.answer(f"Mode switched to {mode_lbl}!", show_alert=True)
    await query.message.edit_text(
        await t(user_id, 'settings_title'),
        reply_markup=await main_buttons(user_id)
    )

async def main_buttons(user_id=None):
  # Get current mode
  mode = 'forward'
  if user_id:
      try:
          data = await get_configs(user_id)
          mode = data.get('bot_mode', 'forward')
      except Exception:
          pass

  if mode == 'merger':
      #  MERGER MODE: Clean separate menu 
      buttons = [[
           InlineKeyboardButton('Mᴇʀɢᴇʀ Mᴏᴅᴇ ⟶ Tᴀᴘ Tᴏ Sᴡɪᴛᴄʜ',
                        callback_data='settings#toggle_mode')
           ],[
           InlineKeyboardButton('Aᴄᴄᴏᴜɴᴛs',
                        callback_data='settings#accounts'),
           InlineKeyboardButton('Cʜᴀɴɴᴇʟs',
                        callback_data='settings#channels')
           ],[
           InlineKeyboardButton('Aᴜᴅɪᴏ Mᴇʀɢᴇ',
                        callback_data='mg#audio_list'),
           InlineKeyboardButton('Vɪᴅᴇᴏ Mᴇʀɢᴇ',
                        callback_data='mg#video_list')
           ],[
           InlineKeyboardButton('Bᴀᴛᴄʜ Lɪɴᴋs Bᴏᴛ Sᴇᴛᴜᴘ',
                        callback_data='settings#sharebot')
           ],[
           InlineKeyboardButton('❮ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ', callback_data='back')
           ]]
  else:
      #  FORWARD MODE: Full original menu 
      buttons = [[
           InlineKeyboardButton('↔️ Fᴏʀᴡᴀʀᴅ Mᴏᴅᴇ ⟶ Tᴀᴘ Tᴏ Sᴡɪᴛᴄʜ',
                        callback_data='settings#toggle_mode')
           ],[
           InlineKeyboardButton('Aᴄᴄᴏᴜɴᴛs',
                        callback_data='settings#accounts'),
           InlineKeyboardButton('Cʜᴀɴɴᴇʟs',
                        callback_data='settings#channels')
           ],[
           InlineKeyboardButton('Cᴀᴘᴛɪᴏɴ',
                        callback_data='settings#caption'),
           InlineKeyboardButton('️ Mᴏɴɢᴏᴅʙ',
                        callback_data='settings#database')
           ],[
           InlineKeyboardButton('Fɪʟᴛᴇʀs',
                        callback_data='settings#filters'),
           InlineKeyboardButton('️ Bᴜᴛᴛᴏɴs',
                        callback_data='settings#button')
           ],[
           InlineKeyboardButton('Exᴛʀᴀ Sᴇᴛᴛɪɴɢs',
                        callback_data='settings#nextfilters'),
           InlineKeyboardButton('EN/हि',
                        callback_data='settings#lang')
           ],[
           InlineKeyboardButton('Mᴀɪɴ Mᴇɴᴜ Iᴍᴀɢᴇ',
                        callback_data='settings#main_menu_img')
           ],[
           InlineKeyboardButton('Bᴀᴛᴄʜ Lɪɴᴋs Bᴏᴛ Sᴇᴛᴜᴘ',
                        callback_data='settings#sharebot')
           ],[
           InlineKeyboardButton('❮ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ', callback_data='back')
           ]]
  return InlineKeyboardMarkup(buttons)



def size_limit(limit):
   if str(limit) == "None":
      return None, ""
   elif str(limit) == "True":
      return True, "more than"
   else:
      return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
       for data in datas:
         if i >= 5:
            i = 0
         if i == 0:
            btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
            i += 1
            continue
         elif i > 0:
            btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
            i += 1
    return btn 

def size_button(size):
  buttons = [[
       InlineKeyboardButton('+',
                    callback_data=f'settings#update_limit-True-{size}'),
       InlineKeyboardButton('=',
                    callback_data=f'settings#update_limit-None-{size}'),
       InlineKeyboardButton('-',
                    callback_data=f'settings#update_limit-False-{size}')
       ],[
       InlineKeyboardButton('+1',
                    callback_data=f'settings#update_size-{size + 1}'),
       InlineKeyboardButton('-1',
                    callback_data=f'settings#update_size_-{size - 1}')
       ],[
       InlineKeyboardButton('+5',
                    callback_data=f'settings#update_size-{size + 5}'),
       InlineKeyboardButton('-5',
                    callback_data=f'settings#update_size_-{size - 5}')
       ],[
       InlineKeyboardButton('+10',
                    callback_data=f'settings#update_size-{size + 10}'),
       InlineKeyboardButton('-10',
                    callback_data=f'settings#update_size_-{size - 10}')
       ],[
       InlineKeyboardButton('+50',
                    callback_data=f'settings#update_size-{size + 50}'),
       InlineKeyboardButton('-50',
                    callback_data=f'settings#update_size_-{size - 50}')
       ],[
       InlineKeyboardButton('+100',
                    callback_data=f'settings#update_size-{size + 100}'),
       InlineKeyboardButton('-100',
                    callback_data=f'settings#update_size_-{size - 100}')
       ],[
       InlineKeyboardButton('❮ Bᴀᴄᴋ',
                    callback_data="settings#main")
     ]]
  return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('Fᴏʀᴡᴀʀᴅ Tᴀɢ',
                    callback_data=f'settings_#updatefilter-forward_tag-{filter["forward_tag"]}'),
       InlineKeyboardButton('[ ON ]' if filter['forward_tag'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')
       ],[
       InlineKeyboardButton('Tᴇxᴛs',
                    callback_data=f'settings_#updatefilter-text-{filters["text"]}'),
       InlineKeyboardButton('[ ON ]' if filters['text'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-text-{filters["text"]}')
       ],[
       InlineKeyboardButton('Dᴏᴄᴜᴍᴇɴᴛs',
                    callback_data=f'settings_#updatefilter-document-{filters["document"]}'),
       InlineKeyboardButton('[ ON ]' if filters['document'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-document-{filters["document"]}')
       ],[
       InlineKeyboardButton('Vɪᴅᴇᴏs',
                    callback_data=f'settings_#updatefilter-video-{filters["video"]}'),
       InlineKeyboardButton('[ ON ]' if filters['video'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-video-{filters["video"]}')
       ],[
       InlineKeyboardButton('Pʜᴏᴛᴏs',
                    callback_data=f'settings_#updatefilter-photo-{filters["photo"]}'),
       InlineKeyboardButton('[ ON ]' if filters['photo'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-photo-{filters["photo"]}')
       ],[
       InlineKeyboardButton('Aᴜᴅɪᴏs',
                    callback_data=f'settings_#updatefilter-audio-{filters["audio"]}'),
       InlineKeyboardButton('[ ON ]' if filters['audio'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-audio-{filters["audio"]}')
       ],[
       InlineKeyboardButton('Vᴏɪᴄᴇs',
                    callback_data=f'settings_#updatefilter-voice-{filters["voice"]}'),
       InlineKeyboardButton('[ ON ]' if filters['voice'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-voice-{filters["voice"]}')
       ],[
       InlineKeyboardButton('Aɴɪᴍᴀᴛɪᴏɴs',
                    callback_data=f'settings_#updatefilter-animation-{filters["animation"]}'),
       InlineKeyboardButton('[ ON ]' if filters['animation'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-animation-{filters["animation"]}')
       ],[
       InlineKeyboardButton('Sᴛɪᴄᴋᴇʀs',
                    callback_data=f'settings_#updatefilter-sticker-{filters["sticker"]}'),
       InlineKeyboardButton('[ ON ]' if filters['sticker'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-sticker-{filters["sticker"]}')
       ],[
       InlineKeyboardButton('Sᴋɪᴘ Dᴜᴘʟɪᴄᴀᴛᴇ',
                    callback_data=f'settings_#updatefilter-duplicate-{filter["duplicate"]}'),
       InlineKeyboardButton('[ ON ]' if filter['duplicate'] else '[ OFF ]',
                    callback_data=f'settings#updatefilter-duplicate-{filter["duplicate"]}')
       ],[
               InlineKeyboardButton('Cᴀᴘᴛɪᴏɴ Sᴇᴛᴛɪɴɢs →',

                     callback_data='settings#caption'),

        InlineKeyboardButton(
            '[ ON ]' if filters.get('rm_caption', False) is True else (
            '[ OFF ]' if filters.get('rm_caption', False) == 2 else '[ OFF ]'),
                     callback_data='settings#caption')

        ],[
       InlineKeyboardButton('❮ Bᴀᴄᴋ',
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  links_on = filters.get('links', False)
  buttons = [[
       InlineKeyboardButton('Pᴏʟʟ',
                    callback_data=f'settings_#updatefilter-poll-{filters.get("poll", True)}'),
       InlineKeyboardButton('[ ON ]' if filters.get('poll', True) else '[ OFF ]',
                    callback_data=f'settings#updatefilter-poll-{filters.get("poll", True)}')
       ],[
       InlineKeyboardButton('Sᴇᴄᴜʀᴇ Mᴇssᴀɢᴇ',
                    callback_data=f'settings_#updatefilter-protect-{filter.get("protect", False)}'),
       InlineKeyboardButton('[ ON ]' if filter.get('protect', False) else '[ OFF ]',
                    callback_data=f'settings#updatefilter-protect-{filter.get("protect", False)}')
       ],[
       InlineKeyboardButton('Dᴏᴡɴʟᴏᴀᴅ Mᴏᴅᴇ',
                    callback_data=f'settings_#updatefilter-download-{filter.get("download", False)}'),
       InlineKeyboardButton('[ ON ]' if filter.get('download', False) else '[ OFF ]',
                    callback_data=f'settings#updatefilter-download-{filter.get("download", False)}')
       ],[
       InlineKeyboardButton('Lɪɴᴋs',
                    callback_data=f'settings_#updatefilter-links-{links_on}'),
       InlineKeyboardButton('[ ON ]' if links_on else '[ OFF ]',
                    callback_data=f'settings#updatefilter-links-{links_on}')
       ],[
       InlineKeyboardButton('Sɪᴢᴇ Lɪᴍɪᴛ',
                    callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('️ Sᴇᴛ Dᴜʀᴀᴛɪᴏɴ',
                    callback_data='settings#set_duration')
       ],[
       InlineKeyboardButton('Exᴛᴇɴsɪᴏɴ',
                    callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('️ Kᴇʏᴡᴏʀᴅs ️',
                    callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('❮ Bᴀᴄᴋ Tᴏ Mᴇɴᴜ', 
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons)
