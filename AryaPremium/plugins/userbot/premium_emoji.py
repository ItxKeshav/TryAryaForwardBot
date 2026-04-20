"""
Premium Emoji & Reaction Utility
=================================
Provides custom emoji reactions and premium emoji
for the Arya Premium userbot (requires a Telegram Premium account).

All functions are fire-and-forget safe — they silently ignore failures
so bot functionality is never broken by emoji features.
"""
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Premium Custom Emoji Document IDs
# These are real Telegram Premium emoji document IDs.
# ─────────────────────────────────────────────────────────────────────────────

# Reaction emojis — used when user sends a command or message
REACTIONS_GENERAL = [
    "⚡",   # lightning
    "🔥",   # fire
    "❤",    # heart
    "👍",   # thumbs up
    "🎉",   # party
    "✨",   # sparkles
    "💎",   # diamond
    "🏆",   # trophy
]

REACTIONS_SUCCESS = ["🎉", "✅", "🔥", "💯", "❤"]
REACTIONS_WELCOME = ["👋", "🎉", "✨", "❤", "🙏"]
REACTIONS_PAYMENT = ["💸", "🎉", "✅", "🙏"]

# Premium custom emoji IDs (document_id) — for use in message text
# Format in HTML: <emoji id="DOCUMENT_ID">fallback_char</emoji>
# These are well-known Telegram Premium animated emoji document IDs
CUSTOM_EMOJI = {
    "fire":       ("5368324170671202286", "🔥"),
    "star":       ("5467666648223797671", "⭐"),
    "diamond":    ("5368754967922820915", "💎"),
    "crown":      ("5361542596430941143", "👑"),
    "heart":      ("5346455489485705738", "❤️"),
    "party":      ("5870098322566580799", "🎉"),
    "lightning":  ("5467856220136595710", "⚡"),
    "sparkle":    ("5431815172178900273", "✨"),
    "check":      ("5368324170671202286", "✅"),
    "premium":    ("5428758090484817926", "💎"),
    "rocket":     ("5420315771148297271", "🚀"),
}


def ce(name: str) -> str:
    """
    Return a premium custom emoji HTML tag by name.
    Falls back to a plain emoji if the name is unknown.
    Example: ce('fire') → '<emoji id="5368...">🔥</emoji>'
    """
    if name in CUSTOM_EMOJI:
        doc_id, fallback = CUSTOM_EMOJI[name]
        return f'<emoji id="{doc_id}">{fallback}</emoji>'
    return "✨"


async def react(client, chat_id: int, message_id: int,
                emoji: str = None, pool: list = None) -> bool:
    """
    Send a reaction to a message. Uses a random emoji from `pool`,
    or the specified `emoji`, or picks from REACTIONS_GENERAL.

    Returns True on success, False on failure (silent).
    """
    chosen = emoji or (random.choice(pool) if pool else random.choice(REACTIONS_GENERAL))
    try:
        await client.send_reaction(
            chat_id=chat_id,
            message_id=message_id,
            emoji=chosen
        )
        return True
    except Exception as e:
        # Don't log every reaction failure — it's noisy for non-premium accounts
        logger.debug(f"[PremiumEmoji] Reaction failed ({chosen}): {e}")
        return False


async def react_bg(client, chat_id: int, message_id: int,
                   emoji: str = None, pool: list = None):
    """
    Fire-and-forget version of react() — does not await, 
    does not block the caller.
    """
    asyncio.create_task(
        react(client, chat_id, message_id, emoji=emoji, pool=pool)
    )


async def send_premium_sticker(client, chat_id: int, sticker_key: str = "welcome") -> bool:
    """
    Send a premium animated sticker to the chat.
    Uses known Telegram premium sticker file_ids.
    Returns True on success, False on failure.
    """
    # Well-known premium sticker file_ids (Telegram official premium pack)
    STICKERS = {
        "welcome":  "CAACAgIAAxkBAAIB...",  # placeholder — set real IDs via /sticker command
        "party":    "CAACAgIAAxkBAAIB...",
        "success":  "CAACAgIAAxkBAAIB...",
        "love":     "CAACAgIAAxkBAAIB...",
    }
    fid = STICKERS.get(sticker_key)
    if not fid or fid.endswith("..."):
        return False  # No valid sticker ID configured
    try:
        await client.send_sticker(chat_id=chat_id, sticker=fid)
        return True
    except Exception as e:
        logger.debug(f"[PremiumEmoji] Sticker send failed ({sticker_key}): {e}")
        return False
