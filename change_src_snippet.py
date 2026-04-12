@Client.on_callback_query(filters.regex(r'^job#src#'))
async def job_src_cb(bot, query):
    user_id = query.from_user.id
    job_id = query.data.split("#", 2)[2]
    await query.message.delete()
    await bot.send_message(user_id, "Opening source change wizard…")
    asyncio.create_task(_do_change_source(bot, user_id, job_id))

async def _do_change_source(bot, uid: int, jid: str):
    from pyrogram.types import ReplyKeyboardRemove
    from plugins.utils import ask_channel_picker, check_chat_protection

    job = await _get_job(jid)
    if not job:
        await bot.send_message(uid, "<b>❌ Job not found.</b>")
        return

    was_running = job.get("status") == "running"
    if was_running:
        await _update_job(jid, {"status": "paused"})
        if jid in _job_tasks and not _job_tasks[jid].done():
            _job_tasks[jid].cancel()

    await bot.send_message(
        uid,
        "<b>✏️ Change Live Job Source</b>\n\n"
        "Select a new source from your saved channels, or tap "
        "<b>✍️ Manual Input</b> to paste a chat ID / topic link directly.\n\n"
        "<i>The job will pause during selection and auto-resume once updated.</i>",
        reply_markup=__import__('pyrogram.types', fromlist=['ReplyKeyboardMarkup'])
            .__class__ 
    )

    picked = await ask_channel_picker(
        bot, uid,
        prompt="Select the new source channel / group:",
        extra_options=["✍️ Manual Input"],
        timeout=300
    )

    new_source = None
    new_source_title = None

    if picked is None:
        pass
    elif picked == "✍️ Manual Input":
        try:
            ask_msg = await bot.ask(
                uid,
                "✍️ <b>Enter the source:</b>\n\n"
                "Accepted formats:\n"
                "• Numeric chat ID: <code>-1001234567890</code>\n"
                "• @username: <code>@mychannel</code>\n"
                "• Topic URL: <code>https://t.me/c/1234567890/5</code>\n"
                "<i>Send ⛔ to cancel.</i>",
                timeout=300,
                reply_markup=ReplyKeyboardRemove()
            )
            text = (ask_msg.text or "").strip()
            if not text or "⛔" in text or text.lower() == "cancel":
                await bot.send_message(uid, "<i>Cancelled.</i>")
            else:
                import re as _re
                m = _re.match(r'https?://t\.me/c/(\d+)/(\d+)', text)
                if m:
                    new_source = f"-100{m.group(1)}"
                    new_source_title = f"Topic /c/{m.group(1)}/{m.group(2)}"
                elif _re.match(r'https?://t\.me/([^/]+)/(\d+)', text):
                    mm = _re.match(r'https?://t\.me/([^/]+)/(\d+)', text)
                    new_source = f"@{mm.group(1)}"
                    new_source_title = f"@{mm.group(1)}"
                elif text.lstrip('-').isdigit() or text.startswith('@'):
                    new_source = text
                    new_source_title = text
                else:
                    await bot.send_message(uid, "<b>❌ Unrecognised format.</b>")
        except asyncio.TimeoutError:
            await bot.send_message(uid, "<i>⏱ Timed out.</i>")
    elif isinstance(picked, dict):
        new_source = str(picked.get("chat_id", ""))
        new_source_title = picked.get("title", new_source)

    if new_source:
        prot = await check_chat_protection(uid, new_source)
        if prot:
            await bot.send_message(uid, prot)
            if was_running:
                await _update_job(jid, {"status": "running"})
                _start_job_task(jid, uid)
            return

        await _update_job(jid, {
            "from_chat": new_source,
            "from_title": new_source_title,
            "last_seen_id": 0,
            "batch_cursor": 0,
        })
        await bot.send_message(
            uid,
            f"<b>✅ Source updated!</b>\n\n"
            f"<b>New Source:</b> <code>{new_source_title}</code>\n"
            f"<b>Scan Position:</b> Reset to 0\n"
        )
    else:
        if picked is not None:
            await bot.send_message(uid, "<i>Source unchanged.</i>")

    if was_running:
        await _update_job(jid, {"status": "running"})
        _start_job_task(jid, uid)
        await bot.send_message(uid, "▶️ <b>Job resumed.</b>")
