"""
Marketplace Seller Bot
======================
Handles the customer UI for buying stories, T&C, and progressive delivery.
"""
import logging
import asyncio
import base64
import io
import re
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import MessageNotModified
from database import db
from config import Config
from utils import native_ask, _deliver_purchased_story
from plugins.userbot.razorpay_helpers import _create_rzp_link, _check_rzp_status
from plugins.userbot.easebuzz_helpers import _create_easebuzz_link, _check_easebuzz_status

logger = logging.getLogger(__name__)
market_clients: dict = {}


def _clean_upi_note(s: str) -> str:
    # Keep it short + app-compatible.
    s = (s or "").strip()
    s = re.sub(r"[^a-zA-Z0-9 _:/#-]+", "", s)
    return s[:40]


def _build_upi_uri(*, upi_id: str, payee_name: str, amount: int, note: str) -> str:
    """
    Build a conservative UPI URI to maximize compatibility across apps.

    - Always include: pa, am, cu
    - Include pn only when explicitly configured (avoid branding mismatch like "Arya YT")
    - Keep tn generic and short to reduce fraud/risk heuristics
    """
    import urllib.parse
    pa = urllib.parse.quote((upi_id or "").strip())
    am = str(amount)
    q = [f"pa={pa}", f"am={am}", "cu=INR"]

    pn_clean = (payee_name or "").strip()
    if pn_clean:
        q.append(f"pn={urllib.parse.quote(pn_clean)}")

    tn_clean = _clean_upi_note(note)
    if tn_clean:
        q.append(f"tn={urllib.parse.quote(tn_clean)}")

    return "upi://pay?" + "&".join(q)


# Telegram URL buttons only allow http/https; pasted URLs often include invisible Unicode (ZWSP, BOM) → BUTTON_URL_INVALID.
_INVISIBLE_URL_JUNK = re.compile(r"[\u200b-\u200f\u2060\ufeff\ufe0f\u200d\u200c\u00a0]+")


def sanitize_https_redirect_base(url: str) -> str:
    if not url:
        return ""
    s = _INVISIBLE_URL_JUNK.sub("", str(url)).strip()
    s = s.rstrip("/").strip()
    if not (s.lower().startswith("http://") or s.lower().startswith("https://")):
        return ""
    # Block accidental query strings on base (we append /r/...)
    if "?" in s:
        s = s.split("?", 1)[0].rstrip("/")
    return s


def build_open_upi_app_https_url(base: str, upi_uri: str) -> str:
    """
    Short HTTPS URL for Telegram buttons: https://host/r/<base64url(upi_uri)>
    Avoids huge ?uri=... links and invisible-char breakage.
    """
    base = sanitize_https_redirect_base(base)
    if not base or not upi_uri:
        return ""
    tok = base64.urlsafe_b64encode(upi_uri.encode("utf-8")).decode("ascii").rstrip("=")
    href = f"{base}/r/{tok}"
    # Telegram inline button URL limit ~2048 bytes
    if len(href) > 2040:
        return ""
    return href


def _can_sliceurl_shorten(url: str) -> bool:
    if not url:
        return False
    u = url.strip()
    if u.startswith("http://") or u.startswith("https://"):
        return True
    return u.lower().startswith("upi://pay?") and "pa=" in u and "am=" in u


async def _sliceurl_api_shorten(url: str) -> str:
    """
    SliceURL api-public ?action=shorten — supports https://… and (after your deploy) upi://pay?…

    Env: SLICEURL_API_URL, SLICEURL_API_KEY (slc_…)
    """
    if not _can_sliceurl_shorten(url):
        return ""

    api_base = (getattr(Config, "SLICEURL_API_URL", None) or "").strip()
    key = (getattr(Config, "SLICEURL_API_KEY", None) or "").strip()

    if api_base and key.startswith("slc_"):
        try:
            import aiohttp
            post_url = f"{api_base.rstrip('/')}?action=shorten"
            headers = {
                "X-API-Key": key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    post_url,
                    json={"long_url": url},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    status = resp.status
                    try:
                        data = await resp.json()
                    except Exception:
                        data = {}
            if status in (200, 201) and isinstance(data, dict) and data.get("success"):
                short = data.get("short_url")
                if isinstance(short, str) and short.startswith("http"):
                    return short
            logger.warning(f"SliceURL shorten rejected: status={status} body={data}")
        except Exception as e:
            logger.warning(f"SliceURL shorten failed: {e}")
        return ""

    # Strict mode: do not use legacy/generic shorteners.
    return ""


def _make_qr_png_bytes(data: str, *, logo_png_bytes: bytes | None = None) -> bytes:
    try:
        import qrcode
        from PIL import Image
    except Exception as e:
        # The runtime may not have optional deps installed; caller should fallback gracefully.
        raise RuntimeError("QR deps missing") from e

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if logo_png_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_png_bytes)).convert("RGBA")
            max_w = int(img.size[0] * 0.22)
            max_h = int(img.size[1] * 0.22)
            logo.thumbnail((max_w, max_h))

            pad = max(6, int(img.size[0] * 0.012))
            bg_w, bg_h = logo.size[0] + pad * 2, logo.size[1] + pad * 2
            bg = Image.new("RGBA", (bg_w, bg_h), (255, 255, 255, 255))
            pos = ((img.size[0] - bg_w) // 2, (img.size[1] - bg_h) // 2)
            img.alpha_composite(bg, pos)
            img.alpha_composite(logo, (pos[0] + pad, pos[1] + pad))
        except Exception:
            pass

    out = io.BytesIO()
    out.name = "upi_qr.png"
    img.save(out, format="PNG", optimize=True)
    return out.getvalue()

def _sc(text: str) -> str:
    return text.translate(str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    ))

def _get_base_header(user) -> str:
    u_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
    return f"<blockquote expandable><b>{_sc('HELLO')} {_sc(u_name)}</b></blockquote>\n\n"

# Language Texts
T = {
    "en": {
        "welcome": "Welcome to",
        "store": "Store",
        "intro": "Browse our premium collection. Tap Marketplace to explore stories by platform.",
        "tc_accept": "✅ I Accept the Terms",
        "tc_reject": "❌ I Reject",
        "no_stories": "No stories currently available.",
        "pay_upi": "Pay via UPI",
        "back": "« Back",
        "qr_msg": "<b>💳 Complete Payment</b>\n\n• Scan the QR code above.\n• Amount: ₹{price}\n\n<b>After paying, send the successful payment screenshot here.</b>",
        "wait_ver": "⏳ Your payment is being verified, please wait (approx 5 minutes)...",
        "notify": "🔔 Notify Admin"
    },
    "hi": {
        "welcome": "स्वागत है",
        "store": "स्टोर",
        "intro": "प्रीमियम कलेक्शन ब्राउज़ करें। Marketplace पर टैप करें।",
        "tc_accept": "✅ मुझे शर्तें मंजूर हैं",
        "tc_reject": "❌ मैं अस्वीकार करता हूँ",
        "no_stories": "वर्तमान में कोई स्टोरी उपलब्ध नहीं है।",
        "pay_upi": "UPI से पेमेंट करें",
        "back": "« वापस",
        "qr_msg": "<b>💳 पेमेंट पूरा करें</b>\n\n• ऊपर QR स्कैन करें।\n• राशि: ₹{price}\n\n<b>पेमेंट के बाद स्क्रीनशॉट यहाँ भेजें।</b>",
        "wait_ver": "⏳ आपके भुगतान का सत्यापन हो रहा है...",
        "notify": "🔔 एडमिन को सूचित करें"
    }
}

def _get_main_menu(lang='en'):
    kb = [
        [InlineKeyboardButton(f"• {_sc('MARKETPLACE')} •", callback_data="mb#main_marketplace"),
         InlineKeyboardButton(f"• {_sc('PROFILE')} •", callback_data="mb#main_profile")],
        [InlineKeyboardButton(f"⚙️ {_sc('SETTINGS')}", callback_data="mb#main_settings"),
         InlineKeyboardButton(f"ℹ️ {_sc('HELP')}", callback_data="mb#main_help")],
        [InlineKeyboardButton(f"✖️ {_sc('CLOSE')}", callback_data="mb#main_close")]
    ]
    return InlineKeyboardMarkup(kb)


def _get_premium_menu_markup(bt_cfg: dict, lang: str):
    """
    Adds optional URL buttons (Updates/Support) like your reference UI.
    Stored in premium_bots.config as `updates_url` / `support_url`.
    """
    rows = []
    updates_url = (bt_cfg.get("updates_url") or "").strip()
    support_url = (bt_cfg.get("support_url") or "").strip()
    if updates_url or support_url:
        r = []
        if updates_url:
            r.append(InlineKeyboardButton(_sc("UPDATES"), url=updates_url))
        if support_url:
            r.append(InlineKeyboardButton(_sc("SUPPORT"), url=support_url))
        if r:
            rows.append(r)
    base = _get_main_menu(lang).inline_keyboard
    # Insert URL row above Close
    if rows:
        base = base[:2] + rows + base[2:]
    return InlineKeyboardMarkup(base)


def _menu_card_text(user, bt_cfg: dict, bot_name: str) -> str:
    welcome = (bt_cfg.get("welcome") or "").strip()
    about = (bt_cfg.get("about") or "").strip()
    quote = (bt_cfg.get("quote") or "").strip()
    author = (bt_cfg.get("quote_author") or "").strip()

    u_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "User"
    welcome_txt = welcome.strip()
    about_txt = about if about else _sc("BROWSE OUR PREMIUM COLLECTION. TAP MARKETPLACE TO EXPLORE STORIES BY PLATFORM.")
    quote_txt = quote if quote else _sc("Quality stories. Fast delivery. Trusted support.")
    author_txt = author if author else _sc("Arya Premium")

    blocks = [f"<blockquote><b>{_sc('HELLO')} {u_name}</b></blockquote>"]
    if welcome_txt:
        blocks.append(f"<blockquote>{welcome_txt}</blockquote>")
    if about_txt:
        blocks.append(f"<blockquote>{about_txt}</blockquote>")
    blocks.append("")
    blocks.append(f"<blockquote>❝ {quote_txt} ❞</blockquote>")
    blocks.append(f"<blockquote>— {author_txt}</blockquote>")
    return "\n".join(blocks) + "\n"


async def _edit_main_menu_in_place(client, query, user, lang: str):
    """
    Edit current message back to main menu when possible.
    Falls back to sending a fresh menu only if Telegram refuses edit.
    """
    bt = await db.db.premium_bots.find_one({"id": client.me.id})
    bt_cfg = bt.get("config", {}) if bt else {}
    bot_name = client.me.first_name
    msg_txt = _menu_card_text(user, bt_cfg, bot_name)
    markup = _get_premium_menu_markup(bt_cfg, lang)
    res = await _safe_edit(query.message, text=msg_txt, markup=markup)
    if not res:
        await _send_main_menu(client, query.from_user.id, user, lang)


async def _safe_edit(msg, *, text: str, markup: InlineKeyboardMarkup):
    is_media = bool(getattr(msg, 'photo', None) or getattr(msg, 'video', None) or getattr(msg, 'animation', None) or getattr(msg, 'document', None))
    try:
        if is_media:
            return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        return await msg.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except MessageNotModified:
        return None
    except Exception as e:
        logger.warning(f"Safe edit failed: {e}")
        return None


async def _send_main_menu(client, user_id: int, user, lang: str):
    bt = await db.db.premium_bots.find_one({"id": client.me.id})
    bt_cfg = bt.get("config", {}) if bt else {}
    bot_name = client.me.first_name
    msg_txt = _menu_card_text(user, bt_cfg, bot_name)
    markup = _get_premium_menu_markup(bt_cfg, lang)

    # Menu media rotation: supports Photo / GIF / Video.
    items = [x for x in _cfg_list(bt_cfg, "menu_media") if isinstance(x, dict) and x.get("file_id")]
    if not items and (bt_cfg.get("menuimg") or "").strip():
        # Backward compatible
        items = [{"type": "photo", "file_id": (bt_cfg.get("menuimg") or "").strip()}]

    if items:
        import random
        random.shuffle(items)
        for it in items[:10]:
            t = (it.get("type") or "photo").strip()
            fid = (it.get("file_id") or "").strip()
            if not fid:
                continue
            try:
                if t == "animation":
                    return await client.send_animation(
                        user_id,
                        animation=fid,
                        caption=msg_txt,
                        reply_markup=markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                if t == "video":
                    return await client.send_video(
                        user_id,
                        video=fid,
                        caption=msg_txt,
                        reply_markup=markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                return await client.send_photo(
                    user_id,
                    photo=fid,
                    caption=msg_txt,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                # Auto-heal: remove broken media entries (MEDIA_EMPTY / expired file_id)
                logger.warning(f"Menu media send failed; pruning. type={t} err={e}")
                try:
                    await db.db.premium_bots.update_one(
                        {"id": client.me.id},
                        {"$pull": {"config.menu_media": {"file_id": fid}}}
                    )
                except Exception:
                    pass
    return await client.send_message(user_id, msg_txt, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


def _fmt_delivery_text(tpl: str, user, story, sent_count: int = 0, fail_count: int = 0) -> str:
    safe_tpl = tpl or ""
    return (
        safe_tpl
        .replace("{user_id}", str(user.id if user else ""))
        .replace("{user_name}", (user.first_name or "User") if user else "User")
        .replace("{story}", str(story.get("story_name_en", "Story")))
        .replace("{price}", str(story.get("price", 0)))
        .replace("{sent}", str(sent_count))
        .replace("{failed}", str(fail_count))
    )


async def _delete_later(client, user_id: int, msg_ids: list, wait_seconds: int):
    await asyncio.sleep(wait_seconds)
    for mid in msg_ids:
        try:
            await client.delete_messages(user_id, mid)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────
# Story Detail Preview (shown before T&C on deep links)
# ─────────────────────────────────────────────────────────────────
async def _show_story_preview(client, user_id, story, lang):
    """Show story name, image, description and episode count. User clicks Continue -> T&C."""
    name = story.get(f'story_name_{lang}', story.get('story_name_en', 'Unknown'))
    ep_count = abs(story.get('end_id', 0) - story.get('start_id', 0)) + 1 if story.get('end_id') else "?"
    platform = story.get('platform', 'Other')
    price = story.get('price', 0)
    desc = story.get('description', 'Premium audio story — exclusive content.')
    s_id = str(story['_id'])

    txt = (
        f"<b>📖 {_sc(name)}</b>\n\n"
        f"<b>{_sc('Platform')}:</b> {platform}\n"
        f"<b>{_sc('Episodes')}:</b> ~{ep_count}\n"
        f"<b>{_sc('Price')}:</b> ₹{price}\n\n"
        f"<blockquote expandable>{_sc(desc)}</blockquote>"
    )
    kb = [[InlineKeyboardButton(f"▶️ {_sc('Continue to Purchase')}", callback_data=f"mb#story_preview_continue_{s_id}")]]

    img = story.get('image_url')
    if img:
        try:
            await client.send_photo(
                user_id,
                photo=img,
                caption=txt,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=enums.ParseMode.HTML
            )
            return
        except Exception:
            pass
    await client.send_message(user_id, txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)


# ─────────────────────────────────────────────────────────────────
# T&C (with Accept and Reject buttons - all inline, no native_ask)
# ─────────────────────────────────────────────────────────────────
def to_mathbold(text: str) -> str:
    return text.translate(str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗"
    ))

def to_mathitalic(text: str) -> str:
    return text.translate(str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"
    ))

async def _show_story_profile(client, user_id, story, lang):
    name = story.get(f'story_name_{lang}', story.get('story_name_en', 'Unknown'))
    status = story.get('status', 'Unknown')
    platform = story.get('platform', 'Unknown')
    genre = story.get('genre', 'Unknown')
    episodes = story.get('episodes', 'Unknown')
    image = story.get('image')
    price = story.get('price', 0)

    # Description intentionally hidden for now.
    header_txt = (
        f"<b>♨️Story :</b> {to_mathbold(name)}\n"
        f"<b>🔰Status :</b> <b>{status}</b>\n"
        f"<b>🖥Platform :</b> <b>{platform}</b>\n"
        f"<b>🧩Genre :</b> <b>{genre}</b>\n"
        f"<b>🎬Episodes :</b> <b>{episodes}</b>\n"
    )
    txt = header_txt
        
    kb = [
        [InlineKeyboardButton(f"✅ {_sc('CONFIRM')}", callback_data=f"mb#show_tc#{str(story['_id'])}")],
        [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#return_main")]
    ]
    markup = InlineKeyboardMarkup(kb)
    
    from pyrogram import enums

    # Need to send a message but remove the reply keyboard first (from marketplace)
    tmp = await client.send_message(user_id, "<i>⏳ Loading Profile...</i>", reply_markup=ReplyKeyboardRemove())
    try:
        await tmp.delete()
    except:
        pass

    if image:
        try:
            await client.send_photo(
                user_id,
                photo=image,
                caption=txt,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML,
            )
            return
        except Exception:
            pass
    await client.send_message(
        user_id,
        txt,
        reply_markup=markup,
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML
    )

async def _show_tc(client, user_id, story_id, lang='en'):
    if lang == 'en':
        tc_text = (
            f"<b>\u26a0\ufe0f {_sc('TERMS & CONDITIONS')}</b>\n\n"
            "<blockquote expandable>"
            + _sc("Before purchasing, you must carefully read and agree to the following:") + "\n\n"
            "\ud83d\udccc " + _sc("MISSING EPISODES") + "\n"
            + _sc("3\u20135 episodes may be unavailable as they were not publicly released. If they become available later, they will be added automatically. If more than 5 are missing, contact support \u2014 we will do our best.") + "\n\n"
            "\ud83d\udccc " + _sc("QUALITY") + "\n"
            + _sc("Some older recorded episodes may have reduced audio/video quality. We cannot guarantee 100% quality, but we always try to deliver the best version available.") + "\n\n"
            "\ud83d\udccc " + _sc("EPISODE ORDER") + "\n"
            + _sc("Episodes may rarely arrive out of sequence. We are not directly responsible, but this almost never happens. All files come with Arya Bot branding and cleaned metadata.") + "\n\n"
            "\ud83d\udccc " + _sc("NO REFUNDS") + "\n"
            + _sc("Strictly no refunds once payment is confirmed and delivery has started.") + "\n\n"
            "\ud83d\udccc " + _sc("FAKE SCREENSHOTS") + "\n"
            + _sc("Sending test, fake, wrong, or random payment screenshots will result in a permanent ban from all our groups and channels. No warnings will be given.")
            + "</blockquote>"
        )
    else:
        tc_text = (
            "<b>\u26a0\ufe0f \u0928\u093f\u092f\u092e \u0914\u0930 \u0936\u0930\u094d\u0924\u0947\u0902</b>\n\n"
            "<blockquote expandable>"
            "\u0916\u0930\u0940\u0926\u0928\u0947 \u0938\u0947 \u092a\u0939\u0932\u0947 \u0907\u0928 \u0928\u093f\u092f\u092e\u094b\u0902 \u0915\u094b \u0927\u094d\u092f\u093e\u0928 \u0938\u0947 \u092a\u0922\u093c\u0947\u0902:\n\n"
            "\ud83d\udccc \u0917\u093e\u092f\u092c \u090f\u092a\u093f\u0938\u094b\u0921\n"
            "3-5 \u090f\u092a\u093f\u0938\u094b\u0921 \u0909\u092a\u0932\u092c\u094d\u0927 \u0928\u0939\u0940\u0902 \u0939\u094b \u0938\u0915\u0924\u0947\u0964 \u092c\u093e\u0926 \u092e\u0947\u0902 \u092e\u093f\u0932\u0928\u0947 \u092a\u0930 \u091c\u094b\u0921\u093c\u0947 \u091c\u093e\u090f\u0902\u0917\u0947\u0964 \u091c\u094d\u092f\u093e\u0926\u093e \u0939\u094b\u0928\u0947 \u092a\u0930 \u0938\u092a\u094b\u0930\u094d\u091f \u0938\u0947 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0902\u0964\n\n"
            "\ud83d\udccc \u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e\n"
            "\u092a\u0941\u0930\u093e\u0928\u0947 \u090f\u092a\u093f\u0938\u094b\u0921 \u0915\u0940 \u0915\u094d\u0935\u093e\u0932\u093f\u091f\u0940 \u0915\u092e \u0939\u094b \u0938\u0915\u0924\u0940 \u0939\u0948\u0964 \u0939\u092e \u092c\u0947\u0939\u0924\u0930\u0940\u0928 \u0909\u092a\u0932\u092c\u094d\u0927 \u0938\u0902\u0938\u094d\u0915\u0930\u0923 \u0926\u0947\u0928\u0947 \u0915\u0940 \u0915\u094b\u0936\u093f\u0936 \u0915\u0930\u0924\u0947 \u0939\u0948\u0902\u0964\n\n"
            "\ud83d\udccc \u090f\u092a\u093f\u0938\u094b\u0921 \u0915\u093e \u0915\u094d\u0930\u092e\n"
            "\u0915\u092d\u0940-\u0915\u092d\u0940 \u0915\u094d\u0930\u092e \u092e\u0947\u0902 \u0905\u0902\u0924\u0930 \u0939\u094b \u0938\u0915\u0924\u093e \u0939\u0948, \u0932\u0947\u0915\u093f\u0928 \u092f\u0939 \u0906\u092e\u0924\u094c\u0930 \u092a\u0930 \u0928\u0939\u0940\u0902 \u0939\u094b\u0924\u093e\u0964 \u092b\u093c\u093e\u0907\u0932\u0947\u0902 Arya Bot \u092c\u094d\u0930\u093e\u0902\u0921\u093f\u0902\u0917 \u0915\u0947 \u0938\u093e\u0925 \u0906\u0924\u0940 \u0939\u0948\u0902\u0964\n\n"
            "\ud83d\udccc \u0915\u094b\u0908 \u0930\u093f\u092b\u0902\u0921 \u0928\u0939\u0940\u0902\n"
            "\u0921\u093f\u0932\u0940\u0935\u0930\u0940 \u0936\u0941\u0930\u0942 \u0939\u094b\u0928\u0947 \u0915\u0947 \u092c\u093e\u0926 <b>\u0915\u094b\u0908 \u0930\u093f\u092b\u0902\u0921 \u0928\u0939\u0940\u0902</b> \u0926\u093f\u092f\u093e \u091c\u093e\u090f\u0917\u093e\u0964\n\n"
            "\ud83d\udccc \u092b\u0930\u094d\u091c\u0940 \u0938\u094d\u0915\u094d\u0930\u0940\u0928\u0936\u0949\u091f\n"
            "\u092b\u0930\u094d\u091c\u0940 \u092f\u093e \u0917\u0932\u0924 \u0938\u094d\u0915\u094d\u0930\u0940\u0928\u0936\u0949\u091f \u092d\u0947\u091c\u0928\u0947 \u092a\u0930 \u0938\u092d\u0940 \u0917\u094d\u0930\u0941\u092a \u0938\u0947 <b>\u0938\u094d\u0925\u093e\u092f\u0940 \u092c\u0948\u0928</b> \u0939\u094b\u0917\u093e\u0964"
            "</blockquote>"
        )
    kb = [
        [InlineKeyboardButton(f"\u2705 {_sc('I ACCEPT THE TERMS')}", callback_data=f"mb#tc_accept_{story_id}"),
         InlineKeyboardButton(f"\u274c {_sc('REJECT')}", callback_data=f"mb#tc_reject")]
    ]
    from pyrogram import enums
    await client.send_message(user_id, tc_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=enums.ParseMode.HTML)

def _cfg_list(cfg: dict, key: str):
    v = (cfg or {}).get(key)
    return v if isinstance(v, list) else []


# ─────────────────────────────────────────────────────────────────
# Story Payment Detail
# ─────────────────────────────────────────────────────────────────
async def _show_story_details(client, msg_or_query, story, lang):
    from pyrogram.types import Message
    is_msg = isinstance(msg_or_query, Message)

    name = story.get(f'story_name_{lang}', story.get('story_name_en'))
    ep_count = abs(story.get('end_id', 0) - story.get('start_id', 0)) + 1 if story.get('end_id') else "?"

    txt = (
        f"<b>♨️ {to_mathbold(name)}</b>\n"
        f"<blockquote>"
        f"<b>🖥 {_sc('Platform')} :</b> <b>{story.get('platform', 'Other')}</b>\n"
        f"<b>🎬 {_sc('Episodes')} :</b> <b>~{ep_count}</b>\n"
        f"<b>💲 {_sc('Price')}    :</b> <b>₹{story.get('price', 0)}</b>"
        f"</blockquote>\n"
        f"<i>{_sc('Select a payment method below:')}</i>"
    )

    kb = [
        [InlineKeyboardButton(f"💳 {_sc('Razorpay')} [{_sc('Recommended')}]", callback_data=f"mb#pay#razorpay#{str(story['_id'])}"),
         InlineKeyboardButton(f"💳 {_sc('Easebuzz')}", callback_data=f"mb#pay#easebuzz#{str(story['_id'])}")],
        [InlineKeyboardButton(f"🏦 {_sc('UPI')} [{_sc('Manual')}]", callback_data=f"mb#pay#upi#{str(story['_id'])}"),
         InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#return_main")]
    ]
    if is_msg:
        await msg_or_query.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await msg_or_query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb))


# ─────────────────────────────────────────────────────────────────
# /start Handler
# ─────────────────────────────────────────────────────────────────
async def _process_start(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    args = message.command

    if 'lang' not in user:
        kb = [[InlineKeyboardButton("English", callback_data="mb#lang#en"),
               InlineKeyboardButton("हिंदी", callback_data="mb#lang#hi")]]
        return await message.reply_text("Please select your language / कृपया अपनी भाषा चुनें:", reply_markup=InlineKeyboardMarkup(kb))

    lang = user.get('lang', 'en')

    # ── Deep Link Handler: show story preview first ──
    if len(args) > 1 and args[1].startswith("buy_"):
        story_id = args[1].replace("buy_", "")
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(story_id)})
        if story:
            has_paid = await db.has_purchase(user_id, story_id)
            if has_paid:
                await message.reply_text("✅ You already own this story. Sending delivery options...")
                return await dispatch_delivery_choice(client, user_id, story)
            return await _show_story_profile(client, user_id, story, lang)

    # Standard Main Menu
    msg_txt = None
        
    wait_msg = await client.send_message(user_id, "<b>› › " + _sc("WAIT A SECOND...") + "</b>")
    await asyncio.sleep(0.5)
    await wait_msg.delete()

    # Always use the centralized menu sender (handles MEDIA_EMPTY and optional URL buttons)
    await _send_main_menu(client, user_id, message.from_user, lang)


# ─────────────────────────────────────────────────────────────────
# Text Handler (only for Reply Keyboard marketplace flow)
# ─────────────────────────────────────────────────────────────────
async def _process_text(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    txt = message.text.strip()

    # Back to main menu
    if txt == "↩️ " + _sc("BACK TO MAIN MENU"):
        m = await message.reply_text("<i>⏳ Loading...</i>", reply_markup=ReplyKeyboardRemove())
        try:
            await m.delete()
        except:
            pass
        await _send_main_menu(client, user_id, message.from_user, lang)
        return

    # Check if it's a story selection e.g. "1. STORY NAME [ ₹ 49 ]"
    if " [ ₹ " in txt and txt.endswith(" ]"):
        parts = txt.split(". ", 1)
        raw = parts[1] if len(parts) > 1 else txt
        sName = raw.split(" [ ₹ ")[0].strip()
        stories = await db.db.premium_stories.find({"bot_id": client.me.id}).to_list(length=None)
        story = None
        for st in stories:
            candidates = [
                st.get("story_name_en", ""),
                st.get("story_name_hi", ""),
                _sc(st.get("story_name_en", "")),
                _sc(st.get("story_name_hi", "")),
            ]
            if sName in candidates:
                story = st
                break
        if not story:
            return await message.reply_text("<i>Story not found or removed.</i>")

        has_paid = await db.has_purchase(user_id, str(story['_id']))
        if has_paid:
            await message.reply_text("✅ You already own this story. Sending delivery options...", reply_markup=ReplyKeyboardRemove())
            return await dispatch_delivery_choice(client, user_id, story)

        return await _show_story_profile(client, user_id, story, lang)

    # Platform selection
    platforms = await db.db.premium_stories.distinct('platform', {"bot_id": client.me.id})
    platforms.append("Other")

    if txt in platforms:
        query_find = {"bot_id": client.me.id}
        if txt != "Other": query_find["platform"] = txt
        stories = await db.db.premium_stories.find(query_find).to_list(length=None)
        if not stories:
            return await message.reply_text("<i>No stories found for this platform.</i>")

        kb = []
        for idx, s in enumerate(stories, start=1):
            s_name = s.get(f'story_name_{lang}', s.get('story_name_en'))
            kb.append([f"{idx}. {_sc(s_name)} [ ₹ {s.get('price', 0)} ]"])
        kb.append(["🔍 " + _sc("SEARCH")])
        kb.append(["↩️ " + _sc("BACK TO MAIN MENU")])

        await message.reply_text(
            f"<b>{_sc('Available Stories')} — {txt}</b>\n\n{_sc('Tap on a story from the menu below:')}",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # ── SEARCH trigger ──
    if txt == "🔍 " + _sc("SEARCH"):
        await message.reply_text(
            f"<b>🔍 {_sc('SEARCH')}</b>\n\n<i>{_sc('Type a few words of the story name to search:')}</i>",
            reply_markup=ReplyKeyboardMarkup([["↩️ " + _sc("CANCEL")]], resize_keyboard=True)
        )
        await db.update_user(user_id, {"state": "searching"})
        return

    # ── CANCEL search ──
    if txt == "↩️ " + _sc("CANCEL") or (user.get("state") == "searching" and txt.startswith("↩️")):
        await db.update_user(user_id, {"state": None})
        m = await message.reply_text("<i>❌ Process Cancelled Successfully!</i>", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(1.5)
        try: await m.delete()
        except: pass
        await _send_main_menu(client, user_id, message.from_user, lang)
        return

    # ── SEARCH query matching ──
    if user.get("state") == "searching":
        q = txt.lower().strip()
        if not q or len(q) < 2:
            return await message.reply_text("<i>Please type at least 2 characters to search.</i>")
        all_stories = await db.db.premium_stories.find({"bot_id": client.me.id}).to_list(length=None)
        matches = [s for s in all_stories if q in s.get("story_name_en", "").lower() or q in s.get("story_name_hi", "").lower()]
        if not matches:
            return await message.reply_text(f"<i>No stories matched '<b>{txt}</b>'. Try different keywords.</i>")
        kb = []
        for idx, s in enumerate(matches, start=1):
            s_name = s.get(f'story_name_{lang}', s.get('story_name_en'))
            kb.append([f"{idx}. {_sc(s_name)} [ ₹ {s.get('price', 0)} ]"])
        kb.append(["↩️ " + _sc("CANCEL")])
        await message.reply_text(
            f"<b>🔍 {_sc('Search Results')} ({len(matches)})</b>\n\n{_sc('Tap on a story to view it:')}",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return


# ─────────────────────────────────────────────────────────────────
# Callback Handler
# ─────────────────────────────────────────────────────────────────
async def _process_callback(client, query):
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    data = query.data.split('#')
    cmd = data[1]

    # ── Main Menu actions (inline buttons) ──
    if cmd.startswith("main_"):
        action = cmd.replace("main_", "")
        await query.answer()

        if action == "marketplace":
            platforms = await db.db.premium_stories.distinct('platform', {"bot_id": client.me.id})
            kb = []
            for i in range(0, len(platforms), 2):
                row = platforms[i:i+2]
                kb.append(row)
            if "Other" not in platforms:
                kb.append(["Other"])
            kb.append(["↩️ " + _sc("BACK TO MAIN MENU")])
            await query.message.delete()
            await client.send_message(
                user_id,
                f"<b>🎧 {_sc('Platform Selection')}</b>\n\n{_sc('Choose a platform from the keyboard below:')}",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
            )

        elif action == "profile":
            u = query.from_user
            joined = user.get('joined_date', 'N/A')
            if isinstance(joined, datetime):
                joined = joined.strftime('%d %b %Y')
            purchases = user.get('purchases', [])
            uname = f"@{u.username}" if u.username else "N/A"
            lang_label = "English" if lang == 'en' else "हिंदी"
            txt_p = (
                f"<b>✧⋄⋆⋅⋆⋄✧⋄⋆⋅⋆⋄✧ 👤 {_sc('PROFILE')} ✧⋄⋆⋅⋆⋄✧⋄⋆⋅⋆⋄✧</b>\n\n"
                f"<blockquote expandable>"
                f"<b>{_sc('Name')}:</b> {u.first_name or ''} {u.last_name or ''}\n"
                f"<b>{_sc('Username')}:</b> {uname}\n"
                f"<b>{_sc('Telegram ID')}:</b> <code>{u.id}</code>\n"
                f"<b>{_sc('Total Purchases')}:</b> {len(purchases)}\n"
                f"<b>{_sc('Language')}:</b> {lang_label}\n"
                f"<b>{_sc('Join Date')}:</b> {joined}"
                f"</blockquote>"
            )
            kb = [
                [InlineKeyboardButton(f"📚 {_sc('Unlocked Stories')} ({len(purchases)})", callback_data="mb#my_buys")],
                [InlineKeyboardButton(f"🌐 {_sc('Language')}", callback_data="mb#main_settings")],
                [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_back")]
            ]
            await _safe_edit(query.message, text=txt_p, markup=InlineKeyboardMarkup(kb))

        elif action == "settings":
            kb = [
                [InlineKeyboardButton("English", callback_data="mb#lang#en"),
                 InlineKeyboardButton("हिंदी", callback_data="mb#lang#hi")],
                [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_back")]
            ]
            await _safe_edit(query.message, text=f"<b>⚙️ {_sc('Settings')}</b>\n\n{_sc('Select your language:')}", markup=InlineKeyboardMarkup(kb))

        elif action == "help":
            kb = [
                [InlineKeyboardButton(f"📜 {_sc('TERMS')}", callback_data="mb#help_tc"),
                 InlineKeyboardButton(f"🔁 {_sc('REFUND POLICY')}", callback_data="mb#help_refund")],
                [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_back")]
            ]
            help_txt = (
                f"<b>ℹ️ {_sc('HELP & SUPPORT')}</b>\n\n"
                f"<blockquote expandable>"
                f"{_sc('For issues with payments, missing episodes, or story delivery, contact the bot administrator.')}\n\n"
                f"{_sc('Use the buttons below to read our Terms & Conditions or Refund Policy.')}"
                f"</blockquote>"
            )
            await _safe_edit(query.message, text=help_txt, markup=InlineKeyboardMarkup(kb))

        elif action == "close":
            await query.message.delete()



        elif action == "back":
            await _edit_main_menu_in_place(client, query, query.from_user, lang)

    elif cmd == "return_main":
        await _edit_main_menu_in_place(client, query, query.from_user, lang)
        return

    elif cmd == "show_tc":
        s_id = data[2]
        try:
            await query.message.delete()
        except:
            pass
        return await _show_tc(client, user_id, s_id, lang)

    # ── My Buys ──
    elif cmd == "my_buys":
        await query.answer()
        purchases = user.get('purchases', [])
        from bson.objectid import ObjectId
        kb = []
        for pid in purchases:
            try:
                st = await db.db.premium_stories.find_one({"_id": ObjectId(pid)})
                if st:
                    s_name = st.get(f'story_name_{lang}', st.get('story_name_en'))
                    kb.append([InlineKeyboardButton(f"{_sc(s_name)}", callback_data=f"mb#access_{pid}")])
            except Exception:
                pass
        kb.append([InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_profile")])

        txt_b = f"<b>{_sc('UNLOCKED STORIES')} ({len(purchases)})</b>\n\n"
        if purchases:
            txt_b += (
                "<blockquote>"
                + _sc(
                    "ALL STORIES LISTED BELOW ARE ALREADY UNLOCKED ON YOUR ACCOUNT. "
                    "SELECT ANY STORY TO ACCESS IT AGAIN INSTANTLY. "
                    "NO ADDITIONAL PAYMENT IS REQUIRED."
                )
                + "</blockquote>"
            )
        else:
            txt_b += (
                "<blockquote>"
                + _sc(
                    "YOU HAVE NO UNLOCKED STORIES YET. "
                    "OPEN MARKETPLACE, CHOOSE A STORY, AND COMPLETE PAYMENT TO SEE IT HERE."
                )
                + "</blockquote>"
            )
        await _safe_edit(query.message, text=txt_b, markup=InlineKeyboardMarkup(kb))

    # ── Language ──
    elif cmd == "lang":
        new_lang = data[2]
        await db.update_user(user_id, {"lang": new_lang})
        await query.answer("Language Updated!")
        await _edit_main_menu_in_place(client, query, query.from_user, new_lang)

    # ── Story preview Continue button ──
    elif cmd.startswith("story_preview_continue_"):
        s_id = cmd.replace("story_preview_continue_", "")
        await query.answer()
        await query.message.delete()
        return await _show_tc(client, user_id, s_id, lang)

    # ── T&C Accept ──
    elif cmd.startswith("tc_accept_"):
        s_id = cmd.replace("tc_accept_", "")
        await db.update_user(user_id, {"tc_accepted": True})
        await query.answer("Terms Accepted!")
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if story:
            return await _show_story_details(client, query, story, lang)

    elif cmd == "help_tc":
        await query.answer()
        tc_text = (
            f"<b>\u26a0\ufe0f {_sc('TERMS & CONDITIONS')}</b>\n\n"
            "<blockquote expandable>"
            + _sc("Before purchasing, you must agree to the following:") + "\n\n"
            + _sc("\ud83d\udccc MISSING EPISODES") + "\n"
            + _sc("3\u20135 episodes may be unavailable as they were not publicly released. If they become available later, they will be added. If more than that is missing, contact support and we will try our best to resolve it.") + "\n\n"
            + _sc("\ud83d\udccc QUALITY") + "\n"
            + _sc("Some older recorded episodes may have reduced audio/video quality. We cannot guarantee 100% quality, but we always try to provide the best available version.") + "\n\n"
            + _sc("\ud83d\udccc ORDER") + "\n"
            + _sc("Episodes may rarely arrive out of sequence. We are not responsible for ordering issues, but this usually does not happen. All files come with Arya Bot branding and cleaned metadata.") + "\n\n"
            + _sc("\ud83d\udccc NO REFUNDS") + "\n"
            + _sc("Strictly no refunds after payment is confirmed and delivery is initiated.") + "\n\n"
            + _sc("\ud83d\udccc FAKE SCREENSHOTS") + "\n"
            + _sc("Submitting test, fake, wrong, or random payment screenshots will result in a permanent ban from all our groups and channels.")
            + "</blockquote>"
        )
        kb = [[InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_help")]]
        await query.message.edit_text(tc_text, reply_markup=InlineKeyboardMarkup(kb))
    elif cmd == "help_refund":
        await query.answer()
        refund_text = (
            f"<b>🔁 {_sc('REFUND POLICY')}</b>\n\n"
            "<blockquote expandable>"
            + _sc("If you paid an incorrect/extra amount or did not receive the story, you may be eligible for a refund after verification.") + "\n\n"
            + _sc("⚠️ IMPORTANT") + "\n"
            + _sc("We store all data: your profile, payment history, which story you paid for, how much you paid, to whom it was paid, whether you received the channel link or delivery, and how many episodes were delivered.") + "\n\n"
            + _sc("Refund requests are reviewed individually and processed after full verification. Misuse of refund requests will result in a ban.")
            + "</blockquote>"
        )
        kb = [[InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_help")]]
        await query.message.edit_text(refund_text, reply_markup=InlineKeyboardMarkup(kb))

    # ── T&C Reject ──
    elif cmd == "tc_reject":
        await query.answer("Cancelled.", show_alert=False)
        await query.message.edit_text(
            "<b>❌ Purchase Cancelled</b>\n\n<i>You have rejected the Terms & Conditions. You can start over anytime from the Marketplace.</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"↩️ ❮ {_sc('MAIN MENU')}", callback_data="mb#main_back")]])
        )

    # ── Back (inline) ──
    elif cmd.startswith("show_tc#"):
        s_id = cmd.split("#")[1]
        try:
            await query.message.delete()
        except:
            pass
        return await _show_tc(client, user_id, s_id, lang)

    elif cmd == "back":
        await query.message.delete()

    # ── Access purchased story directly ──
    elif cmd.startswith("access_"):
        s_id = data[2] if len(data) > 2 else cmd.replace("access_", "")
        await query.answer()
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if story:
            return await dispatch_delivery_choice(client, user_id, story)

    # ── View story (from inline button if any) ──
    elif cmd.startswith("view_") or cmd == "view":
        from bson.objectid import ObjectId
        s_id = data[2] if cmd == "view" else cmd.replace("view_", "")
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if not story: return await query.answer("Story not found!", show_alert=True)

        has_paid = await db.has_purchase(user_id, s_id)
        if has_paid:
            await query.answer("You already own this!", show_alert=True)
            return await dispatch_delivery_choice(client, user_id, story)

        await query.message.delete()
        # Show profile/description card first (with expandable quote), then user can continue to T&C.
        return await _show_story_profile(client, user_id, story, lang)

    # ── Pay ──
    elif cmd == "pay":
        method = data[2]
        s_id = data[3]

        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if not story: return await query.answer("Story not found!", show_alert=True)

        if method in ["razorpay", "easebuzz"]:
            await query.message.edit_text("<i>⏳ Generating secure payment link...</i>")
            import time
            # Max length for Razorpay reference_id is 40. 
            ref_id = f"st_{user_id}_{int(time.time())}"
            price = int(story["price"])
            desc = f"Story: {story.get('story_name_en', 'Premium Content')}"
            
            pl_id = None
            url = None
            if method == "razorpay":
                url, pl_id = await _create_rzp_link(price, desc, ref_id, user.get('first_name', "User"))
            else:
                url, pl_id = await _create_easebuzz_link(price, desc, ref_id, user.get('first_name', "User"))
            
            if not url or (method == "razorpay" and not url.startswith("http")):
                # If url is None, pl_id actually contains the error string now
                empty_key_msg = f"{method.capitalize()} API keys not found in .env!"
                err_msg = pl_id if pl_id else empty_key_msg
                return await query.message.edit_text(f"❌ Could not generate API link for <b>{method}</b>.\n\n<code>{err_msg}</code>\n\nPlease check your .env configuration. For now, try Manual UPI.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_back")]]))

            await db.db.premium_checkout.update_one(
                {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)},
                {"$set": {
                    "status": "pending_gateway",
                    "bot_username": client.me.username,
                    "method": method,
                    "payment_id": pl_id,
                    "amount": price,
                    "pay_link_copy": url,
                    "updated_at": datetime.utcnow(),
                }, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )
            
            kb = [
                [InlineKeyboardButton(f"💳 {_sc('PAY VIA')} {_sc(method.upper())}", url=url)],
                [InlineKeyboardButton(f"✅ {_sc('VERIFY PAYMENT')}", callback_data=f"mb#{method}_check#{s_id}")],
                [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#return_main")]
            ]
            await query.message.edit_text(
                f"<b>💳 Secure {method.capitalize()} Checkout</b>\n\nAmount: ₹{price}\nClick below to pay securely. After payment, click <b>Verify Payment</b> to receive your story automatically.",
                reply_markup=InlineKeyboardMarkup(kb)
            )

        elif method == "upi":
            upi_id = await db.get_config("upi_id") or "heyjeetx@naviaxis"
            bt = await db.db.premium_bots.find_one({"id": client.me.id})
            bt_cfg = bt.get("config", {}) if bt else {}
            # IMPORTANT:
            # - Do not fallback to bot display name for pn, it causes payer-app mismatch alerts.
            # - Leave pn empty unless admin explicitly sets real beneficiary name in config.upi_name.
            payee_name = (bt_cfg.get("upi_name") or "").strip()
            # Keep note neutral; user-id heavy notes can trigger anti-fraud checks in some UPI apps.
            note = "Story purchase"
            upi_uri = _build_upi_uri(
                upi_id=upi_id,
                payee_name=payee_name,
                amount=int(story["price"]),
                note=note
            )

            logo_file_id = (bt_cfg.get("logo") or "").strip()
            logo_bytes = None
            if logo_file_id:
                try:
                    bio = await client.download_media(logo_file_id, in_memory=True)
                    if bio:
                        logo_bytes = bio.getvalue() if hasattr(bio, "getvalue") else None
                except Exception:
                    logo_bytes = None

            qr_png = None
            try:
                qr_png = _make_qr_png_bytes(upi_uri, logo_png_bytes=logo_bytes)
            except Exception:
                qr_png = None

            # Strict SliceURL-only mode: no /r fallback.
            slice_api_url = (getattr(Config, "SLICEURL_API_URL", "") or "").strip()
            slice_api_key = (getattr(Config, "SLICEURL_API_KEY", "") or "").strip()
            slice_direct = ""
            if slice_api_url and slice_api_key.startswith("slc_"):
                slice_direct = await _sliceurl_api_shorten(upi_uri)
            button_url = slice_direct

            # Save checkout BEFORE sending UI.
            await db.db.premium_checkout.update_one(
                {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)},
                {"$set": {
                    "status": "waiting_screenshot",
                    "bot_username": client.me.username,
                    "method": "upi",
                    "upi_uri": upi_uri,
                    "upi_open_https": "",
                    "sliceurl_direct": bool(slice_direct),
                    "pay_link_copy": button_url,
                    "updated_at": datetime.utcnow(),
                }, "$setOnInsert": {"created_at": datetime.utcnow()}},
                upsert=True
            )

            txt = (
                T[lang]['qr_msg'].format(price=story['price'])
                + "\n\n<b>✅ Tap “Open UPI App” below</b> — amount and payee are prefilled.\n"
                + "<i>Or scan the QR. “Copy payment link” is your short SliceURL link (no UPI ID shown).</i>"
            )
            if not button_url:
                txt += (
                    "\n\n⚠️ <i>SliceURL short link unavailable.</i>\n"
                    "<i>Set valid <code>SLICEURL_API_URL</code> + <code>SLICEURL_API_KEY</code> in .env "
                    "and deploy latest SliceURL <b>api-public</b> with UPI support.</i>"
                )

            open_btn = InlineKeyboardButton(f"✅ {_sc('OPEN UPI APP')}", url=button_url) if button_url else None
            kb = []
            if open_btn:
                kb.append([open_btn])
            if button_url:
                kb.append([InlineKeyboardButton(f"📋 {_sc('COPY PAYMENT LINK')}", callback_data=f"mb#pay_link#{s_id}")])
            kb.append([InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#back")])
            await query.message.delete()
            try:
                if qr_png:
                    await client.send_photo(user_id, photo=io.BytesIO(qr_png), caption=txt, reply_markup=InlineKeyboardMarkup(kb))
                else:
                    import urllib.parse
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=900x900&margin=1&data={urllib.parse.quote(upi_uri)}"
                    await client.send_photo(user_id, photo=qr_url, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
            except Exception as e:
                logger.warning(f"UPI payment screen send failed, retrying without Open button: {e}")
                kb2 = []
                if button_url:
                    kb2.append([InlineKeyboardButton(f"📋 {_sc('COPY PAYMENT LINK')}", callback_data=f"mb#pay_link#{s_id}")])
                kb2.append([InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#back")])
                if qr_png:
                    await client.send_photo(user_id, photo=io.BytesIO(qr_png), caption=txt + "\n\n⚠️ <i>Open-app button failed; use QR or copy link.</i>", reply_markup=InlineKeyboardMarkup(kb2))
                else:
                    import urllib.parse
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=900x900&margin=1&data={urllib.parse.quote(upi_uri)}"
                    await client.send_photo(user_id, photo=qr_url, caption=txt + "\n\n⚠️ <i>Open-app button failed; use QR or copy link.</i>", reply_markup=InlineKeyboardMarkup(kb2))

    elif cmd.endswith("_check") and cmd.split("_")[0] in ("razorpay", "easebuzz"):
        s_id = data[2] if len(data) > 2 else None
        if not s_id: return await query.answer("Invalid.", show_alert=True)
        method = cmd.split("_")[0]
        
        from bson.objectid import ObjectId
        checkout = await db.db.premium_checkout.find_one(
            {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id), "status": "pending_gateway"}
        )
        if not checkout or not checkout.get("payment_id"):
            return await query.answer("No pending payment found. Generate link again.", show_alert=True)
        
        await query.answer("Checking payment status... please wait.", show_alert=False)
        m = await query.message.edit_text(f"<i>⏳ Verifying {method.capitalize()} payment...</i>")
        
        status = "failed"
        if method == "razorpay":
            status = await _check_rzp_status(checkout["payment_id"])
        else:
            status = await _check_easebuzz_status(checkout["payment_id"], checkout.get("amount", 0))
            
        if status == "paid":
            # Confirmed!
            await db.db.premium_checkout.update_one(
                {"_id": checkout["_id"]},
                {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
            )
            # Send notification
            await m.edit_text("✅ <b>Payment Confirmed successfully!</b>\nAdding to your unlocked stories...")
            
            # Use utility db function to add purchase 
            story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
            
            if not await db.has_purchase(user_id, str(s_id)):
                await db.db.premium_purchases.insert_one({
                    "user_id": user_id,
                    "story_id": ObjectId(s_id),
                    "bot_id": client.me.id,
                    "purchased_at": datetime.utcnow(),
                    "source": method
                })

            return await dispatch_delivery_choice(client, user_id, story)
            
        else:
            await query.answer(f"Payment not completed yet (Status: {status}). Please pay and try again.", show_alert=True)
            # Revert to payment button state
            kb = [
                [InlineKeyboardButton(f"💳 {_sc('PAY VIA')} {_sc(method.upper())}", url=checkout.get("pay_link_copy", "https://t.me"))] if "pay_link_copy" in checkout else [],
                [InlineKeyboardButton(f"✅ {_sc('VERIFY PAYMENT')}", callback_data=f"mb#{method}_check#{s_id}")],
                [InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#return_main")]
            ]
            # Since url is not strictly saved, we might have lost it.
            # actually we didn't save the short url in db in the first replacement chunk. Let's fix that below if needed, but for now just show a simple back button.
            await m.edit_text(
                f"<b>❌ Payment Not Found</b>\nStatus: <code>{status}</code>\nIf you have paid, please wait a minute and verify again.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Verify Again", callback_data=f"mb#{method}_check#{s_id}")], [InlineKeyboardButton("↩️ Back", callback_data=f"mb#show_tc#{s_id}")]])
            )

    elif cmd in ("pay_link", "upi_uri"):
        # Copy SliceURL short link only (strict mode).
        s_id = data[2] if len(data) > 2 else None
        if not s_id:
            return await query.answer("Invalid request.", show_alert=True)
        from bson.objectid import ObjectId
        checkout = await db.db.premium_checkout.find_one(
            {"user_id": user_id, "bot_id": client.me.id, "story_id": ObjectId(s_id)}
        )
        link = (checkout or {}).get("pay_link_copy") or ""
        if not link and (checkout or {}).get("upi_uri"):
            link = await _sliceurl_api_shorten(checkout["upi_uri"])
        if not link:
            return await query.answer("SliceURL link unavailable. Check SLICEURL_API_URL/KEY and API deploy.", show_alert=True)
        await query.answer()
        await client.send_message(
            user_id,
            "🔗 <b>Payment link</b> — open in browser; it will launch UPI with amount filled.\n"
            f"<code>{link}</code>",
        )

    # ── Delivery choice (DM vs Channel) - handled via callbacks now ──
    elif cmd == "deliver_dm":
        s_id = data[2]
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if not story: return await query.answer("Story not found!", show_alert=True)
        await query.answer()
        await query.message.edit_text(
            "<i>⏳ Starting DM Delivery... Please wait while we fetch all your files.</i>",
            reply_markup=None
        )
        asyncio.create_task(_do_dm_delivery(client, user_id, story, query.message))

    elif cmd == "deliver_channel":
        s_id = data[2]
        from bson.objectid import ObjectId
        story = await db.db.premium_stories.find_one({"_id": ObjectId(s_id)})
        if not story: return await query.answer("Story not found!", show_alert=True)
        await query.answer()
        await query.message.edit_text("<i>⏳ Generating secure 1-time channel link...</i>", reply_markup=None)
        asyncio.create_task(_do_channel_delivery(client, user_id, story, query.message))

    # ── Notify Admin ──
    elif cmd == "notify_admin":
        await query.answer("Admin has been notified. Please wait patiently.", show_alert=True)
        admins = Config.SUDO_USERS or Config.OWNER_IDS
        if not admins:
            return
        for admin in admins:
            try:
                await client.send_message(
                    admin,
                    f"🔔 <b>URGENT PING:</b>\nUser <code>{user_id}</code> is waiting for Payment Validation!\nCheck the Pending queue in Management Bot."
                )
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────
# Screenshot Handler
# ─────────────────────────────────────────────────────────────────
async def _process_screenshot(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')

    checkout = await db.db.premium_checkout.find_one(
        {"user_id": user_id, "bot_id": client.me.id, "status": "waiting_screenshot"}
    )
    if not checkout: return

    # Fake Detection
    p = message.photo
    if p.file_size < 50000:
        return await message.reply_text("❌ <b>Invalid Screenshot!</b>\n\nThe image is too small. Please send a clear, full payment screenshot.", quote=True)
    if p.height < p.width:
        return await message.reply_text("❌ <b>Invalid Screenshot!</b>\n\nPlease send a portrait-mode screenshot (not landscape).", quote=True)

    kb_user = [[InlineKeyboardButton(T[lang]['notify'], callback_data="mb#notify_admin")]]
    txt_user = f"<code>[==========]</code>\n\n{T[lang]['wait_ver']}\n⏳ <b>Live Status:</b> Starting verification..."
    msg = await message.reply_text(txt_user, reply_markup=InlineKeyboardMarkup(kb_user))

    import os
    if not os.path.exists("downloads"): os.makedirs("downloads")
    file_path = await client.download_media(message, file_name=f"downloads/proof_{checkout['_id']}.jpg")
    await db.db.premium_checkout.update_one(
        {"_id": checkout["_id"]},
        {"$set": {
            "status": "pending_admin_approval",
            "proof_path": file_path,
            "proof_file_id": message.photo.file_id,
            "status_msg_id": msg.id,
            "paid_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )

    async def _live_timer(target_msg, remaining):
        try:
            for i in range(remaining, 0, -30):
                m = i // 60
                s = i % 60
                filled = 10 - int((i / remaining) * 10)
                bar = "=" * filled + "-" * (10 - filled)
                await target_msg.edit_text(
                    f"<code>[{bar}]</code>\n\n{T[lang]['wait_ver']}\n⏳ <b>Time Remaining:</b> {m}m {s}s",
                    reply_markup=InlineKeyboardMarkup(kb_user)
                )
                await asyncio.sleep(30)
            await target_msg.edit_text(
                f"<code>[==========]</code>\n\n{T[lang]['wait_ver']}\n⏳ <b>Verification delayed. Click Notify Admin.</b>",
                reply_markup=InlineKeyboardMarkup(kb_user)
            )
        except Exception:
            pass

    asyncio.create_task(_live_timer(msg, 300))


# ─────────────────────────────────────────────────────────────────
# Delivery Choice (now fully Inline — no native_ask needed!)
# ─────────────────────────────────────────────────────────────────
async def dispatch_delivery_choice(client, user_id, story):
    """
    Called when Admin approves OR user already owns. Shows inline delivery options.
    """
    user = await db.get_user(user_id)
    lang = user.get('lang', 'en')
    story_id_str = str(story['_id'])

    used_channels = user.get("used_channels", [])
    mode = story.get("delivery_mode") or ("single" if story.get("channel_id") else "pool")
    fallback = await db.db.premium_channels.find_one({"type": "delivery"})
    pool = story.get("channel_pool") or []
    has_any_delivery = bool(story.get('channel_id') or pool or (fallback and fallback.get("channel_id")))
    can_use_channel = (story_id_str not in used_channels) and (mode != "dm_only") and has_any_delivery

    del_txt = (
        "<b>✅ Access Granted!</b>\n\n"
        "<blockquote expandable><b>ℹ️ Delivery Info</b>\n\n"
        "• <b>DM Delivery:</b> Files are sent directly here. Save or forward them immediately—they auto-delete after some time.\n"
        "• <b>Channel Link:</b> A 1-time private invite link is generated. Each story allows only ONE channel link per account.\n"
        "• <b>Lifetime Access:</b> You can re-access any purchased story anytime from Profile → My Buys."
        "</blockquote>\n\n"
        "How would you like to receive your files?"
    ) if lang == 'en' else (
        "<b>✅ पहुँच स्वीकृत!</b>\n\nआप अपनी फ़ाइलें कैसे प्राप्त करना चाहेंगे?"
    )

    kb = [[InlineKeyboardButton(f"📥 {_sc('RECEIVE IN DM')}", callback_data=f"mb#deliver_dm#{story_id_str}")]]
    if can_use_channel:
        kb.append([InlineKeyboardButton(f"🔗 {_sc('ACCESS CHANNEL LINK')}", callback_data=f"mb#deliver_channel#{story_id_str}")])
    kb.append([InlineKeyboardButton(f"↩️ ❮ {_sc('BACK')}", callback_data="mb#main_back")])

    await client.send_message(user_id, del_txt, reply_markup=InlineKeyboardMarkup(kb))


# ─────────────────────────────────────────────────────────────────
# DM Delivery (Arya-style: copy messages from source channel)
# ─────────────────────────────────────────────────────────────────
async def _do_dm_delivery(client, user_id, story, status_msg=None):
    try:
        bt = await db.db.premium_bots.find_one({"id": client.me.id})
        bt_cfg = bt.get("config", {}) if bt else {}
        user_obj = await client.get_users(user_id)
        src = story.get('source')
        start = story.get('start_id')
        end = story.get('end_id')
        lang_user = (await db.get_user(user_id)).get('lang', 'en')

        if not src or not start or not end:
            await client.send_message(user_id, "❌ Story file range is not configured correctly. Please contact admin.")
            return

        # Send warning first
        await client.send_message(
            user_id,
            "<i>⚠️ <b>Important:</b> Files below will be auto-deleted after some time to avoid copyright flags.\n"
            "Save or forward them immediately! You can re-access this story anytime from Profile → My Buys.</i>"
        )

        sent_count = 0
        failed_count = 0
        sent_ids = []
        cap_tpl = bt_cfg.get("caption", "")
        for msg_id in range(int(start), int(end) + 1):
            try:
                kwargs = dict(
                    chat_id=user_id,
                    from_chat_id=int(src),
                    message_id=msg_id,
                    protect_content=False,
                )
                if cap_tpl:
                    kwargs["caption"] = _fmt_delivery_text(cap_tpl, user_obj, story)
                sent = await client.copy_message(**kwargs)
                sent_ids.append(sent.id)
                sent_count += 1
            except Exception as e:
                logger.warning(f"DM Delivery failed msg {msg_id}: {e}")
                failed_count += 1
            await asyncio.sleep(0.08)  # Rate limit buffer

        s_name = story.get('story_name_en', 'Story')
        suc_tpl = (bt_cfg.get("success_msg") or "").strip()
        if suc_tpl:
            summary = _fmt_delivery_text(
                suc_tpl,
                user_obj,
                story,
                sent_count=sent_count,
                fail_count=failed_count,
            )
        else:
            summary = (
                f"🎉 <b>Delivery Complete!</b>\n\n"
                f"📖 <b>{s_name}</b>\n"
                f"✅ {sent_count} files sent"
                + (f"\n⚠️ {failed_count} files failed (may not exist in source)" if failed_count else "")
                + "\n\n<i>Access this story again anytime from your Profile → My Buys.</i>"
            )
        notice = await client.send_message(user_id, summary)

        try:
            autodel = int(str(bt_cfg.get("autodel", "0")).strip() or "0")
        except Exception:
            autodel = 0
        if autodel > 0 and sent_ids:
            del_tpl = (bt_cfg.get("delete_msg") or "").strip()
            if del_tpl:
                try:
                    await client.send_message(
                        user_id,
                        _fmt_delivery_text(
                            del_tpl,
                            user_obj,
                            story,
                            sent_count=sent_count,
                            fail_count=failed_count,
                        ).replace("{time}", str(autodel)),
                    )
                except Exception:
                    pass
            asyncio.create_task(_delete_later(client, user_id, sent_ids + [notice.id], autodel))

    except Exception as e:
        logger.error(f"DM Delivery error: {e}")
        await client.send_message(user_id, f"❌ Delivery failed: {e}\n\nPlease contact admin.")


# ─────────────────────────────────────────────────────────────────
# Channel Link Delivery
# ─────────────────────────────────────────────────────────────────
async def _do_channel_delivery(client, user_id, story, status_msg=None):
    story_id_str = str(story['_id'])
    try:
        bt = await db.db.premium_bots.find_one({"id": client.me.id})
        bt_cfg = bt.get("config", {}) if bt else {}
        mode = story.get("delivery_mode") or ("single" if story.get("channel_id") else "pool")
        if mode == "dm_only":
            await client.send_message(user_id, "ℹ️ This story is configured for DM delivery only.")
            return await _do_dm_delivery(client, user_id, story)

        # Build candidate pool for rotation/failover
        candidates = []
        if story.get("channel_id"):
            candidates.append(int(story["channel_id"]))
        if isinstance(story.get("channel_pool"), list):
            for cid in story["channel_pool"]:
                try:
                    candidates.append(int(cid))
                except Exception:
                    pass
        if not candidates:
            # fallback to global delivery list
            globals_ = await db.db.premium_channels.find({"type": "delivery"}).to_list(length=300)
            candidates = [int(c["channel_id"]) for c in globals_]

        if not candidates:
            await client.send_message(user_id, "❌ No delivery channels are configured. Falling back to DM delivery...")
            return await _do_dm_delivery(client, user_id, story)

        # Round-robin start index (stored in premium_settings)
        try:
            rr = await db.db.premium_settings.find_one_and_update(
                {"_id": "delivery_rr"},
                {"$inc": {"idx": 1}},
                upsert=True,
                return_document=True,
            )
            start_idx = int((rr or {}).get("idx", 0)) % len(candidates)
        except Exception:
            start_idx = 0

        def _rot(lst, s):
            return lst[s:] + lst[:s]

        channel_id = None
        last_err = None
        for cid in _rot(candidates, start_idx)[: min(25, len(candidates))]:
            try:
                # Validate bot can access/create link
                invite_link = await client.create_chat_invite_link(
                    int(cid),
                    member_limit=1,
                    name=f"user_{user_id}"
                )
                channel_id = int(cid)
                break
            except Exception as e:
                last_err = e
                continue

        if not channel_id:
            await client.send_message(user_id, f"❌ Failed to generate invite link from delivery pool. Falling back to DM.\n<i>{last_err}</i>")
            return await _do_dm_delivery(client, user_id, story)

        # We already created invite_link in loop above when selecting channel_id
        # Create again to get the link object (safe if already created)
        invite_link = await client.create_chat_invite_link(int(channel_id), member_limit=1, name=f"user_{user_id}")
        # Mark this user as having used their channel link
        await db.db.users.update_one(
            {"id": int(user_id)},
            {"$addToSet": {"used_channels": story_id_str}}
        )

        s_name = story.get('story_name_en', 'Story')
        suc_tpl = (bt_cfg.get("success_msg") or "").strip()
        if suc_tpl:
            user_obj = await client.get_users(user_id)
            txt = _fmt_delivery_text(suc_tpl, user_obj, story).replace("{channel_link}", invite_link.invite_link)
        else:
            txt = (
                f"🎉 <b>Your 1-Time Access Link is Ready!</b>\n\n"
                f"📖 <b>{s_name}</b>\n\n"
                f"🔗 {invite_link.invite_link}\n\n"
                f"<i>⚠️ This link works for exactly <b>1 person only</b>. Once used, it expires.\n"
                f"Future access to this story will be via DM Delivery only.</i>"
            )
        await client.send_message(user_id, txt, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Channel Link Error: {e}")
        await client.send_message(
            user_id,
            f"❌ Failed to generate channel link. Falling back to DM Delivery...\n<i>Error: {e}</i>"
        )
        await _do_dm_delivery(client, user_id, story)
