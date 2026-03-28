import asyncio
from pyrogram import Client
from config import Config

async def main():
    bot = Client("bot", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
    await bot.start()
    
    # Send a message to the bot owner to ensure there's at least one message
    chat_id = Config.BOT_OWNER_ID[0]
    msg = await bot.send_message(chat_id, "Testing DM queries.")
    
    mid = msg.id
    print(f"Sent message ID: {mid}")
    
    # Try fetching it
    res = await bot.get_messages(chat_id, [mid, mid - 1, mid - 2])
    print("Fetched:", [m.id for m in res if m and not m.empty])
    
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
