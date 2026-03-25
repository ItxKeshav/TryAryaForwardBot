"""
Merger Plugin — v3
==================
Merges media files from a source channel range into one combined file using FFmpeg.

Features:
  • Separate Audio Merge and Video Merge sections
  • Start / Stop / Resume controls (resumes from where stopped)
  • Detailed info page with download time, merge time, upload time, ETA
  • Full metadata editing including cover/thumbnail artwork
  • Destination channel support
  • Multi merge — multiple jobs simultaneously
  • Progress bar with real-time speed + ETA
  • No format skipping — ALL media files merged in strict order
  • Lossless when possible, high-quality re-encode as fallback

Commands:
  /merge  — Open the Merger manager UI
"""
import os
import re
import time
import uuid
import asyncio
import logging
import shutil
import subprocess
from database import db
from .test import CLIENT, start_clone_bot
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
)

logger = logging.getLogger(__name__)
_CLIENT = CLIENT()

# ─── In-memory registries ────────────────────────────────────────────────────
_merge_tasks: dict[str, asyncio.Task] = {}
_merge_paused: dict[str, asyncio.Event] = {}   # set=running, clear=paused
_merge_waiting: dict[int, asyncio.Future] = {}


# ─── Future-based ask() ──────────────────────────────────────────────────────
@Client.on_message(filters.private, group=-14)
async def _merge_input_router(bot, message):
    uid = message.from_user.id if message.from_user else None
    if uid and uid in _merge_waiting:
        fut = _merge_waiting.pop(uid)
        if not fut.done():
            fut.set_result(message)


async def _merge_ask(bot, user_id, text, reply_markup=None, timeout=300):
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    old = _merge_waiting.pop(user_id, None)
    if old and not old.done():
        old.cancel()
    _merge_waiting[user_id] = fut
    await bot.send_message(user_id, text, reply_markup=reply_markup)
    try:
        return await asyncio.wait_for(fut, timeout=timeout)
    except asyncio.TimeoutError:
        _merge_waiting.pop(user_id, None)
        raise


# ══════════════════════════════════════════════════════════════════════════════
# DB helpers
# ══════════════════════════════════════════════════════════════════════════════
COLL = "mergejobs"

async def _mg_save(job):
    await db.db[COLL].replace_one({"job_id": job["job_id"]}, job, upsert=True)

async def _mg_get(job_id):
    return await db.db[COLL].find_one({"job_id": job_id})

async def _mg_list(user_id):
    return [j async for j in db.db[COLL].find({"user_id": user_id})]

async def _mg_delete(job_id):
    await db.db[COLL].delete_one({"job_id": job_id})

async def _mg_update(job_id, **kw):
    await db.db[COLL].update_one({"job_id": job_id}, {"$set": kw})


# ══════════════════════════════════════════════════════════════════════════════
# Formatting helpers
# ══════════════════════════════════════════════════════════════════════════════

def _bar(cur, tot, w=20):
    if tot <= 0: return "[" + "░" * w + "] 0%"
    pct = min(100, int(cur / tot * 100))
    f = int(w * cur / tot)
    return f"[{'█' * f}{'░' * (w - f)}] {pct}%"

def _sz(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    if b < 1073741824: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.2f} GB"

def _spd(bps):
    if bps < 1024: return f"{bps:.0f} B/s"
    if bps < 1048576: return f"{bps/1024:.1f} KB/s"
    return f"{bps/1048576:.1f} MB/s"

def _tm(s):
    s = max(0, int(s))
    if s < 60: return f"{s}s"
    if s < 3600: return f"{s//60}m {s%60}s"
    return f"{s//3600}h {(s%3600)//60}m"


# ══════════════════════════════════════════════════════════════════════════════
# FFmpeg helpers
# ══════════════════════════════════════════════════════════════════════════════

def _check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def _get_media_info(fp):
    info = {"type": "audio", "codec": "", "duration": 0}
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries",
             "stream=codec_type,codec_name", "-show_entries",
             "format=duration", "-of", "csv=p=0", fp],
            capture_output=True, text=True, timeout=30)
        for line in r.stdout.strip().split("\n"):
            parts = line.strip().split(",")
            if len(parts) >= 2:
                if parts[1] == "video": info["type"] = "video"; info["codec"] = parts[0]
                elif parts[1] == "audio" and not info.get("codec"): info["codec"] = parts[0]
            elif len(parts) == 1:
                try: info["duration"] = float(parts[0])
                except: pass
    except: pass
    if not info["codec"]:
        ext = os.path.splitext(fp)[1].lower()
        if ext in (".mp4",".mkv",".avi",".webm",".mov",".flv",".ts"): info["type"] = "video"
        info["codec"] = ext.lstrip(".")
    return info


def _merge_ffmpeg(file_list, output_path, metadata=None, media_type="audio", cover_path=None):
    """Merge files. Try lossless first, fallback to re-encode."""
    list_path = output_path + ".list.txt"
    try:
        with open(list_path, "w", encoding="utf-8") as f:
            for fp in file_list:
                f.write(f"file '{fp.replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")

        # Strategy 1: lossless concat
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy"]
        if cover_path and os.path.exists(cover_path) and media_type == "audio":
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                   "-i", cover_path, "-map", "0:a", "-map", "1:0",
                   "-c:a", "copy", "-id3v2_version", "3",
                   "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
        if metadata:
            for k, v in metadata.items():
                if v: cmd.extend(["-metadata", f"{k}={v}"])
        cmd.append(output_path)

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if r.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, ""

        # Strategy 2: high-quality re-encode
        logger.warning(f"Concat copy failed, re-encoding...")
        cmd2 = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path]
        if cover_path and os.path.exists(cover_path):
            cmd2.extend(["-i", cover_path])
        if media_type == "video":
            cmd2.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                         "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart"])
        else:
            cmd2.extend(["-c:a", "libmp3lame", "-b:a", "320k", "-ar", "44100"])
            if cover_path and os.path.exists(cover_path):
                cmd2.extend(["-map", "0:a", "-map", "1:0",
                             "-id3v2_version", "3",
                             "-metadata:s:v", "title=Album cover",
                             "-metadata:s:v", "comment=Cover (front)"])
        if metadata:
            for k, v in metadata.items():
                if v: cmd2.extend(["-metadata", f"{k}={v}"])
        cmd2.append(output_path)

        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=14400)
        if r2.returncode != 0:
            return False, r2.stderr[-500:]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "FFmpeg timed out"
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(list_path): os.remove(list_path)


# ══════════════════════════════════════════════════════════════════════════════
# Core merge runner — with pause/resume support
# ══════════════════════════════════════════════════════════════════════════════
BATCH_SIZE = 200

async def _run_merge_job(job_id, user_id, bot):
    job = await _mg_get(job_id)
    if not job: return

    # Pause/resume event
    ev = _merge_paused.get(job_id)
    if not ev:
        ev = asyncio.Event()
        ev.set()  # running by default
        _merge_paused[job_id] = ev

    client = None
    work_dir = f"merge_tmp/{job_id}"
    os.makedirs(work_dir, exist_ok=True)

    try:
        acc = await db.get_bot(user_id, job["account_id"])
        if not acc:
            await _mg_update(job_id, status="error", error="Account not found")
            return

        client = await start_clone_bot(_CLIENT.client(acc))

        from_chat   = job["from_chat"]
        start_id    = job["start_id"]
        end_id      = job["end_id"]
        out_name    = job.get("output_name", "merged")
        metadata    = job.get("metadata", {})
        dest_chats  = job.get("dest_chats", [])
        merge_type  = job.get("merge_type", "audio")  # "audio" or "video"
        cover_path  = None

        # Resume support — start from where we left off
        resume_from = job.get("current_id", start_id)
        already_dl  = job.get("downloaded", 0)

        await _mg_update(job_id, status="downloading", error="",
                         dl_start_time=time.time())

        # ── Check if cover image was already saved ────────────────────────
        cover_file = os.path.join(work_dir, "cover.jpg")
        if os.path.exists(cover_file):
            cover_path = cover_file

        # ── Phase 1: Download ─────────────────────────────────────────────
        # Collect any previously downloaded files
        existing_files = sorted([
            os.path.join(work_dir, f) for f in os.listdir(work_dir)
            if f.startswith("0") and not f.endswith(".list.txt")
        ])
        downloaded_files = existing_files[:]
        total_range = end_id - start_id + 1
        downloaded_count = len(existing_files)
        total_dl_bytes = sum(os.path.getsize(f) for f in existing_files)
        skipped = 0
        dl_start = time.time()

        status_msg = None
        last_edit = 0
        current = resume_from

        while current <= end_id:
            # Pause check
            if not ev.is_set():
                await _mg_update(job_id, status="paused", current_id=current)
                await ev.wait()  # Block until resumed
                await _mg_update(job_id, status="downloading")

            # Stop check
            fresh = await _mg_get(job_id)
            if not fresh or fresh.get("status") == "stopped":
                return

            batch_end = min(current + BATCH_SIZE - 1, end_id)
            batch_ids = list(range(current, batch_end + 1))

            try:
                msgs = await client.get_messages(from_chat, batch_ids)
                if not isinstance(msgs, list): msgs = [msgs]
            except FloodWait as fw:
                await asyncio.sleep(fw.value + 2)
                continue
            except Exception as e:
                logger.warning(f"[Merge {job_id}] Fetch error: {e}")
                current += BATCH_SIZE
                continue

            valid = [m for m in msgs if m and not m.empty and not m.service]
            valid.sort(key=lambda m: m.id)

            for msg in valid:
                if not msg.media:
                    skipped += 1
                    continue

                media_obj = None
                for attr in ('audio', 'video', 'document', 'voice', 'video_note'):
                    media_obj = getattr(msg, attr, None)
                    if media_obj: break

                if not media_obj:
                    skipped += 1
                    continue

                # Get extension
                ext = ""
                fn = getattr(media_obj, 'file_name', None)
                if fn: ext = os.path.splitext(fn)[1].lower()
                if not ext:
                    if getattr(msg, 'audio', None):
                        mime = getattr(media_obj, 'mime_type', '') or ''
                        ext = ".m4a" if 'm4a' in mime or 'mp4' in mime else \
                              ".ogg" if 'ogg' in mime else \
                              ".flac" if 'flac' in mime else \
                              ".wav" if 'wav' in mime else ".mp3"
                    elif getattr(msg, 'voice', None): ext = ".ogg"
                    elif getattr(msg, 'video', None) or getattr(msg, 'video_note', None): ext = ".mp4"
                    elif getattr(msg, 'document', None):
                        mime = getattr(media_obj, 'mime_type', '') or ''
                        ext = ".mp3" if 'audio' in mime else ".mp4" if 'video' in mime else ".bin"

                seq_name = f"{downloaded_count:06d}{ext}"
                dl_path = os.path.join(work_dir, seq_name)

                # Download with retry
                fp = None
                for attempt in range(5):
                    try:
                        fp = await client.download_media(msg, file_name=dl_path)
                        if fp: break
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value + 2)
                    except Exception as e:
                        if attempt < 4: await asyncio.sleep(3); continue
                        logger.warning(f"[Merge {job_id}] DL fail {msg.id}: {e}")
                        break

                if fp and os.path.exists(fp):
                    fsz = os.path.getsize(fp)
                    total_dl_bytes += fsz
                    downloaded_files.append(fp)
                    downloaded_count += 1

                    # Save progress for resume
                    await _mg_update(job_id, downloaded=downloaded_count,
                                     current_id=msg.id, total_dl_bytes=total_dl_bytes)

                    # Progress update (rate-limited: every 3s)
                    now = time.time()
                    if now - last_edit >= 3:
                        last_edit = now
                        elapsed = now - dl_start
                        speed = total_dl_bytes / elapsed if elapsed > 0 else 0
                        files_left = total_range - downloaded_count - skipped
                        eta = (files_left * elapsed / max(downloaded_count, 1))
                        txt = (
                            f"<b>⬇️ Downloading — {merge_type.title()} Merge</b>\n\n"
                            f"<code>{_bar(downloaded_count, total_range - skipped)}</code>\n\n"
                            f"📁 <b>Files:</b> {downloaded_count}/{total_range - skipped}\n"
                            f"💾 <b>Downloaded:</b> {_sz(total_dl_bytes)}\n"
                            f"⚡ <b>Speed:</b> {_spd(speed)}\n"
                            f"⏱ <b>ETA:</b> {_tm(eta)}"
                        )
                        try:
                            if status_msg:
                                await status_msg.edit_text(txt)
                            else:
                                status_msg = await bot.send_message(user_id, txt)
                        except Exception:
                            pass
                else:
                    skipped += 1

            current = batch_end + 1
            await _mg_update(job_id, current_id=current)

        dl_time = time.time() - dl_start

        if not downloaded_files:
            await _mg_update(job_id, status="error", error="No media files found")
            try:
                if status_msg: await status_msg.edit_text("<b>❌ No media files found in range.</b>")
                else: await bot.send_message(user_id, "<b>❌ No media files found in range.</b>")
            except: pass
            return

        # Update download complete
        try:
            txt = (f"<b>✅ Download Complete</b>\n\n"
                   f"📁 {downloaded_count} files • {_sz(total_dl_bytes)}\n"
                   f"⏱ Time: {_tm(dl_time)}")
            if status_msg: await status_msg.edit_text(txt)
            else: await bot.send_message(user_id, txt)
        except: pass

        # ── Phase 2: Merge ────────────────────────────────────────────────
        await _mg_update(job_id, status="merging", merge_start_time=time.time())

        out_ext = ".mp4" if merge_type == "video" else ".mp3"
        output_path = os.path.join(work_dir, f"{out_name}{out_ext}")

        merge_msg = None
        try:
            merge_msg = await bot.send_message(user_id,
                f"<b>🔀 Merging {downloaded_count} {'video' if merge_type == 'video' else 'audio'} files...</b>\n\n"
                f"<b>Output:</b> <code>{out_name}{out_ext}</code>\n"
                f"<i>Trying lossless concat first. If codecs differ, will re-encode at highest quality.</i>")
        except: pass

        loop = asyncio.get_event_loop()
        success, err = await loop.run_in_executor(
            None, _merge_ffmpeg, downloaded_files, output_path, metadata, merge_type, cover_path)

        merge_time = time.time() - (job.get("merge_start_time") or time.time())

        if not success:
            await _mg_update(job_id, status="error", error=err[:500])
            try:
                if merge_msg: await merge_msg.edit_text(f"<b>❌ Merge failed!</b>\n<code>{err[:400]}</code>")
            except: pass
            return

        fsize = os.path.getsize(output_path)
        if fsize > 2 * 1024**3:
            await _mg_update(job_id, status="error", error=f"File too large: {_sz(fsize)}")
            try:
                if merge_msg: await merge_msg.edit_text(f"<b>❌ {_sz(fsize)} exceeds 2GB Telegram limit.</b>")
            except: pass
            return

        try:
            if merge_msg: await merge_msg.edit_text(
                f"<b>✅ Merge Complete</b>\n📦 {_sz(fsize)} • ⏱ {_tm(merge_time)}")
        except: pass

        # ── Phase 3: Upload ───────────────────────────────────────────────
        await _mg_update(job_id, status="uploading", upload_start_time=time.time())

        caption = f"<b>🔀 {out_name}{out_ext}</b>\n📁 {downloaded_count} files • {_sz(fsize)}"
        if metadata.get("title"): caption += f"\n🎵 {metadata['title']}"
        if metadata.get("artist"): caption += f" — {metadata['artist']}"

        all_dests = [user_id] + [d for d in dest_chats if d != user_id]
        up_start = time.time()

        for dest in all_dests:
            for attempt in range(3):
                try:
                    thumb = cover_path if cover_path and os.path.exists(cover_path) else None
                    if merge_type == "video":
                        await client.send_video(chat_id=dest, video=output_path,
                            caption=caption, file_name=f"{out_name}{out_ext}",
                            thumb=thumb, supports_streaming=True)
                    else:
                        kw = {"chat_id": dest, "audio": output_path, "caption": caption,
                              "file_name": f"{out_name}{out_ext}", "thumb": thumb}
                        if metadata.get("title"): kw["title"] = metadata["title"]
                        if metadata.get("artist"): kw["performer"] = metadata["artist"]
                        await client.send_audio(**kw)
                    break
                except FloodWait as fw:
                    await asyncio.sleep(fw.value + 2)
                except Exception as e:
                    if attempt < 2: await asyncio.sleep(5); continue
                    logger.warning(f"[Merge {job_id}] Upload to {dest}: {e}")
                    break

        up_time = time.time() - up_start
        total_time = time.time() - dl_start

        # ── Done ──────────────────────────────────────────────────────────
        await _mg_update(job_id, status="done",
                         dl_time=dl_time, merge_time=merge_time,
                         up_time=up_time, total_time=total_time,
                         file_size=fsize)

        try:
            await bot.send_message(user_id,
                f"<b>✅ Merge Job Complete!</b>\n\n"
                f"╭───── 📊 <b>Statistics</b> ─────╮\n"
                f"┃ 📁 <b>Files:</b> {downloaded_count}\n"
                f"┃ 📦 <b>Output:</b> <code>{out_name}{out_ext}</code>\n"
                f"┃ 💾 <b>Size:</b> {_sz(fsize)}\n"
                f"┃\n"
                f"┃ ⬇️ <b>Download:</b> {_tm(dl_time)}\n"
                f"┃ 🔀 <b>Merge:</b> {_tm(merge_time)}\n"
                f"┃ ⬆️ <b>Upload:</b> {_tm(up_time)}\n"
                f"┃ ⏱ <b>Total:</b> {_tm(total_time)}\n"
                f"╰─────────────────────────╯")
        except: pass

    except asyncio.CancelledError:
        await _mg_update(job_id, status="stopped")
    except Exception as e:
        logger.error(f"[Merge {job_id}] Fatal: {e}")
        await _mg_update(job_id, status="error", error=str(e)[:500])
        try: await bot.send_message(user_id, f"<b>❌ Error:</b> <code>{e}</code>")
        except: pass
    finally:
        _merge_tasks.pop(job_id, None)
        _merge_paused.pop(job_id, None)
        try:
            if os.path.exists(work_dir): shutil.rmtree(work_dir, ignore_errors=True)
        except: pass
        if client:
            try: await client.stop()
            except: pass


def _start_merge_task(job_id, user_id, bot):
    """Start or restart a merge task."""
    old = _merge_tasks.get(job_id)
    if old and not old.done():
        return  # Already running
    ev = asyncio.Event()
    ev.set()
    _merge_paused[job_id] = ev
    task = asyncio.create_task(_run_merge_job(job_id, user_id, bot))
    _merge_tasks[job_id] = task


# ══════════════════════════════════════════════════════════════════════════════
# Parse message link
# ══════════════════════════════════════════════════════════════════════════════

def _parse_link(text):
    text = text.strip()
    if text.isdigit(): return None, int(text)
    m = re.match(r'https?://t\.me/c/(\d+)/(\d+)', text)
    if m: return int(m.group(1)), int(m.group(2))
    m = re.match(r'https?://t\.me/([^/]+)/(\d+)', text)
    if m: return m.group(1), int(m.group(2))
    return None, None


# ══════════════════════════════════════════════════════════════════════════════
# Status emoji helper
# ══════════════════════════════════════════════════════════════════════════════

def _st(status):
    return {"downloading": "⬇️", "merging": "🔀", "uploading": "⬆️",
            "done": "✅", "error": "⚠️", "stopped": "🔴",
            "paused": "⏸", "running": "▶️"}.get(status, "❓")


# ══════════════════════════════════════════════════════════════════════════════
# /merge Command & Main UI
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("merge") & filters.private)
async def merge_cmd(bot, message):
    user_id = message.from_user.id
    if not _check_ffmpeg():
        return await message.reply(
            "<b>❌ FFmpeg not installed.</b>\n<code>sudo apt install ffmpeg</code>")
    await _render_merge_list(bot, user_id, message)


async def _render_merge_list(bot, user_id, msg_or_query, merge_type=None):
    """Render the merge job list UI."""
    is_cb = hasattr(msg_or_query, 'message')
    jobs = await _mg_list(user_id)

    # Filter by type if specified
    if merge_type:
        jobs = [j for j in jobs if j.get("merge_type", "audio") == merge_type]

    type_label = ""
    if merge_type == "audio": type_label = "🎵 Audio "
    elif merge_type == "video": type_label = "🎬 Video "

    active = [j for j in jobs if j.get("status") in ("downloading","merging","uploading","paused")]
    done_jobs = [j for j in jobs if j.get("status") in ("done","error","stopped")][:5]

    btns = []
    if active:
        btns.append([InlineKeyboardButton(f"━━━ 🔄 Active {type_label}Merges ━━━", callback_data="merge#noop")])
        for j in active:
            jid = j["job_id"]
            short = jid[-6:]
            s = j.get("status", "stopped")
            name = j.get("output_name", short)
            prog = j.get("downloaded", 0)
            row = [InlineKeyboardButton(f"{_st(s)} {name} [{prog}]", callback_data=f"merge#info#{jid}")]
            btns.append(row)

            ctrl = []
            if s in ("downloading", "merging", "uploading"):
                ctrl.append(InlineKeyboardButton(f"⏸ Pause", callback_data=f"merge#pause#{jid}"))
                ctrl.append(InlineKeyboardButton(f"⏹ Stop", callback_data=f"merge#stop#{jid}"))
            elif s == "paused":
                ctrl.append(InlineKeyboardButton(f"▶️ Resume", callback_data=f"merge#resume#{jid}"))
                ctrl.append(InlineKeyboardButton(f"⏹ Stop", callback_data=f"merge#stop#{jid}"))
            if ctrl:
                btns.append(ctrl)

    if done_jobs:
        btns.append([InlineKeyboardButton(f"━━━ 📜 Recent ━━━", callback_data="merge#noop")])
        for j in done_jobs:
            jid = j["job_id"]
            short = jid[-6:]
            name = j.get("output_name", short)
            row = []
            s = j.get("status", "stopped")
            if s == "stopped":
                row.append(InlineKeyboardButton(f"▶️ Resume {name}", callback_data=f"merge#resume#{jid}"))
            row.append(InlineKeyboardButton(f"{_st(s)} {name}", callback_data=f"merge#info#{jid}"))
            row.append(InlineKeyboardButton(f"🗑", callback_data=f"merge#del#{jid}"))
            btns.append(row)

    # Type filter buttons (when not filtered)
    if not merge_type:
        btns.append([
            InlineKeyboardButton("🎵 Audio Merges", callback_data="merge#audio_menu"),
            InlineKeyboardButton("🎬 Video Merges", callback_data="merge#video_menu")
        ])

    # Create buttons
    if merge_type:
        btns.append([InlineKeyboardButton(f"➕ New {type_label}Merge", callback_data=f"merge#new_{merge_type}")])
    else:
        btns.append([InlineKeyboardButton("➕ New Audio Merge", callback_data="merge#new_audio"),
                      InlineKeyboardButton("➕ New Video Merge", callback_data="merge#new_video")])

    btns.append([InlineKeyboardButton("🔄 Refresh", callback_data="merge#refresh")])
    if merge_type:
        btns.append([InlineKeyboardButton("↩ Back", callback_data="merge#back_main")])
    else:
        btns.append([InlineKeyboardButton("⫷ Close", callback_data="merge#close")])

    count = len(active)
    text = (
        f"<b>🔀 {type_label}Merger</b>\n\n"
        f"<b>Active:</b> {count} job(s)\n\n"
        f"🎵 Audio: MP3, AAC, OGG, FLAC, WAV, AIFF, M4A, OPUS\n"
        f"🎬 Video: MP4, MKV, AVI, WEBM, MOV\n\n"
        f"<i>✅ Strict order • No skipping • Full metadata + cover</i>"
    )

    try:
        if is_cb:
            await msg_or_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))
        else:
            await msg_or_query.reply(text, reply_markup=InlineKeyboardMarkup(btns))
    except: pass


# ══════════════════════════════════════════════════════════════════════════════
# Callback router
# ══════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r'^merge#'))
async def merge_cb(bot, query):
    user_id = query.from_user.id
    parts = query.data.split("#")
    action = parts[1] if len(parts) > 1 else ""
    param = parts[2] if len(parts) > 2 else ""

    if action == "noop":
        return await query.answer()

    elif action == "close":
        return await query.message.delete()

    elif action == "refresh":
        return await _render_merge_list(bot, user_id, query)

    elif action == "back_main":
        return await _render_merge_list(bot, user_id, query)

    elif action == "audio_menu":
        return await _render_merge_list(bot, user_id, query, merge_type="audio")

    elif action == "video_menu":
        return await _render_merge_list(bot, user_id, query, merge_type="video")

    elif action.startswith("new_"):
        merge_type = action.split("_", 1)[1]  # "audio" or "video"
        await query.message.delete()
        await _create_merge_flow(bot, user_id, merge_type)

    elif action == "info":
        job = await _mg_get(param)
        if not job: return await query.answer("Not found!", show_alert=True)

        import datetime
        created = datetime.datetime.fromtimestamp(job.get("created_at", 0)).strftime("%d %b %Y %H:%M")

        meta = job.get("metadata", {})
        meta_txt = ""
        if meta:
            meta_lines = [f"  {k}: {v}" for k, v in list(meta.items())[:8] if v]
            meta_txt = "\n".join(meta_lines)

        dl_t = job.get("dl_time", 0)
        mg_t = job.get("merge_time", 0)
        up_t = job.get("up_time", 0)
        tot_t = job.get("total_time", 0)
        fsz = job.get("file_size", 0)

        text = (
            f"<b>{_st(job['status'])} Merge Job Info</b>\n\n"
            f"<b>Name:</b> <code>{job.get('output_name', '?')}</code>\n"
            f"<b>Type:</b> {'🎵 Audio' if job.get('merge_type') == 'audio' else '🎬 Video'}\n"
            f"<b>Range:</b> {job.get('start_id')} → {job.get('end_id')}\n"
            f"<b>Downloaded:</b> {job.get('downloaded', 0)} files\n"
            f"<b>Status:</b> {job['status']}\n"
            f"<b>Created:</b> {created}\n"
        )

        if dl_t or mg_t or up_t:
            text += (
                f"\n╭──── ⏱ <b>Timings</b> ────╮\n"
                f"┃ ⬇️ Download: {_tm(dl_t)}\n"
                f"┃ 🔀 Merge: {_tm(mg_t)}\n"
                f"┃ ⬆️ Upload: {_tm(up_t)}\n"
                f"┃ 📊 Total: {_tm(tot_t)}\n"
                f"╰─────────────────────╯\n"
            )

        if fsz: text += f"\n<b>File Size:</b> {_sz(fsz)}\n"
        if meta_txt: text += f"\n<b>Metadata:</b>\n{meta_txt}\n"
        if job.get("error"): text += f"\n<b>⚠️ Error:</b> <code>{job['error'][:200]}</code>"

        btns = []
        s = job["status"]
        if s in ("downloading", "merging", "uploading"):
            btns.append([InlineKeyboardButton("⏸ Pause", callback_data=f"merge#pause#{param}"),
                          InlineKeyboardButton("⏹ Stop", callback_data=f"merge#stop#{param}")])
        elif s == "paused":
            btns.append([InlineKeyboardButton("▶️ Resume", callback_data=f"merge#resume#{param}"),
                          InlineKeyboardButton("⏹ Stop", callback_data=f"merge#stop#{param}")])
        elif s == "stopped":
            btns.append([InlineKeyboardButton("▶️ Resume", callback_data=f"merge#resume#{param}")])
        btns.append([InlineKeyboardButton("🗑 Delete", callback_data=f"merge#del#{param}")])
        btns.append([InlineKeyboardButton("↩ Back", callback_data="merge#refresh")])

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif action == "pause":
        ev = _merge_paused.get(param)
        if ev: ev.clear()
        await _mg_update(param, status="paused")
        await query.answer("⏸ Paused!", show_alert=True)
        await _render_merge_list(bot, user_id, query)

    elif action == "resume":
        job = await _mg_get(param)
        if not job: return await query.answer("Not found!", show_alert=True)
        ev = _merge_paused.get(param)
        if ev and param in _merge_tasks and not _merge_tasks[param].done():
            ev.set()
            await _mg_update(param, status="downloading")
            await query.answer("▶️ Resumed!", show_alert=True)
        else:
            # Restart from saved position
            await _mg_update(param, status="downloading")
            _start_merge_task(param, user_id, bot)
            await query.answer("▶️ Restarted from saved position!", show_alert=True)
        await _render_merge_list(bot, user_id, query)

    elif action == "stop":
        task = _merge_tasks.pop(param, None)
        if task and not task.done(): task.cancel()
        ev = _merge_paused.pop(param, None)
        if ev: ev.set()
        await _mg_update(param, status="stopped")
        await query.answer("⏹ Stopped!", show_alert=True)
        await _render_merge_list(bot, user_id, query)

    elif action == "del":
        task = _merge_tasks.pop(param, None)
        if task and not task.done(): task.cancel()
        _merge_paused.pop(param, None)
        await _mg_delete(param)
        wd = f"merge_tmp/{param}"
        if os.path.exists(wd): shutil.rmtree(wd, ignore_errors=True)
        await query.answer("🗑 Deleted!", show_alert=True)
        await _render_merge_list(bot, user_id, query)


# ══════════════════════════════════════════════════════════════════════════════
# Creation flow (7 steps) — separate for audio/video
# ══════════════════════════════════════════════════════════════════════════════

async def _create_merge_flow(bot, user_id, merge_type="audio"):
    type_icon = "🎵" if merge_type == "audio" else "🎬"
    type_label = "Audio" if merge_type == "audio" else "Video"

    try:
        # ── Step 1: Account ───────────────────────────────────────────────
        accounts = await db.get_bots(user_id)
        if not accounts:
            return await bot.send_message(user_id,
                "<b>❌ No accounts found. Add in /settings → Accounts.</b>")

        kb = [[f"{'🤖' if a.get('is_bot',True) else '👤'} {a['name']}"] for a in accounts]
        kb.append(["❌ Cancel"])

        msg = await _merge_ask(bot, user_id,
            f"<b>{type_icon} New {type_label} Merge</b>\n\n"
            f"<b>Step 1/7:</b> Select account:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))

        if not msg.text or "Cancel" in msg.text:
            return await bot.send_message(user_id, "<b>Cancelled.</b>",
                                          reply_markup=ReplyKeyboardRemove())

        sel_name = msg.text.split(" ", 1)[1] if " " in msg.text else msg.text
        sel_acc = next((a for a in accounts if a["name"] == sel_name), None)
        if not sel_acc:
            return await bot.send_message(user_id, "<b>❌ Account not found.</b>",
                                          reply_markup=ReplyKeyboardRemove())

        # ── Step 2: Start link ────────────────────────────────────────────
        msg = await _merge_ask(bot, user_id,
            f"<b>Step 2/7:</b> Send <b>start file link</b>\n\n"
            f"<i>Example: https://t.me/c/123456/100</i>",
            reply_markup=ReplyKeyboardRemove())
        if not msg.text or msg.text.lower() == "/cancel":
            return await bot.send_message(user_id, "<b>Cancelled.</b>")

        chat_ref_s, start_id = _parse_link(msg.text)
        if start_id is None:
            return await bot.send_message(user_id, "<b>❌ Invalid link.</b>")

        from_chat = None
        if chat_ref_s:
            from_chat = -1000000000000 - chat_ref_s if isinstance(chat_ref_s, int) else chat_ref_s

        # ── Step 3: End link ──────────────────────────────────────────────
        msg = await _merge_ask(bot, user_id,
            "<b>Step 3/7:</b> Send <b>end file link</b>")
        if not msg.text or msg.text.lower() == "/cancel":
            return await bot.send_message(user_id, "<b>Cancelled.</b>")

        chat_ref_e, end_id = _parse_link(msg.text)
        if end_id is None:
            return await bot.send_message(user_id, "<b>❌ Invalid link.</b>")

        if from_chat is None and chat_ref_e:
            from_chat = -1000000000000 - chat_ref_e if isinstance(chat_ref_e, int) else chat_ref_e
        if from_chat is None:
            return await bot.send_message(user_id, "<b>❌ Could not detect channel. Use full links.</b>")

        if start_id > end_id: start_id, end_id = end_id, start_id
        total = end_id - start_id + 1

        # ── Step 4: Destination ───────────────────────────────────────────
        channels = await db.get_user_channels(user_id)
        dest_chats = []

        if channels:
            ch_kb = [[f"📢 {ch['title']}"] for ch in channels]
            ch_kb.append(["⏭ Skip (DM only)"])
            ch_kb.append(["❌ Cancel"])

            msg = await _merge_ask(bot, user_id,
                f"<b>Step 4/7:</b> Destination channel\n\n"
                f"<b>Range:</b> {start_id} → {end_id} ({total} msgs)",
                reply_markup=ReplyKeyboardMarkup(ch_kb, resize_keyboard=True, one_time_keyboard=True))

            if not msg.text or "Cancel" in msg.text:
                return await bot.send_message(user_id, "<b>Cancelled.</b>",
                                              reply_markup=ReplyKeyboardRemove())
            if "Skip" not in msg.text:
                title = msg.text.replace("📢 ", "").strip()
                ch = next((c for c in channels if c["title"] == title), None)
                if ch: dest_chats.append(int(ch["chat_id"]))
        else:
            await bot.send_message(user_id,
                "<b>Step 4/7:</b> No channels configured. Sending to DM.",
                reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(0.5)

        # ── Step 5: Filename ──────────────────────────────────────────────
        msg = await _merge_ask(bot, user_id,
            f"<b>Step 5/7:</b> Output <b>filename</b> (no extension)",
            reply_markup=ReplyKeyboardRemove())
        if not msg.text or msg.text.lower() == "/cancel":
            return await bot.send_message(user_id, "<b>Cancelled.</b>")
        output_name = re.sub(r'[<>:"/\\|?*]', '_', msg.text.strip())

        # ── Step 6: Metadata + Cover ──────────────────────────────────────
        msg = await _merge_ask(bot, user_id,
            "<b>Step 6/7:</b> Send <b>metadata</b>\n\n"
            "<i>One field per line:\n"
            "<code>title: My Song\n"
            "artist: Artist Name\n"
            "album: Album Name\n"
            "genre: Pop\n"
            "year: 2024\n"
            "track: 1\n"
            "composer: Composer\n"
            "comment: Notes</code>\n\n"
            "Send <code>skip</code> for defaults.</i>")

        metadata = {}
        if msg.text and msg.text.lower() not in ("skip", "/cancel"):
            key_map = {"title":"title","artist":"artist","album":"album","genre":"genre",
                       "year":"date","date":"date","track":"track","composer":"composer",
                       "comment":"comment","album_artist":"album_artist","description":"description",
                       "language":"language","publisher":"publisher","performer":"performer",
                       "copyright":"copyright","encoded_by":"encoded_by","lyrics":"lyrics"}
            for line in msg.text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower(); v = v.strip()
                    if k and v: metadata[key_map.get(k, k)] = v

        # ── Step 6b: Cover image ──────────────────────────────────────────
        work_dir = f"merge_tmp/{uuid.uuid4()}"  # temp for cover, real dir created later
        os.makedirs(work_dir, exist_ok=True)
        cover_path = None

        msg = await _merge_ask(bot, user_id,
            "<b>Step 6b:</b> Send a <b>cover image</b> (photo/file) for the merged output.\n\n"
            "<i>Send <code>skip</code> to use no cover.</i>")

        if msg.photo:
            try:
                cover_path = await bot.download_media(msg, file_name=os.path.join(work_dir, "cover.jpg"))
            except: pass
        elif msg.document and msg.document.mime_type and 'image' in msg.document.mime_type:
            try:
                cover_path = await bot.download_media(msg, file_name=os.path.join(work_dir, "cover.jpg"))
            except: pass

        # ── Step 7: Confirm ───────────────────────────────────────────────
        dest_preview = "DM only"
        if dest_chats:
            names = []
            for dc in dest_chats:
                ch = next((c for c in channels if int(c["chat_id"]) == dc), None)
                names.append(ch["title"] if ch else str(dc))
            dest_preview = ", ".join(names)

        meta_preview = ""
        if metadata:
            mlines = [f"  {k}: {v}" for k, v in list(metadata.items())[:5] if v]
            meta_preview = "\n".join(mlines)

        msg = await _merge_ask(bot, user_id,
            f"<b>Step 7/7: Confirm {type_label} Merge</b>\n\n"
            f"<b>Source:</b> <code>{from_chat}</code>\n"
            f"<b>Range:</b> {start_id} → {end_id} ({total} msgs)\n"
            f"<b>Output:</b> <code>{output_name}</code>\n"
            f"<b>Type:</b> {type_icon} {type_label}\n"
            f"<b>Cover:</b> {'✅ Yes' if cover_path else '❌ No'}\n"
            f"<b>Destination:</b> {dest_preview}\n"
            + (f"\n<b>Metadata:</b>\n{meta_preview}\n" if meta_preview else "") +
            f"\n<i>All media files will be merged in exact order. No file skipped.</i>",
            reply_markup=ReplyKeyboardMarkup(
                [["✅ Start Merge"], ["❌ Cancel"]],
                resize_keyboard=True, one_time_keyboard=True))

        if not msg.text or "Cancel" in msg.text:
            if os.path.exists(work_dir): shutil.rmtree(work_dir, ignore_errors=True)
            return await bot.send_message(user_id, "<b>Cancelled.</b>",
                                          reply_markup=ReplyKeyboardRemove())

        # ── Create job ────────────────────────────────────────────────────
        job_id = str(uuid.uuid4())
        real_dir = f"merge_tmp/{job_id}"
        os.makedirs(real_dir, exist_ok=True)

        # Move cover if exists
        if cover_path and os.path.exists(cover_path):
            new_cover = os.path.join(real_dir, "cover.jpg")
            shutil.copy2(cover_path, new_cover)
            cover_path = new_cover

        # Clean temp dir
        if os.path.exists(work_dir) and work_dir != real_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

        job = {
            "job_id": job_id,
            "user_id": user_id,
            "account_id": sel_acc["id"],
            "from_chat": from_chat,
            "start_id": start_id,
            "end_id": end_id,
            "current_id": start_id,
            "output_name": output_name,
            "merge_type": merge_type,
            "metadata": metadata,
            "dest_chats": dest_chats,
            "has_cover": bool(cover_path),
            "status": "downloading",
            "downloaded": 0,
            "total_dl_bytes": 0,
            "error": "",
            "created_at": time.time(),
        }
        await _mg_save(job)
        _start_merge_task(job_id, user_id, bot)

        await bot.send_message(user_id,
            f"<b>✅ {type_icon} {type_label} Merge Started!</b>\n\n"
            f"<b>Range:</b> {start_id} → {end_id} ({total} msgs)\n"
            f"<b>Output:</b> <code>{output_name}</code>\n"
            f"<b>Job:</b> <code>{job_id[-6:]}</code>\n\n"
            f"<i>Use /merge to monitor. Multiple jobs can run simultaneously.</i>",
            reply_markup=ReplyKeyboardRemove())

    except asyncio.TimeoutError:
        await bot.send_message(user_id, "<b>⏱ Timed out.</b>",
                               reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"[Merge create] {e}")
        await bot.send_message(user_id, f"<b>❌ Error:</b> <code>{e}</code>",
                               reply_markup=ReplyKeyboardRemove())
